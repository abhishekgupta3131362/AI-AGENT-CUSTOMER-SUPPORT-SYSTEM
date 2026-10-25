import re
import math
import hashlib
import json
import numpy as np
from typing import List, Optional
import requests
from backend.config import Config

class EmbeddingEngine:
    """
    Pluggable embedding generator:
    - Provides high-dimension semantic hash & n-gram TF-IDF vectorization locally (zero C++ dependencies).
    - Can optionally generate OpenAI or Gemini embeddings when configured.
    """
    def __init__(self, vector_dim: int = 256):
        self.vector_dim = vector_dim

    def _stem(self, word: str) -> str:
        """Lightweight morphological stemmer for English suffixes."""
        for suffix in ['ing', 'ies', 'es', 'ed', 's']:
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                return word[:-len(suffix)]
        return word

    def _tokenize(self, text: str) -> List[str]:
        cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', text.lower())
        raw_words = [t for t in cleaned.split() if len(t) > 1]
        
        # Word stems
        stems = [self._stem(w) for w in raw_words]
        
        # Word bigrams
        bigrams = [f"{stems[i]}_{stems[i+1]}" for i in range(len(stems) - 1)]
        
        # Subword 3-grams & 4-grams (FastText style for semantic fuzzy matching)
        char_ngrams = []
        for w in raw_words:
            if len(w) >= 3:
                for i in range(len(w) - 2):
                    char_ngrams.append(f"#{w[i:i+3]}")
            if len(w) >= 4:
                for i in range(len(w) - 3):
                    char_ngrams.append(f"#{w[i:i+4]}")

        return raw_words + stems + bigrams + char_ngrams

    def _hash_token(self, token: str) -> int:
        h = hashlib.sha256(token.encode('utf-8')).hexdigest()
        return int(h[:8], 16) % self.vector_dim

    def get_local_embedding(self, text: str) -> List[float]:
        """Generates a normalized semantic pseudo-vector using token hashing + TF-IDF weights."""
        tokens = self._tokenize(text)
        if not tokens:
            return [0.0] * self.vector_dim

        vec = np.zeros(self.vector_dim, dtype=np.float32)
        total_tokens = len(tokens)
        
        for token in tokens:
            idx = self._hash_token(token)
            # Higher weight for longer or specific terms
            weight = 1.0 + (0.3 * len(token) if len(token) > 4 else 0.0)
            vec[idx] += weight

        # Apply sub-linear scaling
        vec = np.log1p(np.maximum(0, vec))

        # L2 Normalization
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        return vec.tolist()

    def get_openai_embedding(self, text: str, api_key: str) -> Optional[List[float]]:
        """Fetches dense embeddings from OpenAI text-embedding-3-small."""
        try:
            url = "https://api.openai.com/v1/embeddings"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "input": text,
                "model": "text-embedding-3-small"
            }
            res = requests.post(url, headers=headers, json=payload, timeout=8)
            if res.status_code == 200:
                data = res.json()
                return data["data"][0]["embedding"]
        except Exception as e:
            print(f"[EmbeddingEngine] OpenAI embedding error: {e}")
        return None

    def get_gemini_embedding(self, text: str, api_key: str) -> Optional[List[float]]:
        """Fetches dense embeddings from Google Gemini text-embedding-004."""
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={api_key}"
            payload = {
                "model": "models/text-embedding-004",
                "content": {"parts": [{"text": text}]}
            }
            res = requests.post(url, json=payload, timeout=8)
            if res.status_code == 200:
                data = res.json()
                return data["embedding"]["values"]
        except Exception as e:
            print(f"[EmbeddingEngine] Gemini embedding error: {e}")
        return None

    def embed_text(self, text: str, provider: Optional[str] = None) -> List[float]:
        """Selects the best available embedding mechanism."""
        prov = (provider or Config.DEFAULT_LLM_PROVIDER).lower()
        if prov == "openai" and Config.OPENAI_API_KEY:
            vec = self.get_openai_embedding(text, Config.OPENAI_API_KEY)
            if vec:
                return vec
        elif prov == "gemini" and Config.GEMINI_API_KEY:
            vec = self.get_gemini_embedding(text, Config.GEMINI_API_KEY)
            if vec:
                return vec

        # Default local semantic vector
        return self.get_local_embedding(text)

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Computes cosine similarity between two vectors."""
    a = np.array(v1, dtype=np.float32)
    b = np.array(v2, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))

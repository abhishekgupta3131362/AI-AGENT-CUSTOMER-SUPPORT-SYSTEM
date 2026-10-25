import json
import uuid
from typing import List, Dict, Any, Optional
from backend.database.db import get_db_connection, query_db, execute_db
from backend.rag.embeddings import EmbeddingEngine, cosine_similarity

class VectorStore:
    def __init__(self):
        self.engine = EmbeddingEngine()

    def chunk_text(self, text: str, max_chunk_size: int = 400, overlap: int = 50) -> List[str]:
        """Simple paragraph and sentence aware text chunker."""
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
        chunks = []
        current_chunk = []
        current_len = 0

        for p in paragraphs:
            words = p.split()
            if current_len + len(words) <= max_chunk_size:
                current_chunk.extend(words)
                current_len += len(words)
            else:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                current_chunk = words
                current_len = len(words)

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks if chunks else [text]

    def add_document(self, title: str, category: str, content: str, doc_id: Optional[str] = None) -> str:
        """Adds and indexes a document with chunks and vector embeddings."""
        if not doc_id:
            doc_id = f"KB-{uuid.uuid4().hex[:8].upper()}"

        # Delete existing chunks for this doc_id if updating
        execute_db("DELETE FROM knowledge_documents WHERE id LIKE ?", (f"{doc_id}%",))

        chunks = self.chunk_text(content)
        for idx, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}-C{idx}" if len(chunks) > 1 else doc_id
            # Compute embedding for chunk
            text_to_embed = f"Title: {title}\nCategory: {category}\nContent: {chunk}"
            embedding = self.engine.embed_text(text_to_embed)
            embedding_json = json.dumps(embedding)

            execute_db(
                """
                INSERT INTO knowledge_documents (id, title, category, content, chunk_index, embedding)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (chunk_id, title, category, chunk, idx, embedding_json)
            )

        return doc_id

    def search(self, query: str, top_k: int = 3, min_similarity: float = 0.10) -> List[Dict[str, Any]]:
        """
        Performs semantic vector search over indexed knowledge base chunks.
        Returns top_k most similar chunks sorted by cosine similarity.
        """
        query_vec = self.engine.embed_text(query)
        rows = query_db("SELECT id, title, category, content, chunk_index, embedding FROM knowledge_documents")

        if not rows:
            return []

        scored_results = []
        for row in rows:
            emb_str = row.get("embedding")
            if not emb_str:
                continue
            try:
                doc_vec = json.loads(emb_str)
                score = cosine_similarity(query_vec, doc_vec)
                if score >= min_similarity:
                    scored_results.append({
                        "id": row["id"],
                        "title": row["title"],
                        "category": row["category"],
                        "content": row["content"],
                        "chunk_index": row["chunk_index"],
                        "similarity": round(score, 4)
                    })
            except Exception as e:
                print(f"[VectorStore] Error parsing embedding: {e}")

        # Sort descending by similarity score
        scored_results.sort(key=lambda x: x["similarity"], reverse=True)
        return scored_results[:top_k]

    def list_documents(self) -> List[Dict[str, Any]]:
        """Lists all distinct knowledge documents."""
        rows = query_db("""
            SELECT id, title, category, content, created_at 
            FROM knowledge_documents 
            WHERE chunk_index = 0
            ORDER BY created_at DESC
        """)
        return rows

    def delete_document(self, doc_id: str) -> bool:
        """Deletes a document and all its chunks."""
        execute_db("DELETE FROM knowledge_documents WHERE id LIKE ?", (f"{doc_id}%",))
        return True

    def reindex_all(self):
        """Re-computes embeddings for all documents stored in the database."""
        docs = query_db("SELECT id, title, category, content FROM knowledge_documents WHERE chunk_index = 0")
        for doc in docs:
            # Extract base id (strip -C0 if present)
            base_id = doc["id"].split("-C")[0]
            self.add_document(doc["title"], doc["category"], doc["content"], doc_id=base_id)

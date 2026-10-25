import json
import requests
from typing import Generator, Optional
from backend.llm.base import BaseLLMProvider
from backend.config import Config

class OllamaProvider(BaseLLMProvider):
    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = (base_url or Config.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or Config.OLLAMA_MODEL or "llama3:8b"

    @property
    def provider_name(self) -> str:
        return "ollama"

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }

        try:
            res = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=45)
            if res.status_code == 200:
                return res.json().get("message", {}).get("content", "")
            return f"Ollama error ({res.status_code}): {res.text}"
        except Exception as e:
            return f"Could not connect to Ollama at {self.base_url}. Make sure Ollama is running ('ollama serve'). Error: {str(e)}"

    def generate_stream(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Generator[str, None, None]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True
        }

        try:
            with requests.post(f"{self.base_url}/api/chat", json=payload, stream=True, timeout=45) as res:
                if res.status_code != 200:
                    yield f"Ollama error ({res.status_code}): {res.text}"
                    return
                for line in res.iter_lines():
                    if line:
                        try:
                            data = json.loads(line.decode('utf-8'))
                            content = data.get("message", {}).get("content", "")
                            if content:
                                yield content
                        except Exception:
                            continue
        except Exception as e:
            yield f"Ollama connection error: {str(e)}"

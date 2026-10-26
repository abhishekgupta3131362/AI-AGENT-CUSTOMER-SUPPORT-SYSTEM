import json
try:
    import requests
except ImportError:
    requests = None
from typing import Generator, Optional
from backend.llm.base import BaseLLMProvider
from backend.config import Config

class GroqProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or Config.GROQ_API_KEY
        self.model = model or Config.GROQ_MODEL or "llama-3.3-70b-versatile"

    @property
    def provider_name(self) -> str:
        return "groq"

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        if not self.api_key:
            return "Error: Groq API key is missing. Please set GROQ_API_KEY in your settings or .env file."

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.2),
            "max_tokens": kwargs.get("max_tokens", 1024),
        }

        try:
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=25)
            if res.status_code == 200:
                data = res.json()
                return data["choices"][0]["message"]["content"]
            return f"Error from Groq API ({res.status_code}): {res.text}"
        except Exception as e:
            return f"Groq connection error: {str(e)}"

    def generate_stream(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Generator[str, None, None]:
        if not self.api_key:
            yield "Error: Groq API key is missing. Please configure it in Settings."
            return

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "temperature": kwargs.get("temperature", 0.2),
        }

        try:
            with requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, stream=True, timeout=30) as res:
                if res.status_code != 200:
                    yield f"Error from Groq API ({res.status_code}): {res.text}"
                    return
                for line in res.iter_lines():
                    if line:
                        decoded = line.decode('utf-8')
                        if decoded.startswith("data: ") and not decoded.startswith("data: [DONE]"):
                            raw_json = decoded[6:]
                            try:
                                data = json.loads(raw_json)
                                delta = data["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                            except Exception:
                                continue
        except Exception as e:
            yield f"Groq streaming error: {str(e)}"

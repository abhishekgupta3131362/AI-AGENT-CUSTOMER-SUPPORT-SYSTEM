import json
try:
    import requests
except ImportError:
    requests = None
from typing import Generator, Optional
from backend.llm.base import BaseLLMProvider
from backend.config import Config

class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or Config.OPENAI_API_KEY
        self.model = model or Config.OPENAI_MODEL or "gpt-4o-mini"

    @property
    def provider_name(self) -> str:
        return "openai"

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        if not self.api_key:
            return "Error: OpenAI API key is missing. Please set OPENAI_API_KEY in your settings or .env file."

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
            "temperature": kwargs.get("temperature", 0.3),
            "max_tokens": kwargs.get("max_tokens", 1024),
        }

        try:
            res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=25)
            if res.status_code == 200:
                data = res.json()
                return data["choices"][0]["message"]["content"]
            return f"Error from OpenAI API ({res.status_code}): {res.text}"
        except Exception as e:
            return f"OpenAI connection error: {str(e)}"

    def generate_stream(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Generator[str, None, None]:
        if not self.api_key:
            yield "Error: OpenAI API key is missing. Please configure it in Settings."
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
            "temperature": kwargs.get("temperature", 0.3),
        }

        try:
            with requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, stream=True, timeout=30) as res:
                if res.status_code != 200:
                    yield f"Error from OpenAI API ({res.status_code}): {res.text}"
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
            yield f"OpenAI streaming error: {str(e)}"

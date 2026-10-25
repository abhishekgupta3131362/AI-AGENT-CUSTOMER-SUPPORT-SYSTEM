import json
import requests
from typing import Generator, Optional
from backend.llm.base import BaseLLMProvider
from backend.config import Config

class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or Config.GEMINI_API_KEY
        self.model = model or Config.GEMINI_MODEL or "gemini-2.5-flash"

    @property
    def provider_name(self) -> str:
        return "gemini"

    def _get_url(self, stream: bool = False) -> str:
        action = "streamGenerateContent?alt=sse&key=" if stream else "generateContent?key="
        return f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:{action}{self.api_key}"

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        if not self.api_key:
            return "Error: Gemini API key is missing. Please set GEMINI_API_KEY in your settings or .env file."
        
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"SYSTEM INSTRUCTIONS:\n{system_prompt}"}]})
            contents.append({"role": "model", "parts": [{"text": "Understood. I will act strictly according to these instructions."}]})
        
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": kwargs.get("temperature", 0.3),
                "maxOutputTokens": kwargs.get("max_tokens", 1024),
            }
        }

        try:
            res = requests.post(self._get_url(stream=False), json=payload, timeout=25)
            if res.status_code == 200:
                data = res.json()
                candidates = data.get("candidates", [])
                if candidates and "content" in candidates[0]:
                    parts = candidates[0]["content"].get("parts", [])
                    return "".join(p.get("text", "") for p in parts)
            return f"Error from Gemini API ({res.status_code}): {res.text}"
        except Exception as e:
            return f"Gemini connection error: {str(e)}"

    def generate_stream(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Generator[str, None, None]:
        if not self.api_key:
            yield "Error: Gemini API key is missing. Please configure it in Settings."
            return

        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"SYSTEM INSTRUCTIONS:\n{system_prompt}"}]})
            contents.append({"role": "model", "parts": [{"text": "Understood. I will act strictly according to these instructions."}]})
        
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": kwargs.get("temperature", 0.3),
                "maxOutputTokens": kwargs.get("max_tokens", 1024),
            }
        }

        try:
            with requests.post(self._get_url(stream=True), json=payload, stream=True, timeout=30) as res:
                if res.status_code != 200:
                    yield f"Error from Gemini API ({res.status_code}): {res.text}"
                    return
                for line in res.iter_lines():
                    if line:
                        decoded = line.decode('utf-8')
                        if decoded.startswith("data: "):
                            raw_json = decoded[6:]
                            try:
                                data = json.loads(raw_json)
                                candidates = data.get("candidates", [])
                                if candidates and "content" in candidates[0]:
                                    parts = candidates[0]["content"].get("parts", [])
                                    for p in parts:
                                        text = p.get("text", "")
                                        if text:
                                            yield text
                            except Exception:
                                continue
        except Exception as e:
            yield f"Gemini streaming error: {str(e)}"

from typing import Optional, Dict
from backend.config import Config
from backend.llm.base import BaseLLMProvider
from backend.llm.gemini_provider import GeminiProvider
from backend.llm.openai_provider import OpenAIProvider
from backend.llm.groq_provider import GroqProvider
from backend.llm.ollama_provider import OllamaProvider
from backend.llm.demo_provider import DemoProvider

class LLMFactory:
    _current_provider_name: str = Config.DEFAULT_LLM_PROVIDER
    _providers: Dict[str, BaseLLMProvider] = {}

    @classmethod
    def get_provider(cls, name: Optional[str] = None) -> BaseLLMProvider:
        prov_name = (name or cls._current_provider_name).lower()
        
        if prov_name not in cls._providers:
            if prov_name == "gemini":
                cls._providers[prov_name] = GeminiProvider()
            elif prov_name == "openai":
                cls._providers[prov_name] = OpenAIProvider()
            elif prov_name == "groq":
                cls._providers[prov_name] = GroqProvider()
            elif prov_name == "ollama":
                cls._providers[prov_name] = OllamaProvider()
            else:
                cls._providers["demo"] = DemoProvider()
                return cls._providers["demo"]
                
        return cls._providers[prov_name]

    @classmethod
    def set_active_provider(cls, name: str, **kwargs):
        prov_name = name.lower()
        cls._current_provider_name = prov_name
        
        # Instantiate or reconfigure with custom params (e.g., API key, model)
        if prov_name == "gemini":
            cls._providers[prov_name] = GeminiProvider(
                api_key=kwargs.get("api_key") or Config.GEMINI_API_KEY,
                model=kwargs.get("model") or Config.GEMINI_MODEL
            )
        elif prov_name == "openai":
            cls._providers[prov_name] = OpenAIProvider(
                api_key=kwargs.get("api_key") or Config.OPENAI_API_KEY,
                model=kwargs.get("model") or Config.OPENAI_MODEL
            )
        elif prov_name == "groq":
            cls._providers[prov_name] = GroqProvider(
                api_key=kwargs.get("api_key") or Config.GROQ_API_KEY,
                model=kwargs.get("model") or Config.GROQ_MODEL
            )
        elif prov_name == "ollama":
            cls._providers[prov_name] = OllamaProvider(
                base_url=kwargs.get("base_url") or Config.OLLAMA_BASE_URL,
                model=kwargs.get("model") or Config.OLLAMA_MODEL
            )
        else:
            cls._providers["demo"] = DemoProvider()

    @classmethod
    def get_active_provider_name(cls) -> str:
        return cls._current_provider_name

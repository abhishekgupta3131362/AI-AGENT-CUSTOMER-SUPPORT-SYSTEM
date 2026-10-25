from abc import ABC, abstractmethod
from typing import Generator, Dict, Any, Optional

class BaseLLMProvider(ABC):
    """Abstract Base Class for LLM providers."""
    
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Generates a complete response text."""
        pass

    @abstractmethod
    def generate_stream(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Generator[str, None, None]:
        """Streams response tokens/chunks."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns the unique identifier of the provider."""
        pass

"""LLM provider implementations."""
from backend.llm.base import BaseLLM
from backend.llm.groq_client import GroqClient
from backend.llm.anthropic_client import AnthropicClient
from backend.llm.local_client import LocalClient
from backend.config import Config


def get_llm_client() -> BaseLLM:
    """Factory function to get appropriate LLM client based on configuration."""
    provider = Config.LLM_PROVIDER.lower()
    
    if provider == "groq":
        return GroqClient()
    elif provider == "anthropic":
        return AnthropicClient()
    elif provider == "local":
        return LocalClient()
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


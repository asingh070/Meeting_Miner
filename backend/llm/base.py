"""Base LLM interface."""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict


class BaseLLM(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
        """
        Generate text from prompt.
        
        Args:
            prompt: User prompt
            system_prompt: System/instruction prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        
        Returns:
            Generated text
        """
        pass
    
    @abstractmethod
    def generate_json(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.3) -> Dict:
        """
        Generate JSON response from prompt.
        
        Args:
            prompt: User prompt
            system_prompt: System/instruction prompt
            temperature: Sampling temperature (lower for more deterministic JSON)
        
        Returns:
            Parsed JSON dictionary
        """
        pass
    
    @abstractmethod
    def generate_stream(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.7):
        """
        Generate text stream (for real-time responses).
        
        Args:
            prompt: User prompt
            system_prompt: System/instruction prompt
            temperature: Sampling temperature
        
        Yields:
            Text chunks
        """
        pass




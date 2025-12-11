"""Groq LLM client implementation."""
import json
from typing import Optional, Dict
from groq import Groq
from backend.llm.base import BaseLLM
from backend.config import Config
from backend.logger import logger


class GroqClient(BaseLLM):
    """Groq LLM client."""
    
    def __init__(self):
        """Initialize Groq client."""
        if not Config.GROQ_API_KEY:
            error_msg = "GROQ_API_KEY is not set"
            logger.error(error_msg)
            print(f"ERROR: {error_msg}")
            raise ValueError(error_msg)
        self.client = Groq(api_key=Config.GROQ_API_KEY)
        self.model = Config.GROQ_MODEL
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
        """Generate text using Groq."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
        except Exception as e:
            error_msg = f"Error generating text with Groq: {str(e)}"
            logger.error(error_msg, exc_info=True)
            print(f"ERROR: {error_msg}")
            raise
    
    def generate_json(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.3) -> Dict:
        """Generate JSON response using Groq."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
        except json.JSONDecodeError as e:
            error_msg = f"Error parsing JSON response from Groq: {str(e)}"
            logger.error(error_msg, exc_info=True)
            print(f"ERROR: {error_msg}")
            raise
        except Exception as e:
            error_msg = f"Error generating JSON with Groq: {str(e)}"
            logger.error(error_msg, exc_info=True)
            print(f"ERROR: {error_msg}")
            raise
    
    def generate_stream(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.7):
        """Generate streaming text using Groq."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            error_msg = f"Error streaming text with Groq: {str(e)}"
            logger.error(error_msg, exc_info=True)
            print(f"ERROR: {error_msg}")
            raise



"""Anthropic Claude LLM client implementation."""
import json
from typing import Optional, Dict
from anthropic import Anthropic
from backend.llm.base import BaseLLM
from backend.config import Config
from backend.logger import logger


class AnthropicClient(BaseLLM):
    """Anthropic Claude client."""
    
    def __init__(self):
        """Initialize Anthropic client."""
        if not Config.ANTHROPIC_API_KEY:
            error_msg = "ANTHROPIC_API_KEY is not set"
            logger.error(error_msg)
            print(f"ERROR: {error_msg}")
            raise ValueError(error_msg)
        self.client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        self.model = Config.ANTHROPIC_MODEL
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
        """Generate text using Anthropic."""
        max_tokens = max_tokens or 4096
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt or "",
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    def generate_json(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.3) -> Dict:
        """Generate JSON response using Anthropic."""
        # Anthropic doesn't have native JSON mode, so we'll request JSON in the prompt
        json_prompt = f"{prompt}\n\nPlease respond with valid JSON only, no additional text."
        
        response = self.generate(
            prompt=json_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=4096
        )
        
        # Try to extract JSON from response
        try:
            # Remove markdown code blocks if present
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            return json.loads(response)
        except json.JSONDecodeError as e:
            # Fallback: try to find JSON object in response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            error_msg = f"Failed to parse JSON from Anthropic response: {response[:200]}"
            logger.error(error_msg, exc_info=True)
            print(f"ERROR: {error_msg}")
            raise ValueError(error_msg)
    
    def generate_stream(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.7):
        """Generate streaming text using Anthropic."""
        with self.client.messages.stream(
            model=self.model,
            max_tokens=4096,
            temperature=temperature,
            system=system_prompt or "",
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            for text in stream.text_stream:
                yield text



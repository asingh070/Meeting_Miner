"""Local LLM client implementation (Ollama)."""
import json
import requests
from typing import Optional, Dict
from backend.llm.base import BaseLLM
from backend.config import Config
from backend.logger import logger


class LocalClient(BaseLLM):
    """Local LLM client using Ollama."""
    
    def __init__(self):
        """Initialize local client."""
        self.base_url = Config.OLLAMA_BASE_URL
        self.model = Config.OLLAMA_MODEL
    
    def _make_request(self, endpoint: str, data: Dict) -> Dict:
        """Make request to Ollama API."""
        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.post(url, json=data, timeout=120)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = f"Error making request to Ollama API: {str(e)}"
            logger.error(error_msg, exc_info=True)
            print(f"ERROR: {error_msg}")
            raise
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
        """Generate text using local model."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        data = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        if max_tokens:
            data["options"]["num_predict"] = max_tokens
        
        response = self._make_request("api/chat", data)
        return response.get("message", {}).get("content", "")
    
    def generate_json(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.3) -> Dict:
        """Generate JSON response using local model."""
        # Request JSON format
        json_prompt = f"{prompt}\n\nPlease respond with valid JSON only, no additional text."
        
        response_text = self.generate(
            prompt=json_prompt,
            system_prompt=system_prompt,
            temperature=temperature
        )
        
        # Try to extract JSON from response
        try:
            # Remove markdown code blocks if present
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            # Fallback: try to find JSON object in response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            error_msg = f"Failed to parse JSON from local model response: {response_text[:200]}"
            logger.error(error_msg, exc_info=True)
            print(f"ERROR: {error_msg}")
            raise ValueError(error_msg)
    
    def generate_stream(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.7):
        """Generate streaming text using local model."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        data = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature
            }
        }
        
        try:
            url = f"{self.base_url}/api/chat"
            response = requests.post(url, json=data, stream=True, timeout=120)
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        if "message" in chunk and "content" in chunk["message"]:
                            yield chunk["message"]["content"]
                    except json.JSONDecodeError:
                        continue
        except requests.exceptions.RequestException as e:
            error_msg = f"Error streaming from Ollama API: {str(e)}"
            logger.error(error_msg, exc_info=True)
            print(f"ERROR: {error_msg}")
            raise



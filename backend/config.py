"""Configuration management for MeetingMiner."""
import os
from typing import Optional
from dotenv import load_dotenv
from backend.logger import logger

# Load environment variables
load_dotenv()


class Config:
    """Application configuration."""
    
    # LLM Provider
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq").lower()
    
    # Groq Configuration
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    
    # Anthropic Configuration
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
    
    # Local/Ollama Configuration
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama2")
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/meetingminer.db")
    
    # Embeddings Configuration
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    
    @classmethod
    def validate(cls) -> None:
        """Validate configuration."""
        if cls.LLM_PROVIDER == "groq" and not cls.GROQ_API_KEY:
            error_msg = "GROQ_API_KEY is required when LLM_PROVIDER is 'groq'"
            logger.error(error_msg)
            print(f"ERROR: {error_msg}")
            raise ValueError(error_msg)
        if cls.LLM_PROVIDER == "anthropic" and not cls.ANTHROPIC_API_KEY:
            error_msg = "ANTHROPIC_API_KEY is required when LLM_PROVIDER is 'anthropic'"
            logger.error(error_msg)
            print(f"ERROR: {error_msg}")
            raise ValueError(error_msg)


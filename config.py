"""Configuration management for the content generation system."""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class OpenAIConfig:
    """OpenAI API configuration."""
    api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    model: str = "gpt-4o"
    temperature: float = 0.7
    max_retries: int = 3
    
    def validate(self) -> bool:
        """Validate configuration."""
        if not self.api_key:
            return False
        if self.temperature < 0 or self.temperature > 2:
            return False
        return True


@dataclass
class APIConfig:
    """REST API configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    cors_origins: list[str] = field(default_factory=lambda: ["*"])


@dataclass
class Config:
    """
    Global application configuration.
    
    Supports configuration via:
    - Environment variables
    - Config file
    - Runtime parameters
    """
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    api: APIConfig = field(default_factory=APIConfig)
    
    # Output defaults
    default_language: str = "en"
    default_tone: str = "friendly"
    
    # Evaluation thresholds
    min_seo_score: float = 70.0
    min_readability_score: float = 60.0
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls(
            openai=OpenAIConfig(
                api_key=os.getenv("OPENAI_API_KEY", ""),
                model=os.getenv("OPENAI_MODEL", "gpt-4o"),
                temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
                max_retries=int(os.getenv("OPENAI_MAX_RETRIES", "3")),
            ),
            api=APIConfig(
                host=os.getenv("API_HOST", "0.0.0.0"),
                port=int(os.getenv("API_PORT", "8000")),
                debug=os.getenv("API_DEBUG", "false").lower() == "true",
            ),
            default_language=os.getenv("DEFAULT_LANGUAGE", "en"),
            default_tone=os.getenv("DEFAULT_TONE", "friendly"),
        )


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def set_config(config: Config) -> None:
    """Set global configuration instance."""
    global _config
    _config = config


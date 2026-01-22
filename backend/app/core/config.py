import os
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional, List


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Gateway"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    SECRET_KEY: str = os.getenv("SESSION_SECRET", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    
    ALLOWED_HOSTS: List[str] = ["*"]
    
    DEFAULT_RATE_LIMIT: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    
    # Vault Configuration
    VAULT_ENABLED: bool = os.getenv("VAULT_ENABLED", "false").lower() == "true"
    VAULT_ADDR: Optional[str] = os.getenv("VAULT_ADDR")
    VAULT_TOKEN: Optional[str] = os.getenv("VAULT_TOKEN")
    VAULT_ROLE_ID: Optional[str] = os.getenv("VAULT_ROLE_ID")
    VAULT_SECRET_ID: Optional[str] = os.getenv("VAULT_SECRET_ID")
    VAULT_SECRET_PATH: str = os.getenv("VAULT_SECRET_PATH", "ai-gateway")
    
    ENABLE_GUARDRAILS: bool = True
    ENABLE_RATE_LIMITING: bool = True
    ENABLE_USAGE_LOGGING: bool = True
    
    LOG_LEVEL: str = "INFO"
    
    ENABLE_TELEMETRY: bool = True
    OTLP_ENDPOINT: Optional[str] = os.getenv("OTLP_ENDPOINT")
    TELEMETRY_CONSOLE_EXPORT: bool = False
    
    ENABLE_SEMANTIC_CACHE: bool = True
    SEMANTIC_CACHE_SIMILARITY_THRESHOLD: float = 0.92
    SEMANTIC_CACHE_TTL_SECONDS: int = 3600
    SEMANTIC_CACHE_MAX_SIZE: int = 10000
    
    ENABLE_CONTENT_ROUTING: bool = True
    
    ENABLE_STREAM_INSPECTION: bool = True
    STREAM_INSPECTION_INTERVAL: int = 10
    STREAM_INSPECTION_MIN_CHARS: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

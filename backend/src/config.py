"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str
    db_pool_size: int = 10  # Moderate traffic baseline (production ready)
    db_max_overflow: int = 20  # Burst capacity for concurrent requests
    db_pool_timeout: int = 30  # Wait time for connection availability
    
    # Application
    app_name: str = "Todo API"
    debug: bool = False
    api_v1_prefix: str = "/api"
    
    # CORS
    cors_origins: str = "*"  # Comma-separated list of allowed origins, or "*" for all
    
    # Authentication (Feature 2)
    better_auth_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiry_days: int = 7

    # OpenAI Configuration (for voice/Whisper/TTS features)
    openai_api_key: str = ""

    # Groq Configuration (Phase 3 - AI Chat Agent)
    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"
    groq_base_url: str = "https://api.groq.com/openai/v1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    def __init__(self, **kwargs):
        """Validate settings on initialization."""
        super().__init__(**kwargs)
        
        # Validate BETTER_AUTH_SECRET
        if len(self.better_auth_secret) < 32:
            raise ValueError(
                "BETTER_AUTH_SECRET must be at least 32 characters long. "
                "Generate a strong secret with: python3 -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


# Global settings instance
settings = Settings()


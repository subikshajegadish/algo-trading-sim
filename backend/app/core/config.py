"""
Application configuration using Pydantic settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Algo Trading Simulator"
    VERSION: str = "1.0.0"
    
    # CORS - stored as string, parsed to list
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    @computed_field
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS string into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


# Global settings instance
settings = Settings()

"""
Application configuration settings
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/worklog_db"
    
    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    
    # App
    app_name: str = "WorkLog Payment Dashboard"
    debug: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

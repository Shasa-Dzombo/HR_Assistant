"""
Application Settings Configuration
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Database Configuration  
    DATABASE_URL: str = "sqlite+aiosqlite:///./hr_assistant.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Google Gemini AI Configuration
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.0-flash-exp"
    
    # Email Configuration
    SENDGRID_API_KEY: Optional[str] = None
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    EMAIL_USERNAME: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Application Settings
    APP_NAME: str = "HR Assistant"
    APP_VERSION: str = "1.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    MAX_WORKERS: int = 4
    UPLOAD_DIR: str = "uploads/"
    
    # External Services
    LINKEDIN_API_KEY: Optional[str] = None
    INDEED_API_KEY: Optional[str] = None
    
    # Company Information
    COMPANY_NAME: str = "Your Company Name"
    COMPANY_EMAIL: str = "hr@company.com"
    COMPANY_WEBSITE: str = "https://company.com"
    
    # Performance Settings
    MAX_CONCURRENT_REQUESTS: int = 100
    REQUEST_TIMEOUT: int = 30
    CACHE_TTL: int = 3600  # 1 hour
    
    # File Upload Settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: list = [".pdf", ".doc", ".docx", ".txt"]
    
    # Workflow Settings
    MAX_WORKFLOW_EXECUTION_TIME: int = 1800  # 30 minutes
    MAX_CONCURRENT_WORKFLOWS: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings (singleton pattern)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings():
    """Reload settings from environment"""
    global _settings
    _settings = None
    return get_settings()
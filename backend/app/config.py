from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Configuration settings untuk aplikasi ThreatSense
    Load dari environment variables atau .env file
    """
    
    # Application
    APP_NAME: str = "ThreatSense API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "sqlite:///./threatsense.db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000"]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # File Upload
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: list = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "text/plain",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    
    # ML Model Paths (untuk future implementation)
    ML_MODEL_PATH: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create singleton instance
settings = Settings()
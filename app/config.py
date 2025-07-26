try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from typing import List, Optional
import os
from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings): # type: ignore
    PROJECT_NAME: str = "DreamBig"
    API_V1_STR: str = "/api/v1"

    SQLALCHEMY_DATABASE_URI: Optional[str] = os.getenv("DATABASE_URL")

    FIREBASE_CREDENTIALS: str = "app/dreambig_firebase_credentioal.json"

    CORS_ORIGINS: List[str] = ["*"]

    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None

    # AI Service configuration
    AI_SERVICE_URL: Optional[str] = None
    AI_SERVICE_KEY: Optional[str] = None

    # JWT Configuration for testing
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-for-testing-only")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    class Config:
        env_file = ".env"
        extra = "allow"  # Allow extra fields for compatibility
        
settings = Settings()

    
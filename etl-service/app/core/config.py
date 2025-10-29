from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://fhir_admin:SecurePass123@postgres:5432/fhir_analytics"
    )
    FHIR_SERVER_URL: str = os.getenv("FHIR_SERVER_URL", "https://hapi.fhir.org/baseR4")
    BULK_DATA_DIR: str = os.getenv("BULK_DATA_DIR", "/data/bulk")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://:RedisSecurePass456@redis:6379/0")
    
    # CORS - Parse from comma-separated string
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000")
    
    # Retry and Timeout Configuration
    RETRY_MAX_ATTEMPTS: int = int(os.getenv("RETRY_MAX_ATTEMPTS", "5"))
    RETRY_BASE_DELAY: float = float(os.getenv("RETRY_BASE_DELAY", "1.0"))
    RETRY_MAX_DELAY: float = float(os.getenv("RETRY_MAX_DELAY", "60.0"))
    
    # HTTP Timeouts (in seconds)
    HTTP_TIMEOUT_CONNECT: float = float(os.getenv("HTTP_TIMEOUT_CONNECT", "10.0"))
    HTTP_TIMEOUT_READ: float = float(os.getenv("HTTP_TIMEOUT_READ", "300.0"))
    HTTP_TIMEOUT_WRITE: float = float(os.getenv("HTTP_TIMEOUT_WRITE", "300.0"))
    HTTP_TIMEOUT_POOL: float = float(os.getenv("HTTP_TIMEOUT_POOL", "60.0"))
    
    # Progress Logging
    PROGRESS_LOG_INTERVAL: int = int(os.getenv("PROGRESS_LOG_INTERVAL", "10"))
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()


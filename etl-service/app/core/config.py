from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://fhir_user:fhir_password@localhost:5432/fhir_analytics"
    )
    FHIR_SERVER_URL: str = os.getenv("FHIR_SERVER_URL", "https://hapi.fhir.org/baseR4")
    BULK_DATA_DIR: str = os.getenv("BULK_DATA_DIR", "/data/bulk")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # CORS - Security: Only allow specific origins
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",      # Frontend development
        "http://localhost:3001",      # Frontend alternative port
        "http://127.0.0.1:3000",
        "http://localhost:8000",      # Backend API
        "http://127.0.0.1:8000",
    ]
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()


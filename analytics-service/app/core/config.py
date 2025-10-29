from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://fhir_admin:SecurePass123@postgres:5432/fhir_analytics"
    )
    
    # CORS - Parse from comma-separated string
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000")
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()


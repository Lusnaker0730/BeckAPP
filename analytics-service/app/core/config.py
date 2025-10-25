from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://fhir_user:fhir_password@localhost:5432/fhir_analytics"
    )
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()


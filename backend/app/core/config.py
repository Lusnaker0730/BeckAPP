from pydantic_settings import BaseSettings
from typing import List
import os
import secrets

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://fhir_user:fhir_password@localhost:5432/fhir_analytics"
    )
    
    # JWT - Security: Require strong JWT secret
    JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # FHIR Server
    FHIR_SERVER_URL: str = os.getenv("FHIR_SERVER_URL", "https://hapi.fhir.org/baseR4")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ]
    
    # Security
    BCRYPT_ROUNDS: int = 12
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    class Config:
        case_sensitive = True
        env_file = ".env"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_jwt_secret()
    
    def _validate_jwt_secret(self):
        """Validate JWT Secret strength and existence"""
        
        # In production, JWT_SECRET must be set and strong
        if self.ENVIRONMENT == "production":
            if not self.JWT_SECRET:
                raise ValueError(
                    "❌ CRITICAL SECURITY ERROR: JWT_SECRET environment variable must be set in production!\n"
                    "Generate a strong secret with: openssl rand -hex 32\n"
                    "Then set it in your .env file or environment variables."
                )
            
            if len(self.JWT_SECRET) < 32:
                raise ValueError(
                    f"❌ CRITICAL SECURITY ERROR: JWT_SECRET must be at least 32 characters long in production!\n"
                    f"Current length: {len(self.JWT_SECRET)} characters\n"
                    "Generate a strong secret with: openssl rand -hex 32"
                )
        
        # In development, warn if using weak or empty secret
        elif self.ENVIRONMENT == "development":
            if not self.JWT_SECRET:
                # Generate a temporary secret for development
                self.JWT_SECRET = secrets.token_hex(32)
                print("⚠️  WARNING: No JWT_SECRET found. Generated temporary secret for development.")
                print("⚠️  For production, set JWT_SECRET environment variable!")
                print(f"⚠️  Generate with: openssl rand -hex 32")
            elif len(self.JWT_SECRET) < 32:
                print(f"⚠️  WARNING: JWT_SECRET is weak ({len(self.JWT_SECRET)} chars). Recommended: 32+ characters")
                print("⚠️  Generate a strong secret with: openssl rand -hex 32")
        
        # Check for common weak secrets
        weak_secrets = [
            "your-secret-key-change-in-production",
            "secret",
            "password",
            "12345",
            "test",
            "admin",
        ]
        
        if self.JWT_SECRET.lower() in weak_secrets:
            if self.ENVIRONMENT == "production":
                raise ValueError(
                    "❌ CRITICAL SECURITY ERROR: JWT_SECRET is using a common weak value!\n"
                    "This is extremely dangerous in production.\n"
                    "Generate a strong secret with: openssl rand -hex 32"
                )
            else:
                print("⚠️  WARNING: JWT_SECRET is using a weak/common value!")
                print("⚠️  Generate a strong secret with: openssl rand -hex 32")

settings = Settings()


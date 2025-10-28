from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.database import engine, Base
from app.api.routes import auth, analytics, export, admin, cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_default_valuesets(db):
    """Initialize default SNOMED-CT and ICD-10 valuesets"""
    from app.models.valueset import Valueset
    
    default_valuesets = [
        {
            "name": "Common Diagnoses (SNOMED-CT)",
            "url": "http://fhir-analytics.local/ValueSet/common-diagnoses-snomed",
            "version": "1.0.0",
            "code_system": "SNOMED-CT",
            "description": "Common diagnosis codes from SNOMED-CT",
            "codes": [
                {"code": "6142004", "display": "Influenza"},
                {"code": "442438000", "display": "Influenza-like symptoms"},
                {"code": "22298006", "display": "Myocardial infarction"},
                {"code": "73211009", "display": "Diabetes mellitus"},
                {"code": "44054006", "display": "Diabetes mellitus type 2"},
                {"code": "38341003", "display": "Essential hypertension"},
                {"code": "13645005", "display": "Chronic obstructive lung disease"},
                {"code": "254637007", "display": "Non-small cell lung cancer"},
            ]
        },
        {
            "name": "ICD-10 Diagnosis Codes",
            "url": "http://fhir-analytics.local/ValueSet/icd10-diagnoses",
            "version": "1.0.0",
            "code_system": "ICD-10",
            "description": "Common ICD-10 diagnosis codes",
            "codes": [
                {"code": "J09", "display": "Influenza due to identified zoonotic influenza virus"},
                {"code": "J10", "display": "Influenza due to other identified influenza virus"},
                {"code": "J11", "display": "Influenza, virus not identified"},
                {"code": "I21", "display": "ST elevation (STEMI) myocardial infarction"},
                {"code": "E10", "display": "Type 1 diabetes mellitus"},
                {"code": "E11", "display": "Type 2 diabetes mellitus"},
                {"code": "I10", "display": "Essential (primary) hypertension"},
                {"code": "J44", "display": "Other chronic obstructive pulmonary disease"},
                {"code": "C34", "display": "Malignant neoplasm of bronchus and lung"},
            ]
        }
    ]
    
    for vs_data in default_valuesets:
        existing = db.query(Valueset).filter(Valueset.url == vs_data["url"]).first()
        if not existing:
            valueset = Valueset(**vs_data, status="active", is_system=True)
            db.add(valueset)
            logger.info(f"Created valueset: {vs_data['name']}")
        else:
            logger.info(f"Valueset already exists: {vs_data['name']}")
    
    try:
        db.commit()
        logger.info("Valuesets initialization completed")
    except Exception as e:
        logger.error(f"Error initializing valuesets: {e}")
        db.rollback()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables
    logger.info("Starting up FHIR Analytics Backend...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
    
    # Create default admin user if not exists
    from app.models.user import User
    from app.core.security import get_password_hash
    from app.core.database import SessionLocal
    
    # Import password validator
    from app.core.password_validator import validate_password_or_raise, PasswordStrengthError
    
    db = SessionLocal()
    try:
        # Get credentials from environment variables
        admin_username = settings.ADMIN_USERNAME
        admin_password = settings.ADMIN_PASSWORD
        admin_email = settings.ADMIN_EMAIL
        
        engineer_username = settings.ENGINEER_USERNAME
        engineer_password = settings.ENGINEER_PASSWORD
        engineer_email = settings.ENGINEER_EMAIL
        
        # Create admin user (ONLY if not exists - NO password reset)
        admin_user = db.query(User).filter(User.username == admin_username).first()
        if not admin_user:
            # Validate password strength
            if not admin_password:
                logger.error("❌ ADMIN_PASSWORD not set in environment variables!")
                logger.error("   Please set ADMIN_PASSWORD in .env file")
                logger.error("   Password must meet complexity requirements (12+ chars, uppercase, lowercase, digit, special char)")
            else:
                try:
                    validate_password_or_raise(admin_password, min_length=12)
                    logger.info("✅ Creating admin user...")
                    admin_user = User(
                        username=admin_username,
                        email=admin_email,
                        hashed_password=get_password_hash(admin_password),
                        full_name="System Administrator",
                        role="admin",
                        is_active=True
                    )
                    db.add(admin_user)
                    logger.info(f"✅ Admin user created: {admin_username}")
                    logger.warning("⚠️  IMPORTANT: Change the admin password after first login!")
                except PasswordStrengthError as e:
                    logger.error(f"❌ Admin password does not meet security requirements:")
                    logger.error(f"   {str(e)}")
                    logger.error("   Please update ADMIN_PASSWORD in .env file")
        else:
            logger.info(f"ℹ️  Admin user already exists: {admin_username}")
            logger.info("   Password will NOT be automatically reset for security reasons")
            logger.info("   To reset password, use the admin panel or database directly")
        
        # Create engineer user (ONLY if not exists - NO password reset)
        engineer_user = db.query(User).filter(User.username == engineer_username).first()
        if not engineer_user:
            # Validate password strength
            if not engineer_password:
                logger.error("❌ ENGINEER_PASSWORD not set in environment variables!")
                logger.error("   Please set ENGINEER_PASSWORD in .env file")
            else:
                try:
                    validate_password_or_raise(engineer_password, min_length=12)
                    logger.info("✅ Creating engineer user...")
                    engineer_user = User(
                        username=engineer_username,
                        email=engineer_email,
                        hashed_password=get_password_hash(engineer_password),
                        full_name="System Engineer",
                        role="engineer",
                        is_active=True
                    )
                    db.add(engineer_user)
                    logger.info(f"✅ Engineer user created: {engineer_username}")
                    logger.warning("⚠️  IMPORTANT: Change the engineer password after first login!")
                except PasswordStrengthError as e:
                    logger.error(f"❌ Engineer password does not meet security requirements:")
                    logger.error(f"   {str(e)}")
                    logger.error("   Please update ENGINEER_PASSWORD in .env file")
        else:
            logger.info(f"ℹ️  Engineer user already exists: {engineer_username}")
            logger.info("   Password will NOT be automatically reset for security reasons")
        
        db.commit()
        
        # Initialize default SNOMED-CT valuesets
        logger.info("Initializing default SNOMED-CT valuesets...")
        init_default_valuesets(db)
        
    except Exception as e:
        logger.error(f"Error managing default users: {e}")
        db.rollback()
    finally:
        db.close()
    
    yield
    # Shutdown
    logger.info("Shutting down...")

# Create FastAPI app
app = FastAPI(
    title="FHIR Analytics Platform API",
    description="Backend API for FHIR data analytics and visualization",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security headers middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking attacks
        response.headers["X-Frame-Options"] = "DENY"
        
        # Enable XSS protection (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Force HTTPS in production
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # Content Security Policy
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # Adjust for production
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self' " + " ".join(settings.ALLOWED_ORIGINS),
            "frame-ancestors 'none'",
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        
        # Permissions Policy (formerly Feature Policy)
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(export.router, prefix="/api/export", tags=["Export"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(cache.router, prefix="/api/cache", tags=["Cache Management"])

@app.get("/")
async def root():
    return {
        "message": "FHIR Analytics Platform API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )


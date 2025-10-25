from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.database import engine, Base
from app.api.routes import auth, analytics, export, admin

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
    
    db = SessionLocal()
    try:
        # Create/update admin user
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            logger.info("Creating default admin user...")
            admin_user = User(
                username="admin",
                email="admin@fhir-analytics.local",
                hashed_password=get_password_hash("admin123"),
                full_name="System Administrator",
                role="admin",
                is_active=True
            )
            db.add(admin_user)
            logger.info("Default admin user created (username: admin, password: admin123)")
        else:
            # Reset admin password for existing user
            logger.info("Resetting admin user password to default...")
            admin_user.hashed_password = get_password_hash("admin123")
            admin_user.is_active = True
            logger.info("Admin password reset (username: admin, password: admin123)")
        
        # Create/update engineer user
        engineer_user = db.query(User).filter(User.username == "engineer").first()
        if not engineer_user:
            logger.info("Creating default engineer user...")
            engineer_user = User(
                username="engineer",
                email="engineer@fhir-analytics.local",
                hashed_password=get_password_hash("engineer123"),
                full_name="System Engineer",
                role="engineer",
                is_active=True
            )
            db.add(engineer_user)
            logger.info("Default engineer user created (username: engineer, password: engineer123)")
        else:
            logger.info("Resetting engineer user password to default...")
            engineer_user.hashed_password = get_password_hash("engineer123")
            engineer_user.is_active = True
            logger.info("Engineer password reset (username: engineer, password: engineer123)")
        
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

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(export.router, prefix="/api/export", tags=["Export"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])

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


from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.api import bulk_data, transform

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="FHIR ETL Service",
    description="ETL service for FHIR BULK DATA processing",
    version="1.0.0"
)

# Configure CORS - Security: Only allow whitelisted origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # Restricted to specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicit methods
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin"],  # Explicit headers
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Include routers
app.include_router(bulk_data.router, prefix="/api/bulk-data", tags=["Bulk Data"])
app.include_router(transform.router, prefix="/api/transform", tags=["Transform"])

@app.get("/")
async def root():
    return {
        "service": "FHIR ETL Service",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )


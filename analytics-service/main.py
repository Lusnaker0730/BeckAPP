from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.api import visualization, statistics, cohort

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="FHIR Analytics Service",
    description="Advanced analytics and data science for FHIR data",
    version="1.0.0"
)

# Configure CORS - Security: Only allow whitelisted origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),  # Parse comma-separated origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicit methods
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin"],  # Explicit headers
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Include routers
app.include_router(visualization.router, prefix="/api/visualization", tags=["Visualization"])
app.include_router(statistics.router, prefix="/api/statistics", tags=["Statistics"])
app.include_router(cohort.router, prefix="/api/cohort", tags=["Cohort Analysis"])

@app.get("/")
async def root():
    return {
        "service": "FHIR Analytics Service",
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
        port=8002,
        reload=True
    )


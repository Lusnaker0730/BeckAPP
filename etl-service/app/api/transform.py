from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import json
import logging
import os

from app.core.config import settings
from app.services.fhir_transformer import FHIRTransformer

router = APIRouter()
logger = logging.getLogger(__name__)

class TransformRequest(BaseModel):
    job_id: str
    resource_types: List[str]

class TransformResult(BaseModel):
    job_id: str
    status: str
    records_processed: int
    records_failed: int
    details: List[dict]

@router.post("/process")
async def transform_bulk_data(request: TransformRequest):
    """
    Transform NDJSON bulk data files into structured format for database loading.
    """
    
    job_dir = os.path.join(settings.BULK_DATA_DIR, request.job_id)
    
    if not os.path.exists(job_dir):
        raise HTTPException(status_code=404, detail="Job directory not found")
    
    transformer = FHIRTransformer()
    results = []
    total_processed = 0
    total_failed = 0
    
    for resource_type in request.resource_types:
        ndjson_file = os.path.join(job_dir, f"{resource_type}.ndjson")
        
        if not os.path.exists(ndjson_file):
            logger.warning(f"File not found: {ndjson_file}")
            continue
        
        try:
            # Transform the NDJSON file
            result = await transformer.transform_file(ndjson_file, resource_type)
            
            results.append({
                "resource_type": resource_type,
                "records_processed": result["processed"],
                "records_failed": result["failed"],
                "output_file": result["output_file"]
            })
            
            total_processed += result["processed"]
            total_failed += result["failed"]
            
            logger.info(f"Transformed {resource_type}: {result['processed']} records")
        
        except Exception as e:
            logger.error(f"Error transforming {resource_type}: {e}")
            results.append({
                "resource_type": resource_type,
                "error": str(e)
            })
            total_failed += 1
    
    return {
        "job_id": request.job_id,
        "status": "completed" if total_failed == 0 else "completed_with_errors",
        "records_processed": total_processed,
        "records_failed": total_failed,
        "details": results
    }

@router.post("/load-to-database")
async def load_to_database(request: TransformRequest):
    """
    Load transformed data into PostgreSQL database.
    """
    
    job_dir = os.path.join(settings.BULK_DATA_DIR, request.job_id, "transformed")
    
    if not os.path.exists(job_dir):
        raise HTTPException(status_code=404, detail="Transformed data not found")
    
    from app.services.database_loader import DatabaseLoader
    loader = DatabaseLoader()
    
    results = []
    total_loaded = 0
    total_failed = 0
    
    for resource_type in request.resource_types:
        json_file = os.path.join(job_dir, f"{resource_type}.json")
        
        if not os.path.exists(json_file):
            continue
        
        try:
            result = await loader.load_file(json_file, resource_type)
            
            results.append({
                "resource_type": resource_type,
                "records_loaded": result["loaded"],
                "records_failed": result["failed"]
            })
            
            total_loaded += result["loaded"]
            total_failed += result["failed"]
            
            logger.info(f"Loaded {resource_type}: {result['loaded']} records")
        
        except Exception as e:
            logger.error(f"Error loading {resource_type}: {e}")
            results.append({
                "resource_type": resource_type,
                "error": str(e)
            })
    
    return {
        "job_id": request.job_id,
        "status": "completed",
        "records_loaded": total_loaded,
        "records_failed": total_failed,
        "details": results
    }


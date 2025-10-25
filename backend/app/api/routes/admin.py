from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
import httpx
import logging
import json

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.etl_job import ETLJob
from app.models.valueset import Valueset

router = APIRouter()
logger = logging.getLogger(__name__)

# ETL Service URL
ETL_SERVICE_URL = "http://etl-service:8001"

# Schemas
class BulkDataConfig(BaseModel):
    fhirServerUrl: str
    resourceTypes: List[str]
    since: Optional[str] = None

class ValuesetCreate(BaseModel):
    name: str
    url: str
    version: Optional[str] = None
    description: Optional[str] = None
    code_system: str
    codes: List[dict]

@router.get("/etl-jobs")
async def get_etl_jobs(
    current_user: dict = Depends(require_role(["admin", "engineer"])),
    db: Session = Depends(get_db),
    limit: int = 50
):
    """Get ETL job history"""
    jobs = db.query(ETLJob).order_by(ETLJob.created_at.desc()).limit(limit).all()
    
    return [
        {
            "id": job.job_id,
            "resourceType": job.resource_type,
            "status": job.status,
            "startTime": job.start_time.isoformat() if job.start_time else None,
            "endTime": job.end_time.isoformat() if job.end_time else None,
            "recordsProcessed": job.records_processed,
            "recordsFailed": job.records_failed
        }
        for job in jobs
    ]

@router.post("/bulk-data/fetch")
async def fetch_bulk_data(
    config: BulkDataConfig,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_role(["admin", "engineer"])),
    db: Session = Depends(get_db)
):
    """Initiate FHIR BULK DATA fetch"""
    
    # Call ETL service to start bulk data export
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            etl_request = {
                "fhir_server_url": config.fhirServerUrl,
                "resource_types": config.resourceTypes,
                "since": config.since
            }
            
            logger.info(f"Calling ETL service to fetch bulk data: {etl_request}")
            
            response = await client.post(
                f"{ETL_SERVICE_URL}/api/bulk-data/kick-off",
                json=etl_request
            )
            
            if response.status_code == 200:
                result = response.json()
                etl_job_id = result.get("job_id")
                
                # Create ETL job record in database
                etl_job = ETLJob(
                    job_id=etl_job_id,
                    resource_type=",".join(config.resourceTypes),
                    status="in-progress",
                    fhir_server_url=config.fhirServerUrl,
                    config={
                        "since": config.since,
                        "resource_types": config.resourceTypes
                    },
                    created_by=current_user.get("sub"),
                    start_time=datetime.now()
                )
                
                db.add(etl_job)
                db.commit()
                
                logger.info(f"Bulk data fetch initiated successfully: job_id={etl_job_id}")
                
                # Add background task to monitor the job
                background_tasks.add_task(monitor_etl_job, etl_job_id, db)
                
                return {
                    "message": "BULK DATA fetch initiated successfully",
                    "job_id": etl_job_id,
                    "resource_types": config.resourceTypes,
                    "status_url": result.get("status_url")
                }
            else:
                error_msg = f"ETL service returned error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise HTTPException(status_code=500, detail=error_msg)
                
    except httpx.RequestError as e:
        error_msg = f"Error connecting to ETL service: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

async def monitor_etl_job(job_id: str, db: Session):
    """Monitor ETL job status and update database"""
    import asyncio
    
    max_attempts = 120  # Monitor for up to 10 minutes (120 * 5 seconds)
    attempt = 0
    
    while attempt < max_attempts:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{ETL_SERVICE_URL}/api/bulk-data/status/{job_id}")
                
                if response.status_code == 200:
                    status_data = response.json()
                    job_status = status_data.get("status")
                    
                    # Update job in database
                    job = db.query(ETLJob).filter(ETLJob.job_id == job_id).first()
                    if job:
                        job.status = job_status
                        
                        # Update records count - count ACTUAL database records within job timeframe
                        from datetime import timedelta
                        from app.models.fhir_resources import Patient, Condition, Encounter, Observation
                        from sqlalchemy import func
                        
                        if job.start_time:
                            # Expand time window to capture data loaded after job completion
                            time_start = job.start_time - timedelta(hours=6)  # Include 6 hours before
                            time_end = datetime.now() + timedelta(hours=1)  # Include up to now
                            
                            patient_count = db.query(func.count(Patient.id)).filter(
                                Patient.created_at >= time_start,
                                Patient.created_at <= time_end
                            ).scalar() or 0
                            
                            condition_count = db.query(func.count(Condition.id)).filter(
                                Condition.created_at >= time_start,
                                Condition.created_at <= time_end
                            ).scalar() or 0
                            
                            encounter_count = db.query(func.count(Encounter.id)).filter(
                                Encounter.created_at >= time_start,
                                Encounter.created_at <= time_end
                            ).scalar() or 0
                            
                            observation_count = db.query(func.count(Observation.id)).filter(
                                Observation.created_at >= time_start,
                                Observation.created_at <= time_end
                            ).scalar() or 0
                            
                            actual_loaded = patient_count + condition_count + encounter_count + observation_count
                            job.records_processed = actual_loaded
                            logger.info(f"Counted {actual_loaded} actual DB records (P:{patient_count} C:{condition_count} E:{encounter_count} O:{observation_count})")
                        else:
                            # Fallback: use FHIR server counts
                            if "total_resources" in status_data:
                                job.records_processed = status_data["total_resources"]
                            elif "result" in status_data and isinstance(status_data["result"], dict):
                                result_data = status_data["result"]
                                if "output" in result_data:
                                    total_records = sum(f.get("count", 0) for f in result_data["output"])
                                    job.records_processed = total_records
                        
                        if job_status == "completed":
                            job.end_time = datetime.now()
                            job.result = status_data
                            
                            # Extract detailed information
                            if "files" in status_data:
                                files_info = status_data["files"]
                                job.error_log = json.dumps({
                                    "message": status_data.get("message", "Completed successfully"),
                                    "files": files_info,
                                    "method": status_data.get("method", "unknown"),
                                    "total_resources": status_data.get("total_resources", 0)
                                }, ensure_ascii=False)
                            
                            db.commit()
                            logger.info(f"Job {job_id} completed successfully with {job.records_processed} records")
                            break
                            
                        elif job_status == "failed":
                            job.end_time = datetime.now()
                            error_msg = status_data.get("error", "Unknown error")
                            job.error_log = json.dumps({
                                "error": error_msg,
                                "status_data": status_data
                            }, ensure_ascii=False)
                            db.commit()
                            logger.error(f"Job {job_id} failed: {error_msg}")
                            break
                        
                        db.commit()
                
        except Exception as e:
            logger.error(f"Error monitoring job {job_id}: {e}")
        
        attempt += 1
        await asyncio.sleep(5)  # Check every 5 seconds
    
    # If max attempts reached and job still not completed
    if attempt >= max_attempts:
        try:
            job = db.query(ETLJob).filter(ETLJob.job_id == job_id).first()
            if job and job.status == "in-progress":
                job.status = "timeout"
                job.end_time = datetime.now()
                job.error_log = json.dumps({
                    "error": "Monitoring timeout after 10 minutes"
                }, ensure_ascii=False)
                db.commit()
                logger.warning(f"Job {job_id} monitoring timeout")
        except Exception as e:
            logger.error(f"Error setting timeout status for job {job_id}: {e}")

@router.get("/etl-jobs/{job_id}/status")
async def get_job_status(
    job_id: str,
    current_user: dict = Depends(require_role(["admin", "engineer"])),
    db: Session = Depends(get_db)
):
    """Get ETL job status"""
    job = db.query(ETLJob).filter(ETLJob.job_id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job.job_id,
        "resource_type": job.resource_type,
        "status": job.status,
        "fhir_server_url": job.fhir_server_url,
        "start_time": job.start_time.isoformat() if job.start_time else None,
        "end_time": job.end_time.isoformat() if job.end_time else None,
        "records_processed": job.records_processed,
        "records_failed": job.records_failed,
        "error_log": job.error_log,
        "result": job.result
    }

@router.delete("/etl-jobs/{job_id}")
async def delete_etl_job(
    job_id: str,
    current_user: dict = Depends(require_role(["admin", "engineer"])),
    db: Session = Depends(get_db)
):
    """Delete an ETL job (especially useful for failed jobs)"""
    
    job = db.query(ETLJob).filter(ETLJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    db.delete(job)
    db.commit()
    
    return {
        "message": "ETL job deleted successfully",
        "job_id": job_id
    }

@router.get("/valuesets")
async def get_valuesets(
    current_user: dict = Depends(require_role(["admin", "engineer"])),
    db: Session = Depends(get_db)
):
    """Get all valuesets"""
    valuesets = db.query(Valueset).filter(Valueset.status == "active").all()
    
    return [
        {
            "id": vs.id,
            "name": vs.name,
            "url": vs.url,
            "version": vs.version,
            "code_system": vs.code_system,
            "description": vs.description,
            "code_count": len(vs.codes) if vs.codes else 0,
            "updated_at": vs.updated_at.isoformat() if vs.updated_at else None
        }
        for vs in valuesets
    ]

@router.get("/valuesets/{valueset_id}")
async def get_valueset(
    valueset_id: int,
    current_user: dict = Depends(require_role(["admin", "engineer"])),
    db: Session = Depends(get_db)
):
    """Get a single valueset by ID"""
    valueset = db.query(Valueset).filter(Valueset.id == valueset_id).first()
    if not valueset:
        raise HTTPException(status_code=404, detail="Valueset not found")
    
    return {
        "id": valueset.id,
        "name": valueset.name,
        "url": valueset.url,
        "version": valueset.version,
        "code_system": valueset.code_system,
        "description": valueset.description,
        "codes": valueset.codes,
        "status": valueset.status,
        "created_at": valueset.created_at.isoformat() if valueset.created_at else None,
        "updated_at": valueset.updated_at.isoformat() if valueset.updated_at else None
    }

@router.post("/valuesets")
async def create_valueset(
    valueset_data: ValuesetCreate,
    current_user: dict = Depends(require_role(["admin", "engineer"])),
    db: Session = Depends(get_db)
):
    """Create a new valueset"""
    
    # Check if valueset with same URL exists
    existing = db.query(Valueset).filter(Valueset.url == valueset_data.url).first()
    if existing:
        raise HTTPException(status_code=400, detail="Valueset with this URL already exists")
    
    valueset = Valueset(
        name=valueset_data.name,
        url=valueset_data.url,
        version=valueset_data.version,
        description=valueset_data.description,
        code_system=valueset_data.code_system,
        codes=valueset_data.codes,
        status="active"
    )
    
    db.add(valueset)
    db.commit()
    db.refresh(valueset)
    
    return {
        "id": valueset.id,
        "name": valueset.name,
        "url": valueset.url,
        "message": "Valueset created successfully"
    }

@router.put("/valuesets/{valueset_id}")
async def update_valueset(
    valueset_id: int,
    valueset_data: ValuesetCreate,
    current_user: dict = Depends(require_role(["admin", "engineer"])),
    db: Session = Depends(get_db)
):
    """Update an existing valueset"""
    
    valueset = db.query(Valueset).filter(Valueset.id == valueset_id).first()
    if not valueset:
        raise HTTPException(status_code=404, detail="Valueset not found")
    
    valueset.name = valueset_data.name
    valueset.url = valueset_data.url
    valueset.version = valueset_data.version
    valueset.description = valueset_data.description
    valueset.code_system = valueset_data.code_system
    valueset.codes = valueset_data.codes
    
    db.commit()
    
    return {
        "id": valueset.id,
        "message": "Valueset updated successfully"
    }

@router.delete("/valuesets/{valueset_id}")
async def delete_valueset(
    valueset_id: int,
    current_user: dict = Depends(require_role(["admin", "engineer"])),
    db: Session = Depends(get_db)
):
    """Delete a valueset"""
    
    valueset = db.query(Valueset).filter(Valueset.id == valueset_id).first()
    if not valueset:
        raise HTTPException(status_code=404, detail="Valueset not found")
    
    # Soft delete by setting status to retired
    valueset.status = "retired"
    db.commit()
    
    return {
        "message": "Valueset deleted successfully"
    }


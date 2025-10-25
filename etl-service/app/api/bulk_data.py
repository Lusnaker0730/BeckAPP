from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import httpx
import asyncio
import logging
from datetime import datetime
import os
import json

from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

class BulkDataRequest(BaseModel):
    fhir_server_url: str
    resource_types: List[str]
    since: Optional[str] = None
    bearer_token: Optional[str] = None

class BulkDataStatus(BaseModel):
    job_id: str
    status: str
    progress: int
    message: str

# In-memory job tracking (in production, use Redis or database)
jobs = {}

@router.post("/kick-off")
async def kick_off_bulk_export(
    request: BulkDataRequest,
    background_tasks: BackgroundTasks
):
    """
    Initiate FHIR Bulk Data export following the FHIR Bulk Data Access spec.
    If $export is not supported, falls back to regular FHIR search.
    https://hl7.org/fhir/uv/bulkdata/export/index.html
    """
    
    # Validate FHIR server URL
    if not request.fhir_server_url:
        raise HTTPException(status_code=400, detail="FHIR server URL is required")
    
    # Try Bulk Data $export first
    export_url = f"{request.fhir_server_url}/$export"
    params = {
        "_type": ",".join(request.resource_types)
    }
    
    if request.since:
        params["_since"] = request.since
    
    headers = {
        "Accept": "application/fhir+json",
        "Prefer": "respond-async"
    }
    
    if request.bearer_token:
        headers["Authorization"] = f"Bearer {request.bearer_token}"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(export_url, params=params, headers=headers)
            
            if response.status_code == 202:
                # Bulk export supported - use async workflow
                status_url = response.headers.get("Content-Location")
                job_id = status_url.split("/")[-1] if status_url else str(datetime.now().timestamp())
                
                jobs[job_id] = {
                    "status": "in-progress",
                    "status_url": status_url,
                    "fhir_server_url": request.fhir_server_url,
                    "resource_types": request.resource_types,
                    "started_at": datetime.now().isoformat(),
                    "method": "bulk_export"
                }
                
                background_tasks.add_task(poll_export_status, job_id, status_url, headers)
                
                return {
                    "job_id": job_id,
                    "status": "accepted",
                    "message": "Bulk export initiated",
                    "status_url": status_url
                }
            else:
                # $export not supported, use regular FHIR search as fallback
                logger.info(f"$export not supported (status {response.status_code}), using FHIR search fallback")
                job_id = f"search_{int(datetime.now().timestamp())}"
                
                jobs[job_id] = {
                    "status": "in-progress",
                    "fhir_server_url": request.fhir_server_url,
                    "resource_types": request.resource_types,
                    "started_at": datetime.now().isoformat(),
                    "method": "fhir_search"
                }
                
                # Use FHIR search API instead
                background_tasks.add_task(
                    fetch_via_search, 
                    job_id, 
                    request.fhir_server_url, 
                    request.resource_types,
                    request.since,
                    headers
                )
                
                return {
                    "job_id": job_id,
                    "status": "accepted",
                    "message": "Data fetch initiated using FHIR search API (fallback mode)",
                    "method": "fhir_search"
                }
    
    except httpx.RequestError as e:
        logger.error(f"Error connecting to FHIR server: {e}")
        raise HTTPException(status_code=500, detail=f"Error connecting to FHIR server: {str(e)}")

async def poll_export_status(job_id: str, status_url: str, headers: dict):
    """Poll the export status endpoint until completion"""
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            try:
                response = await client.get(status_url, headers=headers)
                
                if response.status_code == 200:
                    # Export completed
                    result = response.json()
                    
                    # Check for REAL errors (not empty error fields)
                    has_error = False
                    error_msg = None
                    
                    # Check if 'error' field exists and is not empty
                    if "error" in result:
                        error_value = result.get("error")
                        # Error is real if it's a non-empty string, list, or dict
                        if error_value and (
                            (isinstance(error_value, str) and error_value.strip()) or
                            (isinstance(error_value, (list, dict)) and len(error_value) > 0)
                        ):
                            has_error = True
                            error_msg = str(error_value)
                    
                    # Check for OperationOutcome (FHIR error format)
                    if "OperationOutcome" in result:
                        has_error = True
                        error_msg = str(result.get("OperationOutcome"))
                    
                    if has_error:
                        logger.warning(f"Bulk export failed: {error_msg}")
                        
                        # Check if error is "Too many files" - try fallback
                        if "too many files" in str(error_msg).lower():
                            logger.info(f"Too many files error, switching to FHIR search fallback for job {job_id}")
                            
                            # Get job info for fallback
                            job_info = jobs.get(job_id, {})
                            fhir_server_url = job_info.get("fhir_server_url")
                            resource_types = job_info.get("resource_types")
                            
                            if fhir_server_url and resource_types:
                                # Switch to FHIR search method
                                jobs[job_id]["status"] = "in-progress"
                                jobs[job_id]["method"] = "fhir_search"
                                jobs[job_id]["message"] = "Bulk export failed, using FHIR search fallback"
                                
                                await fetch_via_search(
                                    job_id,
                                    fhir_server_url,
                                    resource_types,
                                    None,
                                    headers
                                )
                            else:
                                jobs[job_id]["status"] = "failed"
                                jobs[job_id]["error"] = error_msg
                        else:
                            jobs[job_id]["status"] = "failed"
                            jobs[job_id]["error"] = error_msg
                        break
                    
                    # No error - process successful result
                    jobs[job_id]["status"] = "completed"
                    jobs[job_id]["result"] = result
                    jobs[job_id]["completed_at"] = datetime.now().isoformat()
                    
                    # Download files
                    await download_bulk_files(job_id, result)
                    break
                
                elif response.status_code == 202:
                    # Still in progress
                    await asyncio.sleep(5)  # Wait 5 seconds before next poll
                    continue
                
                else:
                    # HTTP Error - check if we should fallback
                    error_text = response.text
                    logger.warning(f"Bulk export error (status {response.status_code}): {error_text}")
                    
                    if "too many files" in error_text.lower():
                        logger.info(f"Too many files error, switching to FHIR search fallback for job {job_id}")
                        job_info = jobs.get(job_id, {})
                        fhir_server_url = job_info.get("fhir_server_url")
                        resource_types = job_info.get("resource_types")
                        
                        if fhir_server_url and resource_types:
                            jobs[job_id]["status"] = "in-progress"
                            jobs[job_id]["method"] = "fhir_search"
                            jobs[job_id]["message"] = "Bulk export failed, using FHIR search fallback"
                            
                            await fetch_via_search(
                                job_id,
                                fhir_server_url,
                                resource_types,
                                None,
                                headers
                            )
                        else:
                            jobs[job_id]["status"] = "failed"
                            jobs[job_id]["error"] = error_text
                    else:
                        jobs[job_id]["status"] = "failed"
                        jobs[job_id]["error"] = error_text
                    break
            
            except Exception as e:
                logger.error(f"Error polling export status: {e}")
                jobs[job_id]["status"] = "failed"
                jobs[job_id]["error"] = str(e)
                break

async def download_bulk_files(job_id: str, result: dict):
    """Download NDJSON files from bulk export result"""
    
    output_dir = os.path.join(settings.BULK_DATA_DIR, job_id)
    os.makedirs(output_dir, exist_ok=True)
    
    files_downloaded = []
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for output in result.get("output", []):
            url = output.get("url")
            resource_type = output.get("type")
            
            if not url:
                continue
            
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    filename = f"{resource_type}.ndjson"
                    filepath = os.path.join(output_dir, filename)
                    
                    with open(filepath, "wb") as f:
                        f.write(response.content)
                    
                    files_downloaded.append({
                        "resource_type": resource_type,
                        "filename": filename,
                        "size": len(response.content)
                    })
                    
                    logger.info(f"Downloaded {filename} for job {job_id}")
            
            except Exception as e:
                logger.error(f"Error downloading file {url}: {e}")
    
    jobs[job_id]["files"] = files_downloaded
    jobs[job_id]["download_completed_at"] = datetime.now().isoformat()
    
    # Automatically trigger transform and load after download
    if files_downloaded:
        logger.info(f"[{job_id}] Starting auto transform and load after bulk download")
        resource_types = list(set([f["resource_type"] for f in files_downloaded]))
        await auto_transform_and_load(job_id, resource_types)

@router.get("/status/{job_id}")
async def get_export_status(job_id: str):
    """Get the status of a bulk export job"""
    
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return jobs[job_id]

@router.get("/jobs")
async def list_jobs():
    """List all bulk export jobs"""
    return {
        "jobs": [
            {
                "job_id": job_id,
                "status": job_info["status"],
                "started_at": job_info.get("started_at"),
                "resource_types": job_info.get("resource_types")
            }
            for job_id, job_info in jobs.items()
        ]
    }

async def auto_transform_and_load(job_id: str, resource_types: List[str]):
    """
    Automatically transform NDJSON files and load into database
    """
    try:
        logger.info(f"[{job_id}] Starting auto transform and load process...")
        
        # Import transformer and loader
        from app.services.fhir_transformer import FHIRTransformer
        from app.services.database_loader import DatabaseLoader
        
        job_dir = os.path.join(settings.BULK_DATA_DIR, job_id)
        transformer = FHIRTransformer()
        loader = DatabaseLoader()
        
        total_transformed = 0
        total_loaded = 0
        
        # Process each resource type
        for resource_type in resource_types:
            ndjson_file = os.path.join(job_dir, f"{resource_type}.ndjson")
            
            if not os.path.exists(ndjson_file):
                logger.warning(f"[{job_id}] File not found: {ndjson_file}")
                continue
            
            try:
                # Transform NDJSON to structured JSON
                logger.info(f"[{job_id}] Transforming {resource_type}...")
                transform_result = await transformer.transform_file(ndjson_file, resource_type)
                total_transformed += transform_result["processed"]
                logger.info(f"[{job_id}] Transformed {transform_result['processed']} {resource_type} records")
                
                # Load into database
                logger.info(f"[{job_id}] Loading {resource_type} into database with job_id={job_id}...")
                load_result = await loader.load_file(transform_result["output_file"], resource_type, job_id=job_id)
                total_loaded += load_result["loaded"]
                logger.info(f"[{job_id}] Loaded {load_result['loaded']} {resource_type} records")
                
            except Exception as e:
                logger.error(f"[{job_id}] Error processing {resource_type}: {e}")
                continue
        
        # Update job status with load info
        if job_id in jobs:
            jobs[job_id]["transform_load_completed"] = datetime.now().isoformat()
            jobs[job_id]["records_transformed"] = total_transformed
            jobs[job_id]["records_loaded"] = total_loaded
            jobs[job_id]["message"] = f"Successfully loaded {total_loaded} records into database"
        
        logger.info(f"[{job_id}] Auto transform and load completed: {total_loaded} records loaded")
        
    except Exception as e:
        logger.error(f"[{job_id}] Error in auto_transform_and_load: {e}")
        if job_id in jobs:
            jobs[job_id]["transform_load_error"] = str(e)

async def fetch_via_search(
    job_id: str, 
    fhir_server_url: str, 
    resource_types: List[str],
    since: Optional[str],
    headers: dict
):
    """
    Fallback method: Fetch FHIR resources using regular search API
    """
    try:
        output_dir = os.path.join(settings.BULK_DATA_DIR, job_id)
        os.makedirs(output_dir, exist_ok=True)
        
        total_resources = 0
        files_created = []
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            for resource_type in resource_types:
                logger.info(f"Fetching {resource_type} resources from {fhir_server_url}")
                
                # Build search URL
                search_url = f"{fhir_server_url}/{resource_type}"
                params = {"_count": "100"}  # Fetch 100 at a time
                
                if since:
                    params["_lastUpdated"] = f"ge{since}"
                
                resources = []
                page_count = 0
                max_pages = 10  # Limit to 10 pages (1000 resources) per type to avoid overwhelming the system
                
                while page_count < max_pages:
                    try:
                        response = await client.get(search_url, params=params, headers=headers)
                        
                        if response.status_code == 200:
                            bundle = response.json()
                            entries = bundle.get("entry", [])
                            
                            if not entries:
                                break
                            
                            # Extract resources
                            for entry in entries:
                                resource = entry.get("resource")
                                if resource:
                                    resources.append(resource)
                            
                            # Check for next link (pagination)
                            next_link = None
                            for link in bundle.get("link", []):
                                if link.get("relation") == "next":
                                    next_link = link.get("url")
                                    break
                            
                            if not next_link:
                                break
                            
                            # Use next link for pagination
                            search_url = next_link
                            params = {}  # Next link already includes parameters
                            page_count += 1
                        else:
                            logger.error(f"Error fetching {resource_type}: {response.status_code} - {response.text}")
                            break
                    
                    except Exception as e:
                        logger.error(f"Error during pagination for {resource_type}: {e}")
                        break
                
                # Save resources to NDJSON file
                if resources:
                    filename = f"{resource_type}.ndjson"
                    filepath = os.path.join(output_dir, filename)
                    
                    with open(filepath, "w", encoding="utf-8") as f:
                        for resource in resources:
                            f.write(json.dumps(resource) + "\n")
                    
                    files_created.append({
                        "resource_type": resource_type,
                        "filename": filename,
                        "count": len(resources)
                    })
                    
                    total_resources += len(resources)
                    logger.info(f"Saved {len(resources)} {resource_type} resources to {filename}")
        
        # Update job status
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["files"] = files_created
        jobs[job_id]["total_resources"] = total_resources
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        jobs[job_id]["message"] = f"Successfully fetched {total_resources} resources"
        
        logger.info(f"Job {job_id} completed: {total_resources} resources fetched")
        
        # Automatically trigger transform and load
        if total_resources > 0:
            logger.info(f"Starting auto transform and load for job {job_id}")
            await auto_transform_and_load(job_id, resource_types)
    
    except Exception as e:
        logger.error(f"Error in fetch_via_search for job {job_id}: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["completed_at"] = datetime.now().isoformat()


from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import httpx
import asyncio
import logging
from datetime import datetime
import os
import json

from app.core.config import settings
from app.core.smart_auth import SMARTBackendAuth
from app.core.retry_utils import RetryConfig, retry_with_backoff, ProgressTracker, retry_http_call

router = APIRouter()
logger = logging.getLogger(__name__)

class BulkDataRequest(BaseModel):
    fhir_server_url: str
    resource_types: List[str]
    since: Optional[str] = None
    bearer_token: Optional[str] = None
    # SMART Backend Services authentication
    use_smart_auth: Optional[bool] = False
    token_url: Optional[str] = None
    client_id: Optional[str] = None
    private_key: Optional[str] = None
    jwks_url: Optional[str] = None
    algorithm: Optional[str] = "RS384"

class BulkDataStatus(BaseModel):
    job_id: str
    status: str
    progress: int
    message: str

class ResumeExportRequest(BaseModel):
    """Request to resume a bulk export from a status URL"""
    status_url: str
    bearer_token: Optional[str] = None

# In-memory job tracking (in production, use Redis or database)
jobs = {}

# Retry configuration for different operations
RETRY_CONFIG_NETWORK = RetryConfig(
    max_attempts=settings.RETRY_MAX_ATTEMPTS,
    base_delay=settings.RETRY_BASE_DELAY,
    max_delay=settings.RETRY_MAX_DELAY
)

RETRY_CONFIG_DOWNLOAD = RetryConfig(
    max_attempts=settings.RETRY_MAX_ATTEMPTS + 2,  # More retries for downloads
    base_delay=settings.RETRY_BASE_DELAY,
    max_delay=settings.RETRY_MAX_DELAY
)

# HTTP timeout configuration
HTTP_TIMEOUT = httpx.Timeout(
    connect=settings.HTTP_TIMEOUT_CONNECT,
    read=settings.HTTP_TIMEOUT_READ,
    write=settings.HTTP_TIMEOUT_WRITE,
    pool=settings.HTTP_TIMEOUT_POOL
)

@router.post("/kick-off")
async def kick_off_bulk_export(
    request: BulkDataRequest,
    background_tasks: BackgroundTasks
):
    """
    Initiate FHIR Bulk Data export following the FHIR Bulk Data Access spec.
    If $export is not supported, falls back to regular FHIR search.
    https://hl7.org/fhir/uv/bulkdata/export/index.html
    
    Enhanced with:
    - Automatic retry with exponential backoff
    - Detailed progress logging
    - Configurable timeouts
    """
    
    logger.info(f"🚀 Starting bulk export from {request.fhir_server_url}")
    logger.info(f"📋 Resource types: {', '.join(request.resource_types)}")
    if request.since:
        logger.info(f"📅 Since: {request.since}")
    
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
    
    # Handle authentication
    if request.use_smart_auth and request.token_url and request.client_id and request.private_key:
        # Use SMART Backend Services authentication
        logger.info("🔐 Using SMART Backend Services authentication")
        try:
            smart_auth = SMARTBackendAuth(
                token_url=request.token_url,
                client_id=request.client_id,
                private_key=request.private_key,
                jwks_url=request.jwks_url,
                algorithm=request.algorithm or "RS384"
            )
            
            # Get access token with retry
            auth_headers = await smart_auth.get_auth_header(scope="system/*.read")
            headers.update(auth_headers)
            
            logger.info("✅ SMART authentication successful")
            
        except Exception as e:
            logger.error(f"❌ SMART authentication failed: {e}")
            raise HTTPException(
                status_code=401,
                detail=f"SMART authentication failed: {str(e)}"
            )
    
    elif request.bearer_token:
        # Use provided bearer token
        headers["Authorization"] = f"Bearer {request.bearer_token}"
        logger.info("🔐 Using provided bearer token")
    
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            # Use retry mechanism for kick-off request
            response = await retry_http_call(
                client, 
                "GET", 
                export_url, 
                RETRY_CONFIG_NETWORK,
                params=params, 
                headers=headers
            )
            
            if response.status_code == 202:
                # Bulk export supported - use async workflow
                status_url = response.headers.get("Content-Location")
                job_id = status_url.split("/")[-1] if status_url else str(datetime.now().timestamp())
                
                logger.info(f"✅ Bulk export accepted! Job ID: {job_id}")
                logger.info(f"📍 Status endpoint: {status_url}")
                
                jobs[job_id] = {
                    "status": "in-progress",
                    "status_url": status_url,
                    "fhir_server_url": request.fhir_server_url,
                    "resource_types": request.resource_types,
                    "started_at": datetime.now().isoformat(),
                    "method": "bulk_export",
                    "headers": headers  # Store headers for resume capability
                }
                
                background_tasks.add_task(poll_export_status, job_id, status_url, headers)
                
                return {
                    "job_id": job_id,
                    "status": "accepted",
                    "message": "Bulk export initiated",
                    "status_url": status_url,
                    "tip": "If this export fails, you can resume it using the /resume endpoint with the status_url"
                }
            else:
                # $export not supported, use regular FHIR search as fallback
                logger.info(f"ℹ️  $export not supported (status {response.status_code}), using FHIR search fallback")
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
        logger.error(f"❌ Error connecting to FHIR server: {e}")
        raise HTTPException(status_code=500, detail=f"Error connecting to FHIR server: {str(e)}")

@router.post("/resume")
async def resume_bulk_export(
    request: ResumeExportRequest,
    background_tasks: BackgroundTasks
):
    """
    Resume a bulk export from a status URL (useful if the export was interrupted)
    
    This allows you to continue monitoring an export that was started but the
    client connection was lost or the process was interrupted.
    """
    
    logger.info(f"🔄 Resuming bulk export from status URL: {request.status_url}")
    
    # Generate job ID from status URL
    job_id = f"resume_{request.status_url.split('/')[-1]}"
    
    headers = {
        "Accept": "application/fhir+json"
    }
    
    if request.bearer_token:
        headers["Authorization"] = f"Bearer {request.bearer_token}"
    
    # Check if we already have this job
    if job_id in jobs:
        logger.info(f"ℹ️  Job {job_id} already exists, returning existing status")
        return {
            "job_id": job_id,
            "status": "resumed",
            "message": "Job already exists, monitoring will continue",
            "current_status": jobs[job_id].get("status")
        }
    
    # Create new job entry for resumed export
    jobs[job_id] = {
        "status": "in-progress",
        "status_url": request.status_url,
        "started_at": datetime.now().isoformat(),
        "method": "bulk_export_resumed",
        "headers": headers
    }
    
    # Start polling in background
    background_tasks.add_task(poll_export_status, job_id, request.status_url, headers)
    
    logger.info(f"✅ Resumed monitoring for job {job_id}")
    
    return {
        "job_id": job_id,
        "status": "resumed",
        "message": "Export resumed, now monitoring for completion",
        "status_url": request.status_url
    }

async def poll_export_status(job_id: str, status_url: str, headers: dict):
    """
    Poll the export status endpoint until completion
    
    Enhanced with:
    - Automatic retry on transient failures
    - Progress logging
    - Better error handling
    """
    
    logger.info(f"👀 Starting to poll status for job {job_id}")
    poll_count = 0
    
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        while True:
            poll_count += 1
            
            try:
                # Use retry mechanism for status polling
                response = await retry_http_call(
                    client,
                    "GET",
                    status_url,
                    RETRY_CONFIG_NETWORK,
                    headers=headers
                )
                
                if response.status_code == 200:
                    # Export completed
                    result = response.json()
                    logger.info(f"🎉 Export completed for job {job_id} after {poll_count} status checks")
                    
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
                        logger.warning(f"⚠️  Bulk export reported error: {error_msg}")
                        
                        # Check if error is "Too many files" - try fallback
                        if "too many files" in str(error_msg).lower():
                            logger.info(f"🔄 Too many files error, switching to FHIR search fallback for job {job_id}")
                            
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
                    output_count = len(result.get("output", []))
                    logger.info(f"📦 Found {output_count} file(s) to download")
                    
                    jobs[job_id]["status"] = "downloading"
                    jobs[job_id]["result"] = result
                    jobs[job_id]["file_count"] = output_count
                    
                    # Download files with progress tracking (pass headers for authentication)
                    await download_bulk_files(job_id, result, headers)
                    
                    jobs[job_id]["status"] = "completed"
                    jobs[job_id]["completed_at"] = datetime.now().isoformat()
                    break
                
                elif response.status_code == 202:
                    # Still in progress
                    if poll_count % 6 == 0:  # Log every 6th poll (every 30 seconds if polling every 5s)
                        logger.info(f"⏳ Export still in progress for job {job_id} (checked {poll_count} times)")
                    
                    # Check for X-Progress header if available
                    progress_header = response.headers.get("X-Progress")
                    if progress_header:
                        jobs[job_id]["progress"] = progress_header
                        logger.info(f"📊 Progress: {progress_header}")
                    
                    await asyncio.sleep(5)  # Wait 5 seconds before next poll
                    continue
                
                else:
                    # HTTP Error - check if we should fallback
                    error_text = response.text
                    logger.warning(f"⚠️  Bulk export error (status {response.status_code}): {error_text}")
                    
                    if "too many files" in error_text.lower():
                        logger.info(f"🔄 Too many files error, switching to FHIR search fallback for job {job_id}")
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
                logger.error(f"❌ Error polling export status: {type(e).__name__}: {e}")
                jobs[job_id]["status"] = "failed"
                jobs[job_id]["error"] = str(e)
                break

async def download_bulk_files(job_id: str, result: dict, auth_headers: dict = None):
    """
    Download NDJSON files from bulk export result
    
    Enhanced with:
    - Automatic retry on download failures
    - Progress tracking
    - Authentication support
    
    Args:
        job_id: Job identifier
        result: Bulk export result with output file URLs
        auth_headers: Authentication headers (e.g., Authorization: Bearer token)
    """
    
    output_dir = os.path.join(settings.BULK_DATA_DIR, job_id)
    os.makedirs(output_dir, exist_ok=True)
    
    files_downloaded = []
    output_files = result.get("output", [])
    
    if not output_files:
        logger.warning(f"⚠️  No output files found for job {job_id}")
        return
    
    # Initialize progress tracker
    progress = ProgressTracker(
        total=len(output_files),
        operation_name=f"Download files for job {job_id}",
        log_interval=settings.PROGRESS_LOG_INTERVAL
    )
    
    logger.info(f"📥 Starting download of {len(output_files)} file(s)")
    
    # Prepare download headers (include authentication if provided)
    download_headers = {"Accept": "application/fhir+ndjson"}
    if auth_headers:
        download_headers.update(auth_headers)
        logger.info("🔐 Using authenticated downloads")
    
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        for idx, output in enumerate(output_files, 1):
            url = output.get("url")
            resource_type = output.get("type")
            
            if not url:
                logger.warning(f"⚠️  Skipping output entry {idx} - no URL provided")
                progress.update()
                continue
            
            try:
                logger.info(f"📥 [{idx}/{len(output_files)}] Downloading {resource_type} from {url[:100]}...")
                
                # Use retry mechanism for downloads (with authentication headers)
                @retry_with_backoff(RETRY_CONFIG_DOWNLOAD)
                async def download_file():
                    return await client.get(url, headers=download_headers)
                
                response = await download_file()
                
                if response.status_code == 200:
                    filename = f"{resource_type}.ndjson"
                    filepath = os.path.join(output_dir, filename)
                    
                    # Write file
                    with open(filepath, "wb") as f:
                        f.write(response.content)
                    
                    file_size_mb = len(response.content) / (1024 * 1024)
                    
                    files_downloaded.append({
                        "resource_type": resource_type,
                        "filename": filename,
                        "size_bytes": len(response.content),
                        "size_mb": round(file_size_mb, 2)
                    })
                    
                    logger.info(f"✅ Downloaded {filename} ({file_size_mb:.2f} MB)")
                else:
                    logger.error(f"❌ Failed to download {resource_type}: HTTP {response.status_code}")
            
            except Exception as e:
                logger.error(f"❌ Error downloading file {url}: {type(e).__name__}: {e}")
            
            finally:
                progress.update()
    
    progress.complete()
    
    jobs[job_id]["files"] = files_downloaded
    jobs[job_id]["download_completed_at"] = datetime.now().isoformat()
    
    total_size_mb = sum(f["size_mb"] for f in files_downloaded)
    logger.info(f"📦 Downloaded {len(files_downloaded)}/{len(output_files)} files successfully (total: {total_size_mb:.2f} MB)")
    
    # Automatically trigger transform and load after download
    if files_downloaded:
        logger.info(f"🔄 Starting auto transform and load after bulk download")
        resource_types = list(set([f["resource_type"] for f in files_downloaded]))
        await auto_transform_and_load(job_id, resource_types)

@router.get("/status/{job_id}")
async def get_export_status(job_id: str):
    """Get the status of a bulk export job"""
    
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_info = jobs[job_id]
    
    # Calculate elapsed time
    if "started_at" in job_info:
        started = datetime.fromisoformat(job_info["started_at"])
        elapsed_seconds = (datetime.now() - started).total_seconds()
        job_info["elapsed_seconds"] = round(elapsed_seconds, 1)
        job_info["elapsed_minutes"] = round(elapsed_seconds / 60, 1)
    
    return job_info

@router.get("/jobs")
async def list_jobs():
    """List all bulk export jobs with summary information"""
    return {
        "total": len(jobs),
        "jobs": [
            {
                "job_id": job_id,
                "status": job_info["status"],
                "method": job_info.get("method"),
                "started_at": job_info.get("started_at"),
                "completed_at": job_info.get("completed_at"),
                "resource_types": job_info.get("resource_types"),
                "files_downloaded": len(job_info.get("files", [])),
                "records_loaded": job_info.get("records_loaded"),
                "status_url": job_info.get("status_url")  # Include for resume capability
            }
            for job_id, job_info in jobs.items()
        ]
    }

async def auto_transform_and_load(job_id: str, resource_types: List[str]):
    """
    Automatically transform NDJSON files and load into database
    
    Enhanced with progress tracking
    """
    try:
        logger.info(f"🔄 [{job_id}] Starting auto transform and load process...")
        
        # Import transformer and loader
        from app.services.fhir_transformer import FHIRTransformer
        from app.services.database_loader import DatabaseLoader
        
        job_dir = os.path.join(settings.BULK_DATA_DIR, job_id)
        transformer = FHIRTransformer()
        loader = DatabaseLoader()
        
        total_transformed = 0
        total_loaded = 0
        
        # Progress tracker
        progress = ProgressTracker(
            total=len(resource_types),
            operation_name=f"Transform & Load for job {job_id}",
            log_interval=settings.PROGRESS_LOG_INTERVAL
        )
        
        # Process each resource type
        for resource_type in resource_types:
            ndjson_file = os.path.join(job_dir, f"{resource_type}.ndjson")
            
            if not os.path.exists(ndjson_file):
                logger.warning(f"⚠️  [{job_id}] File not found: {ndjson_file}")
                progress.update()
                continue
            
            try:
                # Transform NDJSON to structured JSON
                logger.info(f"🔄 [{job_id}] Transforming {resource_type}...")
                transform_result = await transformer.transform_file(ndjson_file, resource_type)
                total_transformed += transform_result["processed"]
                logger.info(f"✅ [{job_id}] Transformed {transform_result['processed']} {resource_type} records")
                
                # Load into database
                logger.info(f"💾 [{job_id}] Loading {resource_type} into database with job_id={job_id}...")
                load_result = await loader.load_file(transform_result["output_file"], resource_type, job_id=job_id)
                total_loaded += load_result["loaded"]
                logger.info(f"✅ [{job_id}] Loaded {load_result['loaded']} {resource_type} records")
                
            except Exception as e:
                logger.error(f"❌ [{job_id}] Error processing {resource_type}: {type(e).__name__}: {e}")
            finally:
                progress.update()
        
        progress.complete()
        
        # Update job status with load info
        if job_id in jobs:
            jobs[job_id]["transform_load_completed"] = datetime.now().isoformat()
            jobs[job_id]["records_transformed"] = total_transformed
            jobs[job_id]["records_loaded"] = total_loaded
            jobs[job_id]["message"] = f"Successfully loaded {total_loaded} records into database"
        
        logger.info(f"🎉 [{job_id}] Auto transform and load completed: {total_loaded} records loaded")
        
    except Exception as e:
        logger.error(f"❌ [{job_id}] Error in auto_transform_and_load: {type(e).__name__}: {e}")
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
    
    Enhanced with:
    - Retry mechanism
    - Progress tracking
    - Better pagination handling
    """
    try:
        logger.info(f"🔍 [{job_id}] Starting FHIR search fallback method")
        
        output_dir = os.path.join(settings.BULK_DATA_DIR, job_id)
        os.makedirs(output_dir, exist_ok=True)
        
        total_resources = 0
        files_created = []
        
        # Progress tracker
        progress = ProgressTracker(
            total=len(resource_types),
            operation_name=f"FHIR search for job {job_id}",
            log_interval=settings.PROGRESS_LOG_INTERVAL
        )
        
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            for resource_type in resource_types:
                logger.info(f"🔍 [{job_id}] Fetching {resource_type} resources...")
                
                # Build search URL
                search_url = f"{fhir_server_url}/{resource_type}"
                params = {"_count": "100"}  # Fetch 100 at a time
                
                if since:
                    params["_lastUpdated"] = f"ge{since}"
                
                resources = []
                page_count = 0
                max_pages = 10  # Limit to 10 pages (1000 resources) per type
                
                while page_count < max_pages:
                    try:
                        # Use retry mechanism
                        response = await retry_http_call(
                            client,
                            "GET",
                            search_url,
                            RETRY_CONFIG_NETWORK,
                            params=params,
                            headers=headers
                        )
                        
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
                            
                            logger.info(f"📄 [{job_id}] Page {page_count + 1}: fetched {len(entries)} {resource_type} resources")
                            
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
                            logger.error(f"❌ Error fetching {resource_type}: HTTP {response.status_code}")
                            break
                    
                    except Exception as e:
                        logger.error(f"❌ Error during pagination for {resource_type}: {type(e).__name__}: {e}")
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
                    logger.info(f"✅ [{job_id}] Saved {len(resources)} {resource_type} resources to {filename}")
                
                progress.update()
        
        progress.complete()
        
        # Update job status
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["files"] = files_created
        jobs[job_id]["total_resources"] = total_resources
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        jobs[job_id]["message"] = f"Successfully fetched {total_resources} resources"
        
        logger.info(f"🎉 [{job_id}] FHIR search completed: {total_resources} resources fetched")
        
        # Automatically trigger transform and load
        if total_resources > 0:
            logger.info(f"🔄 [{job_id}] Starting auto transform and load")
            await auto_transform_and_load(job_id, resource_types)
    
    except Exception as e:
        logger.error(f"❌ Error in fetch_via_search for job {job_id}: {type(e).__name__}: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["completed_at"] = datetime.now().isoformat()

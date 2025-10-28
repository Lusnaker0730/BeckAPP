"""
Cache Management API Routes

Provides endpoints for monitoring and managing Redis cache
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
import logging

from app.core.security import get_current_user, require_role
from app.core.cache import (
    get_cache_stats,
    invalidate_cache,
    clear_all_cache,
    invalidate_diagnosis_cache,
    invalidate_analytics_cache,
    invalidate_all_after_etl,
    REDIS_AVAILABLE
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/stats")
async def get_cache_statistics(
    current_user: dict = Depends(get_current_user)
):
    """
    Get Redis cache statistics
    
    Returns cache hit/miss rates, memory usage, and other metrics
    """
    if not REDIS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Redis cache is not available"
        )
    
    stats = get_cache_stats()
    
    if stats and stats.get("status") == "error":
        raise HTTPException(
            status_code=500,
            detail=f"Error getting cache stats: {stats.get('error')}"
        )
    
    return {
        "status": "success",
        "data": stats
    }


@router.post("/invalidate")
async def invalidate_cache_pattern(
    pattern: str,
    current_user: dict = Depends(require_role(["admin", "engineer"]))
):
    """
    Invalidate cache entries matching a pattern
    
    Args:
        pattern: Redis key pattern (e.g., "diagnosis:*", "top_conditions:*")
    
    Requires: admin or engineer role
    """
    if not REDIS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Redis cache is not available"
        )
    
    try:
        deleted_count = invalidate_cache(pattern)
        logger.info(f"User {current_user.get('sub')} invalidated {deleted_count} cache entries with pattern: {pattern}")
        
        return {
            "status": "success",
            "message": f"Invalidated {deleted_count} cache entries",
            "pattern": pattern,
            "deleted_count": deleted_count
        }
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error invalidating cache: {str(e)}"
        )


@router.post("/clear-all")
async def clear_all_cache_entries(
    current_user: dict = Depends(require_role(["admin"]))
):
    """
    Clear ALL cache entries (use with caution!)
    
    Requires: admin role only
    """
    if not REDIS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Redis cache is not available"
        )
    
    try:
        success = clear_all_cache()
        
        if success:
            logger.warning(f"User {current_user.get('sub')} cleared ALL cache entries")
            return {
                "status": "success",
                "message": "All cache entries cleared successfully"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to clear cache"
            )
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing cache: {str(e)}"
        )


@router.post("/invalidate/diagnosis")
async def invalidate_diagnosis_cache_endpoint(
    current_user: dict = Depends(require_role(["admin", "engineer"]))
):
    """
    Invalidate all diagnosis-related cache
    
    Useful after ETL jobs complete or data updates
    """
    if not REDIS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Redis cache is not available"
        )
    
    try:
        invalidate_diagnosis_cache()
        logger.info(f"User {current_user.get('sub')} invalidated diagnosis cache")
        
        return {
            "status": "success",
            "message": "Diagnosis cache invalidated"
        }
    except Exception as e:
        logger.error(f"Error invalidating diagnosis cache: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )


@router.post("/invalidate/analytics")
async def invalidate_analytics_cache_endpoint(
    current_user: dict = Depends(require_role(["admin", "engineer"]))
):
    """
    Invalidate all analytics-related cache
    """
    if not REDIS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Redis cache is not available"
        )
    
    try:
        invalidate_analytics_cache()
        logger.info(f"User {current_user.get('sub')} invalidated analytics cache")
        
        return {
            "status": "success",
            "message": "Analytics cache invalidated"
        }
    except Exception as e:
        logger.error(f"Error invalidating analytics cache: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )


@router.post("/invalidate/after-etl")
async def invalidate_after_etl_endpoint(
    current_user: dict = Depends(require_role(["admin", "engineer"]))
):
    """
    Invalidate all relevant cache after ETL job completes
    
    This should be called automatically after ETL jobs finish
    """
    if not REDIS_AVAILABLE:
        return {
            "status": "success",
            "message": "Redis not available, no cache to invalidate"
        }
    
    try:
        total_deleted = invalidate_all_after_etl()
        logger.info(f"User {current_user.get('sub')} invalidated {total_deleted} entries after ETL")
        
        return {
            "status": "success",
            "message": f"Invalidated {total_deleted} cache entries after ETL",
            "deleted_count": total_deleted
        }
    except Exception as e:
        logger.error(f"Error invalidating cache after ETL: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )


@router.get("/health")
async def check_cache_health():
    """
    Check if Redis cache is available and healthy
    """
    if not REDIS_AVAILABLE:
        return {
            "status": "unavailable",
            "message": "Redis cache is not available. API will work but without caching."
        }
    
    try:
        stats = get_cache_stats()
        if stats and stats.get("status") != "error":
            return {
                "status": "healthy",
                "message": "Redis cache is operational",
                "total_keys": stats.get("total_keys", 0)
            }
        else:
            return {
                "status": "error",
                "message": f"Redis cache error: {stats.get('error')}"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error checking cache health: {str(e)}"
        }


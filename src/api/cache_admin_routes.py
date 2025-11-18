"""Cache administration endpoints for semantic cache management."""

import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel

from fastapi import APIRouter, HTTPException, status

from src.services.semantic_cache import get_cache_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/cache", tags=["Cache Admin"])


# ============================================================================
# Request/Response Models
# ============================================================================

class CacheStatsResponse(BaseModel):
    """Cache statistics response."""
    status: str
    total_entries: int
    total_hits: int
    avg_hits_per_entry: Optional[float]
    max_hits: Optional[int]
    entries_with_hits: int
    entries_never_hit: int
    hit_percentage: Optional[float]
    table_size: str
    data_size: str
    index_size: str

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "total_entries": 150,
                "total_hits": 500,
                "avg_hits_per_entry": 3.33,
                "max_hits": 25,
                "entries_with_hits": 130,
                "entries_never_hit": 20,
                "hit_percentage": 86.67,
                "table_size": "256 MB",
                "data_size": "200 MB",
                "index_size": "50 MB"
            }
        }


class InvalidateCacheRequest(BaseModel):
    """Request to invalidate cache entries."""
    query_id: Optional[int] = None
    model_name: Optional[str] = None
    older_than_hours: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "query_id": None,
                "model_name": "claude-3-5-sonnet-20241022",
                "older_than_hours": 24
            }
        }


class InvalidateCacheResponse(BaseModel):
    """Response from cache invalidation."""
    status: str
    entries_deleted: int
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "entries_deleted": 45,
                "message": "Successfully deleted 45 cache entries older than 24 hours"
            }
        }


class CacheHealthResponse(BaseModel):
    """Cache health check response."""
    status: str
    healthy: bool
    total_entries: int
    total_hits: int
    hit_rate: Optional[float]
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "healthy": True,
                "total_entries": 150,
                "total_hits": 500,
                "hit_rate": 0.65,
                "message": "Cache is operational with 65% hit rate"
            }
        }


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/stats", response_model=CacheStatsResponse)
async def get_cache_stats():
    """
    Get cache performance statistics.

    **Returns:**
    - Cache statistics including hit rate, size, and entry count

    **Example Response:**
    ```json
    {
        "status": "healthy",
        "total_entries": 150,
        "total_hits": 500,
        "avg_hits_per_entry": 3.33,
        "max_hits": 25,
        "hit_percentage": 86.67
    }
    ```
    """
    try:
        cache_service = get_cache_service()
        if not cache_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Cache service not initialized"
            )

        stats = await cache_service.get_cache_stats()

        return CacheStatsResponse(
            status="healthy",
            total_entries=stats.get("total_entries", 0),
            total_hits=stats.get("total_hits", 0),
            avg_hits_per_entry=stats.get("avg_hits_per_entry"),
            max_hits=stats.get("max_hits"),
            entries_with_hits=stats.get("entries_with_hits", 0),
            entries_never_hit=stats.get("entries_never_hit", 0),
            hit_percentage=stats.get("hit_percentage"),
            table_size=stats.get("table_size", "Unknown"),
            data_size=stats.get("data_size", "Unknown"),
            index_size=stats.get("index_size", "Unknown")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache stats: {str(e)[:100]}"
        )


@router.get("/health", response_model=CacheHealthResponse)
async def check_cache_health():
    """
    Check cache service health.

    **Returns:**
    - Health status, hit rate, and operational metrics

    **Example Response:**
    ```json
    {
        "status": "healthy",
        "healthy": true,
        "total_entries": 150,
        "total_hits": 500,
        "hit_rate": 0.65,
        "message": "Cache is operational with 65% hit rate"
    }
    ```
    """
    try:
        cache_service = get_cache_service()
        if not cache_service:
            return CacheHealthResponse(
                status="unavailable",
                healthy=False,
                total_entries=0,
                total_hits=0,
                hit_rate=None,
                message="Cache service not initialized"
            )

        stats = await cache_service.get_cache_stats()

        total_entries = stats.get("total_entries", 0)
        total_hits = stats.get("total_hits", 0)
        hit_rate = total_hits / total_entries if total_entries > 0 else 0

        is_healthy = True
        message = f"Cache is operational with {hit_rate * 100:.1f}% hit rate"

        return CacheHealthResponse(
            status="healthy" if is_healthy else "degraded",
            healthy=is_healthy,
            total_entries=total_entries,
            total_hits=total_hits,
            hit_rate=hit_rate,
            message=message
        )

    except Exception as e:
        logger.error(f"Error checking cache health: {e}", exc_info=True)
        return CacheHealthResponse(
            status="error",
            healthy=False,
            total_entries=0,
            total_hits=0,
            hit_rate=None,
            message=f"Error checking health: {str(e)[:100]}"
        )


@router.post("/invalidate", response_model=InvalidateCacheResponse)
async def invalidate_cache(request: InvalidateCacheRequest):
    """
    Invalidate cache entries based on criteria.

    **Parameters:**
    - **query_id**: Delete specific query by ID (optional)
    - **model_name**: Delete all entries for a specific model (optional)
    - **older_than_hours**: Delete entries older than specified hours (optional)

    **Returns:**
    - Number of entries deleted and operation status

    **Examples:**
    ```json
    // Delete all entries older than 24 hours
    {
        "older_than_hours": 24
    }

    // Delete all entries for a specific model
    {
        "model_name": "claude-3-5-sonnet-20241022"
    }

    // Delete a specific cache entry
    {
        "query_id": 123
    }
    ```

    **Response:**
    ```json
    {
        "status": "success",
        "entries_deleted": 45,
        "message": "Successfully deleted 45 cache entries older than 24 hours"
    }
    ```
    """
    try:
        cache_service = get_cache_service()
        if not cache_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Cache service not initialized"
            )

        count = await cache_service.invalidate_cache(
            query_id=request.query_id,
            model_name=request.model_name,
            older_than_hours=request.older_than_hours
        )

        # Build message based on what was deleted
        message = f"Successfully deleted {count} cache entries"
        if request.query_id:
            message = f"Successfully deleted cache entry (ID: {request.query_id})"
        elif request.model_name:
            message = f"Successfully deleted {count} cache entries for model '{request.model_name}'"
        elif request.older_than_hours:
            message = f"Successfully deleted {count} cache entries older than {request.older_than_hours} hours"

        logger.info(message)

        return InvalidateCacheResponse(
            status="success",
            entries_deleted=count,
            message=message
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to invalidate cache: {str(e)[:100]}"
        )


@router.post("/clear", response_model=Dict[str, Any])
async def clear_cache():
    """
    Clear all cache entries (use with caution!).

    **WARNING:** This operation will delete all cached responses.

    **Returns:**
    - Confirmation of cache clearing operation

    **Response:**
    ```json
    {
        "status": "success",
        "message": "Cache cleared successfully",
        "entries_deleted": 150
    }
    ```
    """
    try:
        cache_service = get_cache_service()
        if not cache_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Cache service not initialized"
            )

        # Clear all entries by deleting without conditions
        count = await cache_service.invalidate_cache()

        logger.warning(f"Cache cleared: {count} entries deleted")

        return {
            "status": "success",
            "message": "Cache cleared successfully",
            "entries_deleted": count
        }

    except Exception as e:
        logger.error(f"Error clearing cache: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)[:100]}"
        )

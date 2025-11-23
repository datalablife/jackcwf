#!/usr/bin/env python3
"""
FastAPI integration with Redis cache and performance optimizations.

This module extends the main FastAPI app with:
- Redis cache initialization
- Cache middleware
- Performance monitoring
- Optimized database connection pooling
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.infrastructure.redis_cache import RedisCache, set_redis_cache
from src.middleware.cache_middleware import CacheMiddleware, CacheWarmup
from src.infrastructure.cache_metrics import setup_cache_metrics

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan_with_cache(app: FastAPI):
    """
    Enhanced lifespan manager with Redis cache.

    This should replace or extend the existing lifespan function in main.py.
    """
    # Startup
    logger.info("Starting application with performance optimizations...")

    # Initialize Redis cache
    redis_cache = RedisCache()
    cache_initialized = await redis_cache.initialize()

    if cache_initialized:
        set_redis_cache(redis_cache)
        logger.info("Redis cache initialized successfully")

        # Warm up cache with hot data
        warmup = CacheWarmup()
        try:
            warmup_results = await warmup.warmup_all()
            logger.info(f"Cache warmup complete: {warmup_results}")
        except Exception as e:
            logger.warning(f"Cache warmup failed: {e}")

        # Setup Prometheus metrics for cache
        setup_cache_metrics(app)
    else:
        logger.warning("Redis cache initialization failed - running without cache")

    yield

    # Shutdown
    logger.info("Shutting down application...")

    if cache_initialized:
        await redis_cache.close()
        logger.info("Redis cache closed")


def setup_performance_optimizations(app: FastAPI):
    """
    Apply all performance optimizations to FastAPI app.

    Call this function in main.py after creating the FastAPI app:

    ```python
    from src.integrations.fastapi_redis_integration import setup_performance_optimizations

    app = FastAPI(lifespan=lifespan_with_cache)
    setup_performance_optimizations(app)
    ```
    """
    # Add cache middleware
    app.add_middleware(CacheMiddleware, default_ttl=3600)
    logger.info("Cache middleware enabled")

    # Add performance monitoring middleware
    from src.middleware.performance_middleware import PerformanceMonitoringMiddleware
    app.add_middleware(PerformanceMonitoringMiddleware)
    logger.info("Performance monitoring middleware enabled")

    return app


# Example of optimized route with caching
"""
from src.middleware.cache_middleware import cache_response, invalidate_cache_pattern

@router.get("/api/conversations")
@cache_response(ttl=7200, key_prefix="conv_list", include_user=True)
async def list_conversations(
    request: Request,
    user_id: str = Header(..., alias="X-User-ID"),
    session: AsyncSession = Depends(get_async_session)
):
    # This response will be cached for 2 hours per user
    from src.infrastructure.query_optimization import get_conversations_with_messages_optimized
    from src.infrastructure.redis_cache import get_redis_cache

    conversations = await get_conversations_with_messages_optimized(
        session,
        user_id,
        cache=get_redis_cache()
    )

    return {
        "conversations": [conv.to_dict() for conv in conversations],
        "count": len(conversations)
    }


@router.post("/api/conversations")
@invalidate_cache_pattern("conv_list:*")
async def create_conversation(
    data: ConversationCreate,
    session: AsyncSession = Depends(get_async_session)
):
    # Creating a conversation will invalidate all conversation list caches
    conversation = await conversation_service.create(session, data)
    return conversation
"""

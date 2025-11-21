"""FastAPI main application for LangChain AI Conversation."""

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
import asyncpg
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

# Load environment variables from .env file
load_dotenv()

from src.db.config import engine
from src.db.migrations import init_db
from src.exceptions import APIException
from src.infrastructure.shutdown import get_shutdown_manager
from src.services.semantic_cache import SemanticCacheService, set_cache_service

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI app.

    Handles startup and shutdown events with graceful shutdown support.
    Includes initialization of semantic cache service for RAG optimization.
    """
    # Startup
    logger.info("Starting LangChain AI Conversation backend...")
    try:
        await init_db(engine)
        logger.info("Database initialization completed")

        # Initialize asyncpg connection pool for semantic cache
        logger.info("Initializing asyncpg connection pool for semantic cache...")
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            logger.warning("DATABASE_URL not set, skipping semantic cache initialization")
        else:
            try:
                # Convert SQLAlchemy URL format to asyncpg format
                # From: postgresql+asyncpg://user:pass@host:port/db
                # To:   postgresql://user:pass@host:port/db
                asyncpg_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

                app.state.db_pool = await asyncpg.create_pool(
                    asyncpg_url,
                    min_size=5,
                    max_size=20,
                    command_timeout=60,
                    max_inactive_connection_lifetime=300
                )
                logger.info("asyncpg connection pool created successfully")

                # Initialize semantic cache service
                logger.info("Initializing semantic cache service...")
                cache_service = SemanticCacheService(app.state.db_pool)
                init_success = await cache_service.initialize()

                if init_success:
                    set_cache_service(cache_service)
                    logger.info("✅ Semantic cache initialized successfully")

                    # Initialize cache stats updater for Prometheus metrics
                    logger.info("Initializing cache stats updater...")
                    from src.infrastructure.cache_stats_updater import start_cache_stats_updater
                    await start_cache_stats_updater(interval_seconds=30)
                    logger.info("✅ Cache stats updater started (30s interval)")
                else:
                    logger.warning("⚠️ Semantic cache initialization failed - running without cache")
            except Exception as e:
                logger.error(f"Failed to initialize semantic cache: {e}", exc_info=True)
                logger.warning("⚠️ Semantic cache initialization failed - running without cache")

        # Setup graceful shutdown
        shutdown_manager = get_shutdown_manager()
        await shutdown_manager.setup_signal_handlers()
        logger.info("Graceful shutdown handlers registered")

    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down LangChain AI Conversation backend...")

    # Stop cache stats updater
    try:
        from src.infrastructure.cache_stats_updater import stop_cache_stats_updater
        await stop_cache_stats_updater()
        logger.info("Cache stats updater stopped")
    except Exception as e:
        logger.error(f"Error stopping cache stats updater: {e}")

    # Close asyncpg pool if it exists
    if hasattr(app.state, "db_pool") and app.state.db_pool:
        try:
            await app.state.db_pool.close()
            logger.info("asyncpg connection pool closed")
        except Exception as e:
            logger.error(f"Error closing asyncpg pool: {e}")

    shutdown_manager = get_shutdown_manager()
    try:
        await shutdown_manager.shutdown()
        await shutdown_manager.cleanup_resources()
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    finally:
        logger.info("Shutdown completed")


# Create FastAPI application
app = FastAPI(
    title="LangChain AI Conversation API",
    description="API for LangChain v1.0 AI Conversation with Agents and RAG",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")
ALLOWED_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware stack (in REVERSE order - last added executes first in request processing)
# Execution order: Authentication → ContentModeration → MemoryInjection → ResponseStructuring → AuditLogging
logger.info("Registering middleware stack...")
from src.middleware.audit_logging_middleware import AuditLoggingMiddleware
from src.middleware.response_structuring_middleware import ResponseStructuringMiddleware
from src.middleware.content_moderation_middleware import ContentModerationMiddleware
from src.middleware.memory_injection_middleware import MemoryInjectionMiddleware
from src.middleware.auth_middleware import AuthenticationMiddleware

# Add in REVERSE order (last added = first executed in request processing)
app.add_middleware(AuditLoggingMiddleware)  # Last in execution (logs everything)
app.add_middleware(ResponseStructuringMiddleware)  # 4th in execution (structures response)
app.add_middleware(MemoryInjectionMiddleware)  # 3rd in execution (injects memory/context)
app.add_middleware(ContentModerationMiddleware)  # 2nd in execution (rate limiting, content check)
app.add_middleware(AuthenticationMiddleware)  # First in execution (auth check)
logger.info("Middleware stack registered successfully")


# Global exception handlers
@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    """Handle API exceptions with structured response."""
    logger.error(
        f"API Exception: {exc.error_code} - {exc.message}",
        extra={"error_details": exc.details, "request_id": getattr(request.state, "request_id", "unknown")}
    )
    content = exc.to_dict()
    content["timestamp"] = __import__("datetime").datetime.utcnow().isoformat()
    if hasattr(request.state, "request_id"):
        content["request_id"] = request.state.request_id

    return JSONResponse(
        status_code=exc.status_code,
        content=content,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.error(f"Validation error on {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validation error",
            "error_code": "VALIDATION_ERROR",
            "details": exc.errors(),
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception on {request.url}: {str(exc)}", exc_info=True)
    is_debug = os.getenv("DEBUG", "false").lower() == "true"

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "details": str(exc) if is_debug else None,
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "LangChain AI Conversation API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/health",
        "endpoints": {
            "conversations": "/api/v1/conversations",
            "documents": "/api/v1/documents",
            "messages": "/api/v1/conversations/{id}/messages",
            "tools": "/api/v1/tools",
            "websocket": "/api/v1/ws/{conversation_id}",
        },
    }


# Register health check routes
logger.info("Registering health check endpoints...")
from src.infrastructure.health import create_health_routes
health_router = create_health_routes()
app.include_router(health_router, tags=["Health"])
logger.info("Health check endpoints registered")


# Register API routes
logger.info("Registering API routes...")

# Conversation routes
from src.api.conversation_routes import router as conversation_router
app.include_router(conversation_router)
logger.info("Registered conversation routes")

# Document routes
from src.api.document_routes import router as document_router
app.include_router(document_router)
logger.info("Registered document routes")

# Message routes
from src.api.message_routes import router as message_router
app.include_router(message_router)
logger.info("Registered message routes")

# Tools routes
from src.api.tools_routes import router as tools_router
app.include_router(tools_router)
logger.info("Registered tools routes")

# WebSocket routes
from src.api.websocket_routes import router as websocket_router
app.include_router(websocket_router)
logger.info("Registered WebSocket routes")

# Streaming routes (Story 3.3)
from src.api.streaming_routes import router as streaming_router
app.include_router(streaming_router)
logger.info("Registered streaming routes")

# Cache admin routes (Phase 1 AI Optimization)
from src.api.cache_admin_routes import router as cache_admin_router
app.include_router(cache_admin_router)
logger.info("Registered cache admin routes")

# Claude Prompt Cache routes (Phase 3 AI Optimization)
from src.api.claude_cache_routes import router as claude_cache_router
app.include_router(claude_cache_router)
logger.info("Registered Claude Prompt Cache routes")

# Thread API routes (Epic 4 - LangGraph Integration)
from src.api.thread_routes import router as thread_router
app.include_router(thread_router)
logger.info("Registered Thread API routes")

# Initialize Claude integration with caching
from src.services.claude_integration import initialize_claude_integration
initialize_claude_integration()
logger.info("Initialized Claude integration with Prompt Caching support")

# Prometheus metrics endpoint
logger.info("Registering Prometheus metrics endpoint...")
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from src.infrastructure.cache_metrics import cache_registry

@app.get("/metrics", tags=["Metrics"])
async def metrics():
    """Prometheus metrics endpoint for monitoring."""
    return generate_latest(cache_registry)

logger.info("Registered Prometheus metrics endpoint at /metrics")

logger.info("All routes registered successfully")

# Initialize monitoring (Story 3.3)
logger.info("Initializing monitoring...")
from src.infrastructure.monitoring import get_monitoring_manager

async def initialize_monitoring():
    """Initialize monitoring on startup."""
    monitoring_manager = get_monitoring_manager()
    if os.getenv("ENABLE_MONITORING", "true").lower() == "true":
        interval = int(os.getenv("MONITORING_INTERVAL_SECONDS", "10"))
        await monitoring_manager.start_monitoring(interval)
        logger.info(f"Monitoring started with {interval}s interval")
    else:
        logger.info("Monitoring disabled")

# Update lifespan to include monitoring
original_lifespan = lifespan

@asynccontextmanager
async def updated_lifespan(app: FastAPI):
    """Updated lifespan with monitoring."""
    async with original_lifespan(app):
        await initialize_monitoring()
        yield
    # Shutdown monitoring
    monitoring_manager = get_monitoring_manager()
    await monitoring_manager.stop_monitoring()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("ENV", "development") == "development",
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )


"""FastAPI main application for LangChain AI Conversation."""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from src.db.config import engine
from src.db.migrations import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI app.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting LangChain AI Conversation backend...")
    try:
        await init_db(engine)
        logger.info("Database initialization completed")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down LangChain AI Conversation backend...")
    await engine.dispose()
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

# Add custom middleware (in correct order for execution)
# Due to middleware stacking, last added runs first in request processing
# Correct execution order: Auth → ContentModeration → MemoryInjection → ResponseStructuring → AuditLogging
from src.middleware.audit_logging_middleware import AuditLoggingMiddleware
from src.middleware.response_structuring_middleware import ResponseStructuringMiddleware
from src.middleware.content_moderation_middleware import ContentModerationMiddleware
from src.middleware.memory_injection_middleware import MemoryInjectionMiddleware
from src.middleware.auth_middleware import AuthenticationMiddleware

# Add in REVERSE order (last added = first executed)
app.add_middleware(AuditLoggingMiddleware)  # Executes last (logs everything)
app.add_middleware(ResponseStructuringMiddleware)  # Executes 4th (structures response)
app.add_middleware(MemoryInjectionMiddleware)  # Executes 3rd (injects memory/context)
app.add_middleware(ContentModerationMiddleware)  # Executes 2nd (rate limiting, content check)
app.add_middleware(AuthenticationMiddleware)  # Executes first (auth check)


# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.error(f"Validation error on {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception on {request.url}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc) if os.getenv("DEBUG", "false").lower() == "true" else "An error occurred",
        },
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "LangChain AI Conversation API",
        "version": "1.0.0",
    }


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
            "conversations": "/api/conversations",
            "documents": "/api/documents",
            "messages": "/api/conversations/{id}/messages",
            "tools": "/api/tools",
            "websocket": "/ws/conversations/{id}",
        },
    }


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

logger.info("All routes registered successfully")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("ENV", "development") == "development",
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )

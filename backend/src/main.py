"""FastAPI application entry point with configuration and middleware setup."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("Starting up Text2SQL Backend application")
    yield
    logger.info("Shutting down Text2SQL Backend application")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="Text2SQL Data Source Integration API",
        description="AI-powered data source integration backend",
        version="0.1.0",
        lifespan=lifespan
    )

    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint for monitoring."""
        return {
            "status": "ok",
            "service": "text2sql-backend",
            "version": "0.1.0"
        }

    # API version endpoint
    @app.get("/api/version", tags=["Info"])
    async def api_version():
        """Get API version information."""
        return {
            "version": "0.1.0",
            "name": "Text2SQL Data Source Integration API"
        }

    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint with API documentation link."""
        return {
            "message": "Text2SQL Backend API",
            "docs": "/docs",
            "openapi": "/openapi.json"
        }

    logger.info("FastAPI application configured successfully")
    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

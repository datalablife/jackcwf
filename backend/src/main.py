"""FastAPI 应用程序入口点，包括配置和中间件设置。"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api import datasources

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用程序启动和关闭事件。"""
    logger.info("启动 Text2SQL 后端应用程序")
    yield
    logger.info("关闭 Text2SQL 后端应用程序")


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用程序。"""

    app = FastAPI(
        title="Text2SQL 数据源集成 API",
        description="AI 驱动的数据源集成后端",
        version="0.1.0",
        lifespan=lifespan
    )

    # 配置 CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 包含路由
    app.include_router(datasources.router)

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

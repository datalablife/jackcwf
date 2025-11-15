"""Memori configuration and settings."""

import os
from typing import Optional

from pydantic_settings import BaseSettings


class MemoriConfig(BaseSettings):
    """Configuration for Memori memory management system."""

    # Memori core settings
    enabled: bool = True
    conscious_ingest: bool = True
    auto_ingest: bool = True

    # Database configuration for Memori
    db_type: str = "postgresql"  # 'sqlite', 'postgresql', 'mysql', 'mongodb'
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_name: str = os.getenv("DB_NAME", "memori_memory")
    db_user: str = os.getenv("DB_USER", "postgres")
    db_password: str = os.getenv("DB_PASSWORD", "")

    # For SQLite (alternative)
    sqlite_path: str = "./memori.db"

    # Anthropic/Claude configuration
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    claude_model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 2048

    # Memory management settings
    max_memory_items: int = 1000
    memory_retention_days: int = 90
    enable_semantic_search: bool = True
    embedding_model: str = "text-embedding-3-small"  # for semantic search

    # Performance settings
    batch_size: int = 32
    cache_ttl_seconds: int = 300
    enable_caching: bool = True

    # Monitoring and logging
    enable_monitoring: bool = True
    log_level: str = "INFO"

    # Multi-tenant support
    enable_multi_tenant: bool = True
    tenant_isolation: bool = True

    class Config:
        """Pydantic settings configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables from .env

    @property
    def db_connection_string(self) -> str:
        """Generate database connection string based on db_type."""
        if self.db_type == "sqlite":
            return f"sqlite:///{self.sqlite_path}"
        elif self.db_type == "postgresql":
            return (
                f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
                f"@{self.db_host}:{self.db_port}/{self.db_name}"
            )
        elif self.db_type == "mysql":
            return (
                f"mysql+aiomysql://{self.db_user}:{self.db_password}"
                f"@{self.db_host}:{self.db_port}/{self.db_name}"
            )
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

    def get_memori_config_dict(self) -> dict:
        """Get Memori-specific configuration dictionary."""
        return {
            "db_type": self.db_type,
            "db_path": self.sqlite_path if self.db_type == "sqlite" else None,
            "db_host": self.db_host if self.db_type != "sqlite" else None,
            "db_port": self.db_port if self.db_type != "sqlite" else None,
            "db_name": self.db_name if self.db_type != "sqlite" else None,
            "db_user": self.db_user if self.db_type != "sqlite" else None,
            "db_password": self.db_password if self.db_type != "sqlite" else None,
            "conscious_ingest": self.conscious_ingest,
            "auto_ingest": self.auto_ingest,
            "enable_semantic_search": self.enable_semantic_search,
        }


# Global config instance
memory_config = MemoriConfig()

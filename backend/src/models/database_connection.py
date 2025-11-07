"""
DatabaseConnection ORM model - stores encrypted PostgreSQL connection details.

This model stores sensitive credentials (password, hostname) in encrypted format.
Credentials are encrypted with AES-256 before storage and decrypted on retrieval.
"""

from sqlalchemy import Column, String, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from src.db.base import BaseModel


class DatabaseConnection(BaseModel):
    """
    ORM model for PostgreSQL connection details.

    Stores encrypted connection credentials for PostgreSQL data sources.
    All sensitive fields (password, connection string) are encrypted before storage.

    Attributes:
        id (int): Primary key
        data_source_id (int): Foreign key to DataSource
        host (str): PostgreSQL server hostname (e.g., "localhost", "db.example.com")
        port (int): PostgreSQL server port (default: 5432)
        database (str): Database name to connect to
        username (str): PostgreSQL username
        encrypted_password (str): Encrypted password (AES-256)
        connection_string (str): Full connection string for reference (encrypted)
        ssl_enabled (bool): Whether to use SSL for connection
        ssl_certificate (str): Optional SSL certificate path
        pool_size (int): Connection pool size (default: 5)
        max_overflow (int): Max overflow connections (default: 10)
        created_at (datetime): Timestamp when connection was created
        updated_at (datetime): Timestamp when connection was last updated

    Relationships:
        - DataSource: Refers to the data source this connection belongs to

    Notes:
        - Password is stored encrypted and never returned in plain text
        - Connection testing happens before saving to verify credentials are valid
        - Supports connection pooling with configurable pool size

    Example:
        conn = DatabaseConnection(
            data_source_id=1,
            host="postgres.example.com",
            port=5432,
            database="analytics",
            username="analyst",
            encrypted_password="...",  # Encrypted
            ssl_enabled=True
        )
    """

    __tablename__ = "database_connections"

    data_source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=False, index=True)
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False, default=5432)
    database = Column(String(255), nullable=False)
    username = Column(String(255), nullable=False)
    encrypted_password = Column(String(1024), nullable=False)  # Encrypted with AES-256
    connection_string = Column(String(1024), nullable=True)  # For reference, also encrypted
    ssl_enabled = Column(Boolean, default=False)
    ssl_certificate = Column(String(2048), nullable=True)  # PEM format
    pool_size = Column(Integer, default=5)
    max_overflow = Column(Integer, default=10)

    # Relationships
    data_source = relationship("DataSource", foreign_keys=[data_source_id], backref="database_connection")

    def __repr__(self) -> str:
        """String representation."""
        return f"<DatabaseConnection id={self.id} host={self.host} database={self.database}>"

"""
Schema ORM model - caches database schema information with TTL.

Caches table and column metadata from PostgreSQL databases to improve
query performance. Cache is invalidated after configured TTL.
"""

from sqlalchemy import Column, String, Integer, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from src.db.base import BaseModel


class Schema(BaseModel):
    """
    ORM model for cached database schema.

    Caches schema information (table names, columns, data types) from PostgreSQL
    databases. Cache is automatically invalidated after TTL (default 5 minutes).

    Attributes:
        id (int): Primary key
        data_source_id (int): Foreign key to DataSource
        table_name (str): Name of the table in the database
        table_schema (str): Schema name (usually 'public' in PostgreSQL)
        column_count (int): Number of columns in the table
        column_info (str): JSON array of column metadata
            Example: [
                {"name": "id", "type": "integer", "nullable": false},
                {"name": "email", "type": "character varying", "nullable": true}
            ]
        row_count (int): Approximate row count (0 if not yet analyzed)
        size_bytes (int): Approximate table size in bytes
        is_materialized (bool): Whether this is a materialized view
        created_at (datetime): Timestamp when schema was cached
        updated_at (datetime): Timestamp when schema was last refreshed
        cache_valid (bool): Whether cache is still valid (not expired)

    Relationships:
        - DataSource: Refers to the PostgreSQL data source

    Notes:
        - Schema cache TTL configured via SCHEMA_CACHE_TTL env var (seconds)
        - When cache expires, next query will automatically refresh
        - Cache also invalidated when user refreshes schema manually
        - Unique constraint on (data_source_id, table_name, table_schema)

    Example:
        schema = Schema(
            data_source_id=1,
            table_name="customers",
            table_schema="public",
            column_count=5,
            column_info='[{"name": "id", "type": "integer"}, ...]',
            row_count=100000
        )
    """

    __tablename__ = "schemas"

    data_source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=False, index=True)
    table_name = Column(String(255), nullable=False, index=True)
    table_schema = Column(String(255), nullable=False, default="public")
    column_count = Column(Integer, nullable=False, default=0)
    column_info = Column(Text, nullable=False)  # JSON array of column metadata
    row_count = Column(Integer, nullable=False, default=0)
    size_bytes = Column(Integer, nullable=False, default=0)
    is_materialized = Column(Boolean, default=False)
    cache_valid = Column(Boolean, default=True, index=True)

    # Relationships
    data_source = relationship("DataSource", foreign_keys=[data_source_id], backref="schemas")

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Schema id={self.id} table={self.table_schema}.{self.table_name} "
            f"columns={self.column_count} cache_valid={self.cache_valid}>"
        )

    __table_args__ = (
        # Unique constraint on data source, table name, and schema
        # to prevent duplicate schema entries for the same table
    )

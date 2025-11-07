"""
DataSourceConfig ORM model - stores user configuration and preferences for data sources.

Tracks user preferences like default data source selection, last accessed source,
and other personalization settings.
"""

from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from src.db.base import BaseModel


class DataSourceConfig(BaseModel):
    """
    ORM model for user configuration and preferences.

    Stores user-specific settings and preferences for data sources, including
    default selections, recent access history, and personalization options.

    Attributes:
        id (int): Primary key
        data_source_id (int): Foreign key to DataSource (unique - one config per source)
        is_default (bool): Whether this is the user's default data source
        last_accessed (datetime): Timestamp of last access (updated dynamically)
        query_timeout (int): Query timeout in seconds (default: 30)
        max_result_rows (int): Maximum rows to return in query results (default: 10000)
        enable_cache (bool): Whether to cache query results
        cache_ttl (int): Cache TTL in seconds (default: 300)
        auto_disconnect_timeout (int): Auto-disconnect after N minutes of inactivity
        metadata_json (str): JSON field for additional user preferences
            Example: {
                "last_schema_refresh": "2025-11-08T10:30:00Z",
                "preferred_tables": ["customers", "orders", "products"],
                "custom_labels": {"customers": "Customer Records"}
            }
        created_at (datetime): Timestamp when config was created
        updated_at (datetime): Timestamp when config was last updated

    Relationships:
        - DataSource: Refers to the data source this config applies to

    Notes:
        - One config per data source (unique constraint on data_source_id)
        - Default data source is selected on app startup
        - Timeouts prevent long-running queries from blocking the system
        - Cache settings apply to query result caching only

    Example:
        config = DataSourceConfig(
            data_source_id=1,
            is_default=True,
            query_timeout=60,
            max_result_rows=50000,
            enable_cache=True,
            cache_ttl=600
        )
    """

    __tablename__ = "datasource_configs"

    data_source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=False, unique=True, index=True)
    is_default = Column(Boolean, default=False, index=True)
    query_timeout = Column(Integer, default=30)  # Seconds
    max_result_rows = Column(Integer, default=10000)
    enable_cache = Column(Boolean, default=True)
    cache_ttl = Column(Integer, default=300)  # Seconds
    auto_disconnect_timeout = Column(Integer, default=30)  # Minutes
    metadata_json = Column(Text, nullable=True)  # Additional preferences

    # Relationships
    data_source = relationship(
        "DataSource",
        foreign_keys=[data_source_id],
        backref="config",
        uselist=False,
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<DataSourceConfig id={self.id} data_source_id={self.data_source_id} "
            f"default={self.is_default} timeout={self.query_timeout}s>"
        )

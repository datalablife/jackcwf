"""
DataSource ORM model - represents a connected data source (PostgreSQL or file upload).

Data sources are the primary entities that users connect to for data analysis.
They store metadata about the connection without storing sensitive credentials
(those are stored separately in DatabaseConnection or FileUpload models).
"""

from enum import Enum
from sqlalchemy import Column, String, Enum as SQLEnum, Text
from src.db.base import BaseModel


class DataSourceType(str, Enum):
    """Enumeration of supported data source types."""

    POSTGRESQL = "postgresql"
    FILE_UPLOAD = "file_upload"
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"


class DataSourceStatus(str, Enum):
    """Enumeration of data source connection status."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    TESTING = "testing"
    ERROR = "error"


class DataSource(BaseModel):
    """
    ORM model for data sources.

    Represents a user-connected data source with metadata but not sensitive credentials.

    Attributes:
        id (int): Primary key
        name (str): User-friendly name for the data source (e.g., "Production DB", "Q4 Sales Data")
        description (str): Optional description of the data source
        type (DataSourceType): Type of data source (postgresql, file_upload, csv, excel, json)
        status (DataSourceStatus): Connection status (connected, disconnected, testing, error)
        error_message (str): Optional error message if status is ERROR
        created_at (datetime): Timestamp when data source was created
        updated_at (datetime): Timestamp when data source was last updated

    Relationships:
        - DatabaseConnection (1-to-1): PostgreSQL connection details (if type="postgresql")
        - FileUpload (1-to-1): File upload details (if type="file_upload")
        - Schema (1-to-many): Cached database schema (for PostgreSQL sources)
        - DataSourceConfig (1-to-1): User configuration and preferences

    Example:
        ds = DataSource(
            name="Production PostgreSQL",
            description="Main production database",
            type=DataSourceType.POSTGRESQL,
            status=DataSourceStatus.CONNECTED
        )
    """

    __tablename__ = "data_sources"

    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    type = Column(
        SQLEnum(DataSourceType),
        nullable=False,
        default=DataSourceType.POSTGRESQL,
        index=True,
    )
    status = Column(
        SQLEnum(DataSourceStatus),
        nullable=False,
        default=DataSourceStatus.DISCONNECTED,
        index=True,
    )
    error_message = Column(Text, nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return f"<DataSource id={self.id} name={self.name!r} type={self.type} status={self.status}>"

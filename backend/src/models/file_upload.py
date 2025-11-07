"""
FileUpload ORM model - stores metadata for uploaded data files.

Tracks uploaded CSV, Excel, and JSON files with their parsing information
and parsed schema metadata.
"""

from enum import Enum
from sqlalchemy import Column, String, Integer, ForeignKey, Float, Boolean, Text
from sqlalchemy.orm import relationship
from src.db.base import BaseModel


class FileFormat(str, Enum):
    """Enumeration of supported file formats."""

    CSV = "csv"
    EXCEL = "excel"
    XLSX = "xlsx"
    XLS = "xls"
    JSON = "json"
    JSONL = "jsonl"


class FileParseStatus(str, Enum):
    """Enumeration of file parsing status."""

    PENDING = "pending"
    PARSING = "parsing"
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"  # Partial success with warnings


class FileUpload(BaseModel):
    """
    ORM model for uploaded data files.

    Stores metadata about uploaded files (CSV, Excel, JSON) used as data sources.
    Includes file path, format, size, and parsing results.

    Attributes:
        id (int): Primary key
        data_source_id (int): Foreign key to DataSource
        filename (str): Original filename (e.g., "sales_data.csv")
        file_path (str): Storage path on server (relative to UPLOAD_DIR)
        file_format (FileFormat): Format of the file (csv, excel, json, etc.)
        file_size (float): File size in bytes
        row_count (int): Number of rows/records in the file (0 if not yet parsed)
        column_count (int): Number of columns (0 if not yet parsed)
        parse_status (FileParseStatus): Status of file parsing (pending, success, error)
        parse_error (str): Error message if parsing failed
        parse_warnings (str): JSON string of parsing warnings
        is_indexed (bool): Whether the file data is indexed for search
        metadata_json (str): JSON metadata extracted from file (column types, etc.)
        created_at (datetime): Timestamp when file was uploaded
        updated_at (datetime): Timestamp when file was last processed

    Relationships:
        - DataSource: Refers to the data source this file belongs to

    Notes:
        - File content is stored in filesystem, not in database (file_path is relative)
        - Parsing creates the schema and stores it in Schema model
        - Max file size: 500MB (configured via MAX_FILE_SIZE env var)

    Example:
        upload = FileUpload(
            data_source_id=2,
            filename="customer_data.csv",
            file_path="uploads/2025-11-08/customer_data_abc123.csv",
            file_format=FileFormat.CSV,
            file_size=1024000,
            row_count=5000,
            column_count=12,
            parse_status=FileParseStatus.SUCCESS
        )
    """

    __tablename__ = "file_uploads"

    data_source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=False, index=True)
    filename = Column(String(1024), nullable=False)
    file_path = Column(String(1024), nullable=False, unique=True)
    file_format = Column(String(20), nullable=False)  # csv, excel, json, etc.
    file_size = Column(Float, nullable=False)  # Size in bytes
    row_count = Column(Integer, default=0)
    column_count = Column(Integer, default=0)
    parse_status = Column(String(20), default=FileParseStatus.PENDING)
    parse_error = Column(Text, nullable=True)
    parse_warnings = Column(Text, nullable=True)  # JSON array of warnings
    is_indexed = Column(Boolean, default=False)
    metadata_json = Column(Text, nullable=True)  # JSON with column info, types, etc.

    # Relationships
    data_source = relationship("DataSource", foreign_keys=[data_source_id], backref="file_uploads")

    def __repr__(self) -> str:
        """String representation."""
        return f"<FileUpload id={self.id} filename={self.filename!r} format={self.file_format}>"

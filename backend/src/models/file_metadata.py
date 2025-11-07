"""
FileMetadata ORM model - stores parsed metadata from uploaded files.

Contains information about file structure, columns, data types, and parsing results.
"""

from typing import Optional
from sqlalchemy import Column, String, Integer, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from src.db.base import BaseModel


class FileMetadata(BaseModel):
    """
    ORM model for file metadata and parsing results.

    Stores detailed metadata extracted from uploaded files after parsing,
    including column information, data types, row counts, etc.

    Attributes:
        id (int): Primary key
        file_upload_id (int): Foreign key to FileUpload (one-to-one relationship)
        rows_count (int): Total number of rows in the file
        columns_count (int): Total number of columns in the file
        column_names (list): JSON array of column names [str, str, ...]
        data_types (list): JSON array of inferred data types ["string", "integer", ...]
        storage_path (str): Full path where parsed data is stored (for caching)
        created_at (datetime): Timestamp when metadata was extracted
        updated_at (datetime): Timestamp when metadata was last updated

    Relationships:
        - FileUpload: One-to-one relationship with FileUpload model

    Notes:
        - Each FileUpload has exactly one FileMetadata (or none if parsing failed)
        - Data types are inferred by the parser (string, integer, float, date, boolean, etc.)
        - Column names are extracted from file headers
        - Storage path allows retrieval of cached parsed data

    Example:
        metadata = FileMetadata(
            file_upload_id=1,
            rows_count=5000,
            columns_count=12,
            column_names=["id", "name", "email", "age", "created_at"],
            data_types=["integer", "string", "string", "integer", "datetime"],
            storage_path="/data/parsed/file_1.parquet"
        )
    """

    __tablename__ = "file_metadata"

    file_upload_id = Column(Integer, ForeignKey("file_uploads.id"), nullable=False, unique=True, index=True)
    rows_count = Column(Integer, nullable=True)  # NULL if not yet parsed
    columns_count = Column(Integer, nullable=True)  # NULL if not yet parsed
    column_names = Column(JSON, nullable=True)  # Array of column name strings
    data_types = Column(JSON, nullable=True)  # Array of data type strings
    storage_path = Column(String(1024), nullable=True)  # Path to cached parsed data
    additional_metadata = Column(Text, nullable=True)  # JSON string for extra metadata

    # Relationships
    file_upload = relationship("FileUpload", foreign_keys=[file_upload_id], uselist=False, backref="metadata")

    def __repr__(self) -> str:
        """String representation."""
        return f"<FileMetadata id={self.id} file_upload_id={self.file_upload_id} columns={self.columns_count}>"

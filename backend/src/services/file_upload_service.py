"""
File upload management service for handling file CRUD operations.

Manages file uploads, metadata, preview generation, and file deletion.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os

from src.models import FileUpload, FileMetadata
from src.services.file_validation import FileValidationService
from src.services.csv_parser import CSVParserService
from src.services.excel_parser import ExcelParserService


class FileUploadService:
    """
    Service for managing file uploads and metadata.

    Provides methods for saving, retrieving, listing, and deleting uploaded files.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Initialize the service with a database session.

        Args:
            db_session: AsyncSession for database operations
        """
        self.db_session = db_session

    async def save_upload(
        self,
        data_source_id: int,
        filename: str,
        file_path: str,
        file_format: str,
        file_size: float,
    ) -> FileUpload:
        """
        Save a file upload record to the database.

        Args:
            data_source_id: ID of the associated data source
            filename: Original filename
            file_path: Path where file is stored
            file_format: File format (csv, xlsx, xls, etc.)
            file_size: File size in bytes

        Returns:
            Created FileUpload model instance

        Raises:
            Exception: If file cannot be saved

        Example:
            >>> upload = await service.save_upload(
            ...     data_source_id=1,
            ...     filename="data.csv",
            ...     file_path="/uploads/data_abc123.csv",
            ...     file_format="csv",
            ...     file_size=102400
            ... )
        """
        try:
            # Validate file first
            FileValidationService.validate_file(file_path, file_size, filename)

            # Create file upload record
            file_upload = FileUpload(
                data_source_id=data_source_id,
                filename=filename,
                file_path=file_path,
                file_format=file_format,
                file_size=file_size,
                parse_status="pending",
            )

            self.db_session.add(file_upload)
            await self.db_session.flush()  # Get the ID without committing

            return file_upload

        except Exception as e:
            raise Exception(f"Failed to save file upload: {str(e)}")

    async def get_file(self, file_id: int) -> Optional[FileUpload]:
        """
        Get a file upload by ID.

        Args:
            file_id: File upload ID

        Returns:
            FileUpload instance or None if not found

        Example:
            >>> upload = await service.get_file(1)
        """
        try:
            stmt = select(FileUpload).where(FileUpload.id == file_id)
            result = await self.db_session.execute(stmt)
            return result.scalars().first()

        except Exception as e:
            raise Exception(f"Failed to get file: {str(e)}")

    async def list_files(
        self,
        data_source_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[FileUpload]:
        """
        List file uploads with optional filtering.

        Args:
            data_source_id: Filter by data source ID (optional)
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of FileUpload instances

        Example:
            >>> files = await service.list_files(data_source_id=1, limit=20)
        """
        try:
            stmt = select(FileUpload)

            if data_source_id is not None:
                stmt = stmt.where(FileUpload.data_source_id == data_source_id)

            stmt = stmt.offset(skip).limit(limit).order_by(FileUpload.created_at.desc())

            result = await self.db_session.execute(stmt)
            return result.scalars().all()

        except Exception as e:
            raise Exception(f"Failed to list files: {str(e)}")

    async def delete_file(self, file_id: int) -> bool:
        """
        Delete a file upload and its associated file from disk.

        Args:
            file_id: File upload ID

        Returns:
            True if deletion was successful

        Raises:
            Exception: If file cannot be deleted

        Example:
            >>> success = await service.delete_file(1)
        """
        try:
            # Get the file upload record
            file_upload = await self.get_file(file_id)
            if not file_upload:
                raise Exception(f"File upload {file_id} not found")

            # Delete file from disk
            if file_upload.file_path and os.path.exists(file_upload.file_path):
                try:
                    os.remove(file_upload.file_path)
                except OSError as e:
                    raise Exception(f"Failed to delete file from disk: {str(e)}")

            # Delete associated metadata
            if file_upload.metadata:
                await self.db_session.delete(file_upload.metadata)

            # Delete file upload record
            await self.db_session.delete(file_upload)
            await self.db_session.flush()

            return True

        except Exception as e:
            raise Exception(f"Failed to delete file: {str(e)}")

    async def get_preview(
        self,
        file_id: int,
        max_rows: int = 20,
        sheet_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get preview data for a file upload.

        Args:
            file_id: File upload ID
            max_rows: Maximum number of rows to return
            sheet_name: Sheet name for Excel files (optional)

        Returns:
            Dictionary with preview data

        Raises:
            Exception: If preview cannot be generated

        Example:
            >>> preview = await service.get_preview(1)
        """
        try:
            # Get file upload
            file_upload = await self.get_file(file_id)
            if not file_upload:
                raise Exception(f"File upload {file_id} not found")

            # Check if file exists
            if not os.path.exists(file_upload.file_path):
                raise Exception(f"File not found: {file_upload.file_path}")

            # Generate preview based on format
            if file_upload.file_format == "csv":
                preview = CSVParserService.get_preview(
                    file_upload.file_path,
                    max_rows=max_rows
                )

            elif file_upload.file_format in ("xlsx", "xls", "excel"):
                preview = ExcelParserService.get_preview(
                    file_upload.file_path,
                    max_rows=max_rows,
                    sheet_name=sheet_name,
                )

            else:
                raise Exception(f"Unsupported file format: {file_upload.file_format}")

            return {
                "file_id": file_id,
                "filename": file_upload.filename,
                "file_format": file_upload.file_format,
                "file_size": file_upload.file_size,
                **preview,
            }

        except Exception as e:
            raise Exception(f"Failed to get preview: {str(e)}")

    async def parse_file(
        self,
        file_id: int,
        sheet_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Parse a file and extract metadata.

        Args:
            file_id: File upload ID
            sheet_name: Sheet name for Excel files (optional)

        Returns:
            Dictionary with parsed metadata

        Raises:
            Exception: If file cannot be parsed

        Example:
            >>> metadata = await service.parse_file(1)
        """
        try:
            # Get file upload
            file_upload = await self.get_file(file_id)
            if not file_upload:
                raise Exception(f"File upload {file_id} not found")

            # Check if file exists
            if not os.path.exists(file_upload.file_path):
                raise Exception(f"File not found: {file_upload.file_path}")

            # Mark as parsing
            file_upload.parse_status = "parsing"
            self.db_session.add(file_upload)
            await self.db_session.flush()

            try:
                # Parse based on format
                if file_upload.file_format == "csv":
                    parsed_data = CSVParserService.parse_csv(file_upload.file_path)

                elif file_upload.file_format in ("xlsx", "xls", "excel"):
                    parsed_data = ExcelParserService.parse_excel(
                        file_upload.file_path,
                        sheet_name=sheet_name,
                    )

                else:
                    raise Exception(f"Unsupported file format: {file_upload.file_format}")

                # Update file upload record
                file_upload.row_count = parsed_data.get("row_count", 0)
                file_upload.column_count = parsed_data.get("columns_count", len(parsed_data.get("column_names", [])))
                file_upload.parse_status = "success"

                # Create or update metadata
                metadata = await self._get_or_create_metadata(file_id)
                if not metadata:
                    metadata = FileMetadata(file_upload_id=file_id)
                    self.db_session.add(metadata)

                metadata.rows_count = parsed_data.get("row_count", 0)
                metadata.columns_count = len(parsed_data.get("column_names", []))
                metadata.column_names = parsed_data.get("column_names", [])
                metadata.data_types = parsed_data.get("data_types", [])

                self.db_session.add(file_upload)
                self.db_session.add(metadata)
                await self.db_session.flush()

                return {
                    "file_id": file_id,
                    "status": "success",
                    **parsed_data,
                }

            except Exception as e:
                # Mark as failed
                file_upload.parse_status = "error"
                file_upload.parse_error = str(e)
                self.db_session.add(file_upload)
                await self.db_session.flush()
                raise Exception(f"Failed to parse file: {str(e)}")

        except Exception as e:
            raise Exception(f"Failed to parse file: {str(e)}")

    async def _get_or_create_metadata(self, file_id: int) -> Optional[FileMetadata]:
        """Get existing metadata or None."""
        try:
            stmt = select(FileMetadata).where(FileMetadata.file_upload_id == file_id)
            result = await self.db_session.execute(stmt)
            return result.scalars().first()
        except Exception:
            return None

    async def update_parse_status(
        self,
        file_id: int,
        status: str,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        Update the parse status of a file upload.

        Args:
            file_id: File upload ID
            status: New status (pending, parsing, success, error)
            error_message: Error message if status is error

        Returns:
            True if update was successful

        Example:
            >>> success = await service.update_parse_status(1, "success")
        """
        try:
            file_upload = await self.get_file(file_id)
            if not file_upload:
                raise Exception(f"File upload {file_id} not found")

            file_upload.parse_status = status
            if error_message:
                file_upload.parse_error = error_message

            self.db_session.add(file_upload)
            await self.db_session.flush()

            return True

        except Exception as e:
            raise Exception(f"Failed to update parse status: {str(e)}")

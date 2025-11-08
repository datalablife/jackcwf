"""
文件预览 API 端点。

提供 REST API 来预览文件内容、元数据和工作表信息。
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_async_session
from src.services import FileUploadService


# Pydantic 响应模型

class PreviewRow(BaseModel):
    """预览行数据。"""

    pass  # 动态字段，使用 dict


class FilePreviewResponse(BaseModel):
    """文件预览响应模型。"""

    file_id: int
    filename: str
    file_format: str
    file_size: float
    column_names: List[str]
    rows: List[Dict[str, Any]]
    displayed_rows: int
    max_rows: int


class FileMetadataResponse(BaseModel):
    """文件元数据响应模型。"""

    file_id: int
    filename: str
    file_format: str
    rows_count: Optional[int]
    columns_count: Optional[int]
    column_names: Optional[List[str]]
    data_types: Optional[List[str]]


class FileSheet(BaseModel):
    """Excel 工作表信息。"""

    name: str
    index: int


class FileSheetListResponse(BaseModel):
    """工作表列表响应模型。"""

    file_id: int
    filename: str
    file_format: str
    sheets: List[FileSheet]


class FileParseResponse(BaseModel):
    """文件解析响应模型。"""

    file_id: int
    filename: str
    file_format: str
    status: str
    rows_count: Optional[int]
    columns_count: Optional[int]
    column_names: Optional[List[str]]
    data_types: Optional[List[str]]


# 路由创建
router = APIRouter(prefix="/api/file-uploads", tags=["File Preview"])


@router.get("/{file_id}/preview", response_model=FilePreviewResponse)
async def get_file_preview(
    file_id: int,
    max_rows: int = 20,
    sheet_name: Optional[str] = None,
    db: AsyncSession = Depends(get_async_session),
) -> FilePreviewResponse:
    """
    获取文件预览数据。

    返回文件的前 N 行数据、列名和其他信息。

    Args:
        file_id: 文件 ID
        max_rows: 最大返回行数（默认 20）
        sheet_name: Excel 工作表名称（可选）
        db: 数据库会话

    Returns:
        文件预览数据

    Raises:
        HTTPException: 如果文件不存在或无法预览

    Example:
        GET /api/file-uploads/1/preview?max_rows=20
    """
    try:
        service = FileUploadService(db)

        # 检查文件是否存在
        file_upload = await service.get_file(file_id)
        if not file_upload:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"文件 {file_id} 不存在",
            )

        # 生成预览
        preview = await service.get_preview(
            file_id=file_id,
            max_rows=max_rows,
            sheet_name=sheet_name,
        )

        return FilePreviewResponse(**preview)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取预览失败: {str(e)}",
        )


@router.get("/{file_id}/metadata", response_model=FileMetadataResponse)
async def get_file_metadata(
    file_id: int,
    db: AsyncSession = Depends(get_async_session),
) -> FileMetadataResponse:
    """
    获取文件元数据。

    包括行数、列数、列名、数据类型等信息。

    Args:
        file_id: 文件 ID
        db: 数据库会话

    Returns:
        文件元数据

    Raises:
        HTTPException: 如果文件不存在

    Example:
        GET /api/file-uploads/1/metadata
    """
    try:
        service = FileUploadService(db)

        # 检查文件是否存在
        file_upload = await service.get_file(file_id)
        if not file_upload:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"文件 {file_id} 不存在",
            )

        # 获取元数据
        metadata = file_upload.metadata if hasattr(file_upload, "metadata") else None

        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"文件 {file_id} 的元数据不存在，可能未解析",
            )

        return FileMetadataResponse(
            file_id=file_id,
            filename=file_upload.filename,
            file_format=file_upload.file_format,
            rows_count=metadata.rows_count,
            columns_count=metadata.columns_count,
            column_names=metadata.column_names,
            data_types=metadata.data_types,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取元数据失败: {str(e)}",
        )


@router.get("/{file_id}/sheets", response_model=FileSheetListResponse)
async def get_file_sheets(
    file_id: int,
    db: AsyncSession = Depends(get_async_session),
) -> FileSheetListResponse:
    """
    获取 Excel 文件的工作表列表。

    仅适用于 Excel 格式文件（.xlsx, .xls）。

    Args:
        file_id: 文件 ID
        db: 数据库会话

    Returns:
        工作表列表

    Raises:
        HTTPException: 如果文件不存在或不是 Excel 格式

    Example:
        GET /api/file-uploads/1/sheets
    """
    try:
        from src.services import ExcelParserService

        service = FileUploadService(db)

        # 检查文件是否存在
        file_upload = await service.get_file(file_id)
        if not file_upload:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"文件 {file_id} 不存在",
            )

        # 检查文件格式
        if file_upload.file_format not in ("xlsx", "xls", "excel"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"文件格式 {file_upload.file_format} 不支持获取工作表列表",
            )

        # 获取工作表列表
        sheet_names = ExcelParserService.list_sheets(file_upload.file_path)
        sheets = [
            FileSheet(name=name, index=idx)
            for idx, name in enumerate(sheet_names)
        ]

        return FileSheetListResponse(
            file_id=file_id,
            filename=file_upload.filename,
            file_format=file_upload.file_format,
            sheets=sheets,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工作表列表失败: {str(e)}",
        )


@router.post("/{file_id}/parse", response_model=FileParseResponse)
async def parse_file(
    file_id: int,
    sheet_name: Optional[str] = None,
    db: AsyncSession = Depends(get_async_session),
) -> FileParseResponse:
    """
    解析文件并提取元数据。

    该端点会解析文件内容，提取列信息、数据类型等。

    Args:
        file_id: 文件 ID
        sheet_name: Excel 工作表名称（可选）
        db: 数据库会话

    Returns:
        解析结果

    Raises:
        HTTPException: 如果文件不存在或解析失败

    Example:
        POST /api/file-uploads/1/parse
    """
    try:
        service = FileUploadService(db)

        # 检查文件是否存在
        file_upload = await service.get_file(file_id)
        if not file_upload:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"文件 {file_id} 不存在",
            )

        # 解析文件
        result = await service.parse_file(
            file_id=file_id,
            sheet_name=sheet_name,
        )

        await db.commit()

        return FileParseResponse(
            file_id=file_id,
            filename=file_upload.filename,
            file_format=file_upload.file_format,
            status="success",
            rows_count=result.get("row_count"),
            columns_count=result.get("columns_count"),
            column_names=result.get("column_names"),
            data_types=result.get("data_types"),
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"解析文件失败: {str(e)}",
        )

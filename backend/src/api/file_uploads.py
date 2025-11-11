"""
文件上传 API 端点。

提供 REST API 来上传、管理和预览数据文件（CSV、Excel 等）。
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
import os
from datetime import datetime

from src.db import get_async_session
from src.models import FileUpload, FileMetadata, FileFormat, FileParseStatus
from src.services import FileUploadService, FileValidationService, FileValidationError


# Pydantic 请求/响应模型

class FileUploadResponse(BaseModel):
    """文件上传响应模型。"""

    id: int
    data_source_id: int
    filename: str
    file_format: str
    file_size: float
    row_count: Optional[int]
    column_count: Optional[int]
    parse_status: str
    parse_error: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FileListResponse(BaseModel):
    """文件列表响应模型。"""

    total: int
    items: List[FileUploadResponse]
    skip: int
    limit: int


class FilePreviewResponse(BaseModel):
    """文件预览响应模型。"""

    file_id: int
    filename: str
    file_format: str
    file_size: float
    column_names: List[str]
    rows: List[dict]
    displayed_rows: int
    max_rows: int


class FileMetadataResponse(BaseModel):
    """文件元数据响应模型。"""

    file_id: int
    rows_count: Optional[int]
    columns_count: Optional[int]
    column_names: Optional[List[str]]
    data_types: Optional[List[str]]


class FileDeleteResponse(BaseModel):
    """文件删除响应模型。"""

    success: bool
    message: str
    file_id: int


# 路由创建
router = APIRouter(prefix="/api/file-uploads", tags=["File Uploads"])


@router.post("/", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    data_source_id: int = Form(..., description="数据源 ID"),
    file: UploadFile = File(..., description="上传的文件"),
    db: AsyncSession = Depends(get_async_session),
) -> FileUploadResponse:
    """
    上传一个数据文件。

    支持的格式: CSV, XLSX, XLS, JSON, JSONL

    最大文件大小: 500MB

    Args:
        data_source_id: 关联的数据源 ID
        file: 上传的文件
        db: 数据库会话

    Returns:
        已创建的文件上传记录

    Raises:
        HTTPException: 如果文件验证失败或上传失败

    Example:
        POST /api/file-uploads
        FormData:
            data_source_id: 1
            file: <binary file content>
    """
    try:
        # 验证文件
        file_size = len(await file.read())
        await file.seek(0)  # 重置文件指针

        FileValidationService.validate_file(
            file_path="",  # 暂时没有实际路径
            file_size=file_size,
            filename=file.filename,
        )

        # 保存文件到临时目录
        upload_dir = "/tmp/uploads"
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, f"{data_source_id}_{file.filename}")
        with open(file_path, "wb") as f:
            f.write(await file.read())

        # 确定文件格式
        file_ext = os.path.splitext(file.filename)[1].lower().lstrip(".")
        if file_ext not in ["csv", "xlsx", "xls", "json", "jsonl"]:
            raise FileValidationError(f"不支持的文件格式: {file_ext}")

        # 创建文件上传记录
        service = FileUploadService(db)
        file_upload = await service.save_upload(
            data_source_id=data_source_id,
            filename=file.filename,
            file_path=file_path,
            file_format=file_ext,
            file_size=file_size,
        )

        await db.commit()
        await db.refresh(file_upload)

        return FileUploadResponse.from_orm(file_upload)

    except FileValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件验证失败: {e.message}",
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件上传失败: {str(e)}",
        )


@router.get("/", response_model=FileListResponse)
async def list_files(
    data_source_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_async_session),
) -> FileListResponse:
    """
    列出文件上传记录。

    支持按数据源过滤和分页。

    Args:
        data_source_id: 可选的数据源 ID 过滤
        skip: 跳过的记录数
        limit: 返回的最大记录数
        db: 数据库会话

    Returns:
        文件列表和分页信息

    Example:
        GET /api/file-uploads?data_source_id=1&skip=0&limit=20
    """
    try:
        service = FileUploadService(db)
        files = await service.list_files(
            data_source_id=data_source_id,
            skip=skip,
            limit=limit,
        )

        return FileListResponse(
            total=len(files),
            items=[FileUploadResponse.from_orm(f) for f in files],
            skip=skip,
            limit=limit,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文件列表失败: {str(e)}",
        )


@router.get("/{file_id}", response_model=FileUploadResponse)
async def get_file(
    file_id: int,
    db: AsyncSession = Depends(get_async_session),
) -> FileUploadResponse:
    """
    获取单个文件上传记录。

    Args:
        file_id: 文件 ID
        db: 数据库会话

    Returns:
        文件上传记录

    Raises:
        HTTPException: 如果文件不存在

    Example:
        GET /api/file-uploads/1
    """
    try:
        service = FileUploadService(db)
        file = await service.get_file(file_id)

        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"文件 {file_id} 不存在",
            )

        return FileUploadResponse.from_orm(file)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文件失败: {str(e)}",
        )


@router.delete("/{file_id}", response_model=FileDeleteResponse)
async def delete_file(
    file_id: int,
    db: AsyncSession = Depends(get_async_session),
) -> FileDeleteResponse:
    """
    删除文件上传记录及相关文件。

    Args:
        file_id: 文件 ID
        db: 数据库会话

    Returns:
        删除结果

    Raises:
        HTTPException: 如果删除失败

    Example:
        DELETE /api/file-uploads/1
    """
    try:
        service = FileUploadService(db)
        await service.delete_file(file_id)
        await db.commit()

        return FileDeleteResponse(
            success=True,
            message=f"文件 {file_id} 已成功删除",
            file_id=file_id,
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除文件失败: {str(e)}",
        )

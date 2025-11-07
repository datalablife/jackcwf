"""
数据源 API 端点。

提供 REST API 来管理数据源（创建、检索、测试、删除）。
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_async_session
from src.models import DataSource, DataSourceStatus, DataSourceType
from src.services import DataSourceService


# Pydantic 请求/响应模型
class PostgresConnectionRequest(BaseModel):
    """PostgreSQL 连接请求模型。"""

    name: str = Field(..., description="数据源名称")
    description: str | None = Field(None, description="数据源描述")
    host: str = Field(..., description="PostgreSQL 主机名")
    port: int = Field(5432, description="PostgreSQL 端口")
    database: str = Field(..., description="数据库名称")
    username: str = Field(..., description="数据库用户名")
    password: str = Field(..., description="数据库密码")


class DataSourceResponse(BaseModel):
    """数据源响应模型。"""

    id: int
    name: str
    description: str | None
    type: str
    status: str
    error_message: str | None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class TestConnectionResponse(BaseModel):
    """连接测试响应模型。"""

    success: bool
    message: str


class DataSourceListResponse(BaseModel):
    """数据源列表响应模型。"""

    total: int
    datasources: List[DataSourceResponse]


# 创建路由
router = APIRouter(prefix="/api/datasources", tags=["datasources"])


@router.post("/postgres", response_model=DataSourceResponse, status_code=status.HTTP_201_CREATED)
async def create_postgres_datasource(
    request: PostgresConnectionRequest,
    session: AsyncSession = Depends(get_async_session),
) -> DataSourceResponse:
    """
    创建新的 PostgreSQL 数据源。

    参数:
        request: PostgreSQL 连接请求
        session: 数据库会话

    返回:
        DataSourceResponse: 创建的数据源

    错误:
        400: 无法连接到数据库
        500: 内部服务器错误
    """
    try:
        datasource = await DataSourceService.create_postgres_datasource(
            session=session,
            name=request.name,
            description=request.description,
            host=request.host,
            port=request.port,
            database=request.database,
            username=request.username,
            password=request.password,
        )
        return DataSourceResponse.model_validate(datasource)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建数据源失败: {str(e)}",
        )


@router.get("", response_model=DataSourceListResponse)
async def list_datasources(
    session: AsyncSession = Depends(get_async_session),
) -> DataSourceListResponse:
    """
    列出所有数据源。

    参数:
        session: 数据库会话

    返回:
        DataSourceListResponse: 数据源列表
    """
    try:
        datasources = await DataSourceService.list_datasources(session)
        return DataSourceListResponse(
            total=len(datasources),
            datasources=[DataSourceResponse.model_validate(ds) for ds in datasources],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"检索数据源失败: {str(e)}",
        )


@router.get("/{datasource_id}", response_model=DataSourceResponse)
async def get_datasource(
    datasource_id: int,
    session: AsyncSession = Depends(get_async_session),
) -> DataSourceResponse:
    """
    获取特定数据源。

    参数:
        datasource_id: 数据源 ID
        session: 数据库会话

    返回:
        DataSourceResponse: 数据源详情

    错误:
        404: 数据源未找到
    """
    try:
        datasource = await DataSourceService.get_datasource(session, datasource_id)
        if not datasource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"数据源 {datasource_id} 未找到",
            )
        return DataSourceResponse.model_validate(datasource)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"检索数据源失败: {str(e)}",
        )


@router.post("/{datasource_id}/test", response_model=TestConnectionResponse)
async def test_datasource_connection(
    datasource_id: int,
    session: AsyncSession = Depends(get_async_session),
) -> TestConnectionResponse:
    """
    测试数据源连接。

    参数:
        datasource_id: 数据源 ID
        session: 数据库会话

    返回:
        TestConnectionResponse: 连接测试结果

    错误:
        404: 数据源未找到
        400: 无效的数据源类型
    """
    try:
        result = await DataSourceService.test_connection(session, datasource_id)
        return TestConnectionResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"连接测试失败: {str(e)}",
        )


@router.delete("/{datasource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_datasource(
    datasource_id: int,
    session: AsyncSession = Depends(get_async_session),
) -> None:
    """
    删除数据源。

    参数:
        datasource_id: 数据源 ID
        session: 数据库会话

    错误:
        404: 数据源未找到
        500: 删除失败
    """
    try:
        success = await DataSourceService.delete_datasource(session, datasource_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"数据源 {datasource_id} 未找到",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除数据源失败: {str(e)}",
        )

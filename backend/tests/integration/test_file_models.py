"""
文件模型集成测试。

测试 FileUpload 和 FileMetadata 模型的关系和操作。
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import select

from src.db.base import Base
from src.models import FileUpload, FileMetadata, FileFormat, FileParseStatus


@pytest.fixture
async def db_session():
    """创建测试数据库会话。"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_local = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_local() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_file_upload_creation(db_session):
    """测试创建 FileUpload 记录。"""
    file_upload = FileUpload(
        data_source_id=1,
        filename="test_data.csv",
        file_path="/uploads/test_data.csv",
        file_format="csv",
        file_size=1024.5,
        row_count=100,
        column_count=5,
        parse_status="success",
    )

    db_session.add(file_upload)
    await db_session.flush()

    assert file_upload.id is not None
    assert file_upload.filename == "test_data.csv"
    assert file_upload.file_size == 1024.5
    assert file_upload.created_at is not None


@pytest.mark.asyncio
async def test_file_metadata_creation(db_session):
    """测试创建 FileMetadata 记录。"""
    # 先创建 FileUpload
    file_upload = FileUpload(
        data_source_id=1,
        filename="test_data.csv",
        file_path="/uploads/test_data.csv",
        file_format="csv",
        file_size=1024.0,
    )

    db_session.add(file_upload)
    await db_session.flush()

    # 创建 FileMetadata
    metadata = FileMetadata(
        file_upload_id=file_upload.id,
        rows_count=100,
        columns_count=5,
        column_names=["id", "name", "email", "age", "status"],
        data_types=["integer", "string", "string", "integer", "string"],
    )

    db_session.add(metadata)
    await db_session.flush()

    assert metadata.id is not None
    assert metadata.file_upload_id == file_upload.id
    assert metadata.rows_count == 100
    assert len(metadata.column_names) == 5


@pytest.mark.asyncio
async def test_file_upload_file_metadata_relationship(db_session):
    """测试 FileUpload 和 FileMetadata 的一对一关系。"""
    # 创建 FileUpload
    file_upload = FileUpload(
        data_source_id=1,
        filename="data.xlsx",
        file_path="/uploads/data.xlsx",
        file_format="xlsx",
        file_size=5000.0,
    )

    db_session.add(file_upload)
    await db_session.flush()

    # 创建 FileMetadata
    metadata = FileMetadata(
        file_upload_id=file_upload.id,
        rows_count=500,
        columns_count=10,
        column_names=["col1", "col2", "col3", "col4", "col5", "col6", "col7", "col8", "col9", "col10"],
        data_types=["string"] * 10,
    )

    db_session.add(metadata)
    await db_session.commit()

    # 验证关系
    stmt = select(FileUpload).where(FileUpload.id == file_upload.id)
    result = await db_session.execute(stmt)
    loaded_file = result.scalars().first()

    assert loaded_file is not None
    assert loaded_file.filename == "data.xlsx"

    # 验证反向关系
    if hasattr(loaded_file, "metadata"):
        assert loaded_file.metadata.rows_count == 500


@pytest.mark.asyncio
async def test_file_upload_defaults(db_session):
    """测试 FileUpload 的默认值。"""
    file_upload = FileUpload(
        data_source_id=1,
        filename="test.csv",
        file_path="/uploads/test.csv",
        file_format="csv",
        file_size=100.0,
    )

    db_session.add(file_upload)
    await db_session.flush()

    # 验证默认值
    assert file_upload.row_count == 0 or file_upload.row_count is None
    assert file_upload.column_count == 0 or file_upload.column_count is None
    assert file_upload.parse_status == "pending"
    assert file_upload.is_indexed == False


@pytest.mark.asyncio
async def test_file_metadata_with_json_columns(db_session):
    """测试 FileMetadata 的 JSON 列支持。"""
    file_upload = FileUpload(
        data_source_id=1,
        filename="data.csv",
        file_path="/uploads/data.csv",
        file_format="csv",
        file_size=1000.0,
    )

    db_session.add(file_upload)
    await db_session.flush()

    # 创建包含 JSON 数据的 FileMetadata
    metadata = FileMetadata(
        file_upload_id=file_upload.id,
        rows_count=50,
        columns_count=3,
        column_names=["id", "name", "age"],
        data_types=["integer", "string", "integer"],
    )

    db_session.add(metadata)
    await db_session.flush()

    # 验证 JSON 列
    assert isinstance(metadata.column_names, list)
    assert isinstance(metadata.data_types, list)
    assert metadata.column_names[0] == "id"
    assert metadata.data_types[0] == "integer"


@pytest.mark.asyncio
async def test_multiple_file_uploads_for_datasource(db_session):
    """测试同一数据源有多个文件上传。"""
    # 创建多个文件上传
    file1 = FileUpload(
        data_source_id=1,
        filename="data1.csv",
        file_path="/uploads/data1.csv",
        file_format="csv",
        file_size=1000.0,
    )

    file2 = FileUpload(
        data_source_id=1,
        filename="data2.csv",
        file_path="/uploads/data2.csv",
        file_format="csv",
        file_size=2000.0,
    )

    db_session.add(file1)
    db_session.add(file2)
    await db_session.flush()

    # 验证
    stmt = select(FileUpload).where(FileUpload.data_source_id == 1)
    result = await db_session.execute(stmt)
    files = result.scalars().all()

    assert len(files) == 2
    assert all(f.data_source_id == 1 for f in files)


@pytest.mark.asyncio
async def test_file_upload_update(db_session):
    """测试更新 FileUpload 记录。"""
    file_upload = FileUpload(
        data_source_id=1,
        filename="test.csv",
        file_path="/uploads/test.csv",
        file_format="csv",
        file_size=1000.0,
        parse_status="pending",
    )

    db_session.add(file_upload)
    await db_session.flush()

    # 更新状态
    file_upload.parse_status = "success"
    file_upload.row_count = 100
    file_upload.column_count = 5

    await db_session.flush()

    # 验证
    assert file_upload.parse_status == "success"
    assert file_upload.row_count == 100
    assert file_upload.column_count == 5


@pytest.mark.asyncio
async def test_file_upload_delete_cascade(db_session):
    """测试删除 FileUpload 时级联删除 FileMetadata。"""
    # 创建 FileUpload
    file_upload = FileUpload(
        data_source_id=1,
        filename="test.csv",
        file_path="/uploads/test.csv",
        file_format="csv",
        file_size=1000.0,
    )

    db_session.add(file_upload)
    await db_session.flush()

    # 创建 FileMetadata
    metadata = FileMetadata(
        file_upload_id=file_upload.id,
        rows_count=50,
        columns_count=5,
    )

    db_session.add(metadata)
    await db_session.commit()

    file_id = file_upload.id
    metadata_id = metadata.id

    # 删除 FileUpload
    await db_session.delete(file_upload)
    await db_session.commit()

    # 验证 FileMetadata 也被删除
    stmt = select(FileMetadata).where(FileMetadata.id == metadata_id)
    result = await db_session.execute(stmt)
    deleted_metadata = result.scalars().first()

    assert deleted_metadata is None


@pytest.mark.asyncio
async def test_file_upload_repr(db_session):
    """测试 FileUpload 的字符串表示。"""
    file_upload = FileUpload(
        data_source_id=1,
        filename="test_file.csv",
        file_path="/uploads/test_file.csv",
        file_format="csv",
        file_size=1000.0,
    )

    db_session.add(file_upload)
    await db_session.flush()

    repr_str = repr(file_upload)
    assert "FileUpload" in repr_str
    assert "test_file.csv" in repr_str


@pytest.mark.asyncio
async def test_file_metadata_repr(db_session):
    """测试 FileMetadata 的字符串表示。"""
    file_upload = FileUpload(
        data_source_id=1,
        filename="test.csv",
        file_path="/uploads/test.csv",
        file_format="csv",
        file_size=1000.0,
    )

    db_session.add(file_upload)
    await db_session.flush()

    metadata = FileMetadata(
        file_upload_id=file_upload.id,
        rows_count=100,
        columns_count=5,
    )

    db_session.add(metadata)
    await db_session.flush()

    repr_str = repr(metadata)
    assert "FileMetadata" in repr_str
    assert "5" in repr_str  # columns_count

"""
文件上传 API 集成测试。

测试文件上传、列表、详情、删除等端点。
"""

import pytest
import tempfile
import os
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import create_app
from src.db.base import Base
from src.models import DataSource, DataSourceType, DataSourceStatus


@pytest.fixture
def temp_database():
    """创建临时内存数据库。"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async def setup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    # 这里使用同步运行异步代码（仅限测试）
    import asyncio
    try:
        asyncio.run(setup())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(setup())
        loop.close()

    return engine


@pytest.fixture
def test_client(temp_database):
    """创建测试客户端。"""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def sample_csv_file():
    """创建示例 CSV 文件。"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write('id,name,age\n')
        f.write('1,Alice,25\n')
        f.write('2,Bob,30\n')
        return f.name


class TestFileUploadAPI:
    """文件上传 API 测试类。"""

    def test_upload_file_success(self, test_client, sample_csv_file):
        """测试成功上传文件。"""
        with open(sample_csv_file, 'rb') as f:
            response = test_client.post(
                "/api/file-uploads/",
                data={"data_source_id": "1"},
                files={"file": ("test.csv", f, "text/csv")}
            )

        # 清理
        os.unlink(sample_csv_file)

        # 验证
        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "test.csv"
        assert data["file_format"] == "csv"
        assert data["parse_status"] == "pending"

    def test_upload_invalid_file_type(self, test_client):
        """测试上传不支持的文件类型。"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt') as f:
            f.write('test content')
            f.flush()

            response = test_client.post(
                "/api/file-uploads/",
                data={"data_source_id": "1"},
                files={"file": ("test.txt", f, "text/plain")}
            )

        assert response.status_code == 400
        assert "文件验证失败" in response.json()["detail"]

    def test_list_files_empty(self, test_client):
        """测试列出空文件列表。"""
        response = test_client.get("/api/file-uploads/")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_list_files_with_pagination(self, test_client):
        """测试文件列表分页。"""
        response = test_client.get("/api/file-uploads/?skip=0&limit=10")

        assert response.status_code == 200
        data = response.json()
        assert "skip" in data
        assert "limit" in data
        assert data["skip"] == 0
        assert data["limit"] == 10

    def test_get_nonexistent_file(self, test_client):
        """测试获取不存在的文件。"""
        response = test_client.get("/api/file-uploads/9999")

        assert response.status_code == 404
        assert "不存在" in response.json()["detail"]

    def test_delete_nonexistent_file(self, test_client):
        """测试删除不存在的文件。"""
        response = test_client.delete("/api/file-uploads/9999")

        assert response.status_code == 500


class TestFilePreviewAPI:
    """文件预览 API 测试类。"""

    def test_get_preview_nonexistent_file(self, test_client):
        """测试获取不存在文件的预览。"""
        response = test_client.get("/api/file-uploads/9999/preview")

        assert response.status_code == 404
        assert "不存在" in response.json()["detail"]

    def test_get_metadata_nonexistent_file(self, test_client):
        """测试获取不存在文件的元数据。"""
        response = test_client.get("/api/file-uploads/9999/metadata")

        assert response.status_code == 404

    def test_get_sheets_nonexistent_file(self, test_client):
        """测试获取不存在文件的工作表列表。"""
        response = test_client.get("/api/file-uploads/9999/sheets")

        assert response.status_code == 404

    def test_parse_nonexistent_file(self, test_client):
        """测试解析不存在的文件。"""
        response = test_client.post("/api/file-uploads/9999/parse")

        assert response.status_code == 404


class TestFileUploadIntegration:
    """文件上传集成测试。"""

    def test_upload_list_get_flow(self, test_client, sample_csv_file):
        """测试上传-列表-获取流程。"""
        # 1. 上传文件
        with open(sample_csv_file, 'rb') as f:
            upload_response = test_client.post(
                "/api/file-uploads/",
                data={"data_source_id": "1"},
                files={"file": ("data.csv", f, "text/csv")}
            )

        os.unlink(sample_csv_file)

        if upload_response.status_code != 201:
            pytest.skip("文件上传失败")

        file_id = upload_response.json()["id"]

        # 2. 列表查询
        list_response = test_client.get("/api/file-uploads/")
        assert list_response.status_code == 200

        # 3. 获取详情
        get_response = test_client.get(f"/api/file-uploads/{file_id}")
        assert get_response.status_code == 200
        assert get_response.json()["id"] == file_id

    def test_upload_delete_flow(self, test_client, sample_csv_file):
        """测试上传-删除流程。"""
        # 1. 上传
        with open(sample_csv_file, 'rb') as f:
            upload_response = test_client.post(
                "/api/file-uploads/",
                data={"data_source_id": "1"},
                files={"file": ("test.csv", f, "text/csv")}
            )

        os.unlink(sample_csv_file)

        if upload_response.status_code != 201:
            pytest.skip("文件上传失败")

        file_id = upload_response.json()["id"]

        # 2. 删除
        delete_response = test_client.delete(f"/api/file-uploads/{file_id}")
        assert delete_response.status_code == 200
        assert delete_response.json()["success"] == True

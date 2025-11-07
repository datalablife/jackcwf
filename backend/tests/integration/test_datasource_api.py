"""
数据源 API 集成测试

测试所有数据源管理 API 端点：
- POST /api/datasources/postgres - 创建 PostgreSQL 连接
- GET /api/datasources - 列表查询
- GET /api/datasources/{id} - 单个查询
- POST /api/datasources/{id}/test - 连接测试
- DELETE /api/datasources/{id} - 删除操作
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from src.main import app
from src.models.datasource import DataSource, DataSourceStatus
from src.models.database_connection import DatabaseConnection
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def postgres_connection_data():
    """PostgreSQL 连接数据"""
    return {
        "name": "test_postgres",
        "description": "测试 PostgreSQL 连接",
        "host": "localhost",
        "port": 5432,
        "database": "test_db",
        "username": "test_user",
        "password": "test_password",
        "ssl_enabled": False,
    }


@pytest.fixture
def mock_db_session():
    """模拟数据库会话"""
    session = AsyncMock(spec=AsyncSession)
    return session


class TestDataSourceAPI:
    """数据源 API 测试类"""

    def test_create_postgres_datasource_success(self, client, postgres_connection_data):
        """测试成功创建 PostgreSQL 数据源"""
        with patch("src.api.datasources.DataSourceService") as mock_service:
            # 模拟数据源创建
            expected_response = {
                "id": 1,
                "name": "test_postgres",
                "type": "postgresql",
                "status": "connected",
                "description": "测试 PostgreSQL 连接",
                "created_at": "2025-11-08T12:00:00",
                "updated_at": "2025-11-08T12:00:00",
                "error_message": None,
            }

            mock_service_instance = MagicMock()
            mock_service.return_value = mock_service_instance
            mock_service_instance.create_postgres_datasource = AsyncMock(
                return_value=expected_response
            )

            response = client.post(
                "/api/datasources/postgres",
                json=postgres_connection_data,
            )

            assert response.status_code == 201
            assert response.json()["id"] == 1
            assert response.json()["name"] == "test_postgres"

    def test_create_postgres_datasource_invalid_data(self, client):
        """测试使用无效数据创建数据源"""
        invalid_data = {
            "name": "",  # 名称为空
            "host": "localhost",
            "port": "invalid",  # 端口应为数字
        }

        response = client.post(
            "/api/datasources/postgres",
            json=invalid_data,
        )

        assert response.status_code == 422  # 验证错误

    def test_create_postgres_datasource_connection_failed(
        self, client, postgres_connection_data
    ):
        """测试连接失败的数据源创建"""
        with patch("src.api.datasources.DataSourceService") as mock_service:
            mock_service_instance = MagicMock()
            mock_service.return_value = mock_service_instance
            # 模拟连接失败
            mock_service_instance.create_postgres_datasource = AsyncMock(
                side_effect=Exception("连接失败")
            )

            response = client.post(
                "/api/datasources/postgres",
                json=postgres_connection_data,
            )

            assert response.status_code == 400

    def test_list_datasources_empty(self, client):
        """测试列出空的数据源列表"""
        with patch("src.api.datasources.DataSourceService") as mock_service:
            mock_service_instance = MagicMock()
            mock_service.return_value = mock_service_instance
            mock_service_instance.list_datasources = AsyncMock(return_value=[])

            response = client.get("/api/datasources")

            assert response.status_code == 200
            assert response.json()["datasources"] == []

    def test_list_datasources_multiple(self, client):
        """测试列出多个数据源"""
        datasources = [
            {
                "id": 1,
                "name": "postgres_1",
                "type": "postgresql",
                "status": "connected",
                "description": "数据库 1",
                "created_at": "2025-11-08T10:00:00",
                "updated_at": "2025-11-08T10:00:00",
                "error_message": None,
            },
            {
                "id": 2,
                "name": "postgres_2",
                "type": "postgresql",
                "status": "error",
                "description": "数据库 2",
                "created_at": "2025-11-08T11:00:00",
                "updated_at": "2025-11-08T11:00:00",
                "error_message": "连接超时",
            },
        ]

        with patch("src.api.datasources.DataSourceService") as mock_service:
            mock_service_instance = MagicMock()
            mock_service.return_value = mock_service_instance
            mock_service_instance.list_datasources = AsyncMock(return_value=datasources)

            response = client.get("/api/datasources")

            assert response.status_code == 200
            assert len(response.json()["datasources"]) == 2

    def test_get_datasource_success(self, client):
        """测试成功获取单个数据源"""
        expected_datasource = {
            "id": 1,
            "name": "test_postgres",
            "type": "postgresql",
            "status": "connected",
            "description": "测试连接",
            "created_at": "2025-11-08T12:00:00",
            "updated_at": "2025-11-08T12:00:00",
            "error_message": None,
        }

        with patch("src.api.datasources.DataSourceService") as mock_service:
            mock_service_instance = MagicMock()
            mock_service.return_value = mock_service_instance
            mock_service_instance.get_datasource = AsyncMock(
                return_value=expected_datasource
            )

            response = client.get("/api/datasources/1")

            assert response.status_code == 200
            assert response.json()["name"] == "test_postgres"

    def test_get_datasource_not_found(self, client):
        """测试获取不存在的数据源"""
        with patch("src.api.datasources.DataSourceService") as mock_service:
            mock_service_instance = MagicMock()
            mock_service.return_value = mock_service_instance
            mock_service_instance.get_datasource = AsyncMock(return_value=None)

            response = client.get("/api/datasources/999")

            assert response.status_code == 404

    def test_test_connection_success(self, client):
        """测试连接测试成功"""
        with patch("src.api.datasources.DataSourceService") as mock_service:
            mock_service_instance = MagicMock()
            mock_service.return_value = mock_service_instance
            mock_service_instance.test_connection = AsyncMock(return_value=True)

            response = client.post("/api/datasources/1/test")

            assert response.status_code == 200
            assert response.json()["connected"] is True

    def test_test_connection_failed(self, client):
        """测试连接测试失败"""
        with patch("src.api.datasources.DataSourceService") as mock_service:
            mock_service_instance = MagicMock()
            mock_service.return_value = mock_service_instance
            mock_service_instance.test_connection = AsyncMock(return_value=False)

            response = client.post("/api/datasources/1/test")

            assert response.status_code == 200
            assert response.json()["connected"] is False

    def test_test_connection_not_found(self, client):
        """测试不存在的数据源连接测试"""
        with patch("src.api.datasources.DataSourceService") as mock_service:
            mock_service_instance = MagicMock()
            mock_service.return_value = mock_service_instance
            mock_service_instance.test_connection = AsyncMock(
                side_effect=Exception("数据源不存在")
            )

            response = client.post("/api/datasources/999/test")

            assert response.status_code == 400

    def test_delete_datasource_success(self, client):
        """测试成功删除数据源"""
        with patch("src.api.datasources.DataSourceService") as mock_service:
            mock_service_instance = MagicMock()
            mock_service.return_value = mock_service_instance
            mock_service_instance.delete_datasource = AsyncMock(return_value=True)

            response = client.delete("/api/datasources/1")

            assert response.status_code == 200
            assert response.json()["success"] is True

    def test_delete_datasource_not_found(self, client):
        """测试删除不存在的数据源"""
        with patch("src.api.datasources.DataSourceService") as mock_service:
            mock_service_instance = MagicMock()
            mock_service.return_value = mock_service_instance
            mock_service_instance.delete_datasource = AsyncMock(return_value=False)

            response = client.delete("/api/datasources/999")

            assert response.status_code == 404

    def test_datasource_lifecycle(self, client, postgres_connection_data):
        """测试数据源生命周期：创建 -> 查询 -> 测试 -> 删除"""
        with patch("src.api.datasources.DataSourceService") as mock_service:
            mock_service_instance = MagicMock()
            mock_service.return_value = mock_service_instance

            # 创建数据源
            created_datasource = {
                "id": 1,
                "name": "test_postgres",
                "type": "postgresql",
                "status": "connected",
                "created_at": "2025-11-08T12:00:00",
                "updated_at": "2025-11-08T12:00:00",
                "error_message": None,
            }
            mock_service_instance.create_postgres_datasource = AsyncMock(
                return_value=created_datasource
            )

            response = client.post(
                "/api/datasources/postgres",
                json=postgres_connection_data,
            )
            assert response.status_code == 201

            # 获取数据源
            mock_service_instance.get_datasource = AsyncMock(
                return_value=created_datasource
            )
            response = client.get("/api/datasources/1")
            assert response.status_code == 200

            # 测试连接
            mock_service_instance.test_connection = AsyncMock(return_value=True)
            response = client.post("/api/datasources/1/test")
            assert response.status_code == 200

            # 删除数据源
            mock_service_instance.delete_datasource = AsyncMock(return_value=True)
            response = client.delete("/api/datasources/1")
            assert response.status_code == 200

    def test_error_handling_bad_request(self, client):
        """测试错误处理：不完整的请求数据"""
        incomplete_data = {
            "name": "test",
            # 缺少必需的字段
        }

        response = client.post(
            "/api/datasources/postgres",
            json=incomplete_data,
        )

        assert response.status_code == 422

    def test_error_handling_internal_server_error(self, client):
        """测试错误处理：内部服务器错误"""
        with patch("src.api.datasources.DataSourceService") as mock_service:
            mock_service_instance = MagicMock()
            mock_service.return_value = mock_service_instance
            mock_service_instance.list_datasources = AsyncMock(
                side_effect=Exception("数据库错误")
            )

            response = client.get("/api/datasources")

            assert response.status_code == 500

    def test_concurrent_datasource_operations(self, client):
        """测试并发数据源操作"""
        with patch("src.api.datasources.DataSourceService") as mock_service:
            mock_service_instance = MagicMock()
            mock_service.return_value = mock_service_instance

            datasources = [
                {
                    "id": i,
                    "name": f"postgres_{i}",
                    "type": "postgresql",
                    "status": "connected",
                    "created_at": "2025-11-08T12:00:00",
                    "updated_at": "2025-11-08T12:00:00",
                }
                for i in range(1, 6)
            ]

            mock_service_instance.list_datasources = AsyncMock(return_value=datasources)

            response = client.get("/api/datasources")

            assert response.status_code == 200
            assert len(response.json()["datasources"]) == 5

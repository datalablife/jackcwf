"""
数据源管理服务。

处理数据源的创建、检索、测试和删除操作。
与 PostgreSQL 和加密服务集成。
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models import DataSource, DataSourceType, DataSourceStatus, DatabaseConnection
from src.services import get_encryption_service, PostgresService


class DataSourceService:
    """
    数据源管理服务。

    提供数据源的创建、检索、测试和删除操作。
    """

    @staticmethod
    async def create_postgres_datasource(
        session: AsyncSession,
        name: str,
        description: Optional[str],
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
    ) -> DataSource:
        """
        创建新的 PostgreSQL 数据源。

        参数:
            session: 数据库异步会话
            name: 数据源名称
            description: 可选的描述
            host: PostgreSQL 主机
            port: PostgreSQL 端口
            database: 数据库名称
            username: 数据库用户名
            password: 数据库密码（将被加密存储）

        返回:
            DataSource: 创建的数据源

        抛出异常:
            Exception: 如果创建失败
        """
        # 首先测试连接
        postgres = PostgresService(host, port, database, username, password)
        try:
            await postgres.test_connection()
            await postgres.disconnect()
        except Exception as e:
            raise ValueError(f"无法连接到 PostgreSQL: {e}")

        # 加密密码
        cipher = get_encryption_service()
        encrypted_password = cipher.encrypt(password)

        # 创建数据源
        data_source = DataSource(
            name=name,
            description=description,
            type=DataSourceType.POSTGRESQL,
            status=DataSourceStatus.CONNECTED,
        )

        # 创建数据库连接
        db_connection = DatabaseConnection(
            data_source=data_source,
            host=host,
            port=port,
            database=database,
            username=username,
            encrypted_password=encrypted_password,
        )

        session.add(data_source)
        session.add(db_connection)
        await session.commit()
        await session.refresh(data_source)

        return data_source

    @staticmethod
    async def get_datasource(
        session: AsyncSession, datasource_id: int
    ) -> Optional[DataSource]:
        """
        根据 ID 检索数据源。

        参数:
            session: 异步会话
            datasource_id: 数据源 ID

        返回:
            DataSource 或 None（如果未找到）
        """
        stmt = select(DataSource).where(DataSource.id == datasource_id)
        result = await session.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def list_datasources(session: AsyncSession) -> List[DataSource]:
        """
        列出所有数据源。

        参数:
            session: 异步会话

        返回:
            DataSource 对象列表
        """
        stmt = select(DataSource).order_by(DataSource.created_at.desc())
        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def delete_datasource(
        session: AsyncSession, datasource_id: int
    ) -> bool:
        """
        删除数据源。

        参数:
            session: 异步会话
            datasource_id: 数据源 ID

        返回:
            bool: 如果删除成功返回 True，如果未找到返回 False
        """
        datasource = await DataSourceService.get_datasource(session, datasource_id)
        if not datasource:
            return False

        await session.delete(datasource)
        await session.commit()
        return True

    @staticmethod
    async def test_connection(
        session: AsyncSession, datasource_id: int
    ) -> Dict[str, Any]:
        """
        测试数据源的连接。

        参数:
            session: 异步会话
            datasource_id: 数据源 ID

        返回:
            dict: 测试结果字典 {'success': bool, 'message': str}

        抛出异常:
            ValueError: 如果数据源未找到
        """
        datasource = await DataSourceService.get_datasource(session, datasource_id)
        if not datasource:
            raise ValueError(f"数据源 {datasource_id} 未找到")

        if datasource.type != DataSourceType.POSTGRESQL:
            raise ValueError("仅支持 PostgreSQL 连接")

        # 获取连接详情
        stmt = select(DatabaseConnection).where(
            DatabaseConnection.data_source_id == datasource_id
        )
        result = await session.execute(stmt)
        connection = result.scalars().first()

        if not connection:
            raise ValueError("此数据源未找到数据库连接")

        # 解密密码
        cipher = get_encryption_service()
        decrypted_password = cipher.decrypt(connection.encrypted_password)

        # 测试连接
        postgres = PostgresService(
            connection.host,
            connection.port,
            connection.database,
            connection.username,
            decrypted_password,
        )

        try:
            await postgres.test_connection()
            await postgres.disconnect()
            return {"success": True, "message": "连接成功"}
        except Exception as e:
            return {"success": False, "message": f"连接失败: {e}"}

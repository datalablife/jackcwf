# Epic 1 - 实现路线图与代码参考

## 详细的分步实现计划

### 第1阶段：基础设施准备（第1-2周）

#### Week 1, Day 1-2: 数据库迁移完善

**目标**：完善现有迁移系统，实现自动化维护任务

**文件创建**：`src/db/migrations_advanced.py`

```python
"""高级迁移管理系统"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from src.db.config import engine

logger = logging.getLogger(__name__)

class AdvancedMigrationManager:
    """完善的迁移管理器"""

    def __init__(self, db_engine: AsyncEngine = None):
        self.engine = db_engine or engine

    async def run_all_migrations(self):
        """运行所有迁移步骤"""
        async with self.engine.begin() as conn:
            # 1. 启用扩展
            await self._enable_extensions(conn)

            # 2. 创建表
            await self._create_tables(conn)

            # 3. 创建索引
            await self._create_indices(conn)

            # 4. 设置分区
            await self._setup_partitions(conn)

            # 5. 创建触发器
            await self._create_triggers(conn)

    async def _enable_extensions(self, conn):
        """启用所有必需的 PostgreSQL 扩展"""
        extensions = [
            "vector",  # pgvector
            "uuid-ossp",  # UUID 生成
            "pg_trgm",  # 全文搜索
        ]

        for ext in extensions:
            try:
                await conn.execute(text(f"CREATE EXTENSION IF NOT EXISTS {ext}"))
                logger.info(f"Enabled extension: {ext}")
            except Exception as e:
                logger.warning(f"Could not enable extension {ext}: {e}")

    async def _create_tables(self, conn):
        """创建所有表"""
        from src.db.base import Base

        await conn.run_sync(Base.metadata.create_all)
        logger.info("All tables created")

    async def _create_indices(self, conn):
        """创建所有索引"""
        indices = [
            # Conversations 索引
            """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversations_user_active
               ON conversations (user_id) WHERE is_deleted = false""",

            # Messages 索引
            """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_conversation_recent
               ON messages (conversation_id, created_at DESC)""",

            # Embeddings HNSW 索引
            """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_embeddings_vector_hnsw
               ON embeddings USING hnsw (embedding vector_cosine_ops)
               WITH (m = 16, ef_construction = 64)""",
        ]

        for idx_sql in indices:
            try:
                await conn.execute(text(idx_sql))
                logger.info(f"Created index")
            except Exception as e:
                if "already exists" not in str(e):
                    logger.warning(f"Index creation issue: {e}")

    async def _setup_partitions(self, conn):
        """设置表分区"""
        await self._setup_embeddings_partitions(conn)
        logger.info("Partitions set up")

    async def _setup_embeddings_partitions(self, conn):
        """为 embeddings 表设置月份分区"""
        now = datetime.utcnow()

        # 创建当前月、下月、以及往前推1个月的分区
        for offset in [-1, 0, 1]:
            month_date = now + timedelta(days=30 * offset)
            month_str = month_date.strftime("%Y_%m")
            partition_name = f"embeddings_{month_str}"

            start_date = month_date.strftime("%Y-%m-01")
            next_month = month_date + timedelta(days=30)
            next_month_date = next_month.replace(day=1)
            end_date = next_month_date.strftime("%Y-%m-%d")

            try:
                await conn.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS {partition_name}
                    PARTITION OF embeddings
                    FOR VALUES FROM ('{start_date}') TO ('{end_date}')
                """))
                logger.info(f"Created partition: {partition_name}")
            except Exception as e:
                if "already exists" not in str(e):
                    logger.warning(f"Partition creation: {e}")

    async def _create_triggers(self, conn):
        """创建数据库触发器"""
        # 自动更新 updated_at 字段
        trigger_sql = """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';

        CREATE TRIGGER update_conversations_updated_at
            BEFORE UPDATE ON conversations
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();

        CREATE TRIGGER update_documents_updated_at
            BEFORE UPDATE ON documents
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """

        try:
            await conn.execute(text(trigger_sql))
            logger.info("Triggers created")
        except Exception as e:
            logger.warning(f"Trigger creation: {e}")

    async def verify_migrations(self):
        """验证迁移是否成功"""
        async with self.engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('conversations', 'messages', 'documents', 'embeddings')
            """))

            tables = [row[0] for row in result]
            expected_tables = {'conversations', 'messages', 'documents', 'embeddings'}

            if set(tables) == expected_tables:
                logger.info("All tables created successfully")
                return True
            else:
                missing = expected_tables - set(tables)
                logger.error(f"Missing tables: {missing}")
                return False

    async def get_migration_status(self) -> dict:
        """获取迁移状态"""
        async with self.engine.begin() as conn:
            # 表统计
            result = await conn.execute(text("""
                SELECT
                    tablename,
                    pg_size_pretty(pg_total_relation_size('public.' || tablename)) as size,
                    (SELECT count(*) FROM public.conversations)::text as conversation_count,
                    (SELECT count(*) FROM public.messages)::text as message_count,
                    (SELECT count(*) FROM public.embeddings)::text as embedding_count
                FROM pg_tables
                WHERE schemaname = 'public'
                AND tablename IN ('conversations', 'messages', 'documents', 'embeddings')
            """))

            return {"tables": result.fetchall()}
```

**改进的初始化函数**：

```python
# 更新 src/db/migrations.py

async def init_db(db_engine: Optional[AsyncEngine] = None) -> None:
    """
    完整的数据库初始化
    """
    if db_engine is None:
        db_engine = engine

    manager = AdvancedMigrationManager(db_engine)

    try:
        logger.info("Starting database initialization...")

        # 运行所有迁移
        await manager.run_all_migrations()

        # 验证迁移
        if not await manager.verify_migrations():
            raise Exception("Migration verification failed")

        # 显示状态
        status = await manager.get_migration_status()
        logger.info(f"Migration status: {status}")

        logger.info("Database initialization completed successfully")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        raise
```

#### Week 1, Day 3-5: BaseRepository 增强

**文件更新**：`src/repositories/base.py`

已在前面的文档中详细提供。关键改进：
- 错误分类系统
- 重试装饰器
- 事务管理
- 批量操作优化

#### Week 2, Day 1-3: 异常处理系统

**文件创建**：`src/exceptions.py`

```python
"""统一异常处理系统"""

class ApplicationException(Exception):
    """应用程序基异常"""

    def __init__(self, message: str, code: str = "UNKNOWN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)

class RepositoryException(ApplicationException):
    """存储库层异常"""
    pass

class DuplicateRecordError(RepositoryException):
    """唯一性约束违反"""

    def __init__(self):
        super().__init__(
            "Record already exists or constraint violated",
            "DUPLICATE_RECORD"
        )

class RecordNotFoundError(RepositoryException):
    """记录不存在"""

    def __init__(self, record_type: str, record_id: str):
        super().__init__(
            f"{record_type} with ID {record_id} not found",
            "RECORD_NOT_FOUND"
        )

class TransactionError(RepositoryException):
    """事务错误"""

    def __init__(self, message: str = "Transaction failed"):
        super().__init__(message, "TRANSACTION_ERROR")

class ValidationError(ApplicationException):
    """验证错误"""

    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message, "VALIDATION_ERROR")

class AuthenticationError(ApplicationException):
    """认证错误"""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_ERROR")

class AuthorizationError(ApplicationException):
    """授权错误"""

    def __init__(self, message: str = "Access denied"):
        super().__init__(message, "AUTHORIZATION_ERROR")
```

### 第2阶段：存储库实现（第2-3周）

#### Week 2, Day 4-5 + Week 3, Day 1-2: 完整存储库实现

**检查清单**：

- [ ] ConversationRepository 完整
- [ ] MessageRepository 完整
- [ ] DocumentRepository 完整
- [ ] EmbeddingRepository 完整
- [ ] 性能测试通过
- [ ] 单元测试覆盖 > 80%

**性能测试脚本**：

```python
# tests/test_repository_performance.py

import pytest
import time
import asyncio
from uuid import uuid4
import numpy as np

from src.db.config import AsyncSessionLocal
from src.repositories import (
    ConversationRepository,
    MessageRepository,
    EmbeddingRepository,
)

@pytest.fixture
async def test_user_id():
    return f"test_user_{uuid4()}"

@pytest.mark.asyncio
async def test_conversation_crud_performance(test_user_id):
    """测试对话 CRUD 性能"""
    async with AsyncSessionLocal() as session:
        repo = ConversationRepository(session)

        # 创建性能测试
        start = time.time()
        for i in range(10):
            await repo.create(
                user_id=test_user_id,
                title=f"Test Conv {i}",
                system_prompt="Test prompt"
            )
        create_time = (time.time() - start) * 1000

        assert create_time < 500, f"Expected < 500ms, got {create_time:.2f}ms"

        # 列表查询性能测试
        start = time.time()
        conversations = await repo.get_user_conversations(test_user_id)
        list_time = (time.time() - start) * 1000

        assert list_time < 100, f"Expected < 100ms, got {list_time:.2f}ms"

        # 搜索性能测试
        start = time.time()
        results = await repo.search_by_title(test_user_id, "Test")
        search_time = (time.time() - start) * 1000

        assert search_time < 150, f"Expected < 150ms, got {search_time:.2f}ms"
```

### 第3阶段：API 层实现（第3-4周）

#### Week 3, Day 3-5 + Week 4, Day 1-2: API 路由完善

**改进的路由文件**：

```python
# src/api/dependencies.py（已在前面提供）
# src/api/conversation_routes.py（已在前面提供）
# 补充其他路由文件...
```

**消息路由**：

```python
# src/api/message_routes.py - 完整版本

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import (
    UserIdType,
    RequestIdType,
    get_async_session,
)
from src.repositories import MessageRepository
from src.schemas.conversation_schema import MessageSchema
from src.main import APIError, limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations/{conversation_id}/messages")

@router.get("", response_model=list[MessageSchema])
@limiter.limit("30/minute")
async def get_conversation_messages(
    request_id: RequestIdType,
    user_id: UserIdType,
    conversation_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    """获取对话消息"""
    try:
        repo = MessageRepository(session)
        messages = await repo.get_conversation_messages(
            conversation_id,
            skip=skip,
            limit=limit
        )

        return [
            MessageSchema(
                role=msg.role,
                content=msg.content,
                tool_calls=msg.tool_calls,
                tool_results=msg.tool_results,
                tokens_used=msg.tokens_used,
                created_at=msg.created_at,
            )
            for msg in messages
        ]

    except Exception as e:
        logger.error(f"[{request_id}] Error getting messages: {e}")
        raise APIError(
            message="Failed to get messages",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="GET_MESSAGES_ERROR"
        )

@router.post("", response_model=MessageSchema, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_message(
    request_id: RequestIdType,
    user_id: UserIdType,
    conversation_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    content: str = None,
):
    """创建新消息"""
    try:
        repo = MessageRepository(session)

        message = await repo.create(
            conversation_id=conversation_id,
            role="user",
            content=content
        )

        return MessageSchema(
            role=message.role,
            content=message.content,
            tokens_used=message.tokens_used,
            created_at=message.created_at,
        )

    except Exception as e:
        logger.error(f"[{request_id}] Error creating message: {e}")
        raise APIError(
            message="Failed to create message",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="CREATE_MESSAGE_ERROR"
        )
```

#### Week 4, Day 3-5: 测试和文档

**API 集成测试**：

```python
# tests/test_api_integration.py

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from src.main import app

client = TestClient(app)

@pytest.fixture
def user_id():
    return f"test_user_{uuid4()}"

def test_create_conversation(user_id):
    """测试创建对话"""
    response = client.post(
        "/api/v1/conversations",
        json={
            "title": "Test Conversation",
            "system_prompt": "You are helpful",
        },
        headers={"X-User-ID": user_id}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Conversation"
    assert "id" in data

def test_list_conversations(user_id):
    """测试列表查询"""
    response = client.get(
        "/api/v1/conversations",
        headers={"X-User-ID": user_id}
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
```

### 第4阶段：优化和监控（第4-5周）

#### Week 4, Day 1-2: 缓存集成

**文件创建**：`src/cache/redis_cache.py`（已在前面提供）

#### Week 4, Day 3-5: 日志和监控

**文件创建**：`src/utils/logging_config.py`

```python
"""日志配置和监控"""

import logging
import logging.handlers
from pythonjsonlogger import jsonlogger

def setup_logging(level="INFO", format="standard"):
    """设置结构化日志"""

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if format == "json":
        # JSON 日志格式（用于生产）
        handler = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter()
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
    else:
        # 标准日志格式（用于开发）
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)

    # 文件日志（可选）
    file_handler = logging.handlers.RotatingFileHandler(
        'logs/app.log',
        maxBytes=10_000_000,  # 10MB
        backupCount=5
    )
    file_formatter = jsonlogger.JsonFormatter()
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    return root_logger
```

#### Week 5, Day 1-3: 生产部署准备

**检查清单**：

- [ ] 所有测试通过 (coverage > 80%)
- [ ] 性能基准达标
- [ ] 安全审查完成
- [ ] 文档完整
- [ ] 部署脚本准备
- [ ] 监控配置就位

---

## 代码参考实现汇总

### 快速参考：关键文件修改清单

#### 新增文件

```
src/
├── db/
│   └── migrations_advanced.py (新)
├── cache/
│   └── redis_cache.py (新)
├── exceptions.py (新)
├── utils/
│   └── logging_config.py (新)
└── api/
    └── dependencies.py (新)
```

#### 修改文件

```
src/
├── db/
│   ├── config.py (增强连接配置)
│   └── migrations.py (集成 AdvancedMigrationManager)
├── main.py (增强 FastAPI 初始化)
├── repositories/
│   ├── base.py (增强事务和错误处理)
│   ├── conversation.py (已完整)
│   └── message.py (已完整)
└── api/
    ├── conversation_routes.py (改进依赖注入)
    └── message_routes.py (新增路由)
```

### 完整代码示例：日志配置

```python
# src/utils/logging_config.py

import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging(level="INFO", format_type="standard"):
    """
    配置应用日志系统

    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: 日志格式 ("standard" 或 "json")

    Returns:
        配置后的 logger
    """

    logger = logging.getLogger()
    logger.setLevel(level)

    # 确保 logs 目录存在
    os.makedirs("logs", exist_ok=True)

    # 标准输出处理器（用于容器日志）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    # 文件处理器（带轮转）
    file_handler = RotatingFileHandler(
        "logs/app.log",
        maxBytes=10_000_000,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(level)

    # 错误文件处理器
    error_handler = RotatingFileHandler(
        "logs/error.log",
        maxBytes=10_000_000,
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)

    # 格式器
    if format_type == "json":
        try:
            from pythonjsonlogger import jsonlogger

            formatter = jsonlogger.JsonFormatter(
                '%(timestamp)s %(level)s %(name)s %(message)s'
            )
        except ImportError:
            formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            )
    else:
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    # 应用格式器
    for handler in [console_handler, file_handler, error_handler]:
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
```

---

## 测试覆盖检查清单

### 单元测试

- [ ] BaseRepository (CRUD, 事务, 错误处理)
- [ ] ConversationRepository (查询, 软删除, 搜索)
- [ ] MessageRepository (角色过滤, Token 追踪)
- [ ] EmbeddingRepository (向量搜索, 性能)

### 集成测试

- [ ] API 端点 (CRUD, 错误响应)
- [ ] 数据库连接 (连接池, 关闭)
- [ ] 事务处理 (提交, 回滚)
- [ ] 缓存集成 (读取, 更新, 失效)

### 性能测试

- [ ] 对话查询 < 100ms
- [ ] 向量搜索 < 200ms
- [ ] 批量插入 < 150ms
- [ ] 连接池健康

### 安全测试

- [ ] SQL 注入防护
- [ ] 认证检验
- [ ] 授权检验
- [ ] 速率限制

---

## 部署检查清单

### 开发环境

- [ ] 依赖安装完整
- [ ] 数据库已初始化
- [ ] 所有测试通过
- [ ] 本地服务器正常运行

### 测试环境

- [ ] 数据库迁移完成
- [ ] 连接池配置正确
- [ ] 缓存服务可用
- [ ] 日志正确写入

### 生产环境

- [ ] SSL/TLS 配置
- [ ] 数据库备份策略
- [ ] 监控告警配置
- [ ] 日志聚合配置

---

**实现指南完成**

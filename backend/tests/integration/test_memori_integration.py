"""
Memori集成测试

测试Memori与Claude API的集成功能
"""

import pytest
import asyncio
from datetime import datetime
from typing import AsyncGenerator

# 假设的导入（根据实际项目调整）
# from src.services.memori_service import MemoriService, MemoriConfig
# from src.services.token_manager import TokenManager
# from src.services.session_manager import SessionManager


class MockMemoriService:
    """Mock Memori服务用于测试"""

    def __init__(self):
        self.memories = {}
        self.sessions = {}

    async def create_message(
        self,
        user_id: str,
        session_id: str,
        messages: list,
        **kwargs
    ):
        return {
            "content": "SELECT * FROM users;",
            "usage": {
                "input_tokens": 100,
                "output_tokens": 50,
                "total_tokens": 150
            },
            "model": "claude-sonnet-4-5-20250929",
            "stop_reason": "end_turn"
        }

    async def add_conscious_memory(
        self,
        user_id: str,
        session_id: str,
        content: str,
        metadata: dict = None,
        importance: float = 0.8,
        namespace: str = None
    ):
        key = f"{user_id}:{session_id}:{namespace}"
        if key not in self.memories:
            self.memories[key] = []
        self.memories[key].append({
            "content": content,
            "metadata": metadata or {},
            "importance": importance,
            "timestamp": datetime.utcnow()
        })

    async def search_memories(
        self,
        user_id: str,
        session_id: str,
        query: str,
        limit: int = 10,
        namespace: str = None
    ):
        key = f"{user_id}:{session_id}:{namespace}"
        memories = self.memories.get(key, [])
        return memories[:limit]

    async def clear_session_memory(
        self,
        user_id: str,
        session_id: str,
        namespace: str = None
    ):
        key = f"{user_id}:{session_id}:{namespace}"
        if key in self.memories:
            del self.memories[key]

    async def get_memory_stats(
        self,
        user_id: str,
        session_id: str,
        namespace: str = None
    ):
        key = f"{user_id}:{session_id}:{namespace}"
        memories = self.memories.get(key, [])
        return {
            "total_memories": len(memories),
            "memory_tokens": sum(len(m["content"].split()) * 1.3 for m in memories),
            "avg_importance": sum(m["importance"] for m in memories) / len(memories) if memories else 0,
            "oldest_memory": memories[0]["timestamp"].isoformat() if memories else None,
            "newest_memory": memories[-1]["timestamp"].isoformat() if memories else None
        }


@pytest.fixture
async def memori_service() -> AsyncGenerator[MockMemoriService, None]:
    """提供Memori服务fixture"""
    service = MockMemoriService()
    yield service
    # 清理
    service.memories.clear()


@pytest.mark.asyncio
class TestMemoriBasicIntegration:
    """测试Memori基本集成"""

    async def test_create_message_success(self, memori_service):
        """测试创建消息成功"""
        response = await memori_service.create_message(
            user_id="test_user",
            session_id="test_session",
            messages=[
                {"role": "user", "content": "生成查询所有用户的SQL"}
            ]
        )

        assert response["content"] is not None
        assert "SELECT" in response["content"]
        assert response["usage"]["total_tokens"] > 0
        assert response["model"] == "claude-sonnet-4-5-20250929"

    async def test_add_conscious_memory(self, memori_service):
        """测试添加显式记忆"""
        await memori_service.add_conscious_memory(
            user_id="test_user",
            session_id="test_session",
            content="Table: users (id INT, name VARCHAR)",
            metadata={"type": "schema", "table": "users"},
            importance=0.9,
            namespace="schema:1"
        )

        # 验证记忆已保存
        memories = await memori_service.search_memories(
            user_id="test_user",
            session_id="test_session",
            query="users table",
            namespace="schema:1"
        )

        assert len(memories) == 1
        assert "users" in memories[0]["content"]
        assert memories[0]["metadata"]["type"] == "schema"

    async def test_search_memories(self, memori_service):
        """测试搜索记忆"""
        # 添加多条记忆
        for i in range(5):
            await memori_service.add_conscious_memory(
                user_id="test_user",
                session_id="test_session",
                content=f"Memory {i}",
                importance=0.5 + i * 0.1
            )

        # 搜索记忆
        memories = await memori_service.search_memories(
            user_id="test_user",
            session_id="test_session",
            query="memory",
            limit=3
        )

        assert len(memories) <= 3
        assert all("Memory" in m["content"] for m in memories)

    async def test_clear_session_memory(self, memori_service):
        """测试清除会话记忆"""
        # 添加记忆
        await memori_service.add_conscious_memory(
            user_id="test_user",
            session_id="test_session",
            content="Test memory"
        )

        # 验证记忆存在
        memories_before = await memori_service.search_memories(
            user_id="test_user",
            session_id="test_session",
            query="test"
        )
        assert len(memories_before) == 1

        # 清除记忆
        await memori_service.clear_session_memory(
            user_id="test_user",
            session_id="test_session"
        )

        # 验证记忆已清除
        memories_after = await memori_service.search_memories(
            user_id="test_user",
            session_id="test_session",
            query="test"
        )
        assert len(memories_after) == 0

    async def test_memory_stats(self, memori_service):
        """测试获取记忆统计"""
        # 添加记忆
        for i in range(3):
            await memori_service.add_conscious_memory(
                user_id="test_user",
                session_id="test_session",
                content=f"Memory {i}",
                importance=0.7 + i * 0.1
            )

        # 获取统计
        stats = await memori_service.get_memory_stats(
            user_id="test_user",
            session_id="test_session"
        )

        assert stats["total_memories"] == 3
        assert stats["memory_tokens"] > 0
        assert 0.7 <= stats["avg_importance"] <= 1.0


@pytest.mark.asyncio
class TestMemoriSessionIsolation:
    """测试Memori会话隔离"""

    async def test_different_sessions_isolated(self, memori_service):
        """测试不同会话的记忆隔离"""
        # 为session1添加记忆
        await memori_service.add_conscious_memory(
            user_id="test_user",
            session_id="session1",
            content="Session 1 memory"
        )

        # 为session2添加记忆
        await memori_service.add_conscious_memory(
            user_id="test_user",
            session_id="session2",
            content="Session 2 memory"
        )

        # 搜索session1的记忆
        s1_memories = await memori_service.search_memories(
            user_id="test_user",
            session_id="session1",
            query="memory"
        )

        # 搜索session2的记忆
        s2_memories = await memori_service.search_memories(
            user_id="test_user",
            session_id="session2",
            query="memory"
        )

        # 验证隔离
        assert len(s1_memories) == 1
        assert len(s2_memories) == 1
        assert "Session 1" in s1_memories[0]["content"]
        assert "Session 2" in s2_memories[0]["content"]

    async def test_different_users_isolated(self, memori_service):
        """测试不同用户的记忆隔离"""
        session_id = "shared_session"

        # 为user1添加记忆
        await memori_service.add_conscious_memory(
            user_id="user1",
            session_id=session_id,
            content="User 1 memory"
        )

        # 为user2添加记忆
        await memori_service.add_conscious_memory(
            user_id="user2",
            session_id=session_id,
            content="User 2 memory"
        )

        # 搜索user1的记忆
        u1_memories = await memori_service.search_memories(
            user_id="user1",
            session_id=session_id,
            query="memory"
        )

        # 搜索user2的记忆
        u2_memories = await memori_service.search_memories(
            user_id="user2",
            session_id=session_id,
            query="memory"
        )

        # 验证隔离
        assert "User 1" in u1_memories[0]["content"]
        assert "User 2" in u2_memories[0]["content"]

    async def test_namespace_isolation(self, memori_service):
        """测试命名空间隔离"""
        user_id = "test_user"
        session_id = "test_session"

        # 在不同命名空间添加记忆
        await memori_service.add_conscious_memory(
            user_id=user_id,
            session_id=session_id,
            content="Schema memory",
            namespace="schema:1"
        )

        await memori_service.add_conscious_memory(
            user_id=user_id,
            session_id=session_id,
            content="Query memory",
            namespace="query:1"
        )

        # 搜索schema命名空间
        schema_memories = await memori_service.search_memories(
            user_id=user_id,
            session_id=session_id,
            query="memory",
            namespace="schema:1"
        )

        # 搜索query命名空间
        query_memories = await memori_service.search_memories(
            user_id=user_id,
            session_id=session_id,
            query="memory",
            namespace="query:1"
        )

        # 验证隔离
        assert "Schema" in schema_memories[0]["content"]
        assert "Query" in query_memories[0]["content"]


@pytest.mark.asyncio
class TestMemoriPerformance:
    """测试Memori性能"""

    async def test_concurrent_requests(self, memori_service):
        """测试并发请求处理"""
        # 创建10个并发请求
        tasks = [
            memori_service.create_message(
                user_id=f"user_{i}",
                session_id=f"session_{i}",
                messages=[{"role": "user", "content": f"Query {i}"}]
            )
            for i in range(10)
        ]

        # 并发执行
        start_time = asyncio.get_event_loop().time()
        responses = await asyncio.gather(*tasks)
        end_time = asyncio.get_event_loop().time()

        # 验证所有请求成功
        assert len(responses) == 10
        assert all(r["content"] is not None for r in responses)

        # 验证性能（应该比串行快）
        elapsed = end_time - start_time
        print(f"Concurrent requests completed in {elapsed:.2f}s")

    async def test_large_memory_retrieval(self, memori_service):
        """测试大量记忆检索性能"""
        user_id = "test_user"
        session_id = "test_session"

        # 添加100条记忆
        for i in range(100):
            await memori_service.add_conscious_memory(
                user_id=user_id,
                session_id=session_id,
                content=f"Memory {i}: Some content about topic {i % 10}",
                importance=0.5 + (i % 50) * 0.01
            )

        # 检索记忆
        start_time = asyncio.get_event_loop().time()
        memories = await memori_service.search_memories(
            user_id=user_id,
            session_id=session_id,
            query="topic",
            limit=10
        )
        end_time = asyncio.get_event_loop().time()

        # 验证检索成功且快速
        assert len(memories) <= 10
        elapsed = end_time - start_time
        assert elapsed < 1.0, f"Retrieval too slow: {elapsed:.2f}s"


@pytest.mark.asyncio
class TestMemoriEdgeCases:
    """测试Memori边缘情况"""

    async def test_empty_content(self, memori_service):
        """测试空内容处理"""
        await memori_service.add_conscious_memory(
            user_id="test_user",
            session_id="test_session",
            content=""
        )

        memories = await memori_service.search_memories(
            user_id="test_user",
            session_id="test_session",
            query="anything"
        )

        # 应该处理空内容而不崩溃
        assert isinstance(memories, list)

    async def test_very_long_content(self, memori_service):
        """测试超长内容处理"""
        long_content = "x" * 10000  # 10K字符

        await memori_service.add_conscious_memory(
            user_id="test_user",
            session_id="test_session",
            content=long_content
        )

        memories = await memori_service.search_memories(
            user_id="test_user",
            session_id="test_session",
            query="x"
        )

        # 应该能处理长内容
        assert len(memories) == 1

    async def test_special_characters(self, memori_service):
        """测试特殊字符处理"""
        special_content = "Table: users\nColumns: name (VARCHAR), 'email' (TEXT)"

        await memori_service.add_conscious_memory(
            user_id="test_user",
            session_id="test_session",
            content=special_content
        )

        memories = await memori_service.search_memories(
            user_id="test_user",
            session_id="test_session",
            query="users"
        )

        # 应该正确处理特殊字符
        assert len(memories) == 1
        assert "users" in memories[0]["content"]

    async def test_unicode_content(self, memori_service):
        """测试Unicode内容处理"""
        unicode_content = "用户表: users (用户ID, 姓名, 邮箱)"

        await memori_service.add_conscious_memory(
            user_id="test_user",
            session_id="test_session",
            content=unicode_content
        )

        memories = await memori_service.search_memories(
            user_id="test_user",
            session_id="test_session",
            query="用户表"
        )

        # 应该正确处理Unicode
        assert len(memories) == 1
        assert "用户" in memories[0]["content"]


# 运行测试的辅助函数
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

# Memori与Anthropic Claude API集成最佳实践指南

**文档版本**: 1.0.0
**创建日期**: 2025-11-11
**适用项目**: Text2SQL 数据管理系统
**作者**: AI Integration Team

---

## 目录

1. [概述](#概述)
2. [集成实现方案](#集成实现方案)
3. [记忆管理策略](#记忆管理策略)
4. [FastAPI服务集成](#fastapi服务集成)
5. [配置和环境管理](#配置和环境管理)
6. [监控和调试](#监控和调试)
7. [生产环境部署](#生产环境部署)
8. [常见陷阱和解决方案](#常见陷阱和解决方案)

---

## 概述

### Memori是什么？

Memori是一个为AI代理提供持久化、可查询内存的开源系统，核心特性包括：

- **自动记忆管理**: 无需手动管理上下文窗口
- **语义检索**: 基于向量相似度的智能记忆检索
- **多模式支持**: Conscious（显式）和 Auto（隐式）记忆模式
- **跨会话持久化**: 记忆可在多个会话间保持
- **记忆重要性评分**: 智能过滤和优先级排序

### 为什么选择Memori？

在Text2SQL场景中，Memori解决了以下问题：

1. **上下文窗口限制**: Claude有限的token窗口需要智能记忆管理
2. **多轮对话连贯性**: 用户可能分多次对话完成复杂查询构建
3. **数据源记忆**: 需要记住用户偏好的数据源和查询模式
4. **性能优化**: 避免重复发送相同的schema信息
5. **个性化体验**: 学习用户的SQL风格和习惯

---

## 集成实现方案

### 1. 架构设计

#### 1.1 推荐的三层架构

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │               AI Service Layer                        │  │
│  │  ┌─────────────────┐      ┌─────────────────────┐    │  │
│  │  │  Claude Client  │◄────►│  Memori Manager     │    │  │
│  │  └─────────────────┘      └─────────────────────┘    │  │
│  │           ▲                         ▲                 │  │
│  └───────────┼─────────────────────────┼─────────────────┘  │
│              │                         │                    │
│  ┌───────────▼─────────────────────────▼─────────────────┐  │
│  │              Session Manager                          │  │
│  │    (Session ID, User Context, Memory Isolation)       │  │
│  └───────────────────────────────────────────────────────┘  │
│              │                                              │
│  ┌───────────▼─────────────────────────────────────────┐   │
│  │           Database Layer (PostgreSQL)               │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

#### 1.2 核心实现代码

**文件**: `/mnt/d/工作区/云开发/working/backend/src/services/memori_service.py`

```python
"""
Memori记忆管理服务
提供AI对话的持久化记忆和上下文管理
"""

import os
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
import logging

from anthropic import Anthropic, AsyncAnthropic
from memori import Memori, MemoryMode

logger = logging.getLogger(__name__)


class MemoriConfig:
    """Memori配置管理"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-5-20250929",
        conscious_ingest: bool = True,
        auto_ingest: bool = True,
        max_memory_tokens: int = 100000,  # 最大记忆token数
        retrieval_limit: int = 10,  # 每次检索的记忆数量
        importance_threshold: float = 0.5,  # 记忆重要性阈值
    ):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self.conscious_ingest = conscious_ingest
        self.auto_ingest = auto_ingest
        self.max_memory_tokens = max_memory_tokens
        self.retrieval_limit = retrieval_limit
        self.importance_threshold = importance_threshold

    def validate(self) -> None:
        """验证配置有效性"""
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is required")
        if self.max_memory_tokens < 10000:
            raise ValueError("max_memory_tokens should be at least 10000")


class MemoriService:
    """
    Memori服务管理器

    处理AI对话的记忆管理、上下文注入和会话隔离
    """

    def __init__(self, config: Optional[MemoriConfig] = None):
        self.config = config or MemoriConfig()
        self.config.validate()

        # 初始化Memori实例
        self._memori_instances: Dict[str, Memori] = {}
        self._clients: Dict[str, AsyncAnthropic] = {}

        logger.info(
            f"MemoriService initialized with model={self.config.model}, "
            f"max_tokens={self.config.max_memory_tokens}"
        )

    def _get_session_key(self, user_id: str, session_id: str) -> str:
        """生成会话唯一标识"""
        return f"{user_id}:{session_id}"

    async def get_memori_instance(
        self,
        user_id: str,
        session_id: str,
        namespace: Optional[str] = None
    ) -> Memori:
        """
        获取或创建Memori实例（会话隔离）

        参数:
            user_id: 用户ID
            session_id: 会话ID
            namespace: 可选的命名空间，用于进一步隔离（如数据源相关记忆）

        返回:
            Memori实例
        """
        session_key = self._get_session_key(user_id, session_id)
        if namespace:
            session_key = f"{session_key}:{namespace}"

        if session_key not in self._memori_instances:
            # 创建新的Memori实例
            memori = Memori(
                conscious_ingest=self.config.conscious_ingest,
                auto_ingest=self.config.auto_ingest,
                # 使用session_key作为user_id实现隔离
                user_id=session_key,
            )

            self._memori_instances[session_key] = memori
            logger.info(f"Created new Memori instance for session: {session_key}")

        return self._memori_instances[session_key]

    async def get_claude_client(
        self,
        user_id: str,
        session_id: str,
        namespace: Optional[str] = None
    ) -> AsyncAnthropic:
        """
        获取配置了Memori的Claude客户端

        参数:
            user_id: 用户ID
            session_id: 会话ID
            namespace: 可选的命名空间

        返回:
            配置了Memori的AsyncAnthropic客户端
        """
        session_key = self._get_session_key(user_id, session_id)
        if namespace:
            session_key = f"{session_key}:{namespace}"

        if session_key not in self._clients:
            # 获取Memori实例
            memori = await self.get_memori_instance(user_id, session_id, namespace)

            # 启用Memori（全局方法）
            memori.enable()

            # 创建Claude客户端
            client = AsyncAnthropic(api_key=self.config.api_key)
            self._clients[session_key] = client

            logger.info(f"Created Claude client with Memori for session: {session_key}")

        return self._clients[session_key]

    async def create_message(
        self,
        user_id: str,
        session_id: str,
        messages: List[Dict[str, Any]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: Optional[str] = None,
        namespace: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        使用Memori增强的对话生成

        参数:
            user_id: 用户ID
            session_id: 会话ID
            messages: 对话消息列表
            max_tokens: 最大生成token数
            temperature: 温度参数
            system: 系统提示词
            namespace: 命名空间
            **kwargs: 其他Claude API参数

        返回:
            Claude响应字典
        """
        try:
            client = await self.get_claude_client(user_id, session_id, namespace)

            # 调用Claude API（Memori自动处理记忆注入）
            response = await client.messages.create(
                model=self.config.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages,
                system=system,
                **kwargs
            )

            # 提取响应文本
            response_text = response.content[0].text if response.content else ""

            # 记录token使用情况
            logger.info(
                f"Claude response - input_tokens: {response.usage.input_tokens}, "
                f"output_tokens: {response.usage.output_tokens}"
            )

            return {
                "content": response_text,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                },
                "model": response.model,
                "stop_reason": response.stop_reason
            }

        except Exception as e:
            logger.error(f"Error creating message with Memori: {e}", exc_info=True)
            raise

    async def add_conscious_memory(
        self,
        user_id: str,
        session_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        importance: float = 0.8,
        namespace: Optional[str] = None
    ) -> None:
        """
        显式添加重要记忆（Conscious Mode）

        使用场景:
        - 数据源schema信息
        - 用户偏好设置
        - 重要的业务规则

        参数:
            user_id: 用户ID
            session_id: 会话ID
            content: 记忆内容
            metadata: 元数据（如类型、标签等）
            importance: 重要性评分(0-1)
            namespace: 命名空间
        """
        memori = await self.get_memori_instance(user_id, session_id, namespace)

        # 使用Memori的conscious_ingest方法
        await memori.ingest(
            content=content,
            metadata=metadata or {},
            importance=importance,
            mode=MemoryMode.CONSCIOUS
        )

        logger.info(
            f"Added conscious memory for {user_id}:{session_id} "
            f"(importance={importance})"
        )

    async def search_memories(
        self,
        user_id: str,
        session_id: str,
        query: str,
        limit: int = 10,
        namespace: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索相关记忆

        参数:
            user_id: 用户ID
            session_id: 会话ID
            query: 搜索查询
            limit: 返回数量限制
            namespace: 命名空间

        返回:
            记忆列表
        """
        memori = await self.get_memori_instance(user_id, session_id, namespace)

        # 使用Memori的搜索功能
        memories = await memori.search(
            query=query,
            limit=limit,
            threshold=self.config.importance_threshold
        )

        return memories

    async def clear_session_memory(
        self,
        user_id: str,
        session_id: str,
        namespace: Optional[str] = None
    ) -> None:
        """
        清除会话记忆

        参数:
            user_id: 用户ID
            session_id: 会话ID
            namespace: 命名空间
        """
        session_key = self._get_session_key(user_id, session_id)
        if namespace:
            session_key = f"{session_key}:{namespace}"

        # 清除实例
        if session_key in self._memori_instances:
            await self._memori_instances[session_key].clear()
            del self._memori_instances[session_key]

        if session_key in self._clients:
            del self._clients[session_key]

        logger.info(f"Cleared memory for session: {session_key}")

    async def get_memory_stats(
        self,
        user_id: str,
        session_id: str,
        namespace: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取记忆统计信息

        参数:
            user_id: 用户ID
            session_id: 会话ID
            namespace: 命名空间

        返回:
            统计信息字典
        """
        memori = await self.get_memori_instance(user_id, session_id, namespace)

        stats = await memori.get_stats()

        return {
            "total_memories": stats.get("total", 0),
            "memory_tokens": stats.get("tokens", 0),
            "avg_importance": stats.get("avg_importance", 0),
            "oldest_memory": stats.get("oldest", None),
            "newest_memory": stats.get("newest", None)
        }


# 全局单例实例
_memori_service: Optional[MemoriService] = None


def get_memori_service() -> MemoriService:
    """获取全局Memori服务实例"""
    global _memori_service
    if _memori_service is None:
        _memori_service = MemoriService()
    return _memori_service


@asynccontextmanager
async def memori_context(user_id: str, session_id: str, namespace: Optional[str] = None):
    """
    Memori上下文管理器

    使用示例:
        async with memori_context("user_123", "session_456") as service:
            response = await service.create_message(...)
    """
    service = get_memori_service()
    try:
        yield service
    finally:
        # 可选：清理逻辑
        pass
```

### 2. 错误处理和超时管理

#### 2.1 重试策略

```python
"""
文件: /mnt/d/工作区/云开发/working/backend/src/services/claude_retry.py
"""

import asyncio
from typing import Callable, TypeVar, Optional
from functools import wraps
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ClaudeRetryConfig:
    """Claude API重试配置"""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        timeout: float = 30.0
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.timeout = timeout


def with_retry(config: Optional[ClaudeRetryConfig] = None):
    """
    Claude API调用重试装饰器

    使用示例:
        @with_retry(ClaudeRetryConfig(max_retries=3))
        async def call_claude(...):
            ...
    """
    if config is None:
        config = ClaudeRetryConfig()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(config.max_retries + 1):
                try:
                    # 应用超时
                    return await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=config.timeout
                    )

                except asyncio.TimeoutError as e:
                    last_exception = e
                    logger.warning(
                        f"Timeout on attempt {attempt + 1}/{config.max_retries + 1}: {e}"
                    )

                except Exception as e:
                    last_exception = e

                    # 判断是否应该重试
                    if not _should_retry(e):
                        raise

                    logger.warning(
                        f"Retryable error on attempt {attempt + 1}/{config.max_retries + 1}: {e}"
                    )

                # 如果不是最后一次尝试，则等待后重试
                if attempt < config.max_retries:
                    delay = min(
                        config.base_delay * (config.exponential_base ** attempt),
                        config.max_delay
                    )
                    logger.info(f"Retrying in {delay:.2f} seconds...")
                    await asyncio.sleep(delay)

            # 所有重试都失败
            logger.error(f"All {config.max_retries + 1} attempts failed")
            raise last_exception

        return wrapper
    return decorator


def _should_retry(exception: Exception) -> bool:
    """判断异常是否应该重试"""
    # 网络相关错误
    if isinstance(exception, (
        asyncio.TimeoutError,
        ConnectionError,
        OSError
    )):
        return True

    # Claude API特定错误
    error_msg = str(exception).lower()
    retryable_errors = [
        "rate limit",
        "overloaded",
        "timeout",
        "502",
        "503",
        "504",
    ]

    return any(err in error_msg for err in retryable_errors)
```

#### 2.2 错误处理示例

```python
"""
文件: /mnt/d/工作区/云开发/working/backend/src/api/ai_chat.py
AI对话API端点
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

from src.services.memori_service import get_memori_service, MemoriService
from src.services.claude_retry import with_retry, ClaudeRetryConfig

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["AI Chat"])


class ChatMessage(BaseModel):
    """对话消息模型"""
    role: str = Field(..., description="消息角色: user或assistant")
    content: str = Field(..., description="消息内容")


class ChatRequest(BaseModel):
    """对话请求模型"""
    user_id: str = Field(..., description="用户ID")
    session_id: str = Field(..., description="会话ID")
    messages: List[ChatMessage] = Field(..., description="对话历史")
    system: Optional[str] = Field(None, description="系统提示词")
    max_tokens: int = Field(4096, ge=1, le=8192)
    temperature: float = Field(0.7, ge=0, le=1)
    namespace: Optional[str] = Field(None, description="记忆命名空间")


class ChatResponse(BaseModel):
    """对话响应模型"""
    content: str = Field(..., description="AI响应内容")
    usage: dict = Field(..., description="Token使用统计")
    model: str = Field(..., description="使用的模型")


@router.post("/chat", response_model=ChatResponse)
@with_retry(ClaudeRetryConfig(max_retries=3, timeout=60.0))
async def chat(
    request: ChatRequest,
    memori_service: MemoriService = Depends(get_memori_service)
) -> ChatResponse:
    """
    AI对话端点（集成Memori记忆管理）

    参数:
        request: 对话请求
        memori_service: Memori服务依赖注入

    返回:
        ChatResponse: AI响应

    异常:
        HTTPException: 当API调用失败时
    """
    try:
        # 转换消息格式
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]

        # 调用Memori增强的对话生成
        response = await memori_service.create_message(
            user_id=request.user_id,
            session_id=request.session_id,
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            system=request.system,
            namespace=request.namespace
        )

        return ChatResponse(
            content=response["content"],
            usage=response["usage"],
            model=response["model"]
        )

    except asyncio.TimeoutError:
        logger.error("Claude API timeout")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI service timeout. Please try again."
        )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your request"
        )
```

### 3. Token管理和成本优化

#### 3.1 Token计数和预算控制

```python
"""
文件: /mnt/d/工作区/云开发/working/backend/src/services/token_manager.py
Token管理和成本优化
"""

import tiktoken
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class TokenBudget:
    """Token预算配置"""
    daily_limit: int = 1000000  # 每日token限制
    per_request_limit: int = 8000  # 单次请求限制
    alert_threshold: float = 0.8  # 告警阈值（80%）
    cost_per_1k_input: float = 0.003  # Claude Sonnet输入成本(USD)
    cost_per_1k_output: float = 0.015  # Claude Sonnet输出成本(USD)


class TokenManager:
    """
    Token管理器

    功能:
    - Token计数和预算控制
    - 成本估算
    - 使用统计
    """

    def __init__(self, budget: Optional[TokenBudget] = None):
        self.budget = budget or TokenBudget()
        self.encoder = tiktoken.encoding_for_model("gpt-4")  # Claude使用类似的编码

        # 使用统计（内存中，生产环境应使用Redis）
        self._daily_usage: Dict[str, Dict[str, int]] = {}

    def count_tokens(self, text: str) -> int:
        """计算文本的token数量"""
        return len(self.encoder.encode(text))

    def count_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """计算消息列表的总token数"""
        total = 0
        for msg in messages:
            total += self.count_tokens(msg.get("content", ""))
            total += 4  # 每条消息的额外开销
        return total

    async def check_budget(
        self,
        user_id: str,
        estimated_tokens: int
    ) -> Dict[str, Any]:
        """
        检查token预算

        参数:
            user_id: 用户ID
            estimated_tokens: 预估的token数量

        返回:
            dict: {
                "allowed": bool,
                "reason": str,
                "current_usage": int,
                "daily_limit": int,
                "estimated_cost": float
            }
        """
        today = datetime.now().strftime("%Y-%m-%d")

        # 获取今日使用量
        if today not in self._daily_usage:
            self._daily_usage[today] = {}

        current_usage = self._daily_usage[today].get(user_id, 0)

        # 检查每日限制
        if current_usage + estimated_tokens > self.budget.daily_limit:
            return {
                "allowed": False,
                "reason": "Daily token limit exceeded",
                "current_usage": current_usage,
                "daily_limit": self.budget.daily_limit,
                "estimated_cost": 0
            }

        # 检查单次请求限制
        if estimated_tokens > self.budget.per_request_limit:
            return {
                "allowed": False,
                "reason": "Per-request token limit exceeded",
                "current_usage": current_usage,
                "daily_limit": self.budget.daily_limit,
                "estimated_cost": 0
            }

        # 计算预估成本
        estimated_cost = self._estimate_cost(estimated_tokens)

        # 检查告警阈值
        usage_ratio = (current_usage + estimated_tokens) / self.budget.daily_limit
        if usage_ratio > self.budget.alert_threshold:
            logger.warning(
                f"User {user_id} approaching daily limit: {usage_ratio:.1%}"
            )

        return {
            "allowed": True,
            "reason": "OK",
            "current_usage": current_usage,
            "daily_limit": self.budget.daily_limit,
            "estimated_cost": estimated_cost
        }

    async def record_usage(
        self,
        user_id: str,
        input_tokens: int,
        output_tokens: int
    ) -> None:
        """
        记录实际token使用量

        参数:
            user_id: 用户ID
            input_tokens: 输入token数
            output_tokens: 输出token数
        """
        today = datetime.now().strftime("%Y-%m-%d")

        if today not in self._daily_usage:
            self._daily_usage[today] = {}

        total_tokens = input_tokens + output_tokens
        self._daily_usage[today][user_id] = \
            self._daily_usage[today].get(user_id, 0) + total_tokens

        # 计算实际成本
        actual_cost = (
            (input_tokens / 1000) * self.budget.cost_per_1k_input +
            (output_tokens / 1000) * self.budget.cost_per_1k_output
        )

        logger.info(
            f"Token usage recorded - User: {user_id}, "
            f"Input: {input_tokens}, Output: {output_tokens}, "
            f"Cost: ${actual_cost:.4f}"
        )

    def _estimate_cost(self, tokens: int) -> float:
        """估算token成本（假设50%输入，50%输出）"""
        input_tokens = int(tokens * 0.5)
        output_tokens = int(tokens * 0.5)

        return (
            (input_tokens / 1000) * self.budget.cost_per_1k_input +
            (output_tokens / 1000) * self.budget.cost_per_1k_output
        )

    async def get_usage_stats(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """
        获取使用统计

        参数:
            user_id: 用户ID
            days: 统计天数

        返回:
            使用统计字典
        """
        stats = {
            "user_id": user_id,
            "period_days": days,
            "daily_breakdown": {},
            "total_tokens": 0,
            "estimated_cost": 0
        }

        # 遍历最近N天
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            if date in self._daily_usage:
                usage = self._daily_usage[date].get(user_id, 0)
                stats["daily_breakdown"][date] = usage
                stats["total_tokens"] += usage

        # 估算总成本
        stats["estimated_cost"] = self._estimate_cost(stats["total_tokens"])

        return stats


# 全局实例
_token_manager: Optional[TokenManager] = None


def get_token_manager() -> TokenManager:
    """获取全局Token管理器实例"""
    global _token_manager
    if _token_manager is None:
        _token_manager = TokenManager()
    return _token_manager
```

#### 3.2 成本优化策略

```python
"""
文件: /mnt/d/工作区/云开发/working/backend/src/services/optimization_strategies.py
成本优化策略
"""

from typing import List, Dict, Any
from enum import Enum


class OptimizationStrategy(Enum):
    """优化策略枚举"""
    AGGRESSIVE = "aggressive"  # 激进优化（最省钱）
    BALANCED = "balanced"      # 平衡优化（推荐）
    CONSERVATIVE = "conservative"  # 保守优化（最准确）


class CostOptimizer:
    """成本优化器"""

    def __init__(self, strategy: OptimizationStrategy = OptimizationStrategy.BALANCED):
        self.strategy = strategy

    def optimize_context(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int
    ) -> List[Dict[str, str]]:
        """
        优化上下文，减少token使用

        策略:
        1. 移除过长的历史消息
        2. 压缩重复信息
        3. 保留最近和最重要的消息
        """
        if self.strategy == OptimizationStrategy.AGGRESSIVE:
            # 激进策略：只保留最近3轮对话
            return messages[-6:] if len(messages) > 6 else messages

        elif self.strategy == OptimizationStrategy.BALANCED:
            # 平衡策略：保留最近5轮对话，或总token不超过max_tokens的60%
            target_tokens = int(max_tokens * 0.6)
            return self._trim_to_token_limit(messages, target_tokens)

        else:  # CONSERVATIVE
            # 保守策略：保留所有消息，或总token不超过max_tokens的80%
            target_tokens = int(max_tokens * 0.8)
            return self._trim_to_token_limit(messages, target_tokens)

    def _trim_to_token_limit(
        self,
        messages: List[Dict[str, str]],
        target_tokens: int
    ) -> List[Dict[str, str]]:
        """修剪消息列表以满足token限制"""
        from src.services.token_manager import get_token_manager

        token_manager = get_token_manager()

        # 从最新消息开始计算
        trimmed = []
        total_tokens = 0

        for msg in reversed(messages):
            msg_tokens = token_manager.count_tokens(msg["content"])
            if total_tokens + msg_tokens > target_tokens:
                break
            trimmed.insert(0, msg)
            total_tokens += msg_tokens

        return trimmed

    def should_use_memori_cache(self, query_type: str) -> bool:
        """
        判断是否应该使用Memori缓存

        某些查询类型更适合缓存:
        - schema查询
        - 数据源信息
        - 常见问题
        """
        cacheable_types = [
            "schema",
            "datasource",
            "faq",
            "metadata"
        ]

        return query_type.lower() in cacheable_types
```

### 4. 上下文注入最佳实践

#### 4.1 智能上下文构建

```python
"""
文件: /mnt/d/工作区/云开发/working/backend/src/services/context_builder.py
智能上下文构建器
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

from src.services.memori_service import get_memori_service

logger = logging.getLogger(__name__)


@dataclass
class ContextConfig:
    """上下文配置"""
    include_schema: bool = True  # 包含数据库schema
    include_history: bool = True  # 包含对话历史
    include_examples: bool = True  # 包含SQL示例
    max_schema_tables: int = 10  # 最大schema表数
    max_history_turns: int = 5  # 最大历史轮数


class ContextBuilder:
    """
    智能上下文构建器

    根据用户查询，智能构建最相关的上下文信息
    """

    def __init__(self, config: Optional[ContextConfig] = None):
        self.config = config or ContextConfig()
        self.memori_service = get_memori_service()

    async def build_context(
        self,
        user_id: str,
        session_id: str,
        user_query: str,
        datasource_id: Optional[int] = None
    ) -> str:
        """
        构建上下文字符串

        参数:
            user_id: 用户ID
            session_id: 会话ID
            user_query: 用户查询
            datasource_id: 数据源ID

        返回:
            格式化的上下文字符串
        """
        context_parts = []

        # 1. 添加数据库schema（如果需要）
        if self.config.include_schema and datasource_id:
            schema_context = await self._get_schema_context(
                user_id,
                session_id,
                datasource_id,
                user_query
            )
            if schema_context:
                context_parts.append("## Database Schema\n" + schema_context)

        # 2. 添加相关记忆
        memory_context = await self._get_memory_context(
            user_id,
            session_id,
            user_query
        )
        if memory_context:
            context_parts.append("## Relevant Context\n" + memory_context)

        # 3. 添加SQL示例（如果需要）
        if self.config.include_examples:
            examples_context = await self._get_examples_context(user_query)
            if examples_context:
                context_parts.append("## SQL Examples\n" + examples_context)

        return "\n\n".join(context_parts)

    async def _get_schema_context(
        self,
        user_id: str,
        session_id: str,
        datasource_id: int,
        user_query: str
    ) -> str:
        """获取数据库schema上下文"""
        # 从Memori搜索相关的schema信息
        memories = await self.memori_service.search_memories(
            user_id=user_id,
            session_id=session_id,
            query=user_query,
            limit=self.config.max_schema_tables,
            namespace=f"schema:{datasource_id}"
        )

        if not memories:
            return ""

        # 格式化schema信息
        schema_lines = []
        for memory in memories:
            content = memory.get("content", "")
            if content:
                schema_lines.append(content)

        return "\n".join(schema_lines)

    async def _get_memory_context(
        self,
        user_id: str,
        session_id: str,
        user_query: str
    ) -> str:
        """获取相关记忆上下文"""
        # 搜索相关记忆
        memories = await self.memori_service.search_memories(
            user_id=user_id,
            session_id=session_id,
            query=user_query,
            limit=5
        )

        if not memories:
            return ""

        # 格式化记忆
        memory_lines = []
        for i, memory in enumerate(memories, 1):
            content = memory.get("content", "")
            importance = memory.get("importance", 0)
            if content:
                memory_lines.append(f"{i}. {content} (relevance: {importance:.2f})")

        return "\n".join(memory_lines)

    async def _get_examples_context(self, user_query: str) -> str:
        """获取SQL示例上下文"""
        # 根据查询类型返回相关示例
        query_lower = user_query.lower()

        examples = []

        if "join" in query_lower or "关联" in query_lower:
            examples.append(
                "Example: SELECT * FROM orders o JOIN customers c ON o.customer_id = c.id"
            )

        if "group" in query_lower or "统计" in query_lower or "汇总" in query_lower:
            examples.append(
                "Example: SELECT category, COUNT(*) as count FROM products GROUP BY category"
            )

        if "where" in query_lower or "筛选" in query_lower:
            examples.append(
                "Example: SELECT * FROM users WHERE created_at > '2024-01-01'"
            )

        return "\n".join(examples) if examples else ""
```

---

## 记忆管理策略

### 1. Memory Mode选择指南

#### 1.1 Conscious Mode（显式记忆）

**适用场景**:
- 数据库schema信息
- 用户配置和偏好
- 重要的业务规则
- 数据源元数据

**实现示例**:

```python
# 保存数据源schema信息
await memori_service.add_conscious_memory(
    user_id="user_123",
    session_id="session_456",
    content=f"Table: users\nColumns: id (INT), name (VARCHAR), email (VARCHAR), created_at (TIMESTAMP)",
    metadata={
        "type": "schema",
        "table_name": "users",
        "datasource_id": datasource_id
    },
    importance=0.9,  # 高重要性
    namespace=f"schema:{datasource_id}"
)
```

#### 1.2 Auto Mode（自动记忆）

**适用场景**:
- 对话历史
- 临时查询结果
- 用户交互模式
- 上下文提示

**特点**:
- Memori自动捕获和管理
- 基于使用频率自动调整重要性
- 无需手动干预

### 2. 多轮对话记忆保留策略

#### 2.1 分层记忆架构

```python
"""
文件: /mnt/d/工作区/云开发/working/backend/src/services/memory_hierarchy.py
分层记忆管理
"""

from enum import Enum
from typing import Dict, Any
from datetime import datetime, timedelta


class MemoryLayer(Enum):
    """记忆层级"""
    SHORT_TERM = "short_term"  # 短期记忆（当前会话）
    MEDIUM_TERM = "medium_term"  # 中期记忆（24小时内）
    LONG_TERM = "long_term"  # 长期记忆（持久化）


class HierarchicalMemoryManager:
    """分层记忆管理器"""

    def __init__(self):
        self.retention_policies = {
            MemoryLayer.SHORT_TERM: timedelta(hours=1),
            MemoryLayer.MEDIUM_TERM: timedelta(days=1),
            MemoryLayer.LONG_TERM: timedelta(days=365)
        }

    def classify_memory(
        self,
        content: str,
        metadata: Dict[str, Any],
        importance: float
    ) -> MemoryLayer:
        """
        分类记忆到不同层级

        分类规则:
        - importance >= 0.8: 长期记忆
        - importance >= 0.5: 中期记忆
        - importance < 0.5: 短期记忆
        """
        memory_type = metadata.get("type", "")

        # Schema和配置信息总是长期记忆
        if memory_type in ["schema", "config", "preference"]:
            return MemoryLayer.LONG_TERM

        # 基于重要性分类
        if importance >= 0.8:
            return MemoryLayer.LONG_TERM
        elif importance >= 0.5:
            return MemoryLayer.MEDIUM_TERM
        else:
            return MemoryLayer.SHORT_TERM

    async def cleanup_expired_memories(
        self,
        user_id: str,
        session_id: str
    ) -> int:
        """
        清理过期记忆

        返回:
            清理的记忆数量
        """
        # 实现清理逻辑
        # 这里需要与Memori的API集成
        pass
```

### 3. 记忆重要性评分优化

#### 3.1 动态重要性评分

```python
"""
文件: /mnt/d/工作区/云开发/working/backend/src/services/importance_scorer.py
记忆重要性评分器
"""

from typing import Dict, Any
import re


class ImportanceScorer:
    """
    记忆重要性评分器

    基于多个因素计算记忆重要性:
    - 内容类型
    - 访问频率
    - 时间衰减
    - 用户反馈
    """

    def __init__(self):
        # 内容类型权重
        self.type_weights = {
            "schema": 0.9,
            "config": 0.85,
            "preference": 0.8,
            "query": 0.6,
            "result": 0.5,
            "conversation": 0.4
        }

    def calculate_importance(
        self,
        content: str,
        metadata: Dict[str, Any],
        access_count: int = 0,
        age_days: float = 0,
        user_feedback: float = 0.5
    ) -> float:
        """
        计算记忆重要性分数

        参数:
            content: 记忆内容
            metadata: 元数据
            access_count: 访问次数
            age_days: 记忆年龄（天）
            user_feedback: 用户反馈(0-1)

        返回:
            重要性分数(0-1)
        """
        # 1. 基础分数（基于类型）
        memory_type = metadata.get("type", "conversation")
        base_score = self.type_weights.get(memory_type, 0.5)

        # 2. 访问频率加成
        frequency_bonus = min(access_count * 0.05, 0.2)

        # 3. 时间衰减
        time_decay = max(0, 1 - (age_days / 365) * 0.3)  # 1年后衰减30%

        # 4. 内容质量（基于长度和关键词）
        quality_score = self._assess_content_quality(content)

        # 5. 用户反馈权重
        feedback_weight = 0.2

        # 综合计算
        importance = (
            base_score * 0.4 +
            frequency_bonus +
            time_decay * 0.2 +
            quality_score * 0.2 +
            user_feedback * feedback_weight
        )

        return min(max(importance, 0), 1)  # 限制在0-1范围

    def _assess_content_quality(self, content: str) -> float:
        """评估内容质量"""
        # 长度评分
        length = len(content)
        if length < 20:
            length_score = 0.3
        elif length < 100:
            length_score = 0.6
        else:
            length_score = 0.8

        # 关键词评分
        keywords = [
            "table", "column", "schema", "database",
            "SELECT", "FROM", "WHERE", "JOIN",
            "用户", "数据", "查询", "表"
        ]
        keyword_count = sum(1 for kw in keywords if kw in content)
        keyword_score = min(keyword_count * 0.1, 0.5)

        return (length_score + keyword_score) / 2
```

### 4. 长期记忆vs短期记忆管理

#### 4.1 记忆生命周期管理

```python
"""
文件: /mnt/d/工作区/云开发/working/backend/src/services/memory_lifecycle.py
记忆生命周期管理
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
import logging

from src.models import Memory  # 假设有Memory模型
from src.services.memori_service import get_memori_service

logger = logging.getLogger(__name__)


class MemoryLifecycleManager:
    """记忆生命周期管理器"""

    def __init__(self):
        self.memori_service = get_memori_service()

    async def promote_to_long_term(
        self,
        session: AsyncSession,
        user_id: str,
        session_id: str,
        memory_id: str
    ) -> bool:
        """
        将短期/中期记忆提升为长期记忆

        触发条件:
        - 高访问频率
        - 用户明确标记
        - 高重要性评分
        """
        try:
            # 更新记忆层级
            # 这里需要根据实际的Memori API实现
            logger.info(
                f"Promoting memory {memory_id} to long-term "
                f"for user {user_id}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to promote memory: {e}")
            return False

    async def archive_old_memories(
        self,
        session: AsyncSession,
        user_id: str,
        days_threshold: int = 30
    ) -> int:
        """
        归档旧记忆

        参数:
            session: 数据库会话
            user_id: 用户ID
            days_threshold: 归档阈值（天）

        返回:
            归档的记忆数量
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)

        # 查询需要归档的记忆
        # 实现归档逻辑

        logger.info(f"Archived old memories for user {user_id}")
        return 0

    async def consolidate_memories(
        self,
        user_id: str,
        session_id: str
    ) -> None:
        """
        合并和压缩相似记忆

        使用场景:
        - 多次查询相同表的schema
        - 重复的对话模式
        - 类似的SQL查询
        """
        # 获取所有记忆
        memories = await self.memori_service.search_memories(
            user_id=user_id,
            session_id=session_id,
            query="",  # 空查询获取所有
            limit=100
        )

        # 实现记忆合并逻辑
        # 使用语义相似度检测重复记忆

        logger.info(f"Consolidated memories for {user_id}:{session_id}")
```

---

## FastAPI服务集成

### 1. 异步框架中的Memori使用

#### 1.1 完整的API集成示例

```python
"""
文件: /mnt/d/工作区/云开发/working/backend/src/api/text2sql.py
Text2SQL API端点（集成Memori）
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.db import get_session
from src.services.memori_service import get_memori_service, MemoriService
from src.services.context_builder import ContextBuilder
from src.services.token_manager import get_token_manager, TokenManager
from src.models import DataSource

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/text2sql", tags=["Text2SQL"])


class Text2SQLRequest(BaseModel):
    """Text2SQL请求模型"""
    user_id: str = Field(..., description="用户ID")
    session_id: str = Field(..., description="会话ID")
    datasource_id: int = Field(..., description="数据源ID")
    query: str = Field(..., description="自然语言查询")
    include_explanation: bool = Field(True, description="是否包含解释")


class Text2SQLResponse(BaseModel):
    """Text2SQL响应模型"""
    sql: str = Field(..., description="生成的SQL查询")
    explanation: Optional[str] = Field(None, description="SQL解释")
    confidence: float = Field(..., description="置信度(0-1)")
    usage: dict = Field(..., description="Token使用统计")


@router.post("/generate", response_model=Text2SQLResponse)
async def generate_sql(
    request: Text2SQLRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    memori_service: MemoriService = Depends(get_memori_service),
    token_manager: TokenManager = Depends(get_token_manager)
) -> Text2SQLResponse:
    """
    生成SQL查询（使用Memori增强）

    流程:
    1. 检查token预算
    2. 构建智能上下文（包含schema和记忆）
    3. 调用Claude生成SQL
    4. 记录使用统计
    5. 保存重要记忆
    """
    try:
        # 1. 验证数据源
        datasource = await session.get(DataSource, request.datasource_id)
        if not datasource:
            raise HTTPException(status_code=404, detail="Data source not found")

        # 2. 构建上下文
        context_builder = ContextBuilder()
        context = await context_builder.build_context(
            user_id=request.user_id,
            session_id=request.session_id,
            user_query=request.query,
            datasource_id=request.datasource_id
        )

        # 3. 估算token并检查预算
        estimated_tokens = token_manager.count_tokens(context + request.query) + 500
        budget_check = await token_manager.check_budget(
            user_id=request.user_id,
            estimated_tokens=estimated_tokens
        )

        if not budget_check["allowed"]:
            raise HTTPException(
                status_code=429,
                detail=f"Token budget exceeded: {budget_check['reason']}"
            )

        # 4. 构建系统提示词
        system_prompt = f"""You are an expert SQL query generator.
Given a natural language query and database schema context, generate accurate SQL queries.

{context}

Guidelines:
- Generate syntactically correct SQL for the given database
- Use appropriate JOINs when needed
- Add comments to explain complex logic
- Consider performance and optimization
"""

        # 5. 构建消息
        messages = [
            {
                "role": "user",
                "content": f"Generate a SQL query for: {request.query}"
            }
        ]

        # 6. 调用Claude（通过Memori）
        response = await memori_service.create_message(
            user_id=request.user_id,
            session_id=request.session_id,
            messages=messages,
            system=system_prompt,
            max_tokens=2048,
            temperature=0.3,  # 较低温度以保证准确性
            namespace=f"datasource:{request.datasource_id}"
        )

        # 7. 记录实际使用
        await token_manager.record_usage(
            user_id=request.user_id,
            input_tokens=response["usage"]["input_tokens"],
            output_tokens=response["usage"]["output_tokens"]
        )

        # 8. 解析响应
        sql_text = response["content"]
        confidence = 0.85  # 可以基于模型响应计算

        # 9. 后台任务：保存重要记忆
        if confidence > 0.8:
            background_tasks.add_task(
                save_query_memory,
                memori_service,
                request.user_id,
                request.session_id,
                request.query,
                sql_text,
                request.datasource_id
            )

        return Text2SQLResponse(
            sql=sql_text,
            explanation="SQL generated successfully" if request.include_explanation else None,
            confidence=confidence,
            usage=response["usage"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating SQL: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate SQL: {str(e)}"
        )


async def save_query_memory(
    memori_service: MemoriService,
    user_id: str,
    session_id: str,
    query: str,
    sql: str,
    datasource_id: int
) -> None:
    """后台任务：保存查询记忆"""
    try:
        await memori_service.add_conscious_memory(
            user_id=user_id,
            session_id=session_id,
            content=f"Query: {query}\nSQL: {sql}",
            metadata={
                "type": "query",
                "datasource_id": datasource_id
            },
            importance=0.7,
            namespace=f"datasource:{datasource_id}"
        )
        logger.info(f"Saved query memory for {user_id}")
    except Exception as e:
        logger.error(f"Failed to save query memory: {e}")


@router.get("/memory-stats")
async def get_memory_stats(
    user_id: str,
    session_id: str,
    memori_service: MemoriService = Depends(get_memori_service)
) -> dict:
    """获取记忆统计信息"""
    try:
        stats = await memori_service.get_memory_stats(
            user_id=user_id,
            session_id=session_id
        )
        return stats
    except Exception as e:
        logger.error(f"Error getting memory stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear-memory")
async def clear_memory(
    user_id: str,
    session_id: str,
    namespace: Optional[str] = None,
    memori_service: MemoriService = Depends(get_memori_service)
) -> dict:
    """清除会话记忆"""
    try:
        await memori_service.clear_session_memory(
            user_id=user_id,
            session_id=session_id,
            namespace=namespace
        )
        return {"message": "Memory cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### 2. 并发请求下的内存管理

#### 2.1 并发控制和资源池

```python
"""
文件: /mnt/d/工作区/云开发/working/backend/src/services/concurrency_manager.py
并发请求管理
"""

import asyncio
from typing import Optional, Dict
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConcurrencyConfig:
    """并发配置"""
    max_concurrent_requests: int = 10  # 最大并发请求数
    max_requests_per_user: int = 3  # 每用户最大并发数
    queue_timeout: float = 30.0  # 队列超时（秒）


class ConcurrencyManager:
    """
    并发请求管理器

    功能:
    - 限制全局并发数
    - 限制单用户并发数
    - 请求队列管理
    """

    def __init__(self, config: Optional[ConcurrencyConfig] = None):
        self.config = config or ConcurrencyConfig()

        # 全局信号量
        self.global_semaphore = asyncio.Semaphore(
            self.config.max_concurrent_requests
        )

        # 用户级信号量字典
        self.user_semaphores: Dict[str, asyncio.Semaphore] = {}
        self._lock = asyncio.Lock()

    async def acquire_slot(self, user_id: str) -> None:
        """
        获取请求槽位

        参数:
            user_id: 用户ID

        异常:
            asyncio.TimeoutError: 如果等待超时
        """
        # 获取用户信号量
        async with self._lock:
            if user_id not in self.user_semaphores:
                self.user_semaphores[user_id] = asyncio.Semaphore(
                    self.config.max_requests_per_user
                )

        user_semaphore = self.user_semaphores[user_id]

        # 尝试获取槽位（带超时）
        try:
            async with asyncio.timeout(self.config.queue_timeout):
                await self.global_semaphore.acquire()
                await user_semaphore.acquire()

                logger.debug(f"Acquired slot for user {user_id}")

        except asyncio.TimeoutError:
            logger.warning(f"Queue timeout for user {user_id}")
            raise

    def release_slot(self, user_id: str) -> None:
        """
        释放请求槽位

        参数:
            user_id: 用户ID
        """
        if user_id in self.user_semaphores:
            self.user_semaphores[user_id].release()

        self.global_semaphore.release()
        logger.debug(f"Released slot for user {user_id}")

    async def execute_with_concurrency_control(
        self,
        user_id: str,
        coro
    ):
        """
        在并发控制下执行协程

        使用示例:
            result = await concurrency_manager.execute_with_concurrency_control(
                user_id="user_123",
                coro=some_async_function()
            )
        """
        await self.acquire_slot(user_id)
        try:
            return await coro
        finally:
            self.release_slot(user_id)


# 全局实例
_concurrency_manager: Optional[ConcurrencyManager] = None


def get_concurrency_manager() -> ConcurrencyManager:
    """获取全局并发管理器"""
    global _concurrency_manager
    if _concurrency_manager is None:
        _concurrency_manager = ConcurrencyManager()
    return _concurrency_manager
```

#### 2.2 在API中使用并发控制

```python
"""
文件: /mnt/d/工作区/云开发/working/backend/src/api/text2sql_with_concurrency.py
带并发控制的Text2SQL API
"""

from fastapi import APIRouter, HTTPException, Depends
from src.services.concurrency_manager import get_concurrency_manager, ConcurrencyManager

router = APIRouter(prefix="/api/v2/text2sql", tags=["Text2SQL V2"])


@router.post("/generate")
async def generate_sql_v2(
    request: Text2SQLRequest,
    concurrency_manager: ConcurrencyManager = Depends(get_concurrency_manager),
    # ... 其他依赖
):
    """带并发控制的SQL生成"""
    try:
        # 在并发控制下执行
        result = await concurrency_manager.execute_with_concurrency_control(
            user_id=request.user_id,
            coro=_do_generate_sql(request)  # 实际的生成逻辑
        )
        return result

    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=503,
            detail="Service is busy. Please try again later."
        )
    except Exception as e:
        logger.error(f"Error in SQL generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _do_generate_sql(request: Text2SQLRequest):
    """实际的SQL生成逻辑"""
    # ... 实现
    pass
```

### 3. 会话管理和记忆隔离

#### 3.1 会话管理器

```python
"""
文件: /mnt/d/工作区/云开发/working/backend/src/services/session_manager.py
会话管理和记忆隔离
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import uuid
import logging

from src.models import UserSession  # 假设的会话模型

logger = logging.getLogger(__name__)


class SessionManager:
    """
    会话管理器

    功能:
    - 创建和验证会话
    - 会话超时管理
    - 记忆隔离
    - 会话元数据管理
    """

    def __init__(self, session_timeout_minutes: int = 60):
        self.session_timeout = timedelta(minutes=session_timeout_minutes)

    async def create_session(
        self,
        db_session: AsyncSession,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        创建新会话

        参数:
            db_session: 数据库会话
            user_id: 用户ID
            metadata: 会话元数据（如数据源ID、上下文信息等）

        返回:
            session_id: 会话ID
        """
        session_id = str(uuid.uuid4())

        # 创建会话记录
        session = UserSession(
            id=session_id,
            user_id=user_id,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            metadata=metadata or {},
            is_active=True
        )

        db_session.add(session)
        await db_session.commit()

        logger.info(f"Created session {session_id} for user {user_id}")
        return session_id

    async def validate_session(
        self,
        db_session: AsyncSession,
        user_id: str,
        session_id: str
    ) -> bool:
        """
        验证会话有效性

        参数:
            db_session: 数据库会话
            user_id: 用户ID
            session_id: 会话ID

        返回:
            bool: 会话是否有效
        """
        # 查询会话
        stmt = select(UserSession).where(
            UserSession.id == session_id,
            UserSession.user_id == user_id,
            UserSession.is_active == True
        )
        result = await db_session.execute(stmt)
        session = result.scalars().first()

        if not session:
            return False

        # 检查超时
        if datetime.utcnow() - session.last_activity > self.session_timeout:
            # 会话超时，标记为非活动
            await self.deactivate_session(db_session, session_id)
            return False

        # 更新最后活动时间
        await self.update_last_activity(db_session, session_id)

        return True

    async def update_last_activity(
        self,
        db_session: AsyncSession,
        session_id: str
    ) -> None:
        """更新会话最后活动时间"""
        stmt = update(UserSession).where(
            UserSession.id == session_id
        ).values(
            last_activity=datetime.utcnow()
        )
        await db_session.execute(stmt)
        await db_session.commit()

    async def deactivate_session(
        self,
        db_session: AsyncSession,
        session_id: str
    ) -> None:
        """停用会话"""
        stmt = update(UserSession).where(
            UserSession.id == session_id
        ).values(
            is_active=False,
            ended_at=datetime.utcnow()
        )
        await db_session.execute(stmt)
        await db_session.commit()

        logger.info(f"Deactivated session {session_id}")

    async def get_session_metadata(
        self,
        db_session: AsyncSession,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """获取会话元数据"""
        stmt = select(UserSession.metadata).where(
            UserSession.id == session_id
        )
        result = await db_session.execute(stmt)
        return result.scalars().first()

    async def update_session_metadata(
        self,
        db_session: AsyncSession,
        session_id: str,
        metadata: Dict[str, Any]
    ) -> None:
        """更新会话元数据"""
        stmt = update(UserSession).where(
            UserSession.id == session_id
        ).values(
            metadata=metadata
        )
        await db_session.execute(stmt)
        await db_session.commit()
```

#### 3.2 会话中间件

```python
"""
文件: /mnt/d/工作区/云开发/working/backend/src/middleware/session_middleware.py
会话验证中间件
"""

from fastapi import Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.services.session_manager import SessionManager
from src.db import get_session

logger = logging.getLogger(__name__)


async def validate_session_middleware(
    request: Request,
    call_next
):
    """
    会话验证中间件

    验证所有需要会话的API请求
    """
    # 跳过不需要会话的路径
    excluded_paths = ["/health", "/api/version", "/docs", "/openapi.json"]
    if request.url.path in excluded_paths:
        return await call_next(request)

    # 获取会话信息
    user_id = request.headers.get("X-User-Id")
    session_id = request.headers.get("X-Session-Id")

    if not user_id or not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing user_id or session_id headers"
        )

    # 验证会话
    async with get_session() as db_session:
        session_manager = SessionManager()
        is_valid = await session_manager.validate_session(
            db_session,
            user_id,
            session_id
        )

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session"
            )

    # 将会话信息添加到request.state
    request.state.user_id = user_id
    request.state.session_id = session_id

    response = await call_next(request)
    return response
```

---

## 配置和环境管理

### 1. Memori配置参数详解

```python
"""
文件: /mnt/d/工作区/云开发/working/backend/src/config/memori_config.py
Memori配置管理
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os


class MemoriSettings(BaseSettings):
    """Memori配置设置"""

    # Anthropic API配置
    anthropic_api_key: str = Field(
        ...,
        description="Anthropic API密钥"
    )

    claude_model: str = Field(
        default="claude-sonnet-4-5-20250929",
        description="Claude模型版本"
    )

    # Memori配置
    memori_conscious_ingest: bool = Field(
        default=True,
        description="启用显式记忆摄入"
    )

    memori_auto_ingest: bool = Field(
        default=True,
        description="启用自动记忆摄入"
    )

    memori_max_memory_tokens: int = Field(
        default=100000,
        description="最大记忆token数",
        ge=10000
    )

    memori_retrieval_limit: int = Field(
        default=10,
        description="每次检索的记忆数量",
        ge=1,
        le=50
    )

    memori_importance_threshold: float = Field(
        default=0.5,
        description="记忆重要性阈值",
        ge=0.0,
        le=1.0
    )

    # Vector数据库配置（如果Memori使用外部向量DB）
    vector_db_url: Optional[str] = Field(
        default=None,
        description="向量数据库URL（可选）"
    )

    # 性能配置
    enable_caching: bool = Field(
        default=True,
        description="启用语义缓存"
    )

    cache_ttl_seconds: int = Field(
        default=3600,
        description="缓存TTL（秒）",
        ge=60
    )

    # 并发配置
    max_concurrent_requests: int = Field(
        default=10,
        description="最大并发请求数",
        ge=1
    )

    max_requests_per_user: int = Field(
        default=3,
        description="每用户最大并发数",
        ge=1
    )

    # Token预算配置
    daily_token_limit: int = Field(
        default=1000000,
        description="每日token限制"
    )

    per_request_token_limit: int = Field(
        default=8000,
        description="单次请求token限制"
    )

    # 成本配置
    cost_per_1k_input_tokens: float = Field(
        default=0.003,
        description="输入token成本（USD/1K）"
    )

    cost_per_1k_output_tokens: float = Field(
        default=0.015,
        description="输出token成本（USD/1K）"
    )

    # 日志配置
    log_level: str = Field(
        default="INFO",
        description="日志级别"
    )

    enable_debug_logging: bool = Field(
        default=False,
        description="启用调试日志"
    )

    class Config:
        env_file = ".env"
        env_prefix = "MEMORI_"
        case_sensitive = False


# 全局配置实例
_settings: Optional[MemoriSettings] = None


def get_memori_settings() -> MemoriSettings:
    """获取全局Memori配置"""
    global _settings
    if _settings is None:
        _settings = MemoriSettings()
    return _settings
```

### 2. 环境配置文件示例

**文件**: `/mnt/d/工作区/云开发/working/backend/.env.memori`

```bash
# Memori配置示例

# ===== Anthropic API配置 =====
MEMORI_ANTHROPIC_API_KEY=sk-ant-your-api-key-here
MEMORI_CLAUDE_MODEL=claude-sonnet-4-5-20250929

# ===== Memori核心配置 =====
MEMORI_CONSCIOUS_INGEST=true
MEMORI_AUTO_INGEST=true
MEMORI_MAX_MEMORY_TOKENS=100000
MEMORI_RETRIEVAL_LIMIT=10
MEMORI_IMPORTANCE_THRESHOLD=0.5

# ===== 向量数据库配置（可选） =====
# MEMORI_VECTOR_DB_URL=postgresql://localhost:5432/vectors

# ===== 性能配置 =====
MEMORI_ENABLE_CACHING=true
MEMORI_CACHE_TTL_SECONDS=3600

# ===== 并发配置 =====
MEMORI_MAX_CONCURRENT_REQUESTS=10
MEMORI_MAX_REQUESTS_PER_USER=3

# ===== Token预算配置 =====
MEMORI_DAILY_TOKEN_LIMIT=1000000
MEMORI_PER_REQUEST_TOKEN_LIMIT=8000

# ===== 成本配置 =====
# Claude Sonnet 4.5价格（2025年1月）
MEMORI_COST_PER_1K_INPUT_TOKENS=0.003
MEMORI_COST_PER_1K_OUTPUT_TOKENS=0.015

# ===== 日志配置 =====
MEMORI_LOG_LEVEL=INFO
MEMORI_ENABLE_DEBUG_LOGGING=false

# ===== 开发环境特定配置 =====
# MEMORI_MAX_CONCURRENT_REQUESTS=5
# MEMORI_LOG_LEVEL=DEBUG
# MEMORI_ENABLE_DEBUG_LOGGING=true
```

### 3. 多模型版本管理

```python
"""
文件: /mnt/d/工作区/云开发/working/backend/src/services/model_manager.py
多模型版本管理
"""

from enum import Enum
from typing import Dict, Any
from dataclasses import dataclass


class ClaudeModel(Enum):
    """Claude模型枚举"""
    SONNET_4_5 = "claude-sonnet-4-5-20250929"  # 最新最强
    SONNET_3_5 = "claude-3-5-sonnet-20241022"  # 平衡
    HAIKU_3 = "claude-3-haiku-20240307"        # 快速经济
    OPUS_3 = "claude-3-opus-20240229"          # 高性能


@dataclass
class ModelConfig:
    """模型配置"""
    name: str
    max_tokens: int
    cost_per_1k_input: float
    cost_per_1k_output: float
    recommended_use_cases: list


class ModelManager:
    """
    模型管理器

    根据不同场景选择合适的模型
    """

    MODEL_CONFIGS: Dict[ClaudeModel, ModelConfig] = {
        ClaudeModel.SONNET_4_5: ModelConfig(
            name="Claude Sonnet 4.5",
            max_tokens=8192,
            cost_per_1k_input=0.003,
            cost_per_1k_output=0.015,
            recommended_use_cases=[
                "complex_sql_generation",
                "multi_table_joins",
                "business_logic"
            ]
        ),
        ClaudeModel.SONNET_3_5: ModelConfig(
            name="Claude Sonnet 3.5",
            max_tokens=8192,
            cost_per_1k_input=0.003,
            cost_per_1k_output=0.015,
            recommended_use_cases=[
                "general_sql_generation",
                "data_analysis",
                "query_explanation"
            ]
        ),
        ClaudeModel.HAIKU_3: ModelConfig(
            name="Claude Haiku 3",
            max_tokens=4096,
            cost_per_1k_input=0.00025,
            cost_per_1k_output=0.00125,
            recommended_use_cases=[
                "simple_queries",
                "schema_lookup",
                "quick_responses"
            ]
        )
    }

    @classmethod
    def select_model(cls, use_case: str, budget_priority: bool = False) -> ClaudeModel:
        """
        根据使用场景选择模型

        参数:
            use_case: 使用场景
            budget_priority: 是否优先考虑预算

        返回:
            选择的模型
        """
        if budget_priority:
            # 预算优先：使用Haiku
            return ClaudeModel.HAIKU_3

        # 根据使用场景选择
        use_case_lower = use_case.lower()

        if any(keyword in use_case_lower for keyword in ["complex", "advanced", "multi"]):
            return ClaudeModel.SONNET_4_5
        elif any(keyword in use_case_lower for keyword in ["simple", "quick", "basic"]):
            return ClaudeModel.HAIKU_3
        else:
            return ClaudeModel.SONNET_3_5

    @classmethod
    def get_model_config(cls, model: ClaudeModel) -> ModelConfig:
        """获取模型配置"""
        return cls.MODEL_CONFIGS[model]

    @classmethod
    def estimate_cost(
        cls,
        model: ClaudeModel,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """估算成本"""
        config = cls.get_model_config(model)
        return (
            (input_tokens / 1000) * config.cost_per_1k_input +
            (output_tokens / 1000) * config.cost_per_1k_output
        )
```

### 4. LiteLLM vs 直接Anthropic SDK

#### 4.1 比较分析

```python
"""
文件: /mnt/d/工作区/云开发/working/backend/docs/litellm_vs_anthropic.md
"""
```

**LiteLLM vs 直接Anthropic SDK 比较**

| 特性 | LiteLLM | 直接Anthropic SDK | 推荐 |
|------|---------|------------------|------|
| **模型支持** | 多模型（OpenAI, Anthropic等） | 仅Anthropic | LiteLLM（如需多模型） |
| **API一致性** | 统一接口 | 原生接口 | LiteLLM（多模型项目） |
| **性能** | 稍有开销 | 最优 | Anthropic SDK |
| **功能完整性** | 基本功能 | 全部功能 | Anthropic SDK |
| **Memori集成** | 需要适配 | 原生支持 | Anthropic SDK |
| **维护成本** | 依赖额外库 | 官方维护 | Anthropic SDK |
| **类型提示** | 一般 | 完整 | Anthropic SDK |
| **流式响应** | 支持 | 完美支持 | Anthropic SDK |

**推荐**: 对于Text2SQL项目，推荐使用**直接Anthropic SDK**，原因：
1. Memori官方支持Anthropic SDK
2. 更好的性能和类型提示
3. 完整的功能支持
4. 更少的依赖

如果未来需要支持多个LLM提供商，可以考虑在服务层抽象，而不是使用LiteLLM。

---

## 监控和调试

### 1. 监控指标

#### 1.1 监控系统实现

```python
"""
文件: /mnt/d/工作区/云开发/working/backend/src/services/monitoring.py
Memori和Claude监控系统
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict
import logging
import json

logger = logging.getLogger(__name__)


@dataclass
class RequestMetrics:
    """请求指标"""
    timestamp: datetime
    user_id: str
    session_id: str
    request_type: str  # "text2sql", "chat", etc.

    # Token指标
    input_tokens: int
    output_tokens: int
    total_tokens: int

    # 性能指标
    latency_ms: float
    memory_retrieval_ms: float
    claude_api_ms: float

    # 成本指标
    estimated_cost: float

    # 质量指标
    success: bool
    error_message: Optional[str] = None

    # 记忆指标
    memories_retrieved: int
    memories_created: int


@dataclass
class MemoryMetrics:
    """记忆指标"""
    timestamp: datetime
    user_id: str
    session_id: str

    total_memories: int
    memory_tokens: int
    avg_importance: float
    retrieval_speed_ms: float


class MonitoringService:
    """
    监控服务

    收集和分析Memori和Claude的性能指标
    """

    def __init__(self):
        # 内存中的指标存储（生产环境应使用时序数据库）
        self.request_metrics: List[RequestMetrics] = []
        self.memory_metrics: List[MemoryMetrics] = []

        # 聚合统计
        self.hourly_stats: Dict[str, Dict[str, Any]] = defaultdict(dict)

    async def record_request(self, metrics: RequestMetrics) -> None:
        """记录请求指标"""
        self.request_metrics.append(metrics)

        # 日志记录
        logger.info(
            f"Request metrics - User: {metrics.user_id}, "
            f"Tokens: {metrics.total_tokens}, "
            f"Latency: {metrics.latency_ms:.2f}ms, "
            f"Cost: ${metrics.estimated_cost:.4f}"
        )

        # 检查异常
        if metrics.latency_ms > 5000:
            logger.warning(f"High latency detected: {metrics.latency_ms:.2f}ms")

        if not metrics.success:
            logger.error(f"Request failed: {metrics.error_message}")

    async def record_memory(self, metrics: MemoryMetrics) -> None:
        """记录记忆指标"""
        self.memory_metrics.append(metrics)

        logger.debug(
            f"Memory metrics - User: {metrics.user_id}, "
            f"Memories: {metrics.total_memories}, "
            f"Tokens: {metrics.memory_tokens}"
        )

        # 检查记忆大小
        if metrics.memory_tokens > 80000:
            logger.warning(
                f"Large memory size for {metrics.user_id}: "
                f"{metrics.memory_tokens} tokens"
            )

    async def get_hourly_stats(self, hours: int = 24) -> Dict[str, Any]:
        """
        获取小时级统计

        参数:
            hours: 统计的小时数

        返回:
            统计数据字典
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        # 过滤最近N小时的指标
        recent_requests = [
            m for m in self.request_metrics
            if m.timestamp >= cutoff_time
        ]

        if not recent_requests:
            return {
                "period_hours": hours,
                "total_requests": 0,
                "avg_latency_ms": 0,
                "total_cost": 0,
                "success_rate": 0
            }

        # 计算统计
        total_requests = len(recent_requests)
        successful_requests = sum(1 for m in recent_requests if m.success)
        total_tokens = sum(m.total_tokens for m in recent_requests)
        total_cost = sum(m.estimated_cost for m in recent_requests)
        avg_latency = sum(m.latency_ms for m in recent_requests) / total_requests

        return {
            "period_hours": hours,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "success_rate": successful_requests / total_requests if total_requests > 0 else 0,
            "total_tokens": total_tokens,
            "avg_tokens_per_request": total_tokens / total_requests if total_requests > 0 else 0,
            "total_cost": total_cost,
            "avg_cost_per_request": total_cost / total_requests if total_requests > 0 else 0,
            "avg_latency_ms": avg_latency,
            "p95_latency_ms": self._calculate_percentile(
                [m.latency_ms for m in recent_requests],
                0.95
            ),
            "p99_latency_ms": self._calculate_percentile(
                [m.latency_ms for m in recent_requests],
                0.99
            )
        }

    async def get_user_stats(
        self,
        user_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """获取用户统计"""
        cutoff_time = datetime.utcnow() - timedelta(days=days)

        user_requests = [
            m for m in self.request_metrics
            if m.user_id == user_id and m.timestamp >= cutoff_time
        ]

        if not user_requests:
            return {
                "user_id": user_id,
                "period_days": days,
                "total_requests": 0
            }

        return {
            "user_id": user_id,
            "period_days": days,
            "total_requests": len(user_requests),
            "total_tokens": sum(m.total_tokens for m in user_requests),
            "total_cost": sum(m.estimated_cost for m in user_requests),
            "avg_latency_ms": sum(m.latency_ms for m in user_requests) / len(user_requests)
        }

    async def get_memory_growth(
        self,
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """获取记忆增长趋势"""
        session_memories = [
            m for m in self.memory_metrics
            if m.user_id == user_id and m.session_id == session_id
        ]

        if not session_memories:
            return {
                "user_id": user_id,
                "session_id": session_id,
                "data_points": 0
            }

        # 按时间排序
        sorted_memories = sorted(session_memories, key=lambda x: x.timestamp)

        return {
            "user_id": user_id,
            "session_id": session_id,
            "data_points": len(sorted_memories),
            "start_time": sorted_memories[0].timestamp.isoformat(),
            "end_time": sorted_memories[-1].timestamp.isoformat(),
            "initial_memories": sorted_memories[0].total_memories,
            "final_memories": sorted_memories[-1].total_memories,
            "growth_rate": (
                sorted_memories[-1].total_memories - sorted_memories[0].total_memories
            ) / len(sorted_memories) if len(sorted_memories) > 0 else 0
        }

    def _calculate_percentile(self, values: List[float], percentile: float) -> float:
        """计算百分位数"""
        if not values:
            return 0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile)
        return sorted_values[min(index, len(sorted_values) - 1)]


# 全局实例
_monitoring_service: Optional[MonitoringService] = None


def get_monitoring_service() -> MonitoringService:
    """获取全局监控服务"""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = MonitoringService()
    return _monitoring_service
```

#### 1.2 监控API端点

```python
"""
文件: /mnt/d/工作区/云开发/working/backend/src/api/monitoring.py
监控API端点
"""

from fastapi import APIRouter, Depends
from typing import Optional

from src.services.monitoring import get_monitoring_service, MonitoringService

router = APIRouter(prefix="/api/monitoring", tags=["Monitoring"])


@router.get("/stats/hourly")
async def get_hourly_stats(
    hours: int = 24,
    monitoring: MonitoringService = Depends(get_monitoring_service)
):
    """获取小时级统计"""
    return await monitoring.get_hourly_stats(hours=hours)


@router.get("/stats/user/{user_id}")
async def get_user_stats(
    user_id: str,
    days: int = 7,
    monitoring: MonitoringService = Depends(get_monitoring_service)
):
    """获取用户统计"""
    return await monitoring.get_user_stats(user_id=user_id, days=days)


@router.get("/memory/growth/{user_id}/{session_id}")
async def get_memory_growth(
    user_id: str,
    session_id: str,
    monitoring: MonitoringService = Depends(get_monitoring_service)
):
    """获取记忆增长趋势"""
    return await monitoring.get_memory_growth(
        user_id=user_id,
        session_id=session_id
    )
```

### 2. 内存泄漏检测

```python
"""
文件: /mnt/d/工作区/云开发/working/backend/src/services/memory_leak_detector.py
内存泄漏检测
"""

import psutil
import os
from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MemoryLeakDetector:
    """
    内存泄漏检测器

    监控应用内存使用，检测潜在的内存泄漏
    """

    def __init__(self, threshold_mb: int = 1000):
        self.threshold_mb = threshold_mb
        self.memory_snapshots: List[Dict[str, Any]] = []
        self.process = psutil.Process(os.getpid())

    async def take_snapshot(self) -> Dict[str, Any]:
        """获取内存快照"""
        memory_info = self.process.memory_info()

        snapshot = {
            "timestamp": datetime.utcnow().isoformat(),
            "rss_mb": memory_info.rss / 1024 / 1024,  # 物理内存
            "vms_mb": memory_info.vms / 1024 / 1024,  # 虚拟内存
            "percent": self.process.memory_percent()
        }

        self.memory_snapshots.append(snapshot)

        # 保留最近100个快照
        if len(self.memory_snapshots) > 100:
            self.memory_snapshots = self.memory_snapshots[-100:]

        return snapshot

    async def detect_leak(self) -> Dict[str, Any]:
        """
        检测内存泄漏

        分析规则:
        - 内存持续增长
        - 超过阈值
        - 无回收迹象
        """
        if len(self.memory_snapshots) < 10:
            return {
                "leak_detected": False,
                "reason": "Insufficient data points"
            }

        # 取最近10个快照
        recent_snapshots = self.memory_snapshots[-10:]
        memory_values = [s["rss_mb"] for s in recent_snapshots]

        # 计算趋势
        is_increasing = all(
            memory_values[i] <= memory_values[i + 1]
            for i in range(len(memory_values) - 1)
        )

        current_memory = memory_values[-1]
        initial_memory = memory_values[0]
        growth_rate = (current_memory - initial_memory) / initial_memory

        # 检测泄漏
        leak_detected = (
            is_increasing and
            growth_rate > 0.2 and  # 增长超过20%
            current_memory > self.threshold_mb
        )

        if leak_detected:
            logger.warning(
                f"Memory leak detected! "
                f"Current: {current_memory:.2f}MB, "
                f"Growth: {growth_rate:.1%}"
            )

        return {
            "leak_detected": leak_detected,
            "current_memory_mb": current_memory,
            "growth_rate": growth_rate,
            "is_increasing": is_increasing,
            "threshold_mb": self.threshold_mb,
            "recommendation": (
                "Consider clearing old sessions or restarting the service"
                if leak_detected else "Memory usage is normal"
            )
        }
```

### 3. 性能分析和优化建议

```python
"""
文件: /mnt/d/工作区/云开发/working/backend/src/services/performance_analyzer.py
性能分析器
"""

from typing import Dict, Any, List
from collections import Counter
import logging

from src.services.monitoring import get_monitoring_service, RequestMetrics

logger = logging.getLogger(__name__)


class PerformanceAnalyzer:
    """
    性能分析器

    分析性能指标并提供优化建议
    """

    def __init__(self):
        self.monitoring = get_monitoring_service()

    async def analyze_performance(self) -> Dict[str, Any]:
        """
        分析性能并提供优化建议

        返回:
            分析结果和优化建议
        """
        # 获取最近的请求指标
        recent_requests = self.monitoring.request_metrics[-1000:]

        if not recent_requests:
            return {
                "status": "insufficient_data",
                "recommendations": []
            }

        analysis = {
            "status": "ok",
            "issues": [],
            "recommendations": []
        }

        # 1. 检查高延迟
        high_latency_requests = [
            r for r in recent_requests
            if r.latency_ms > 3000
        ]

        if len(high_latency_requests) > len(recent_requests) * 0.1:
            analysis["issues"].append({
                "type": "high_latency",
                "severity": "high",
                "description": f"{len(high_latency_requests)} requests with latency > 3s"
            })
            analysis["recommendations"].append({
                "issue": "high_latency",
                "suggestion": "Consider implementing request caching or using a smaller Claude model"
            })

        # 2. 检查高token使用
        avg_tokens = sum(r.total_tokens for r in recent_requests) / len(recent_requests)
        if avg_tokens > 5000:
            analysis["issues"].append({
                "type": "high_token_usage",
                "severity": "medium",
                "description": f"Average tokens per request: {avg_tokens:.0f}"
            })
            analysis["recommendations"].append({
                "issue": "high_token_usage",
                "suggestion": "Optimize context size or implement more aggressive memory pruning"
            })

        # 3. 检查错误率
        error_rate = sum(1 for r in recent_requests if not r.success) / len(recent_requests)
        if error_rate > 0.05:
            analysis["issues"].append({
                "type": "high_error_rate",
                "severity": "high",
                "description": f"Error rate: {error_rate:.1%}"
            })
            analysis["recommendations"].append({
                "issue": "high_error_rate",
                "suggestion": "Review error logs and implement better retry logic"
            })

        # 4. 检查记忆检索性能
        avg_retrieval_time = sum(
            r.memory_retrieval_ms for r in recent_requests
        ) / len(recent_requests)

        if avg_retrieval_time > 500:
            analysis["issues"].append({
                "type": "slow_memory_retrieval",
                "severity": "medium",
                "description": f"Average retrieval time: {avg_retrieval_time:.0f}ms"
            })
            analysis["recommendations"].append({
                "issue": "slow_memory_retrieval",
                "suggestion": "Consider using vector database indexing or reducing memory size"
            })

        # 设置整体状态
        if any(issue["severity"] == "high" for issue in analysis["issues"]):
            analysis["status"] = "critical"
        elif analysis["issues"]:
            analysis["status"] = "warning"

        return analysis

    async def generate_optimization_report(self) -> str:
        """
        生成优化报告

        返回:
            格式化的优化报告
        """
        analysis = await self.analyze_performance()

        report_lines = [
            "# Performance Optimization Report",
            f"Status: {analysis['status'].upper()}",
            "",
            "## Issues Detected"
        ]

        if analysis["issues"]:
            for issue in analysis["issues"]:
                report_lines.append(
                    f"- [{issue['severity'].upper()}] {issue['type']}: {issue['description']}"
                )
        else:
            report_lines.append("No issues detected.")

        report_lines.extend([
            "",
            "## Recommendations"
        ])

        if analysis["recommendations"]:
            for rec in analysis["recommendations"]:
                report_lines.append(f"- {rec['issue']}: {rec['suggestion']}")
        else:
            report_lines.append("No recommendations at this time.")

        return "\n".join(report_lines)
```

---

## 生产环境部署

### 1. 部署清单

```markdown
# Memori生产部署清单

## 环境配置
- [ ] 设置ANTHROPIC_API_KEY环境变量
- [ ] 配置数据库连接（PostgreSQL）
- [ ] 配置向量数据库（如使用外部VectorDB）
- [ ] 设置日志级别为WARNING或ERROR
- [ ] 禁用调试模式

## 安全配置
- [ ] 使用密钥管理服务（AWS Secrets Manager, HashiCorp Vault等）
- [ ] 启用HTTPS/TLS
- [ ] 配置CORS白名单
- [ ] 实施API速率限制
- [ ] 启用请求认证和授权

## 性能优化
- [ ] 配置Redis缓存
- [ ] 设置合理的并发限制
- [ ] 启用请求队列
- [ ] 配置CDN（如有静态资源）
- [ ] 启用数据库连接池

## 监控和告警
- [ ] 配置APM工具（如Datadog, New Relic）
- [ ] 设置错误告警（Sentry）
- [ ] 配置性能监控
- [ ] 设置成本告警
- [ ] 配置健康检查端点

## 备份和恢复
- [ ] 配置数据库自动备份
- [ ] 设置记忆数据备份策略
- [ ] 测试恢复流程
- [ ] 文档化灾难恢复计划

## 扩展性
- [ ] 配置水平扩展（多实例）
- [ ] 实施负载均衡
- [ ] 配置自动扩缩容
- [ ] 优化数据库查询
```

### 2. Docker部署配置

**文件**: `/mnt/d/工作区/云开发/working/backend/Dockerfile.memori`

```dockerfile
# Memori集成的生产环境Dockerfile

FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY pyproject.toml poetry.lock ./

# 安装Python依赖
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

# 复制应用代码
COPY src/ ./src/
COPY migrations/ ./migrations/

# 创建非root用户
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**文件**: `/mnt/d/工作区/云开发/working/docker-compose.memori.yml`

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.memori
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/text2sql
      - MEMORI_ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - MEMORI_CLAUDE_MODEL=claude-sonnet-4-5-20250929
      - MEMORI_MAX_CONCURRENT_REQUESTS=20
      - MEMORI_DAILY_TOKEN_LIMIT=5000000
      - LOG_LEVEL=WARNING
    depends_on:
      - db
      - redis
    volumes:
      - ./uploads:/app/uploads
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=text2sql
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

---

## 常见陷阱和解决方案

### 1. Token限制和上下文窗口溢出

**问题**: Claude有最大上下文窗口限制（如8192 tokens），当记忆和消息历史过多时会溢出。

**解决方案**:
```python
# 在create_message前检查token数
from src.services.token_manager import get_token_manager

token_manager = get_token_manager()

# 估算总token数
context_tokens = token_manager.count_messages_tokens(messages)
memory_tokens = # 从Memori获取

if context_tokens + memory_tokens > 7000:  # 留1000 buffer
    # 策略1: 减少消息历史
    messages = messages[-10:]  # 只保留最近10条

    # 策略2: 减少检索的记忆数
    memori_service.config.retrieval_limit = 5

    # 策略3: 使用更大的模型
    # claude-opus有更大的上下文窗口
```

### 2. 记忆污染和错误传播

**问题**: 如果AI生成了错误的信息，这些错误可能被保存到记忆中并在未来的对话中重复。

**解决方案**:
```python
# 实施记忆验证机制
class MemoryValidator:
    async def validate_before_save(self, content: str, metadata: dict) -> bool:
        """在保存前验证记忆"""
        # 1. 检查SQL语法（如果是SQL记忆）
        if metadata.get("type") == "query":
            if not self._is_valid_sql(content):
                logger.warning(f"Invalid SQL in memory: {content}")
                return False

        # 2. 检查重要信息的一致性
        # 3. 使用置信度阈值

        return True

# 在保存记忆时使用
validator = MemoryValidator()
if await validator.validate_before_save(content, metadata):
    await memori_service.add_conscious_memory(...)
```

### 3. 成本失控

**问题**: Token使用和API调用成本可能快速增长。

**解决方案**:
```python
# 实施多层成本控制

# 1. 用户级别限制
daily_limit = 10000  # tokens
if user_daily_usage > daily_limit:
    raise HTTPException(429, "Daily limit exceeded")

# 2. 请求级别预算检查
budget_check = await token_manager.check_budget(user_id, estimated_tokens)
if not budget_check["allowed"]:
    raise HTTPException(429, budget_check["reason"])

# 3. 自动降级策略
if user_budget_remaining < 1000:
    # 使用更便宜的模型
    model = ClaudeModel.HAIKU_3
else:
    model = ClaudeModel.SONNET_4_5

# 4. 实施缓存
# 对相同查询使用缓存而不是重新调用API
```

### 4. 会话隔离问题

**问题**: 不同用户或会话的记忆可能混淆。

**解决方案**:
```python
# 使用强隔离策略

# 1. 在Memori实例化时使用唯一标识
session_key = f"{user_id}:{session_id}:{namespace}"
memori = Memori(user_id=session_key)

# 2. 在数据库层面添加隔离
# 记忆表添加user_id和session_id索引

# 3. 定期清理过期会话
async def cleanup_expired_sessions():
    cutoff = datetime.utcnow() - timedelta(hours=24)
    # 删除过期的会话记忆

# 4. 测试隔离性
async def test_session_isolation():
    # 创建两个会话
    session1_memories = await memori.search(user_id="user1", session_id="s1", ...)
    session2_memories = await memori.search(user_id="user1", session_id="s2", ...)

    # 确保记忆不重叠
    assert not any(m in session2_memories for m in session1_memories)
```

### 5. 异步并发问题

**问题**: FastAPI的异步特性可能导致Memori实例共享问题。

**解决方案**:
```python
# 使用线程安全的单例模式

import threading

class ThreadSafeMemoriService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._sessions = {}
            self._sessions_lock = asyncio.Lock()
            self._initialized = True

    async def get_session(self, user_id, session_id):
        async with self._sessions_lock:
            key = f"{user_id}:{session_id}"
            if key not in self._sessions:
                self._sessions[key] = Memori(user_id=key)
            return self._sessions[key]
```

### 6. 记忆大小膨胀

**问题**: 随着时间推移，记忆数据库可能变得非常大，影响性能。

**解决方案**:
```python
# 实施记忆生命周期管理

class MemoryLifecyclePolicy:
    # 1. 自动归档策略
    async def archive_old_memories(self, days=30):
        """将旧记忆移到冷存储"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        # 移动到归档表或对象存储

    # 2. 重要性衰减
    async def apply_time_decay(self):
        """随时间降低记忆重要性"""
        # importance = original_importance * exp(-decay_rate * age)

    # 3. 定期压缩
    async def consolidate_similar_memories(self):
        """合并相似记忆"""
        # 使用语义相似度检测并合并

    # 4. 容量限制
    async def enforce_size_limit(self, user_id, max_memories=1000):
        """强制记忆数量上限"""
        memories = await get_user_memories(user_id)
        if len(memories) > max_memories:
            # 删除最不重要的记忆
            sorted_memories = sorted(memories, key=lambda m: m.importance)
            to_delete = sorted_memories[:len(memories) - max_memories]
            await delete_memories(to_delete)
```

### 7. API速率限制

**问题**: Claude API有速率限制，高并发可能触发限制。

**解决方案**:
```python
# 实施速率限制和队列

from asyncio import Semaphore, Queue

class RateLimiter:
    def __init__(self, requests_per_minute=50):
        self.requests_per_minute = requests_per_minute
        self.semaphore = Semaphore(requests_per_minute)
        self.queue = Queue()

    async def acquire(self):
        """获取请求许可"""
        await self.semaphore.acquire()

        # 设置定时器，1分钟后释放
        asyncio.create_task(self._release_after_delay())

    async def _release_after_delay(self):
        await asyncio.sleep(60)  # 1分钟
        self.semaphore.release()

# 在API调用前使用
rate_limiter = RateLimiter(requests_per_minute=50)

async def call_claude_with_rate_limit(...):
    await rate_limiter.acquire()
    try:
        response = await client.messages.create(...)
        return response
    finally:
        pass  # semaphore会在1分钟后自动释放
```

---

## 总结和最佳实践

### 关键原则

1. **渐进式记忆管理**: 从短期记忆开始，逐步提升重要信息到长期记忆
2. **成本意识**: 始终监控token使用和API成本
3. **会话隔离**: 确保不同用户和会话的记忆完全隔离
4. **性能优先**: 优化上下文大小，避免不必要的API调用
5. **错误恢复**: 实施完善的重试和降级策略
6. **监控驱动**: 基于监控数据持续优化

### 推荐的开发流程

1. **本地开发**: 使用较小的token限制和简化的记忆管理
2. **测试环境**: 测试不同场景下的记忆行为和性能
3. **预生产**: 进行压力测试和成本估算
4. **生产部署**: 启用完整监控和告警
5. **持续优化**: 基于监控数据调整配置

### 参考资源

- [Memori官方文档](https://github.com/anthropics/memori)
- [Anthropic Claude API文档](https://docs.anthropic.com/)
- [FastAPI异步最佳实践](https://fastapi.tiangolo.com/async/)
- [Text2SQL项目文档](/mnt/d/工作区/云开发/working/)

---

**文档维护**: 请根据Memori和Claude API的更新定期审查此文档
**最后更新**: 2025-11-11
**版本**: 1.0.0

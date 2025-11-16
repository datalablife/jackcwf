# LangChain v1.0 AI Conversation - Tasks & Stories

**Feature**: LangChain v1.0 AI Conversation with Agents and RAG
**Version**: 1.0.0
**Created**: 2025-11-16
**Status**: Ready for Development

---

## 📋 概述

本文档将功能规范和实现计划分解为可执行的 **Epics → Stories → Tasks**。

**依赖于**:
- `.specify/memory/constitution.md` (8 个核心原则)
- `langchain-ai-conversation-spec.md` (功能规范)
- `langchain-ai-conversation-plan.md` (实现计划)

---

## 🎯 Epic 分解

### Epic 1: 后端基础设施
**持续时间**: Week 1-2 (10 个工作日)
**预估故事点**: 8-13

### Epic 2: Agent 和 RAG
**持续时间**: Week 2-3 (10 个工作日)
**预估故事点**: 13-21

### Epic 3: 中间件和特性
**持续时间**: Week 3-4 (10 个工作日)
**预估故事点**: 13-21

### Epic 4: 前端开发
**持续时间**: Week 4-5 (10 个工作日)
**预估故事点**: 13-21

### Epic 5: 测试和优化
**持续时间**: Week 5-6 (10 个工作日)
**预估故事点**: 8-13

### Epic 6: 部署和上线
**持续时间**: Week 6-7 (5 个工作日)
**预估故事点**: 3-5

---

## 📚 Story 详细分解

---

# 🚀 EPIC 1: 后端基础设施 (Week 1-2)

## Story 1.1: 数据库设计和迁移

**故事点**: 5
**优先级**: P0 (阻塞)
**分配给**: Backend Lead
**标签**: database, infrastructure, async

### 用户故事

```gherkin
As a backend developer
I want to have a properly designed and tested database
So that data is stored reliably with good query performance

Acceptance Criteria:
- [ ] 4 个数据库表创建成功 (conversations, messages, documents, embeddings)
- [ ] 所有索引创建完成 (7+ 索引)
- [ ] 分区策略配置完成 (embeddings 按月分区)
- [ ] 数据库迁移脚本通过测试
- [ ] 约束和关系设置正确
```

### 任务分解

#### Task 1.1.1: 创建 conversations 表
**故事点**: 1
**完成标准**:
- [ ] 表结构创建 (id, user_id, title, summary, model, system_prompt, metadata, is_deleted, created_at, updated_at)
- [ ] 主键和外键约束
- [ ] 软删除机制 (is_deleted)
- [ ] 时间戳管理 (created_at, updated_at)
- [ ] 单元测试通过

```sql
-- 示例
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR NOT NULL,
    title VARCHAR(255) NOT NULL,
    summary TEXT,
    model VARCHAR(100) DEFAULT 'claude-sonnet-4-5-20250929',
    system_prompt TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,

    CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES users(id)
);
```

#### Task 1.1.2: 创建 messages 表
**故事点**: 1
**完成标准**:
- [ ] 表结构创建 (id, conversation_id, role, content, tool_calls, tool_results, tokens_used, metadata, created_at)
- [ ] 外键约束到 conversations
- [ ] 角色检查约束 (user, assistant, system)
- [ ] JSON 字段用于工具调用/结果
- [ ] 级联删除配置

#### Task 1.1.3: 创建 documents 和 embeddings 表
**故事点**: 2
**完成标准**:
- [ ] documents 表创建 (id, user_id, filename, file_type, content, total_chunks, metadata, is_deleted, created_at, updated_at)
- [ ] embeddings 表创建 (id, document_id, chunk_text, embedding vector(1536), chunk_index, metadata, created_at, is_deleted)
- [ ] 向量类型配置 (pgvector 扩展)
- [ ] 外键关系
- [ ] 级联删除

#### Task 1.1.4: 创建所有索引
**故事点**: 1
**完成标准**:
- [ ] conversations 索引 (user_created, user_active, title_search)
- [ ] messages 索引 (conversation, role, conversation_recent)
- [ ] documents 索引 (user_created, user_active)
- [ ] embeddings 索引 (HNSW vector index, document, created, document_chunk)
- [ ] 索引性能验证

#### Task 1.1.5: 配置分区策略
**故事点**: 1
**完成标准**:
- [ ] embeddings 表按时间分区 (按月)
- [ ] 创建初始分区 (当前月份和下个月份)
- [ ] 自动分区脚本编写 (每月创建新分区)
- [ ] 分区查询性能测试

---

## Story 1.2: 异步存储库实现

**故事点**: 8
**优先级**: P0 (阻塞)
**分配给**: Backend Team (2-3 人)
**标签**: async, repository, database

### 用户故事

```gherkin
As a backend service
I want to have async-first repository layer
So that I/O operations are non-blocking and performant

Acceptance Criteria:
- [ ] 4 个存储库实现 (Conversation, Message, Document, Embedding)
- [ ] 所有数据库操作使用 async/await
- [ ] asyncpg 驱动配置完成
- [ ] SQLAlchemy async session 管理
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] mypy --strict 通过
```

### 任务分解

#### Task 1.2.1: 基础存储库框架
**故事点**: 2
**完成标准**:
- [ ] BaseRepository 抽象类创建
- [ ] AsyncSessionLocal 配置
- [ ] 数据库连接池配置
- [ ] 事务管理实现
- [ ] 错误处理模板

```python
# backend/src/repositories/base_repository.py

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Generic, TypeVar, Optional, List
from abc import ABC, abstractmethod

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """异步存储库基类"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, obj: T) -> T:
        """创建对象"""
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def get(self, id: str) -> Optional[T]:
        """按 ID 获取"""
        return await self.session.get(self.model, id)

    async def list(self, skip: int = 0, limit: int = 10) -> List[T]:
        """列出对象"""
        result = await self.session.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def update(self, obj: T) -> T:
        """更新对象"""
        await self.session.merge(obj)
        await self.session.commit()
        return obj

    async def delete(self, id: str) -> bool:
        """删除对象"""
        obj = await self.get(id)
        if obj:
            await self.session.delete(obj)
            await self.session.commit()
            return True
        return False
```

#### Task 1.2.2: ConversationRepository 实现
**故事点**: 2
**完成标准**:
- [ ] 创建方法 (user_id, title, system_prompt, model)
- [ ] 获取方法 (按 ID 和 user_id)
- [ ] 列表方法 (按 user_id 排序)
- [ ] 更新方法 (title, summary, system_prompt)
- [ ] 软删除方法
- [ ] 单元测试 (≥90% 覆盖)

```python
# 示例方法
class ConversationRepository(BaseRepository[ConversationORM]):
    async def get_by_user(self, user_id: str) -> List[ConversationORM]:
        """获取用户的所有对话"""
        result = await self.session.execute(
            select(ConversationORM)
            .where(ConversationORM.user_id == user_id)
            .where(ConversationORM.is_deleted == False)
            .order_by(ConversationORM.created_at.desc())
        )
        return result.scalars().all()

    async def soft_delete(self, conversation_id: str) -> bool:
        """软删除对话"""
        conversation = await self.get(conversation_id)
        if conversation:
            conversation.is_deleted = True
            conversation.deleted_at = datetime.utcnow()
            await self.update(conversation)
            return True
        return False
```

#### Task 1.2.3: MessageRepository 实现
**故事点**: 2
**完成标准**:
- [ ] 创建方法 (conversation_id, role, content, tool_calls, tool_results)
- [ ] 按对话获取方法 (带分页)
- [ ] 按角色过滤方法
- [ ] 更新工具结果方法
- [ ] 单元测试 (≥90% 覆盖)

#### Task 1.2.4: DocumentRepository 和 EmbeddingRepository 实现
**故事点**: 2
**完成标准**:
- [ ] DocumentRepository (upload, list, get, delete)
- [ ] EmbeddingRepository (insert, search, delete)
- [ ] 向量搜索实现 (HNSW, cosine similarity, ≤200ms)
- [ ] 批量插入优化
- [ ] 单元测试 (≥90% 覆盖)

```python
# EmbeddingRepository 示例

class EmbeddingRepository(BaseRepository[EmbeddingORM]):
    async def search(
        self,
        query_embedding: List[float],
        user_id: str,
        limit: int = 5,
        threshold: float = 0.7
    ) -> List[EmbeddingORM]:
        """
        使用 pgvector 相似性搜索

        Performance Target: ≤ 200ms P99
        """
        import time
        start = time.time()

        # pgvector 余弦相似性搜索
        result = await self.session.execute(
            select(EmbeddingORM)
            .join(DocumentORM)
            .where(DocumentORM.user_id == user_id)
            .where(EmbeddingORM.embedding.cosine_distance(query_embedding) < 1 - threshold)
            .where(EmbeddingORM.is_deleted == False)
            .order_by(EmbeddingORM.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )

        embeddings = result.scalars().all()
        elapsed_ms = (time.time() - start) * 1000

        # 记录性能
        logger.info(f"Vector search completed in {elapsed_ms:.2f}ms")
        assert elapsed_ms <= 200, f"Vector search too slow: {elapsed_ms}ms"

        return embeddings

    async def batch_insert(self, embeddings: List[EmbeddingORM]) -> int:
        """
        批量插入向量

        Performance Target: ≤ 100ms per 1000 vectors
        """
        self.session.add_all(embeddings)
        await self.session.commit()
        return len(embeddings)
```

---

## Story 1.3: API 框架搭建

**故事点**: 5
**优先级**: P0 (阻塞)
**分配给**: Backend Lead
**标签**: api, fastapi, framework

### 任务分解

#### Task 1.3.1: FastAPI 应用初始化
**故事点**: 2
**完成标准**:
- [ ] FastAPI 应用创建
- [ ] 环境变量加载 (.env)
- [ ] CORS 配置
- [ ] 速率限制配置
- [ ] 全局异常处理

#### Task 1.3.2: 路由注册和项目布局
**故事点**: 2
**完成标准**:
- [ ] v1 路由注册
- [ ] API 蓝图分离
- [ ] 依赖注入设置
- [ ] 健康检查端点 (/health)

#### Task 1.3.3: 文档和 OpenAPI 配置
**故事点**: 1
**完成标准**:
- [ ] Swagger UI 配置
- [ ] OpenAPI schema 自动生成
- [ ] 所有端点文档

---

# 🤖 EPIC 2: Agent 和 RAG (Week 2-3)

## Story 2.1: 向量化、RAG 管道 和 长对话总结

**故事点**: 18 (13 + 5 for Task 2.1.5)
**优先级**: P0 (阻塞)
**分配给**: AI/ML Team + Backend Team
**标签**: ai, rag, embedding, langchain, conversation-management

### 用户故事

```gherkin
As a user
I want to upload documents and get AI responses based on them
So that I can have conversations grounded in my specific knowledge

Acceptance Criteria:
- [ ] 文档分块成功 (1000 tokens, 200 token overlap)
- [ ] 向量化完成 (1536-dim, OpenAI Ada)
- [ ] pgvector 存储成功
- [ ] 相似性搜索工作 (≤200ms P99)
- [ ] RAG 集成到 Agent
- [ ] 单元测试覆盖 ≥80%
```

### 任务分解

#### Task 2.1.1: 文档分块管道
**故事点**: 3
**完成标准**:
- [ ] 文档加载器 (PDF, TXT, MD)
- [ ] 文本分块 (1000 tokens, 200 overlap)
- [ ] 元数据提取 (页码, 章节, 位置)
- [ ] 分块验证和错误处理
- [ ] 单元测试

```python
# backend/src/services/document_service.py

import fitz  # PDF
from typing import List, Tuple

class DocumentChunker:
    """文档分块服务"""

    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap

    async def chunk_document(
        self,
        content: str,
        metadata: dict
    ) -> List[Tuple[str, dict]]:
        """
        将文档分块

        Args:
            content: 文档内容
            metadata: 元数据 (页码、来源等)

        Returns:
            [(chunk_text, chunk_metadata), ...]
        """
        chunks = []
        tokens = content.split()  # 简化，实际用 tiktoken

        chunk_idx = 0
        for i in range(0, len(tokens), self.chunk_size - self.overlap):
            chunk_tokens = tokens[i:i + self.chunk_size]
            chunk_text = ' '.join(chunk_tokens)

            chunk_metadata = {
                **metadata,
                'chunk_index': chunk_idx,
                'chunk_start': i,
                'chunk_end': min(i + self.chunk_size, len(tokens))
            }

            chunks.append((chunk_text, chunk_metadata))
            chunk_idx += 1

        return chunks
```

#### Task 2.1.2: OpenAI 向量化集成
**故事点**: 3
**完成标准**:
- [ ] OpenAI 客户端集成
- [ ] text-embedding-3-small 模型 (1536-dim)
- [ ] 批量向量化处理
- [ ] 错误重试机制
- [ ] 成本监控

```python
# backend/src/services/embedding_service.py

from openai import AsyncOpenAI

class EmbeddingService:
    """向量化服务"""

    def __init__(self, openai_key: str):
        self.client = AsyncOpenAI(api_key=openai_key)

    async def embed_text(self, text: str) -> List[float]:
        """向量化单个文本"""
        response = await self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量向量化"""
        response = await self.client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )
        return [item.embedding for item in response.data]

    def validate_embedding(self, embedding: List[float]):
        """验证向量维度"""
        assert len(embedding) == 1536, \
            f"Expected 1536-dim, got {len(embedding)}-dim"
```

#### Task 2.1.3: pgvector 存储和搜索
**故事点**: 4
**完成标准**:
- [ ] pgvector 扩展已安装
- [ ] 向量规范化 (L2)
- [ ] HNSW 索引创建
- [ ] 相似性搜索实现 (cosine)
- [ ] 性能基准测试 (≤200ms P99)
- [ ] 缓存策略 (Redis)

```python
# backend/src/repositories/embedding_repository.py

from sqlalchemy import func
from pgvector.sqlalchemy import Vector

class EmbeddingRepository:
    async def store_embedding(
        self,
        document_id: str,
        chunk_text: str,
        embedding: List[float],
        chunk_index: int,
        metadata: dict
    ) -> str:
        """存储单个向量"""
        embedding_orm = EmbeddingORM(
            document_id=document_id,
            chunk_text=chunk_text,
            embedding=embedding,  # pgvector 自动处理
            chunk_index=chunk_index,
            metadata=metadata
        )
        return await self.create(embedding_orm)

    async def search(
        self,
        query_embedding: List[float],
        user_id: str,
        limit: int = 5,
        threshold: float = 0.7
    ) -> List[dict]:
        """
        相似性搜索

        使用 pgvector <-> 操作符 (cosine distance)
        性能: ≤ 200ms P99
        """
        import time
        start = time.time()

        # 余弦相似性: 1 - (dot_product / (norm_a * norm_b))
        # pgvector: <-> 操作符
        result = await self.session.execute(
            select(
                EmbeddingORM.id,
                EmbeddingORM.chunk_text,
                EmbeddingORM.metadata,
                # 计算相似度分数
                (1 - (EmbeddingORM.embedding <-> query_embedding)).label('score')
            )
            .join(DocumentORM)
            .where(DocumentORM.user_id == user_id)
            .where((1 - (EmbeddingORM.embedding <-> query_embedding)) >= threshold)
            .where(EmbeddingORM.is_deleted == False)
            .order_by('score')
            .limit(limit)
        )

        rows = result.all()
        elapsed_ms = (time.time() - start) * 1000

        logger.info(f"Vector search completed: {len(rows)} results in {elapsed_ms:.2f}ms")

        return [
            {
                'id': row[0],
                'text': row[1],
                'metadata': row[2],
                'score': row[3]
            }
            for row in rows
        ]
```

#### Task 2.1.4: 文档上传端点
**故事点**: 3
**完成标准**:
- [ ] 文件上传处理 (PDF, TXT, MD)
- [ ] 文档分块和向量化
- [ ] 向量批量存储
- [ ] 进度跟踪 (异步处理)
- [ ] 错误处理和恢复

#### Task 2.1.5: 长对话总结和上下文压缩 (A4 补救)
**故事点**: 5
**优先级**: P1 (高)
**完成标准**:
- [ ] 对话长度监控 (>5000 tokens)
- [ ] 自动总结触发机制
- [ ] 基于LLM的总结生成
- [ ] 总结缓存和存储
- [ ] 总结注入到上下文
- [ ] 单元和集成测试

**实现指南**:

```python
# backend/src/services/conversation_summarization_service.py

import tiktoken
from typing import Optional
from datetime import datetime

class ConversationSummarizationService:
    """长对话总结服务 - 防止token膨胀"""

    def __init__(self, anthropic_client, max_context_tokens: int = 6000):
        self.client = anthropic_client
        self.max_context_tokens = max_context_tokens
        self.tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")

    async def check_and_summarize(
        self,
        conversation_id: str,
        messages: List[dict],
        force_summarize: bool = False
    ) -> Optional[dict]:
        """
        检查对话长度，必要时生成总结

        Args:
            conversation_id: 对话ID
            messages: 当前消息列表
            force_summarize: 强制总结（用于特别长的对话）

        Returns:
            总结对象或None（无需总结）
        """
        # 计算当前对话的token数
        total_tokens = await self._count_tokens(messages)

        # 判断是否需要总结
        if total_tokens > self.max_context_tokens or force_summarize:
            return await self._generate_summary(
                conversation_id=conversation_id,
                messages=messages,
                token_count=total_tokens
            )

        return None

    async def _count_tokens(self, messages: List[dict]) -> int:
        """计算消息列表的token数"""
        total = 0
        for msg in messages:
            # 添加消息头开销
            total += 4
            # 添加内容token
            content = msg.get("content", "")
            total += len(self.tokenizer.encode(content))
        return total

    async def _generate_summary(
        self,
        conversation_id: str,
        messages: List[dict],
        token_count: int
    ) -> dict:
        """生成对话总结"""

        # 构建总结提示
        summary_prompt = self._build_summary_prompt(messages)

        # 调用Claude API生成总结
        response = await self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=500,
            system="You are a conversation summarizer. Create concise, factual summaries of conversations.",
            messages=[{
                "role": "user",
                "content": summary_prompt
            }]
        )

        summary_text = response.content[0].text

        # 存储总结到数据库
        summary_record = {
            "conversation_id": conversation_id,
            "summary": summary_text,
            "original_message_count": len(messages),
            "original_token_count": token_count,
            "summarized_message_count": await self._count_summarized_messages(messages),
            "created_at": datetime.utcnow(),
            "is_active": True
        }

        # 保存到数据库
        await self.summary_repository.create(summary_record)

        # 记录事件
        await logger.ainfo(
            "conversation_summarized",
            conversation_id=conversation_id,
            original_tokens=token_count,
            summary_length=len(summary_text)
        )

        return summary_record

    def _build_summary_prompt(self, messages: List[dict]) -> str:
        """构建总结提示"""
        # 只包含最近的消息来降低成本
        recent_messages = messages[-20:]

        prompt = "Summarize this conversation:\n\n"
        for msg in recent_messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            prompt += f"{role}: {content}\n"

        prompt += """
Provide a concise summary covering:
1. Main topics discussed
2. Key decisions or conclusions
3. Important context for future messages
Keep the summary under 200 tokens.
"""
        return prompt

    async def _count_summarized_messages(self, messages: List[dict]) -> int:
        """计算需要被总结的消息数（保留最后几条）"""
        # 保留最后10条消息，其余的将被总结
        return max(0, len(messages) - 10)

    async def inject_summary_into_context(
        self,
        conversation_id: str,
        recent_messages: List[dict]
    ) -> List[dict]:
        """
        将总结注入到上下文中

        返回: [总结消息, ...最近消息]
        """
        # 获取最新的总结
        summary = await self.summary_repository.get_latest(conversation_id)

        if not summary or not summary["is_active"]:
            return recent_messages

        # 构建总结消息
        summary_message = {
            "role": "system",
            "content": f"Previous conversation summary:\n{summary['summary']}"
        }

        # 返回总结 + 最近消息
        return [summary_message] + recent_messages

# 监控和告警
async def monitor_conversation_length(conversation_id: str, message_count: int):
    """监控对话长度，用于告警"""
    if message_count > 100:
        await logger.awarn(
            "conversation_very_long",
            conversation_id=conversation_id,
            message_count=message_count,
            recommendation="consider_summarization"
        )

# 测试
@pytest.mark.asyncio
async def test_long_conversation_summarization():
    """测试长对话总结"""
    service = ConversationSummarizationService(
        anthropic_client=mock_client,
        max_context_tokens=6000
    )

    # 创建超长对话（>6000 tokens）
    long_messages = [
        {"role": "user", "content": "..." * 100},  # 很多token
        {"role": "assistant", "content": "..." * 100},
    ] * 20

    # 触发总结
    summary = await service.check_and_summarize(
        conversation_id="test_conv",
        messages=long_messages
    )

    assert summary is not None
    assert "summary" in summary
    assert summary["original_token_count"] > 6000

@pytest.mark.asyncio
async def test_summary_injection():
    """测试总结注入"""
    service = ConversationSummarizationService(mock_client)

    recent_messages = [
        {"role": "user", "content": "latest question"}
    ]

    # 注入总结
    context_with_summary = await service.inject_summary_into_context(
        conversation_id="test_conv",
        recent_messages=recent_messages
    )

    # 验证总结在开头
    assert context_with_summary[0]["role"] == "system"
    assert "summary" in context_with_summary[0]["content"].lower()
```

**相关配置和监控**:
```python
# backend/.env
CONVERSATION_SUMMARY_TOKEN_THRESHOLD=6000        # 触发总结的token阈值
CONVERSATION_SUMMARY_RETENTION_MESSAGES=10       # 保留的最近消息数
CONVERSATION_SUMMARY_ENABLED=true
CONVERSATION_SUMMARY_COST_MONITOR=true          # 监控成本

# backend/src/monitoring/alerts.yaml
alerts:
  - name: ConversationTooLong
    condition: message_count > 100
    severity: warning
    action: recommend_summarization
```

---

## Story 2.2: LangChain Agent 实现

**故事点**: 13
**优先级**: P0 (阻塞)
**分配给**: AI/ML Team
**标签**: ai, langchain, agent, tools

### 用户故事

```gherkin
As an AI system
I want to create a flexible agent with tools
So that I can handle complex queries with tool usage

Acceptance Criteria:
- [ ] Agent 使用 LangChain v1.0 create_agent() 创建
- [ ] 3 个工具已实现 (search_documents, query_database, web_search)
- [ ] 工具调用成功率 > 95%
- [ ] 工具执行并行化 (asyncio.TaskGroup)
- [ ] 响应生成正确集成工具结果
- [ ] 单元测试覆盖 ≥80%
```

### 任务分解

#### Task 2.2.1: LangChain Agent 基础设置
**故事点**: 3
**完成标准**:
- [ ] LangChain v1.0 依赖安装
- [ ] create_agent 初始化
- [ ] Claude Sonnet 4.5 集成
- [ ] Agent 流程测试

```python
# backend/src/services/agent_service.py

from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic

class AgentService:
    """LangChain Agent 服务"""

    def __init__(self, api_key: str):
        self.model = ChatAnthropic(
            model="claude-sonnet-4-5-20250929",
            api_key=api_key
        )

    async def create_agent(
        self,
        tools: list,
        system_prompt: str,
        middleware: list = None
    ):
        """
        创建 Agent

        使用 LangChain v1.0 create_agent()
        """
        agent = create_agent(
            model=self.model,
            tools=tools,
            system_prompt=system_prompt,
            middleware=middleware or []
        )
        return agent

    async def run_agent(
        self,
        agent,
        user_message: str,
        conversation_history: list,
        rag_context: list
    ) -> dict:
        """运行 Agent"""
        # 构建消息列表
        messages = [
            {"role": "user", "content": msg}
            for msg in conversation_history
        ]
        messages.append({"role": "user", "content": user_message})

        # 注入 RAG 上下文
        if rag_context:
            rag_prompt = self._format_rag_context(rag_context)
            messages.append({
                "role": "system",
                "content": f"Relevant documents:\n{rag_prompt}"
            })

        # 运行 Agent
        result = await agent.ainvoke({
            "messages": messages,
            "tools_called": [],
            "tokens_used": 0
        })

        return result

    def _format_rag_context(self, rag_results: list) -> str:
        """格式化 RAG 上下文"""
        formatted = []
        for result in rag_results:
            formatted.append(f"- {result['text']}")
        return "\n".join(formatted)
```

#### Task 2.2.2: search_documents 工具
**故事点**: 3
**完成标准**:
- [ ] 工具定义 (name, description, input schema)
- [ ] RAG 搜索实现
- [ ] 结果格式化
- [ ] 错误处理

```python
# backend/src/services/agent_tools.py

from langchain.tools import tool

@tool
def search_documents(
    query: str,
    user_id: str,
    conversation_id: str,
    limit: int = 5
) -> str:
    """
    Search uploaded documents using semantic similarity (RAG)

    Args:
        query: 用户查询
        user_id: 用户 ID
        conversation_id: 对话 ID
        limit: 返回结果数

    Returns:
        格式化的搜索结果字符串
    """
    # 向量化查询
    query_embedding = embedding_service.embed(query)

    # 搜索相似文档
    results = embedding_repo.search(
        query_embedding=query_embedding,
        user_id=user_id,
        limit=limit,
        threshold=0.7
    )

    # 格式化结果
    formatted = "Found documents:\n"
    for result in results:
        formatted += f"- {result['text'][:200]}... (score: {result['score']:.2f})\n"

    return formatted
```

#### Task 2.2.3: query_database 工具
**故事点**: 3
**完成标准**:
- [ ] 工具定义
- [ ] 安全 SQL 执行 (SELECT only)
- [ ] 结果格式化
- [ ] SQL 注入防护

#### Task 2.2.4: web_search 工具和工具管理
**故事点**: 4
**完成标准**:
- [ ] web_search 工具实现
- [ ] 并行工具执行 (asyncio.TaskGroup)
- [ ] 工具结果合并
- [ ] 错误恢复和重试

---

# 🔧 EPIC 3: 中间件和特性 (Week 3-4)

## Story 3.1: 5 层中间件实现 + 错误处理

**故事点**: 16 (13 + 3 for Task 3.1.4)
**优先级**: P0 (阻塞)
**分配给**: Backend Team
**标签**: middleware, architecture, observability, error-handling

### 任务分解

#### Task 3.1.1: 认证和记忆注入中间件
**故事点**: 4
**完成标准**:
- [ ] AuthenticationMiddleware 实现
- [ ] MemoryInjectionMiddleware 实现
- [ ] 中间件堆栈集成
- [ ] 单元测试

#### Task 3.1.2: 内容审核和响应结构化中间件
**故事点**: 4
**完成标准**:
- [ ] ContentModerationMiddleware 实现
- [ ] ResponseStructuringMiddleware 实现
- [ ] 中间件堆栈集成
- [ ] 单元测试

#### Task 3.1.3: 审计日志中间件和集成
**故事点**: 5
**完成标准**:
- [ ] AuditLoggingMiddleware 实现
- [ ] 结构化日志配置 (JSON)
- [ ] 请求追踪 ID (X-Request-ID)
- [ ] 中间件执行顺序验证 (5 层)
- [ ] 集成测试

#### Task 3.1.4: 中间件错误处理和容错 (A3 补救)
**故事点**: 3
**优先级**: P0 (高)
**完成标准**:
- [ ] 中间件超时处理机制
- [ ] 向量搜索降级策略
- [ ] 异常传播和记录
- [ ] 单元测试 (错误场景覆盖)

**实现指南**:

```python
# backend/src/infrastructure/middleware/error_handling.py

from fastapi import Request
from typing import Callable
import asyncio
from enum import Enum

class FallbackStrategy(str, Enum):
    """中间件失败的降级策略"""
    RETURN_PARTIAL = "return_partial"  # 返回部分结果
    RETRY_ONCE = "retry_once"          # 重试一次
    SKIP_CONTEXT = "skip_context"      # 跳过该上下文
    RETURN_ERROR = "return_error"       # 返回错误

class MemoryInjectionMiddlewareWithErrorHandling:
    """带容错机制的记忆注入中间件"""

    def __init__(self, timeout_ms: int = 200, strategy: FallbackStrategy = FallbackStrategy.SKIP_CONTEXT):
        self.timeout_ms = timeout_ms
        self.strategy = strategy

    async def __call__(self, request: Request, call_next: Callable) -> Any:
        """执行中间件，含错误处理"""
        user_id = request.state.user_id
        body = await request.json()
        conversation_id = body.get("conversation_id")
        user_message = body.get("message")

        try:
            # 设置超时保护
            async with asyncio.timeout(self.timeout_ms / 1000):
                # 并行查询历史和RAG上下文
                async with asyncio.TaskGroup() as tg:
                    history_task = tg.create_task(
                        self._get_conversation_history(conversation_id)
                    )
                    rag_task = tg.create_task(
                        self._search_rag_context(user_message, user_id)
                    )

                request.state.conversation_history = await history_task
                request.state.rag_context = await rag_task
                request.state.memory_error = None

        except asyncio.TimeoutError:
            await logger.aerror(
                "memory_injection_timeout",
                request_id=request.headers.get("X-Request-ID"),
                timeout_ms=self.timeout_ms,
                strategy=self.strategy.value
            )
            await self._apply_fallback_strategy(request, strategy=self.strategy)

        except Exception as exc:
            await logger.aerror(
                "memory_injection_error",
                request_id=request.headers.get("X-Request-ID"),
                error=str(exc),
                strategy=self.strategy.value
            )
            await self._apply_fallback_strategy(request, strategy=self.strategy)

        try:
            return await call_next(request)
        except Exception as exc:
            # 记录在后续中间件中发生的错误
            await logger.aerror(
                "middleware_chain_error",
                request_id=request.headers.get("X-Request-ID"),
                middleware="MemoryInjection",
                error=str(exc)
            )
            raise

    async def _apply_fallback_strategy(self, request: Request, strategy: FallbackStrategy):
        """应用降级策略"""
        if strategy == FallbackStrategy.SKIP_CONTEXT:
            # 跳过RAG上下文，继续处理
            request.state.conversation_history = []
            request.state.rag_context = []
            request.state.memory_error = "rag_context_skipped_due_to_timeout"

        elif strategy == FallbackStrategy.RETURN_PARTIAL:
            # 尝试返回部分结果
            try:
                async with asyncio.timeout(100 / 1000):  # 100ms快速查询
                    history = await self._get_conversation_history(
                        request.json().get("conversation_id")
                    )
                    request.state.conversation_history = history
                    request.state.rag_context = []
                    request.state.memory_error = "rag_context_unavailable"
            except:
                request.state.conversation_history = []
                request.state.rag_context = []

        elif strategy == FallbackStrategy.RETRY_ONCE:
            # 单次重试
            try:
                async with asyncio.timeout(self.timeout_ms / 1000 * 1.5):  # 延长超时
                    await asyncio.sleep(0.1)  # 短暂延迟
                    rag_context = await self._search_rag_context(
                        request.json().get("message"),
                        request.state.user_id
                    )
                    request.state.rag_context = rag_context
                    request.state.memory_error = None
            except:
                request.state.rag_context = []
                request.state.memory_error = "rag_retry_failed"

    async def _get_conversation_history(self, conversation_id: str) -> List[dict]:
        """获取对话历史"""
        # 实现...
        pass

    async def _search_rag_context(self, query: str, user_id: str) -> List[dict]:
        """搜索RAG上下文"""
        # 实现...
        pass

# 中间件测试
@pytest.mark.asyncio
async def test_memory_injection_timeout():
    """测试超时处理"""
    middleware = MemoryInjectionMiddlewareWithErrorHandling(
        timeout_ms=100,
        strategy=FallbackStrategy.SKIP_CONTEXT
    )
    # 验证超时后正确应用降级策略
    pass

@pytest.mark.asyncio
async def test_memory_injection_error_recovery():
    """测试错误恢复"""
    middleware = MemoryInjectionMiddlewareWithErrorHandling(
        timeout_ms=200,
        strategy=FallbackStrategy.RETURN_PARTIAL
    )
    # 验证错误后仍能返回部分结果
    pass
```

**相关配置**:
```python
# backend/.env
MEMORY_INJECTION_TIMEOUT_MS=200          # 内存注入超时
MEMORY_INJECTION_FALLBACK=skip_context   # skip_context|return_partial|retry_once|return_error
VECTOR_SEARCH_TIMEOUT_MS=200             # 向量搜索超时
VECTOR_SEARCH_RETRY_COUNT=1              # 重试次数
```

---

## Story 3.2: API 端点实现

**故事点**: 8
**优先级**: P1 (高)
**分配给**: Backend Team
**标签**: api, endpoints, rest

### 任务分解

#### Task 3.2.1: 对话端点 (POST /conversations, GET /conversations/{id})
**故事点**: 3
**完成标准**:
- [ ] 创建对话端点
- [ ] 获取对话端点
- [ ] 列表对话端点 (分页)
- [ ] 输入验证 (Pydantic)
- [ ] 错误处理

#### Task 3.2.2: 消息端点和 WebSocket
**故事点**: 3
**完成标准**:
- [ ] POST /conversations/{id}/messages 端点
- [ ] WebSocket 端点 /ws/{id}
- [ ] 实时消息流式处理
- [ ] 连接管理和心跳

#### Task 3.2.3: 文档上传和搜索端点
**故事点**: 2
**完成标准**:
- [ ] POST /documents/upload 端点
- [ ] POST /embeddings/search 端点
- [ ] 文件验证和大小限制
- [ ] 异步处理队列

---

## Story 3.3: 特性完成、集成 和 生产就绪性

**故事点**: 8 (5 + 3 for Task 3.3.4)
**优先级**: P1 (高, P0 for Task 3.3.4)
**分配给**: Backend Team
**标签**: features, integration, production-readiness, health-checks

### 任务分解

#### Task 3.3.1: 流式响应实现
**故事点**: 2
**完成标准**:
- [ ] SSE (Server-Sent Events) 支持
- [ ] WebSocket 流实现
- [ ] 流式 Agent 响应
- [ ] 前端流处理

#### Task 3.3.2: 错误处理和恢复
**故事点**: 2
**完成标准**:
- [ ] 全局异常处理器
- [ ] 错误响应格式
- [ ] 重试机制
- [ ] 优雅降级

#### Task 3.3.3: 后端集成测试
**故事点**: 1
**完成标准**:
- [ ] 端到端对话流程测试
- [ ] RAG 集成测试
- [ ] 中间件堆栈测试
- [ ] 性能基准测试

#### Task 3.3.4: 优雅关闭和健康检查端点 (A8 补救 - Principle #7)
**故事点**: 3
**优先级**: P0 (生产就绪性)
**完成标准**:
- [ ] 健康检查端点 `/health` 实现
- [ ] SIGTERM 信号处理器
- [ ] 优雅关闭流程
- [ ] 连接清理和资源释放
- [ ] 单元和集成测试

**实现指南**:

```python
# backend/src/infrastructure/health.py

from fastapi import FastAPI, HTTPException
from typing import Dict, Any
import asyncio
import signal

class HealthChecker:
    """系统健康检查"""

    def __init__(self, app: FastAPI):
        self.app = app
        self.is_shutting_down = False

    async def check_database(self) -> Dict[str, Any]:
        """检查数据库连接"""
        try:
            async with AsyncSessionLocal() as session:
                # 执行简单查询
                await session.execute(text("SELECT 1"))
            return {"status": "healthy", "latency_ms": 0}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def check_vector_store(self) -> Dict[str, Any]:
        """检查向量存储 (pgvector)"""
        try:
            async with AsyncSessionLocal() as session:
                # 验证pgvector扩展
                result = await session.execute(
                    text("SELECT extname FROM pg_extension WHERE extname='vector'")
                )
                if result.fetchone():
                    return {"status": "healthy", "extension": "pgvector"}
                else:
                    return {"status": "unhealthy", "error": "pgvector extension not installed"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def check_redis(self) -> Dict[str, Any]:
        """检查Redis连接 (缓存)"""
        try:
            # 尝试ping Redis
            await redis_client.ping()
            return {"status": "healthy"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def check_llm_api(self) -> Dict[str, Any]:
        """检查LLM API连接"""
        try:
            # 调用Anthropic API
            response = await anthropic_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=10,
                messages=[{"role": "user", "content": "ping"}]
            )
            return {"status": "healthy", "model": "claude-sonnet-4-5-20250929"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def get_health_status(self) -> Dict[str, Any]:
        """获取完整的健康状态"""
        if self.is_shutting_down:
            return {
                "status": "shutting_down",
                "timestamp": datetime.utcnow().isoformat()
            }

        # 并行检查所有服务
        async with asyncio.TaskGroup() as tg:
            db_task = tg.create_task(self.check_database())
            vector_task = tg.create_task(self.check_vector_store())
            redis_task = tg.create_task(self.check_redis())
            llm_task = tg.create_task(self.check_llm_api())

        db_status = await db_task
        vector_status = await vector_task
        redis_status = await redis_task
        llm_status = await llm_task

        # 计算总体状态
        all_healthy = all([
            db_status["status"] == "healthy",
            vector_status["status"] == "healthy",
            redis_status["status"] == "healthy",
            llm_status["status"] == "healthy"
        ])

        return {
            "status": "healthy" if all_healthy else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "database": db_status,
                "vector_store": vector_status,
                "redis": redis_status,
                "llm_api": llm_status
            }
        }

# 优雅关闭处理
class GracefulShutdownHandler:
    """优雅关闭处理器"""

    def __init__(self, app: FastAPI, shutdown_timeout_seconds: int = 30):
        self.app = app
        self.shutdown_timeout = shutdown_timeout_seconds
        self.active_requests = 0
        self.lock = asyncio.Lock()

    async def on_startup(self):
        """应用启动"""
        await logger.ainfo("app_starting", version="1.0.0")

    async def on_shutdown(self):
        """应用关闭 - SIGTERM处理"""
        await logger.ainfo("app_shutdown_initiated", timeout_seconds=self.shutdown_timeout)

        # 等待活跃请求完成（最多30秒）
        start_time = time.time()
        while self.active_requests > 0:
            elapsed = time.time() - start_time
            if elapsed > self.shutdown_timeout:
                await logger.awarn(
                    "shutdown_timeout_exceeded",
                    active_requests=self.active_requests,
                    elapsed_seconds=elapsed
                )
                break

            await logger.ainfo(
                "waiting_for_requests_completion",
                active_requests=self.active_requests,
                elapsed_seconds=elapsed
            )
            await asyncio.sleep(1)

        # 清理资源
        await self._cleanup_resources()
        await logger.ainfo("app_shutdown_complete")

    async def _cleanup_resources(self):
        """清理数据库连接、缓存等"""
        try:
            # 关闭数据库引擎
            if engine:
                await engine.dispose()

            # 关闭Redis连接
            if redis_client:
                await redis_client.close()

            # 其他清理操作
            await logger.ainfo("all_resources_cleaned_up")
        except Exception as e:
            await logger.aerror("resource_cleanup_error", error=str(e))

    def track_request_start(self):
        """请求开始"""
        self.active_requests += 1

    def track_request_end(self):
        """请求结束"""
        self.active_requests = max(0, self.active_requests - 1)

# FastAPI应用集成
def setup_health_and_shutdown(app: FastAPI):
    """设置健康检查和优雅关闭"""

    health_checker = HealthChecker(app)
    shutdown_handler = GracefulShutdownHandler(app)

    # 注册启动和关闭事件
    app.add_event_handler("startup", shutdown_handler.on_startup)
    app.add_event_handler("shutdown", shutdown_handler.on_shutdown)

    # 健康检查端点
    @app.get("/health", tags=["monitoring"])
    async def health_check() -> Dict[str, Any]:
        """健康检查端点 - 机器可读"""
        status = await health_checker.get_health_status()

        # 设置HTTP状态码
        if status["status"] == "healthy":
            return status
        elif status["status"] == "degraded":
            raise HTTPException(status_code=503, detail=status)
        else:  # shutting_down
            raise HTTPException(status_code=503, detail=status)

    @app.get("/health/live", tags=["monitoring"])
    async def liveness_probe() -> Dict[str, str]:
        """存活性探针 - Kubernetes用"""
        if shutdown_handler.active_requests < 0:
            raise HTTPException(status_code=500)
        return {"status": "alive"}

    @app.get("/health/ready", tags=["monitoring"])
    async def readiness_probe() -> Dict[str, str]:
        """就绪性探针 - Kubernetes用"""
        status = await health_checker.get_health_status()
        if status["status"] == "healthy":
            return {"status": "ready"}
        else:
            raise HTTPException(status_code=503, detail="Not ready")

    # 请求跟踪中间件
    @app.middleware("http")
    async def track_requests(request: Request, call_next):
        """追踪活跃请求数"""
        shutdown_handler.track_request_start()
        try:
            return await call_next(request)
        finally:
            shutdown_handler.track_request_end()

    # 注册SIGTERM处理器
    def handle_sigterm():
        """处理SIGTERM信号"""
        asyncio.create_task(app.router.shutdown())

    signal.signal(signal.SIGTERM, lambda signum, frame: handle_sigterm())

# 测试
@pytest.mark.asyncio
async def test_health_check_all_healthy():
    """测试健康检查 - 所有服务正常"""
    checker = HealthChecker(mock_app)
    status = await checker.get_health_status()

    assert status["status"] == "healthy"
    assert status["checks"]["database"]["status"] == "healthy"
    assert status["checks"]["vector_store"]["status"] == "healthy"

@pytest.mark.asyncio
async def test_graceful_shutdown():
    """测试优雅关闭"""
    handler = GracefulShutdownHandler(mock_app, shutdown_timeout_seconds=5)

    # 模拟活跃请求
    handler.active_requests = 3
    await handler.on_shutdown()

    # 验证资源已清理
    assert handler.active_requests >= 0
```

**Kubernetes 集成** (部署用):
```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: langchain-ai-api
spec:
  template:
    spec:
      containers:
      - name: api
        image: langchain-ai:latest

        # 健康检查配置
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3

        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2

        # 优雅关闭
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 15"]  # 给时间完成请求

        terminationGracePeriodSeconds: 45  # 45秒超时
```

**监控和告警**:
```prometheus
# prometheus/rules.yaml
groups:
  - name: api_health
    rules:
      - alert: APIUnhealthy
        expr: up{job="langchain-api"} == 0
        for: 1m
        annotations:
          summary: "API is unhealthy"

      - alert: HighActiveRequests
        expr: active_requests > 1000
        for: 5m
        annotations:
          summary: "High number of active requests"

      - alert: DatabaseUnhealthy
        expr: health_check_database_status != 1
        for: 2m
        annotations:
          summary: "Database connection failed"
```

---

# 🎨 EPIC 4: 前端开发 (Week 4-5)

## Story 4.1: 基础 UI 组件

**故事点**: 13
**优先级**: P1 (高)
**分配给**: Frontend Team
**标签**: ui, components, tailark

### 任务分解

#### Task 4.1.1: 聊天界面和消息显示
**故事点**: 5
**完成标准**:
- [ ] ChatInterface 主组件
- [ ] ChatMessage 消息组件
- [ ] MessageList 列表组件
- [ ] TypingIndicator 输入指示器
- [ ] Tailark Hero 集成

#### Task 4.1.2: 消息输入和表单
**故事点**: 3
**完成标准**:
- [ ] ChatInput 输入框
- [ ] 表情和附件支持
- [ ] 表单验证 (React Hook Form + Zod)
- [ ] 提交处理

#### Task 4.1.3: 对话管理 UI
**故事点**: 5
**完成标准**:
- [ ] ConversationList 列表
- [ ] ConversationHeader 头部
- [ ] 对话创建对话框
- [ ] 对话删除确认
- [ ] 搜索和过滤

---

## Story 4.2: 文档管理和高级特性

**故事点**: 8
**优先级**: P1 (高)
**分配给**: Frontend Team
**标签**: ui, file-upload, features

### 任务分解

#### Task 4.2.1: 文档上传界面
**故事点**: 3
**完成标准**:
- [ ] FileDropZone 拖拽区域
- [ ] DocumentUploadForm 上传表单
- [ ] UploadProgress 进度条
- [ ] 文件验证反馈

#### Task 4.2.2: 实时通信集成
**故事点**: 3
**完成标准**:
- [ ] Socket.IO 连接
- [ ] 消息接收处理
- [ ] 错误重新连接
- [ ] 连接状态显示

#### Task 4.2.3: 状态管理和数据获取
**故事点**: 2
**完成标准**:
- [ ] Zustand store 创建
- [ ] TanStack Query 集成
- [ ] API 客户端服务
- [ ] 缓存策略

---

## Story 4.3: 样式和优化

**故事点**: 5
**优先级**: P2 (中)
**分配给**: Frontend Team
**标签**: styling, performance, ux

### 任务分解

#### Task 4.3.1: Tailwind 样式和响应式设计
**故事点**: 2
**完成标准**:
- [ ] Tailwind 配置
- [ ] 响应式布局 (mobile, tablet, desktop)
- [ ] 深色模式支持
- [ ] 动画和过渡

#### Task 4.3.2: 性能优化和 SEO
**故事点**: 2
**完成标准**:
- [ ] 代码分割 (Code Splitting)
- [ ] 图片优化
- [ ] 路由懒加载
- [ ] 生产构建优化

#### Task 4.3.3: 可访问性和用户体验
**故事点**: 1
**完成标准**:
- [ ] ARIA 标签
- [ ] 键盘导航
- [ ] 对比度检查
- [ ] 用户反馈 (Toast)

---

# 🧪 EPIC 5: 测试和优化 (Week 5-6)

## Story 5.1: 单元和集成测试

**故事点**: 13
**优先级**: P0 (阻塞)
**分配给**: QA Team
**标签**: testing, quality, coverage

### 任务分解

#### Task 5.1.1: 后端单元测试
**故事点**: 5
**完成标准**:
- [ ] Services 单元测试 (≥90%)
- [ ] Repositories 单元测试 (≥90%)
- [ ] Models 验证测试
- [ ] 单元测试运行成功
- [ ] 覆盖率报告生成

#### Task 5.1.2: 后端集成测试
**故事点**: 4
**完成标准**:
- [ ] API 端点测试
- [ ] 中间件流程测试
- [ ] RAG 流程测试
- [ ] Agent 执行测试

#### Task 5.1.3: 前端单元和 E2E 测试
**故事点**: 4
**完成标准**:
- [ ] 组件单元测试 (Jest)
- [ ] Hooks 单元测试
- [ ] Utils 单元测试
- [ ] E2E 测试 (Playwright)

---

## Story 5.2: 性能优化

**故事点**: 8
**优先级**: P1 (高)
**分配给**: Backend + Frontend Team
**标签**: performance, optimization

### 任务分解

#### Task 5.2.1: 数据库和查询优化
**故事点**: 3
**完成标准**:
- [ ] 查询性能分析
- [ ] 索引优化验证
- [ ] N+1 问题修复
- [ ] 缓存策略实现 (Redis)

#### Task 5.2.2: API 响应时间优化
**故事点**: 3
**完成标准**:
- [ ] 简单查询 ≤500ms
- [ ] RAG 查询 ≤2000ms
- [ ] 向量搜索 ≤200ms
- [ ] 负载测试验证

#### Task 5.2.3: 前端性能优化
**故事点**: 2
**完成标准**:
- [ ] 包大小优化
- [ ] 首屏加载时间 ≤3s
- [ ] Lighthouse 评分 ≥90
- [ ] Core Web Vitals

---

## Story 5.3: 代码质量和文档

**故事点**: 5
**优先级**: P1 (高)
**分配给**: Entire Team
**标签**: quality, documentation, testing

### 任务分解

#### Task 5.3.1: 类型检查和 Linting
**故事点**: 2
**完成标准**:
- [ ] mypy --strict 通过 (0 errors)
- [ ] pylint/flake8 无错误
- [ ] eslint/prettier 通过
- [ ] 代码审查

#### Task 5.3.2: 文档编写
**故事点**: 2
**完成标准**:
- [ ] API 文档 (Swagger/OpenAPI)
- [ ] README 和快速开始
- [ ] 开发指南
- [ ] 部署指南

#### Task 5.3.3: 安全审计
**故事点**: 1
**完成标准**:
- [ ] 安全扫描 (SAST)
- [ ] 依赖漏洞检查
- [ ] 无 SQL 注入漏洞
- [ ] 无 XSS 漏洞

---

# 🚀 EPIC 6: 部署和上线 (Week 6-7)

## Story 6.1: 部署准备和 CI/CD

**故事点**: 8
**优先级**: P0 (阻塞)
**分配给**: DevOps + Backend Lead
**标签**: deployment, ci-cd, docker

### 任务分解

#### Task 6.1.1: Docker 和镜像构建
**故事点**: 2
**完成标准**:
- [ ] Dockerfile 创建和测试
- [ ] Docker 镜像构建成功
- [ ] 镜像大小优化
- [ ] 镜像推送到仓库

#### Task 6.1.2: GitHub Actions CI/CD
**故事点**: 3
**完成标准**:
- [ ] 自动化测试流程
- [ ] 自动化构建流程
- [ ] 自动化部署流程 (Coolify)
- [ ] CI/CD 流程验证

#### Task 6.1.3: 监控和告警配置
**故事点**: 3
**完成标准**:
- [ ] Prometheus 指标配置
- [ ] Grafana 仪表板创建
- [ ] 告警规则配置
- [ ] 监控验证

---

## Story 6.2: 生产部署

**故事点**: 5
**优先级**: P0 (阻塞)
**分配给**: DevOps + Backend Lead
**标签**: deployment, production, coolify

### 任务分解

#### Task 6.2.1: 测试环境部署
**故事点**: 2
**完成标准**:
- [ ] Coolify 配置
- [ ] 数据库初始化
- [ ] 环境变量设置
- [ ] 部署验证

#### Task 6.2.2: 生产部署和验证
**故事点**: 3
**完成标准**:
- [ ] 金丝雀部署 (5% 流量)
- [ ] 监控验证
- [ ] 健康检查通过
- [ ] 全量部署

---

# 📊 Story 优先级和时间线

## 按优先级排序

### P0 (阻塞 - Week 1-4)
1. Story 1.1: 数据库设计 (5 pts, Day 1-5)
2. Story 1.2: 异步存储库 (8 pts, Day 6-12)
3. Story 1.3: API 框架 (5 pts, Day 13-14)
4. Story 2.1: RAG 管道 (13 pts, Day 15-23)
5. Story 2.2: Agent 实现 (13 pts, Day 24-32)
6. Story 3.1: 中间件 (13 pts, Day 33-40)
7. Story 6.1: 部署准备 (8 pts, Day 41-42)
8. Story 6.2: 生产部署 (5 pts, Day 43-42)

### P1 (高 - Week 4-6)
1. Story 3.2: API 端点 (8 pts, Day 33-37)
2. Story 3.3: 特性完成 (5 pts, Day 38-40)
3. Story 4.1: UI 组件 (13 pts, Day 41-50)
4. Story 4.2: 文档管理 (8 pts, Day 51-55)
5. Story 5.1: 测试 (13 pts, Day 56-65)
6. Story 5.2: 性能优化 (8 pts, Day 66-71)

### P2 (中 - Week 5-6)
1. Story 4.3: 样式优化 (5 pts, Day 56-60)
2. Story 5.3: 代码质量 (5 pts, Day 71-75)

---

# 📋 完成标准 (Definition of Done)

每个 Story/Task 完成必须满足:

- [ ] 代码实现完成
- [ ] 单元测试通过且覆盖率符合要求
- [ ] 集成测试通过
- [ ] mypy --strict 通过
- [ ] Linting 无错误
- [ ] 代码审查通过 (≥1 reviewer)
- [ ] 文档更新完成
- [ ] 相关监控/告警已配置
- [ ] 性能指标符合目标
- [ ] 没有新的安全漏洞

---

# 🔗 依赖关系

```
Story 1.1 (数据库)
    ↓
Story 1.2 (存储库) → Story 2.1 (RAG) → Story 2.2 (Agent)
    ↓                      ↓             ↓
Story 1.3 (API框架) → Story 3.1 (中间件) → Story 3.2 (端点) → Story 3.3 (集成)
                                              ↓
                                          Story 4.1 (前端) → Story 4.2 (高级) → Story 4.3 (样式)
                                              ↓
                                          Story 5.1 (测试) → Story 5.2 (性能) → Story 5.3 (质量)
                                              ↓
                                          Story 6.1 (CI/CD) → Story 6.2 (部署)
```

---

# 📊 总体工作量估算

| Epic | Story | Points | 工作日 | 开始 | 结束 |
|------|-------|--------|--------|------|------|
| 1 | 1.1 | 5 | 2.5 | D1 | D5 |
| 1 | 1.2 | 8 | 4 | D6 | D12 |
| 1 | 1.3 | 5 | 2.5 | D13 | D15 |
| 2 | 2.1 | 13 | 6.5 | D16 | D23 |
| 2 | 2.2 | 13 | 6.5 | D24 | D32 |
| 3 | 3.1 | 13 | 6.5 | D33 | D40 |
| 3 | 3.2 | 8 | 4 | D33 | D37 |
| 3 | 3.3 | 5 | 2.5 | D38 | D40 |
| 4 | 4.1 | 13 | 6.5 | D41 | D50 |
| 4 | 4.2 | 8 | 4 | D51 | D55 |
| 4 | 4.3 | 5 | 2.5 | D56 | D60 |
| 5 | 5.1 | 13 | 6.5 | D56 | D65 |
| 5 | 5.2 | 8 | 4 | D66 | D71 |
| 5 | 5.3 | 5 | 2.5 | D72 | D75 |
| 6 | 6.1 | 8 | 4 | D76 | D80 |
| 6 | 6.2 | 5 | 2.5 | D81 | D83 |
| **总计** | **16** | **138** | **69** | **D1** | **D45** |

**更新**: +11 故事点 (3 个 A级补救任务):
- Task 3.1.4: 中间件错误处理 (+3 pts)
- Task 2.1.5: 长对话总结 (+5 pts)
- Task 3.3.4: 优雅关闭和健康检查 (+3 pts)
- 总计: 127 → **138 故事点** | 63.5 → **69 工作日** | 6-7 周 → **~7.5 周**

**日期**:
- 1 Story Point = 0.5 工作日
- 每周 5 个工作日
- 总计: ~3 周半完成基础功能，加上 1.5 周测试和部署

---

**任务分解版本**: 1.0.0
**最后更新**: 2025-11-16
**状态**: 📋 Ready for Development
**下一步**: 按优先级开始实现 Story 1.1

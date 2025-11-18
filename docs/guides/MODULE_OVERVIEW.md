# 代码模块功能说明

以下按功能域梳理 `src/` 核心模块，帮助快速理解 LangChain AI Conversation 后端。每个条目都附带主要文件与职责，可配合 `CLAUDE code` 的上下文搜索。

## 1. FastAPI 应用层
- `src/main.py`
  - 定��� FastAPI 应用、CORS、生命周期钩子与全局异常处理。
  - 挂载自定义中间件（认证、记忆注入、内容安全、统一响应、审计）并注册路由。
  - 暴露健康检查、根路由及 uvicorn 启动入口。
  - **Phase 1 增强** (✨)：
    - 初始化 asyncpg 连接池用于语义缓存（src/main.py:42-61）
    - 初始化 SemanticCacheService 并注入全局 getter（src/main.py:64-76）
    - 启动缓存统计更新器（30 秒间隔）(src/main.py:73-76)
    - 注册 Prometheus /metrics ��点（src/main.py:270-279）
    - 优雅关闭处理：清理数据库连接池与缓存统计任务（src/main.py:98-103）

## 2. API 路由
- `src/api/conversation_routes.py`
  - 提供会话 CRUD、历史查询与发送消息 REST 接口。
  - **Epic 2 增强** (✨)：自动触发对话总结检查（超过 6000 token）
  - **Phase 1 增强** (✨)：
    - 新增 `ChatRequest` 与 `ChatResponse` Pydantic 模型（src/api/conversation_routes.py:33-66）
    - 新增 `POST /api/conversations/v1/chat` 端点，支持语义缓存（src/api/conversation_routes.py:450-523）
    - 支持 `enable_cache` 参数控制缓存启用、A/B 测试
    - 记录缓存命中/未命中及延迟指标
- `src/api/cache_admin_routes.py` (Phase 1 新增 ✨)
  - **模块用途**：提供缓存管理与监控的管理端点
  - **核心端点**：
    - `GET /api/admin/cache/stats` (src/api/cache_admin_routes.py:45-120) - 返回缓存统计信息（命中数、条目数、命中率、表大小等）
    - `GET /api/admin/cache/health` (src/api/cache_admin_routes.py:123-157) - 缓存健康检查及诊断信息
    - `POST /api/admin/cache/invalidate` (src/api/cache_admin_routes.py:160-205) - 灵活清理缓存（按 query_id、model_name、时间范围）
    - `POST /api/admin/cache/clear` (src/api/cache_admin_routes.py:208-235) - 全量清空缓存
  - **Pydantic 模型**：
    - `CacheStatsResponse` - 缓存统计响应（11+ 字段）
    - `CacheHealthResponse` - 健康检查响应
    - `InvalidateCacheRequest` - 清理请求（灵活条件）
    - `InvalidateCacheResponse` - 清理结果
  - **集成**：依赖 `SemanticCacheService` 获取实时统计
- `src/api/message_routes.py`
  - 针对单条消息进行读取、更新工具结果/Token 以及硬删除。
- `src/api/document_routes.py` (Epic 2 ✨)
  - 文档上传、分页、摘要、软删除、**语义搜索与 chunk 拉取**。
  - 新增端点：
    - `POST /documents/upload` - 异步文件上传与处理
    - `POST /documents/search` - RAG 语义相似性搜索
    - `GET /documents/{id}/chunks` - 获取文档分块
- `src/api/tools_routes.py`
  - 列出可用 LangChain 工具，提供受保护的工具执行端点。
  - **Epic 2 新增** (✨)：支持 DuckDuckGo web_search 工具
- `src/api/websocket_routes.py`
  - 管理实时会话 WebSocket：验证、上下文加载、消息处理、心跳。
  - **Epic 2 增强** (✨)：
    - 新增事件类型：`tool_call`, `tool_result`, `complete_state`
    - 支持并行工具执行与结果流式推送

## 3. 数据库与 ORM
- `src/db/config.py`, `src/db/migrations.py`, `src/db/base.py`
  - 配置 async SQLAlchemy + PostgreSQL/pgvector，提供 session 依赖。
  - 初始化表、启用 pgvector、建立 HNSW 索引及 embeddings 按月分区。
- `src/models/*.py`
  - 定义 Conversation、Message、Document、Embedding ORM。
  - **Epic 2 增强** (✨)：
    - `Document` - 新增 `total_chunks`, `meta` (JSONB) 字段
    - `Embedding` - 使用 pgvector Vector(1536)，支持 HNSW 索引
- `src/repositories/*.py`
  - 封装会话/消息/文档/向量的常用查询、计数、软删除、搜索等。
  - **Epic 2 新增** (✨)：
    - `EmbeddingRepository.search()` - pgvector 余弦相似性搜索（P99 ≤200ms）
    - `EmbeddingRepository.batch_insert()` - 批量向量存储
    - `DocumentRepository` - 文档生命周期管理

## 4. 服务层
- `ConversationService`
  - 组合仓储实现会话生命周期、消息写入、上下文聚合。
- `DocumentService` + `DocumentChunker` (Epic 2 ✨)
  - Token-based 文档分割（tiktoken，1000 token 块大小，200 token 重叠）
  - 支持 PDF/TXT/MD 文件加载与处理
  - 文档生命周期管理：上传、分块、向量化、软删除
  - 异步并行处理：使用 `asyncio.TaskGroup` 并行分块和向量化
- `EmbeddingService` (Epic 2 ✨)
  - OpenAI text-embedding-3-small 集成（1536 维）
  - 单文本与批量向量化：`embed_text()`, `embed_batch()`
  - 包含重试机制（3 次）、成本监控、错误处理
- `EmbeddingRepository` (Epic 2 ✨)
  - pgvector 存储与检索：`store_embedding()`, `batch_insert()`, `search()`
  - RAG 相似性搜索：余弦距离（cosine similarity），P99 ≤200ms
  - Redis 缓存策略：搜索结果缓存
- `CachedRAGService` (Phase 1 新增 ✨)
  - **模块用途**：语义缓存集成的 RAG 查询管道服务
  - **核心类与方法**：
    - `RAGResponse` (src/services/cached_rag.py:17-26) - RAG 响应数据类（response_text, cached, latency_ms, cache_distance 等）
    - `CachedRAGService` (src/services/cached_rag.py:29-267) - 主服务类
      - `async query()` (src/services/cached_rag.py:62-186) - 主 RAG 查询管道：编码 → 搜索 → 缓存查找 → 生成/返回 → 缓存
      - `async _search_documents()` (src/services/cached_rag.py:188-229) - 向量相似性搜索（Lantern HNSW 索引）
      - `_build_prompt()` (src/services/cached_rag.py:231-267) - 构建 LLM 提示
  - **集成依赖**：
    - OpenAI embeddings (text-embedding-3-small, 1536-dim)
    - Claude 3.5 Sonnet LLM (claude-3-5-sonnet-20241022)
    - SemanticCacheService 用于缓存查找/存储
    - Prometheus 指标记录（缓存命中/未命中）
  - **性能指标**：
    - 缓存命中：~300ms（避免 LLM 调用）
    - 缓存未命中：~850ms（完整管道）
    - 预期命中率：40-60%（生产环境）
  - **全局单例**：`get_rag_service()`, `reset_rag_service()`
- `SemanticCacheService` (Phase 1 增强 ✨)
  - **增强方法**：
    - `async invalidate_cache()` (src/services/semantic_cache.py) - 灵活清理缓存（按 query_id、model_name、年龄，或全清）
    - `async get_cache_stats()` - 返回 11+ 统计字段（命中数、条目数、表大小、命中率等）
  - **两阶段缓存验证**：向量相似性 (L2 < 0.05) + 上下文文档哈希验证
  - **TTL 管理**：24 小时自动过期清理
- `AgentService` (Epic 2 ✨)
  - 使用 LangChain v1.0 ChatOpenAI (gpt-4-turbo) 构建带工具的代理
  - 核心方法：`run_agent()` 单次推理，`stream_message()` 流式推理
  - 工具集成（新增）：
    - `search_documents_tool()` - RAG 语义搜索（Task 2.2.2）
    - `query_database_tool()` - 安全 SQL 查询，SELECT-only（Task 2.2.3）
    - `web_search_tool()` - DuckDuckGo 网络搜索（Task 2.2.4）
  - 工具结果聚合与流式推送；支持并行工具执行（`asyncio.TaskGroup`）
- `ConversationSummarizationService` (Epic 2 ✨)
  - 自动对话总结：6000 token 阈值触发
  - 保留最近 10 条消息，其余生成摘要
  - 使用 Claude Sonnet 4.5 生成摘要，防止 token 膨胀
  - 方法：`check_and_summarize()`, `inject_summary_into_context()`
- `create_agent.ManagedAgent`
  - 通用代理封装，允许插入 AgentMiddleware 实现成本跟踪、记忆注入等钩子。
- `services/middleware/*`
  - AgentMiddleware 抽象，以及 `CostTrackingMiddleware`、`MemoryInjectionMiddleware` 示例实现。
- `tool_schemas.py`
  - 定义 search_documents/query_database/web_search 工具输入/输出 Pydantic Schema。
- `financial_content_handler.py` & `content_blocks_parser.py`
  - 统一解析多模型 content blocks，抽取金融洞察、校验工具调用；示例见 `src/examples/financial_analysis_examples.py`。

## 5 基础设施监控模块 (Phase 1 新增 ✨)
- `src/infrastructure/cache_metrics.py`
  - **模块用途**：Prometheus 指标定义与记录，用于语义缓存监控
  - **核心指标定义**（17+ 指标）：
    - **计数器 (Counter)**：
      - `llm_cache_hits_total` - 总缓存命中数（按 model, cache_type）
      - `llm_cache_misses_total` - 总缓存未命中数（按 model, cache_type）
      - `llm_cached_responses_served` - 从缓存服务的响应数（按 model）
    - **直方图 (Histogram)**：
      - `llm_cache_hit_latency_ms` - 缓存命中延迟（按 model，9 个 bucket）
      - `llm_cache_miss_latency_ms` - 缓存未命中延迟（按 model，9 个 bucket）
      - `llm_query_latency_ms` - 总查询延迟（按 model, cached）
      - `llm_embedding_latency_ms` - 嵌入生成延迟（按 model）
      - `llm_vector_search_latency_ms` - 向量搜索延迟（按 model）
      - `llm_generation_latency_ms` - LLM 生成延迟（按 model）
      - `llm_cache_distance` - 语义相似度距离（按 model）
    - **仪表盘 (Gauge)**：
      - `llm_cache_size_entries` - 缓存条目数（按 model）
      - `llm_cache_hit_rate` - 命中率百分比 0-100（按 model）
      - `llm_cache_table_size_bytes` - 缓存表大小（按 model）
  - **核心函数**：
    - `record_cache_hit()` (src/infrastructure/cache_metrics.py) - 记录缓存命中事件
    - `record_cache_miss()` (src/infrastructure/cache_metrics.py) - 记录缓存未命中事件与延迟分解
    - `update_cache_stats()` (src/infrastructure/cache_metrics.py) - 更新缓存统计仪表盘
    - `get_metrics_summary()` (src/infrastructure/cache_metrics.py) - 获取指标摘要
  - **注册表**：`cache_registry` - 独立的 Prometheus 注册表，用于缓存指标隔离

- `src/infrastructure/cache_stats_updater.py`
  - **模块用途**：后台定期更新缓存统计信息到 Prometheus 仪表盘
  - **核心类**：
    - `CacheStatsUpdater` (src/infrastructure/cache_stats_updater.py:11-150) - 主更新器类
      - `async start()` - 启动后台更新任务
      - `async stop()` - 优雅关闭更新任务
      - `async _update_loop()` - 主更新循环（可配置间隔，默认 30s）
      - `async _update_stats()` - 从数据库获取统计并更新指标
      - `_parse_size()` - 解析人类可读的大小字符串（如 "256 MB" → 268435456 bytes）
  - **全局函数**：
    - `get_cache_stats_updater()` - 获取或创建全局单例
    - `start_cache_stats_updater()` - 启动后台任务
    - `stop_cache_stats_updater()` - 停止后台任务
  - **集成**：与 SemanticCacheService 集成，从缓存统计视图获取实时数据

## 6 测试验证模块
- `src/test_verification/example_module.py`
  - **模块用途**：用于验证 CLAUDE 模块文档更新规则的生效，演示新功能模块的标准结构
  - **核心类与函数**：
    - `ExampleData` (src/test_verification/example_module.py:18) - 示例数据模型，使用 Pydantic BaseModel
    - `ExampleService` (src/test_verification/example_module.py:26) - 示例服务类，包含完整的 CRUD 操作
      - `create()` (src/test_verification/example_module.py:43) - 创建新的数据记录
      - `read()` (src/test_verification/example_module.py:56) - 读取指定 ID 的数据记录
      - `update()` (src/test_verification/example_module.py:68) - 更新指定 ID 的数据记录
      - `delete()` (src/test_verification/example_module.py:84) - 删除指定 ID 的数据记录
    - `example_helper()` (src/test_verification/example_module.py:100) - 辅助函数示例，演示简单的字符串处理
  - **设计模式**：演示服务层代码组织、数据模型定义与内存存储的基本实现

## 7. 中间件层
- `AuthenticationMiddleware`
  - 拦截请求验证 JWT，向 `request.state` 注入 `user_id`。
- `MemoryInjectionMiddleware`
  - 捕获发送消息请求体，写入记忆上下文供后续 handler 使用。
- `ContentModerationMiddleware`
  - 实现 per-user 速率限制与基础内容校验。
- `ResponseStructuringMiddleware`
  - 将 JSON 响应统一封装 `{success,data,error,timestamp,request_id}` 结构。
- `AuditLoggingMiddleware`
  - 记录请求起止、耗时、错误，并对 >1s 慢请求预警。

## 8. 文档与工具
- `src/utils/file_handler.py`
  - 文件类型检测、PDF/TXT/DOCX/CSV 文本抽取与上传校验。
- `src/examples/financial_analysis_examples.py`
  - 展示如何消费 FinancialContentBlockHandler，进行股票/投资组合分析。

## 使用方式
- 查阅特定功能时，可先定位本文件对应模块，再结合源文件阅读实现细节。
- 若需扩展 Agent 或中间件，优先参考服务层与 `services/middleware` 钩子定义。

## 9. 后端骨架
- `src/main.py`、`src/db/config.py`
  - 启动时初始化 pgvector、注册中间件、统一日志/异常处理，构成 FastAPI 应用骨架。
- 健康检查、根路由与 CORS 配置集中于主入口，便于部署时统一管理。

## 10. 对话与消息流程
- `src/api/conversation_routes.py` + `ConversationService`
  - 会话创建、分页、详情、软删除、历史/上下文聚合。
- `src/api/message_routes.py` + `MessageRepository`
  - 单条消息读/写/删、工具结果回写、token 统计。
- `src/api/websocket_routes.py:387-470`
  - 消费 `AgentService.stream_message` 事件流，实时转发 chunk、tool_call/tool_result，拿到 `complete_state` 后落库并发送完成事件，替代原先的字符串切片“模拟 streaming”。

## 11. 文档 & RAG 管线 (Epic 2 ✨ 完整实现)
- `src/api/document_routes.py` + `DocumentService` + `DocumentChunker`
  - **上传端点** `POST /documents/upload` - 异步文件处理，支持 PDF/TXT/MD
  - **分块处理** - Token-based 分割（tiktoken，1000 token 块，200 token 重叠）
  - **嵌入生成** - OpenAI text-embedding-3-small（1536 维）
  - **软删除** - 文档及其 embeddings 级联删除
  - **语义搜索** `POST /documents/search` - pgvector 余弦相似性搜索（P99 ≤200ms）
  - **Chunk 拉取** `GET /documents/{id}/chunks` - 分页获取文档分块
- `src/services/embedding_service.py` + `EmbeddingRepository`
  - **OpenAI 向量化** - 单文本与批量处理，包含重试机制（3 次）
  - **批量存储** - `batch_insert()` 高效存储向量到 pgvector
  - **相似性搜索** - pgvector `<->` 操作符（余弦距离），Redis 缓存策略

## 12. 智能体与工具 (Epic 2 ✨ 完整实现)
- `src/services/agent_service.py`
  - **LangChain v1.0 集成** - 使用 ChatOpenAI(gpt-4-turbo) + create_agent() API
  - **流式推理** - `stream_message()` 返回 `AsyncIterator[str]`，支持实时响应
  - **三个工具集成**（Epic 2 新增）：
    - `search_documents_tool()` - RAG 语义搜索（Task 2.2.2）
    - `query_database_tool()` - 安全 SQL 查询，SELECT-only（Task 2.2.3）
    - `web_search_tool()` - DuckDuckGo 网络搜索（Task 2.2.4）
  - **并行工具执行** - `asyncio.TaskGroup` 同时运行多个工具，P99 ≤200ms
  - **工具结果聚合** - 合并所有工具输出，注入 Agent 上下文
  - **消息构造** - 重构对话历史、RAG 上下文、总结注入
  - **流式 WebSocket 推送** - 逐块推送内容、工具调用、执行结果
- `src/services/conversation_summarization_service.py` (Epic 2 新增)
  - **自动总结** - 6000 token 阈值触发
  - **保留策略** - 保留最近 10 条消息，其余生成摘要
  - **总结生成** - 使用 Claude Sonnet 4.5，防止 token 膨胀
  - **上下文注入** - 将总结注入到 Agent 推理上下文
- `src/services/create_agent.py` + `services/middleware`
  - 可插拔 AgentMiddleware（成本、记忆、审计等），扩展 LangChain 代理行为。
- `src/api/tools_routes.py`
  - 工具枚举与受控执行（需 Admin Key），便于调试。
  - **Epic 2 新增** - DuckDuckGo web_search 工具支持
- `pyproject.toml:67-125`
  - 加入 `duckduckgo-search` 依赖，支持 Web 搜索。

## 13. 安全与中间件
- `src/middleware/auth_middleware.py`
  - 使用 PyJWT 对 Bearer Token 做 HS/RS 多算法验证，支持 `JWT_AUDIENCE` / `JWT_ISSUER` 约束并正确处理过期/非法 token。
- `content_moderation`, `response_structuring`, `audit_logging`, `memory_injection`
  - 速率限制、安全过滤、统一返回格式、审计日志、记忆注入。

## 14. 财务特性与示例
- `src/services/content_blocks_parser.py`
  - 统一解析 Claude/OpenAI/Gemini reasoning、tool use 等内容块。
- `financial_content_handler.py` + `examples/financial_analysis_examples.py`
  - 抽取估值/风险等金融洞察、验证工具调用、演示股票与投资组合分析。

## 15. 数据库与持久层
- `src/models/*.py` + `src/repositories/*.py`
  - Conversation/Message/Document/Embedding ORM 及仓储，封装 CRUD、软删、搜索、分区。
- `src/db/migrations.py`
  - 初始化 pgvector、HNSW 索引和 embeddings 按月分区策略。

## 16. 文档/示例支持
- `docs/` 及根目录手册
  - 记录史诗级规划、实施指南（例如 EPIC1 文档），帮助跨团队协作。
- `src/examples/financial_analysis_examples.py`
  - 对 FinancialContentBlockHandler 的即用案例。

## 17. 整体功能
- 该后端提供会话/消息管理、RAG 文档检索、LangChain 工具智能体、实时 WebSocket 对话、安全中间件、金融特性扩展，形成自助式 AI 会话平台。

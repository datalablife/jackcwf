# 代码模块功能说明

以下按功能域梳理 `src/` 核心模块，帮助快速理解 LangChain AI Conversation 后端。每个条目都附带主要文件与职责，可配合 `CLAUDE code` 的上下文搜索。

## 1. FastAPI 应用层
- `src/main.py`
  - 定义 FastAPI 应用、CORS、生命周期钩子与全局异常处理。
  - 挂载自定义中间件（认证、记忆注入、内容安全、统一响应、审计）并注册路由。
  - 暴露健康检查、根路由及 uvicorn 启动入口。

## 2. API 路由
- `src/api/conversation_routes.py`
  - 提供会话 CRUD、历史查询与发送消息 REST 接口。
- `src/api/message_routes.py`
  - 针对单条消息进行读取、更新工具结果/Token 以及硬删除。
- `src/api/document_routes.py`
  - 覆盖文档上传、分页、摘要、软删除、语义搜索与 chunk 拉取。
- `src/api/tools_routes.py`
  - 列出可用 LangChain 工具，提供受保护的工具执行端点。
- `src/api/websocket_routes.py`
  - 管理实时会话 WebSocket：验证、上下文加载、消息处理、心跳。

## 3. 数据库与 ORM
- `src/db/config.py`, `src/db/migrations.py`, `src/db/base.py`
  - 配置 async SQLAlchemy + PostgreSQL/pgvector，提供 session 依赖。
  - 初始化表、启用 pgvector、建立 HNSW 索引及 embeddings 按月分区。
- `src/models/*.py`
  - 定义 Conversation、Message、Document、Embedding ORM。
- `src/repositories/*.py`
  - 封装会话/消息/文档/向量的常用查询、计数、软删除、搜索等。

## 4. 服务层
- `ConversationService`
  - 组合仓储实现会话生命周期、消息写入、上下文聚合。
- `DocumentService` + `DocumentChunker`
  - 文档切分、嵌入入库、计数维护及软删除。
- `EmbeddingService`
  - 调用 OpenAI embeddings、批量生成、余弦相似度计算。
- `AgentService`
  - 使用 LangChain ChatOpenAI 构建带工具的代理，支持工具调用、流式/非流式处理、对话总结。
- `create_agent.ManagedAgent`
  - 通用代理封装，允许插入 AgentMiddleware 实现成本跟踪、记忆注入等钩子。
- `services/middleware/*`
  - AgentMiddleware 抽象，以及 `CostTrackingMiddleware`、`MemoryInjectionMiddleware` 示例实现。
- `tool_schemas.py`
  - 定义 search_documents/query_database/web_search 工具输入/输出 Pydantic Schema。
- `financial_content_handler.py` & `content_blocks_parser.py`
  - 统一解析多模型 content blocks，抽取金融洞察、校验工具调用；示例见 `src/examples/financial_analysis_examples.py`。

## 5. 中间件层
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

## 6. 文档与工具
- `src/utils/file_handler.py`
  - 文件类型检测、PDF/TXT/DOCX/CSV 文本抽取与上传校验。
- `src/examples/financial_analysis_examples.py`
  - 展示如何消费 FinancialContentBlockHandler，进行股票/投资组合分析。

## 使用方式
- 查阅特定功能时，可先定位本文件对应模块，再结合源文件阅读实现细节。
- 若需扩展 Agent 或中间件，优先参考服务层与 `services/middleware` 钩子定义。

## 7. 后端骨架
- `src/main.py`、`src/db/config.py`
  - 启动时初始化 pgvector、注册中间件、统一日志/异常处理，构成 FastAPI 应用骨架。
- 健康检查、根路由与 CORS 配置集中于主入口，便于部署时统一管理。

## 8. 对话与消息流程
- `src/api/conversation_routes.py` + `ConversationService`
  - 会话创建、分页、详情、软删除、历史/上下文聚合。
- `src/api/message_routes.py` + `MessageRepository`
  - 单条消息读/写/删、工具结果回写、token 统计。
- `src/api/websocket_routes.py:387-470`
  - 消费 `AgentService.stream_message` 事件流，实时转发 chunk、tool_call/tool_result，拿到 `complete_state` 后落库并发送完成事件，替代原先的字符串切片“模拟 streaming”。

## 9. 文档 & RAG 管线
- `src/api/document_routes.py` + `DocumentService`
  - 上传、chunk 切分、嵌入生成、软删除、语义搜索、chunk 拉取。
- `src/services/embedding_service.py` + `EmbeddingRepository`
  - OpenAI embedding 生成、余弦相似度批量计算、pgvector HNSW 检索。

## 10. 智能体与工具
- `src/services/agent_service.py:35-653`
  - 提供真实 streaming：重构消息构造、SQL/搜索工具校验；新增 DuckDuckGo 搜索与严格 SQL 审核执行；`_stream_with_tools` 递归消费 LangChain `astream` 输出，逐块推送内容并执行工具，最终产出 `complete_state` 元数据。
- `src/services/create_agent.py` + `services/middleware`
  - 可插拔 AgentMiddleware（成本、记忆、审计等），扩展 LangChain 代理行为。
- `src/api/tools_routes.py`
  - 工具枚举与受控执行（需 Admin Key），便于调试。
- `pyproject.toml:67-125`
  - 加入 `PyJWT` 与 `duckduckgo-search` 依赖，支持安全认证与 Web 搜索。

## 11. 安全与中间件
- `src/middleware/auth_middleware.py`
  - 使用 PyJWT 对 Bearer Token 做 HS/RS 多算法验证，支持 `JWT_AUDIENCE` / `JWT_ISSUER` 约束并正确处理过期/非法 token。
- `content_moderation`, `response_structuring`, `audit_logging`, `memory_injection`
  - 速率限制、安全过滤、统一返回格式、审计日志、记忆注入。

## 12. 财务特性与示例
- `src/services/content_blocks_parser.py`
  - 统一解析 Claude/OpenAI/Gemini reasoning、tool use 等内容块。
- `financial_content_handler.py` + `examples/financial_analysis_examples.py`
  - 抽取估值/风险等金融洞察、验证工具调用、演示股票与投资组合分析。

## 13. 数据库与持久层
- `src/models/*.py` + `src/repositories/*.py`
  - Conversation/Message/Document/Embedding ORM 及仓储，封装 CRUD、软删、搜索、分区。
- `src/db/migrations.py`
  - 初始化 pgvector、HNSW 索引和 embeddings 按月分区策略。

## 14. 文档/示例支持
- `docs/` 及根目录手册
  - 记录史诗级规划、实施指南（例如 EPIC1 文档），帮助跨团队协作。
- `src/examples/financial_analysis_examples.py`
  - 对 FinancialContentBlockHandler 的即用案例。

## 15. 整体功能
- 该后端提供会话/消息管理、RAG 文档检索、LangChain 工具智能体、实时 WebSocket 对话、安全中间件、金融特性扩展，形成自助式 AI 会话平台。

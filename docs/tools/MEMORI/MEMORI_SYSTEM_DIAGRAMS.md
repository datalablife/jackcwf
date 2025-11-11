# Memori System Architecture Diagrams

## 1. High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           User Interface Layer                          │
│                     (React/Next.js Frontend)                            │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │ HTTPS/REST API
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        API Gateway Layer                                │
│                   (FastAPI + Middleware)                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │
│  │   CORS       │  │  Rate Limit  │  │  Auth/JWT    │                │
│  └──────────────┘  └──────────────┘  └──────────────┘                │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │
           ┌──────────────────┼──────────────────┬─────────────────────┐
           │                  │                  │                     │
           ▼                  ▼                  ▼                     ▼
┌──────────────────┐ ┌──────────────┐ ┌──────────────────┐ ┌───────────────┐
│  Data Source     │ │ File Upload  │ │ Memory Mgmt API  │ │ Text2SQL API  │
│  API Routes      │ │ API Routes   │ │ (NEW)            │ │ (Enhanced)    │
└────────┬─────────┘ └──────┬───────┘ └────────┬─────────┘ └───────┬───────┘
         │                  │                  │                   │
         ▼                  ▼                  ▼                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Business Logic Layer                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐ │
│  │ DataSource       │  │ File Parser      │  │ Memory Manager       │ │
│  │ Service          │  │ Service          │  │ (NEW)                │ │
│  └──────────────────┘  └──────────────────┘  └──────────────────────┘ │
│                                                                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐ │
│  │ Claude API       │  │ Entity Extractor │  │ Relationship Mapper  │ │
│  │ Client (NEW)     │  │ (NEW)            │  │ (NEW)                │ │
│  └──────────────────┘  └──────────────────┘  └──────────────────────┘ │
│                                                                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐ │
│  │ Embedding        │  │ Rule Engine      │  │ Query Pattern        │ │
│  │ Service (NEW)    │  │ (NEW)            │  │ Analyzer (NEW)       │ │
│  └──────────────────┘  └──────────────────┘  └──────────────────────┘ │
└────────┬──────────────────────────────┬──────────────┬─────────────────┘
         │                              │              │
         ▼                              ▼              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Data Persistence Layer                           │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │              PostgreSQL 16 with pgvector                          │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────────┐  │  │
│  │  │data_sources│  │file_uploads│  │memori_     │  │memori_    │  │  │
│  │  │            │  │            │  │conversations│  │memories   │  │  │
│  │  └────────────┘  └────────────┘  └────────────┘  └───────────┘  │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────────┐  │  │
│  │  │memori_     │  │memori_     │  │memori_rules│  │memori_    │  │  │
│  │  │entities    │  │relationships│  │            │  │query_     │  │  │
│  │  │            │  │            │  │            │  │patterns   │  │  │
│  │  └────────────┘  └────────────┘  └────────────┘  └───────────┘  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    Redis Cache Layer                              │  │
│  │  - Embedding Cache    - Session Cache    - Query Result Cache    │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      External Services Layer                            │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐ │
│  │ Anthropic Claude │  │ OpenAI Embeddings│  │ User Data Sources    │ │
│  │ API              │  │ API              │  │ (PostgreSQL DBs)     │ │
│  └──────────────────┘  └──────────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Memory Lifecycle Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     User Interaction with System                        │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ User sends query │
                    │ "Show me sales"  │
                    └────────┬─────────┘
                             │
                             ▼
        ┌────────────────────────────────────────────┐
        │  Step 1: Context Retrieval                 │
        │  MemoryManager.retrieve_relevant_memories()│
        └────────┬───────────────────────────────────┘
                 │
                 ├─► Generate query embedding (OpenAI)
                 │
                 ├─► Vector similarity search (pgvector)
                 │   └─► Find top-k relevant memories
                 │
                 └─► Apply importance scoring
                     └─► Return ranked memories
                 │
                 ▼
        ┌────────────────────────────────────────────┐
        │  Step 2: Rule Application                  │
        │  RuleEngine.get_applicable_rules()         │
        └────────┬───────────────────────────────────┘
                 │
                 ├─► Query memori_rules table
                 │
                 ├─► Filter by data_source_id
                 │
                 └─► Apply priority ordering
                 │
                 ▼
        ┌────────────────────────────────────────────┐
        │  Step 3: Prompt Construction               │
        │  PromptBuilder.build_enhanced_prompt()     │
        └────────┬───────────────────────────────────┘
                 │
                 ├─► Inject schema context
                 │
                 ├─► Inject relevant memories
                 │
                 ├─► Inject business rules
                 │
                 └─► Format as Claude system prompt
                 │
                 ▼
        ┌────────────────────────────────────────────┐
        │  Step 4: SQL Generation                    │
        │  ClaudeClient.generate_sql()               │
        └────────┬───────────────────────────────────┘
                 │
                 ├─► Call Claude API with enriched context
                 │
                 ├─► Parse and validate response
                 │
                 └─► Extract SQL + explanation
                 │
                 ▼
        ┌────────────────────────────────────────────┐
        │  Step 5: Memory Storage (Conscious Ingest)│
        │  MemoryManager.store_memory()              │
        └────────┬───────────────────────────────────┘
                 │
                 ├─► Store query + SQL as memory
                 │
                 ├─► Generate embedding
                 │
                 ├─► Extract entities
                 │
                 ├─► Calculate importance
                 │
                 └─► Persist to database
                 │
                 ▼
        ┌────────────────────────────────────────────┐
        │  Step 6: Pattern Learning                  │
        │  PatternAnalyzer.record_pattern()          │
        └────────┬───────────────────────────────────┘
                 │
                 ├─► Store in memori_query_patterns
                 │
                 ├─► Update entity usage statistics
                 │
                 └─► Update relationship strengths
                 │
                 ▼
        ┌────────────────────────────────────────────┐
        │  Step 7: Return Response to User           │
        │  { sql: "...", explanation: "..." }        │
        └────────────────────────────────────────────┘
```

---

## 3. Memory Retrieval Process (Semantic Search)

```
┌──────────────────────────────────────────────────────────────────┐
│  Input: User Query = "What were the sales last quarter?"        │
└─────────────────────────┬────────────────────────────────────────┘
                          │
                          ▼
         ┌────────────────────────────────────────┐
         │  1. Embedding Generation               │
         │  EmbeddingService.generate_embedding() │
         └────────────┬───────────────────────────┘
                      │
                      ├─► Call OpenAI Embeddings API
                      │   - Model: text-embedding-ada-002
                      │   - Input: "What were the sales last quarter?"
                      │
                      └─► Output: [0.023, -0.015, 0.042, ..., 0.011]
                          (1536-dimensional vector)
                      │
                      ▼
         ┌────────────────────────────────────────┐
         │  2. Vector Similarity Search           │
         │  SELECT with pgvector                  │
         └────────────┬───────────────────────────┘
                      │
                      ├─► SQL Query:
                      │   SELECT *,
                      │          embedding <-> '[query_vector]' as distance
                      │   FROM memori_memories
                      │   WHERE user_id = 'user123'
                      │     AND is_archived = false
                      │     AND (expires_at IS NULL OR expires_at > NOW())
                      │   ORDER BY distance ASC
                      │   LIMIT 10
                      │
                      └─► Uses HNSW index for fast search
                      │
                      ▼
         ┌────────────────────────────────────────┐
         │  3. Results Retrieved from PostgreSQL  │
         └────────────┬───────────────────────────┘
                      │
                      ├─► Memory 1: "Sales data is in the orders table"
                      │   - Distance: 0.15 → Similarity: 0.85
                      │   - Type: ENTITY
                      │   - Importance: 0.8
                      │
                      ├─► Memory 2: "Q3 sales query: SELECT SUM(amount)..."
                      │   - Distance: 0.22 → Similarity: 0.78
                      │   - Type: RULE
                      │   - Importance: 0.7
                      │
                      └─► Memory 3: "User prefers quarterly breakdowns"
                          - Distance: 0.28 → Similarity: 0.72
                          - Type: RULE
                          - Importance: 0.6
                      │
                      ▼
         ┌────────────────────────────────────────┐
         │  4. Filter by Minimum Similarity       │
         │  (threshold: 0.70)                     │
         └────────────┬───────────────────────────┘
                      │
                      ├─► Keep: Memory 1 (0.85) ✓
                      ├─► Keep: Memory 2 (0.78) ✓
                      └─► Keep: Memory 3 (0.72) ✓
                      │
                      ▼
         ┌────────────────────────────────────────┐
         │  5. Update Access Statistics           │
         │  INCREMENT access_count                │
         │  UPDATE last_accessed_at               │
         │  BOOST importance_score                │
         └────────────┬───────────────────────────┘
                      │
                      ▼
         ┌────────────────────────────────────────┐
         │  6. Return Ranked Results              │
         │  [Memory1, Memory2, Memory3]           │
         │  with similarity scores                │
         └────────────────────────────────────────┘
```

---

## 4. Claude API Integration Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│         User Input: "Show me customers who bought last month"        │
└─────────────────────────┬────────────────────────────────────────────┘
                          │
                          ▼
         ┌────────────────────────────────────────────┐
         │  MemoriClaudeClient.generate_sql()         │
         └────────────┬───────────────────────────────┘
                      │
                      ▼
         ┌────────────────────────────────────────────┐
         │  Phase 1: Context Gathering                │
         └────────────┬───────────────────────────────┘
                      │
                      ├─► A. Get Schema Context
                      │   ┌──────────────────────────┐
                      │   │ Tables:                  │
                      │   │ - customers (id, name)   │
                      │   │ - orders (id, customer_id│
                      │   │           date, amount)  │
                      │   └──────────────────────────┘
                      │
                      ├─► B. Retrieve Memories (Semantic Search)
                      │   ┌──────────────────────────────────────┐
                      │   │ "Last month queries use BETWEEN"     │
                      │   │ "customers table joined via id"      │
                      │   │ "User prefers DATE_TRUNC for dates"  │
                      │   └──────────────────────────────────────┘
                      │
                      └─► C. Get Applicable Rules
                          ┌──────────────────────────────────────┐
                          │ "Always use table aliases"           │
                          │ "Include ORDER BY for readability"   │
                          └──────────────────────────────────────┘
                      │
                      ▼
         ┌────────────────────────────────────────────┐
         │  Phase 2: Prompt Construction              │
         │  PromptBuilder.build_system_prompt()       │
         └────────────┬───────────────────────────────┘
                      │
                      ├─► Construct System Prompt:
                      │   ┌──────────────────────────────────────────┐
                      │   │ You are an expert SQL query generator.   │
                      │   │                                          │
                      │   │ ## Database Schema                       │
                      │   │ Tables: customers, orders                │
                      │   │ ...                                      │
                      │   │                                          │
                      │   │ ## Relevant Historical Context           │
                      │   │ - Last month queries use BETWEEN...      │
                      │   │ - customers table joined via id...       │
                      │   │                                          │
                      │   │ ## User Preferences and Business Rules   │
                      │   │ - Always use table aliases               │
                      │   │ - Include ORDER BY for readability       │
                      │   │                                          │
                      │   │ ## Instructions                          │
                      │   │ Generate syntactically correct SQL...    │
                      │   └──────────────────────────────────────────┘
                      │
                      └─► User Message:
                          "Show me customers who bought last month"
                      │
                      ▼
         ┌────────────────────────────────────────────┐
         │  Phase 3: Claude API Call                  │
         └────────────┬───────────────────────────────┘
                      │
                      ├─► POST https://api.anthropic.com/v1/messages
                      │   Headers:
                      │   - x-api-key: sk-ant-...
                      │   - anthropic-version: 2023-06-01
                      │
                      │   Body:
                      │   {
                      │     "model": "claude-sonnet-4-5-20250929",
                      │     "max_tokens": 2048,
                      │     "system": "[system_prompt]",
                      │     "messages": [
                      │       {"role": "user", "content": "[query]"}
                      │     ]
                      │   }
                      │
                      ▼
         ┌────────────────────────────────────────────┐
         │  Phase 4: Response Parsing                 │
         └────────────┬───────────────────────────────┘
                      │
                      ├─► Claude Response:
                      │   {
                      │     "sql": "SELECT c.name, c.id
                      │             FROM customers c
                      │             JOIN orders o ON c.id = o.customer_id
                      │             WHERE o.date BETWEEN
                      │               DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
                      │               AND DATE_TRUNC('month', CURRENT_DATE)
                      │             ORDER BY c.name",
                      │     "explanation": "This query joins customers with orders...",
                      │     "intent": "select_with_join"
                      │   }
                      │
                      ├─► Validate JSON structure
                      │
                      └─► Extract SQL, explanation, intent
                      │
                      ▼
         ┌────────────────────────────────────────────┐
         │  Phase 5: Memory Storage                   │
         │  MemoryManager.store_memory()              │
         └────────────┬───────────────────────────────┘
                      │
                      ├─► Store as SHORT_TERM memory:
                      │   - Content: "[query] → [sql]"
                      │   - Type: SHORT_TERM
                      │   - Importance: 0.6
                      │   - Tags: ['sql_generation', 'query']
                      │
                      └─► Store in query_patterns table:
                          - Natural query
                          - Generated SQL
                          - Intent: select_with_join
                          - Tables used: [customers, orders]
                      │
                      ▼
         ┌────────────────────────────────────────────┐
         │  Phase 6: Return to User                   │
         │  {                                         │
         │    "sql": "SELECT c.name...",              │
         │    "explanation": "...",                   │
         │    "intent": "select_with_join"            │
         │  }                                         │
         └────────────────────────────────────────────┘
```

---

## 5. Database Schema Relationships

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Existing Tables (Current)                       │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│  data_sources    │
│──────────────────│
│ PK id            │────┐
│    name          │    │
│    type          │    │
│    status        │    │
│    description   │    │
└──────────────────┘    │
                        │ 1:1
                        │
         ┌──────────────┴────────────────┬──────────────────────────┐
         │                               │                          │
         ▼                               ▼                          ▼
┌──────────────────┐          ┌──────────────────┐      ┌──────────────────┐
│database_connections│        │  file_uploads    │      │  schemas         │
│──────────────────│          │──────────────────│      │──────────────────│
│ PK id            │          │ PK id            │      │ PK id            │
│ FK data_source_id│          │ FK data_source_id│      │ FK data_source_id│
│    host          │          │    filename      │      │    table_name    │
│    port          │          │    file_path     │      │    schema_json   │
│    database      │          │    format        │      │                  │
│    username      │          │    status        │      │                  │
│    encrypted_pwd │          │                  │      │                  │
└──────────────────┘          └──────────────────┘      └──────────────────┘


┌─────────────────────────────────────────────────────────────────────┐
│                     New Memori Tables                               │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│ memori_conversations │
│──────────────────────│
│ PK id                │
│ UK conversation_id   │────────┐
│    user_id           │        │
│ FK data_source_id    │──────┐ │
│    title             │      │ │ 1:N
│    metadata          │      │ │
│    is_active         │      │ │
│    last_activity_at  │      │ │
└──────────────────────┘      │ │
         │                    │ │
         │ References         │ │
         ▼                    │ │
┌──────────────────┐          │ │
│  data_sources    │          │ │
└──────────────────┘          │ │
                              │ │
                              │ └──────────────────────┐
                              │                        │
                              │                        ▼
                              │            ┌─────────────────────┐
                              │            │  memori_memories    │
                              │            │─────────────────────│
                              │            │ PK id               │
                              │            │ UK memory_id        │
                              │            │ FK conversation_id  │
                              │            │    user_id          │
                              │            │    content          │
                              │            │    memory_type      │
                              │            │    embedding        │◄─── Vector(1536)
                              │            │    importance_score │
                              │            │    access_count     │
                              │            │    context_tags     │
                              │            │    related_entities │
                              │            │    metadata         │
                              │            │    expires_at       │
                              │            │    is_archived      │
                              │            └─────────────────────┘
                              │
                              │
                              └──────────────┐
                                             │
                                             ▼
                              ┌─────────────────────────┐
                              │ memori_query_patterns   │
                              │─────────────────────────│
                              │ PK id                   │
                              │ UK pattern_id           │
                              │ FK conversation_id      │
                              │ FK data_source_id       │
                              │    user_id              │
                              │    natural_language_query│
                              │    generated_sql        │
                              │    query_intent         │
                              │    execution_time_ms    │
                              │    tables_used          │
                              │    columns_used         │
                              │    user_satisfaction    │
                              └─────────────────────────┘


┌──────────────────────┐            ┌─────────────────────────┐
│  memori_entities     │            │ memori_relationships    │
│──────────────────────│            │─────────────────────────│
│ PK id                │◄───────────│ FK source_entity_id     │
│ UK entity_id         │            │ FK target_entity_id     │──┐
│    user_id           │            │    user_id              │  │
│    entity_name       │            │    relationship_type    │  │
│    entity_type       │            │    strength             │  │
│ FK data_source_id    │            │    context              │  │
│    properties        │            │    metadata             │  │
│    description       │            │    usage_count          │  │
│    mention_count     │            └─────────────────────────┘  │
│    importance_score  │                        │                │
└──────────────────────┘                        └────────────────┘
         │                                       (Self-referential)
         │
         │ References
         ▼
┌──────────────────┐
│  data_sources    │
└──────────────────┘


┌──────────────────────┐
│  memori_rules        │
│──────────────────────│
│ PK id                │
│ UK rule_id           │
│    user_id           │
│ FK data_source_id    │────► data_sources
│    rule_name         │
│    rule_type         │
│    rule_content      │
│    conditions        │
│    priority          │
│    is_active         │
│    application_count │
│    last_applied_at   │
└──────────────────────┘
```

---

## 6. Memory Importance Scoring Algorithm

```
┌──────────────────────────────────────────────────────────────────────┐
│                     Memory Importance Calculation                    │
└──────────────────────────────────────────────────────────────────────┘

Initial Importance Score (0.0 - 1.0)
│
├─► Base Factors:
│   ┌──────────────────────────────────────────────────────────┐
│   │ 1. Memory Type Weight                                    │
│   │    - RULE:         0.8  (High - affects behavior)        │
│   │    - ENTITY:       0.7  (Medium-High - schema info)      │
│   │    - LONG_TERM:    0.6  (Medium - established context)   │
│   │    - SHORT_TERM:   0.5  (Medium-Low - temporary)         │
│   │    - RELATIONSHIP: 0.6  (Medium - connection info)       │
│   └──────────────────────────────────────────────────────────┘
│
├─► Usage-Based Adjustments:
│   ┌──────────────────────────────────────────────────────────┐
│   │ 2. Access Frequency Bonus                                │
│   │    bonus = min(0.2, access_count * 0.02)                 │
│   │                                                           │
│   │    Examples:                                              │
│   │    - 0 accesses:  +0.00                                  │
│   │    - 5 accesses:  +0.10                                  │
│   │    - 10+ accesses: +0.20 (capped)                        │
│   └──────────────────────────────────────────────────────────┘
│
├─► Recency Adjustments:
│   ┌──────────────────────────────────────────────────────────┐
│   │ 3. Recency Decay                                         │
│   │    days_old = (now - created_at).days                    │
│   │    decay = exp(-days_old / 30)  # 30-day half-life      │
│   │                                                           │
│   │    Examples:                                              │
│   │    - 0 days:   1.00 (no decay)                           │
│   │    - 30 days:  0.37 (moderate decay)                     │
│   │    - 60 days:  0.14 (significant decay)                  │
│   │    - 90 days:  0.05 (almost irrelevant)                  │
│   └──────────────────────────────────────────────────────────┘
│
├─► Context Relevance:
│   ┌──────────────────────────────────────────────────────────┐
│   │ 4. Tag Relevance Bonus                                   │
│   │    if context_tags contains query-relevant tags:         │
│   │      bonus = +0.1 per matching tag (max +0.3)            │
│   └──────────────────────────────────────────────────────────┘
│
└─► Final Calculation:
    ┌──────────────────────────────────────────────────────────┐
    │ final_importance =                                       │
    │   base_importance                                        │
    │   + access_frequency_bonus                               │
    │   + tag_relevance_bonus                                  │
    │   * recency_decay                                        │
    │                                                           │
    │ Clamped to [0.0, 1.0]                                    │
    └──────────────────────────────────────────────────────────┘


Example Calculation:
┌──────────────────────────────────────────────────────────────┐
│ Memory: "User prefers using JOINs instead of subqueries"     │
│                                                              │
│ Base importance (RULE):          0.8                         │
│ Access count (7 times):        + 0.14                       │
│ Tag relevance (2 matching):    + 0.2                        │
│ Recency (15 days old):         * 0.70                       │
│                                                              │
│ Calculation:                                                 │
│   (0.8 + 0.14 + 0.2) * 0.70 = 0.798                         │
│                                                              │
│ Final Importance: 0.80 (capped)                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 7. Memory Lifecycle State Machine

```
┌─────────────────────────────────────────────────────────────────┐
│                     Memory Lifecycle States                     │
└─────────────────────────────────────────────────────────────────┘


                  ┌──────────────┐
                  │   CREATED    │
                  │ (short_term) │
                  └──────┬───────┘
                         │
                         │ store_memory()
                         ▼
                  ┌──────────────┐
                  │    ACTIVE    │◄────────┐
                  │ (short_term) │         │
                  └──────┬───────┘         │
                         │                 │
         ┌───────────────┼────────────────┐│
         │               │                ││
         │ High usage    │ Low usage      ││ retrieve()
         │ High importance│ Time passes   ││ (Updates access stats)
         │               │                ││
         ▼               ▼                ││
┌──────────────┐  ┌──────────────┐       ││
│  PROMOTED    │  │   EXPIRING   │       ││
│ (long_term)  │  │ (short_term) │       ││
└──────┬───────┘  └──────┬───────┘       ││
       │                 │                ││
       │                 │ expires_at     ││
       │                 │ reached        ││
       │                 ▼                ││
       │          ┌──────────────┐        ││
       │          │   EXPIRED    │        ││
       │          └──────┬───────┘        ││
       │                 │                ││
       │                 │ Cleanup job    ││
       │                 ▼                ││
       │          ┌──────────────┐        ││
       └─────────►│   ARCHIVED   │        ││
                  │ (is_archived │        ││
                  │    = true)   │        ││
                  └──────┬───────┘        ││
                         │                ││
                         │ Manual restore ││
                         └────────────────┘│
                                          │
                         ┌────────────────┘
                         │
                         │ Periodic cleanup
                         │ (>90 days old)
                         ▼
                  ┌──────────────┐
                  │   DELETED    │
                  │ (hard delete)│
                  └──────────────┘


State Transition Conditions:
═══════════════════════════════════════════════════════════════

CREATED → ACTIVE
  - Automatic upon successful storage

ACTIVE → PROMOTED (long_term)
  - access_count >= 5
  - importance_score >= 0.7
  - Referenced in multiple conversations

ACTIVE → EXPIRING
  - expires_at is set and approaching
  - importance_score < 0.4
  - access_count < 2

EXPIRING → EXPIRED
  - expires_at < current_time

ACTIVE → ARCHIVED
  - Low importance + old age:
    - importance_score < 0.3
    - created_at < (now - 30 days)
    - access_count < 2

EXPIRED → ARCHIVED
  - Cleanup job runs

ARCHIVED → ACTIVE
  - Manual restore by user
  - Important memory retrieved

ARCHIVED → DELETED
  - is_archived = true
  - created_at < (now - 90 days)
  - importance_score < 0.2
```

---

## 8. Performance Optimization Flow

```
┌─────────────────────────────────────────────────────────────────┐
│              Performance Optimization Strategies                │
└─────────────────────────────────────────────────────────────────┘


1. Embedding Generation Optimization
═══════════════════════════════════════════════════════════════

   User Query
        │
        ▼
   ┌──────────────────┐
   │ Check Redis Cache│
   │ Key: emb:{hash}  │
   └────────┬─────────┘
            │
     ┌──────┴───────┐
     │              │
  Cache Hit    Cache Miss
     │              │
     ▼              ▼
  Return      ┌─────────────────┐
  Cached      │ Call OpenAI API │
  Embedding   └────────┬────────┘
     │                 │
     │                 ▼
     │        ┌────────────────┐
     │        │ Store in Cache │
     │        │ TTL: 1 hour    │
     │        └────────┬───────┘
     │                 │
     └────────┬────────┘
              ▼
       Return Embedding


2. Vector Search Optimization
═══════════════════════════════════════════════════════════════

   Search Query
        │
        ▼
   ┌───────────────────────┐
   │ Use HNSW Index        │
   │ (Approximate Search)  │
   └──────────┬────────────┘
              │
              ├─► Probes: 100
              ├─► Lists: 1000
              └─► ef_search: 200
              │
              ▼
   ┌───────────────────────┐
   │ Query Planner         │
   │ - Use index scan      │
   │ - Apply filters first │
   │ - Limit early         │
   └──────────┬────────────┘
              │
              ▼
   ┌───────────────────────┐
   │ Result Set (top-k)    │
   │ Execution: ~50ms      │
   └───────────────────────┘


3. Connection Pooling
═══════════════════════════════════════════════════════════════

   ┌───────────────────────────────────────┐
   │        SQLAlchemy Pool                │
   │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐     │
   │  │Conn1│ │Conn2│ │Conn3│ │...20│     │
   │  └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘     │
   │     │       │       │       │         │
   │   [IDLE] [ACTIVE] [IDLE] [ACTIVE]    │
   └─────┼───────┼───────┼───────┼─────────┘
         │       │       │       │
         │       │       │       │
   Max Pool Size: 20 connections
   Max Overflow: 10 connections
   Pool Timeout: 30 seconds
   Pool Recycle: 3600 seconds


4. Query Result Caching
═══════════════════════════════════════════════════════════════

   API Request
        │
        ▼
   ┌─────────────────────────┐
   │ Generate Cache Key      │
   │ query:{user}:{params}   │
   └──────────┬──────────────┘
              │
       ┌──────┴───────┐
       │              │
    Hit Cache    Miss Cache
       │              │
       ▼              ▼
  Return        ┌─────────────┐
  Cached        │ Execute     │
  Result        │ DB Query    │
       │        └──────┬──────┘
       │               │
       │               ▼
       │        ┌─────────────┐
       │        │ Store Result│
       │        │ TTL: 5 min  │
       │        └──────┬──────┘
       │               │
       └───────┬───────┘
               ▼
         Return Result


5. Batch Processing
═══════════════════════════════════════════════════════════════

   100 Memories to Store
        │
        ▼
   ┌──────────────────────────┐
   │ Batch into groups of 10  │
   └──────────┬───────────────┘
              │
              ├─► Batch 1: [Mem 1-10]   ──► OpenAI API
              ├─► Batch 2: [Mem 11-20]  ──► OpenAI API
              ├─► Batch 3: [Mem 21-30]  ──► OpenAI API
              │   ...                        (Parallel)
              └─► Batch 10: [Mem 91-100] ──► OpenAI API
              │
              ▼
   ┌──────────────────────────┐
   │ Collect all embeddings   │
   └──────────┬───────────────┘
              │
              ▼
   ┌──────────────────────────┐
   │ Bulk INSERT to PostgreSQL│
   │ Using COPY or bulk_save  │
   └──────────────────────────┘

   Time Saved: 80% reduction vs sequential
```

---

## 9. Security Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Security Layers                             │
└─────────────────────────────────────────────────────────────────┘


Layer 1: API Gateway Security
═══════════════════════════════════════════════════════════════

   Client Request
        │
        ▼
   ┌─────────────────┐
   │ Rate Limiting   │  → 100 requests/minute per IP
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ CORS Validation │  → Whitelist allowed origins
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ JWT Validation  │  → Verify token signature
   └────────┬────────┘     Extract user_id
            │
            ▼
   ┌─────────────────┐
   │ Input Sanitization│ → Remove SQL injection attempts
   └────────┬────────┘     HTML escape, validate types
            │
            ▼
      Route Handler


Layer 2: Application Security
═══════════════════════════════════════════════════════════════

   ┌──────────────────────────────────────────┐
   │     Row-Level Security (RLS)             │
   │                                          │
   │  All queries automatically filtered by:  │
   │    WHERE user_id = current_user_id       │
   │                                          │
   │  Enforced at:                            │
   │  - ORM level (SQLAlchemy filters)        │
   │  - Database level (PostgreSQL policies)  │
   └──────────────────────────────────────────┘

   Query Example:
   ┌──────────────────────────────────────────┐
   │ SELECT * FROM memori_memories            │
   │ WHERE user_id = 'user123'  ← Automatic   │
   │   AND is_archived = false                │
   └──────────────────────────────────────────┘


Layer 3: Data Encryption
═══════════════════════════════════════════════════════════════

   ┌─────────────────────────────────────────────┐
   │           Encryption at Rest               │
   │                                             │
   │  PostgreSQL:                                │
   │  - Database credentials (AES-256)           │
   │  - Sensitive memory content (optional)      │
   │                                             │
   │  API Keys:                                  │
   │  - Stored in AWS Secrets Manager            │
   │  - Rotated every 90 days                    │
   └─────────────────────────────────────────────┘

   ┌─────────────────────────────────────────────┐
   │         Encryption in Transit              │
   │                                             │
   │  - TLS 1.3 for all API connections          │
   │  - SSL for PostgreSQL connections           │
   │  - HTTPS only (no HTTP)                     │
   └─────────────────────────────────────────────┘


Layer 4: Access Control
═══════════════════════════════════════════════════════════════

   ┌──────────────────────────────────────┐
   │      Permission Matrix              │
   ├──────────────────────────────────────┤
   │ Resource      │ Owner │ Other Users  │
   ├───────────────┼───────┼──────────────┤
   │ Memories      │ CRUD  │ None         │
   │ Conversations │ CRUD  │ None         │
   │ Entities      │ CRUD  │ Read (shared)│
   │ Rules         │ CRUD  │ None         │
   │ Patterns      │ CRUD  │ None         │
   └──────────────────────────────────────┘


Layer 5: Audit Logging
═══════════════════════════════════════════════════════════════

   Every sensitive operation logs:
   ┌─────────────────────────────────────────┐
   │ - Timestamp                             │
   │ - User ID                               │
   │ - Action (CREATE, READ, UPDATE, DELETE) │
   │ - Resource ID                           │
   │ - IP Address                            │
   │ - User Agent                            │
   │ - Success/Failure                       │
   └─────────────────────────────────────────┘

   Stored in:
   - Application logs (structured JSON)
   - PostgreSQL audit table
   - CloudWatch/ELK for analysis
```

---

**Document Version:** 1.0
**Last Updated:** 2025-11-11
**Purpose:** Visual reference for Memori integration architecture

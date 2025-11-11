# Memori Integration Architecture for Text2SQL System

## Executive Summary

This document outlines the comprehensive architecture for integrating **Memori** (GibsonAI/Memori) as a context memory management system for Claude AI within the Text2SQL data source integration platform.

**Integration Goals:**
- Provide persistent conversation context across user sessions
- Enable intelligent data source discovery and recommendation
- Store query patterns and user preferences for improved SQL generation
- Implement multi-tenant memory isolation for enterprise use cases

---

## 1. Architecture Overview

### 1.1 System Components Interaction

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Frontend (React/Next.js)                     │
└──────────────────────┬──────────────────────────────────────────────┘
                       │ HTTP/REST
                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FastAPI Application Layer                       │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │
│  │  Data Source │  │ File Upload  │  │  Memory Management API   │ │
│  │    Routes    │  │   Routes     │  │      (NEW)               │ │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘ │
└──────────┬──────────────────┬────────────────────┬──────────────────┘
           │                  │                    │
           ▼                  ▼                    ▼
┌──────────────────┐  ┌──────────────┐  ┌─────────────────────────┐
│  DataSource      │  │  File Upload │  │   Memori Service        │
│  Service         │  │  Service     │  │   (NEW)                 │
└────────┬─────────┘  └──────┬───────┘  └───────┬─────────────────┘
         │                   │                   │
         │                   │                   ▼
         │                   │          ┌─────────────────────────┐
         │                   │          │  Claude API Service     │
         │                   │          │  + Memori Integration   │
         │                   │          └───────┬─────────────────┘
         │                   │                  │
         ▼                   ▼                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     PostgreSQL Database                              │
├─────────────────────────────────────────────────────────────────────┤
│  ┌───────────┐  ┌──────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ data_     │  │ file_    │  │ memori_      │  │ memori_      │  │
│  │ sources   │  │ uploads  │  │ conversations│  │ memories     │  │
│  └───────────┘  └──────────┘  └──────────────┘  └──────────────┘  │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │
│  │ memori_      │  │ memori_      │  │ memori_entities          │ │
│  │ rules        │  │ relationships│  │                          │ │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Data Flow Architecture

```
User Query → FastAPI → Claude Service → Memori Context Injection
                ↓                              ↓
         Query Analysis              Memory Retrieval (Semantic Search)
                ↓                              ↓
         SQL Generation ←──── Enriched Context + Historical Patterns
                ↓
         Result Execution
                ↓
    Memory Storage (Conscious Ingest) → PostgreSQL Memori Tables
```

---

## 2. Database Schema Design

### 2.1 Core Memori Tables

#### 2.1.1 `memori_conversations` - Conversation Sessions

```sql
CREATE TABLE memori_conversations (
    id SERIAL PRIMARY KEY,
    conversation_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    user_id VARCHAR(255),  -- For multi-tenant support
    data_source_id INTEGER REFERENCES data_sources(id) ON DELETE SET NULL,
    title VARCHAR(500),
    metadata JSONB DEFAULT '{}',  -- Store session-specific metadata
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_memori_conv_user ON memori_conversations(user_id);
CREATE INDEX idx_memori_conv_datasource ON memori_conversations(data_source_id);
CREATE INDEX idx_memori_conv_active ON memori_conversations(is_active);
CREATE INDEX idx_memori_conv_metadata ON memori_conversations USING GIN(metadata);
```

#### 2.1.2 `memori_memories` - Core Memory Storage

```sql
CREATE TABLE memori_memories (
    id SERIAL PRIMARY KEY,
    memory_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES memori_conversations(conversation_id) ON DELETE CASCADE,
    user_id VARCHAR(255),  -- Denormalized for faster queries

    -- Memory Content
    content TEXT NOT NULL,
    memory_type VARCHAR(50) NOT NULL,  -- 'short_term', 'long_term', 'rule', 'entity', 'relationship'

    -- Semantic Search Support
    embedding VECTOR(1536),  -- For pgvector extension (OpenAI ada-002 dimensions)

    -- Importance and Relevance
    importance_score FLOAT DEFAULT 0.5,  -- 0.0 to 1.0
    access_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP WITH TIME ZONE,

    -- Contextual Information
    context_tags TEXT[],  -- Array of tags for categorical filtering
    related_entities TEXT[],  -- Extracted entity names
    metadata JSONB DEFAULT '{}',

    -- Lifecycle Management
    expires_at TIMESTAMP WITH TIME ZONE,  -- For short-term memories
    is_archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_memori_mem_conv ON memori_memories(conversation_id);
CREATE INDEX idx_memori_mem_user ON memori_memories(user_id);
CREATE INDEX idx_memori_mem_type ON memori_memories(memory_type);
CREATE INDEX idx_memori_mem_importance ON memori_memories(importance_score DESC);
CREATE INDEX idx_memori_mem_tags ON memori_memories USING GIN(context_tags);
CREATE INDEX idx_memori_mem_entities ON memori_memories USING GIN(related_entities);
CREATE INDEX idx_memori_mem_metadata ON memori_memories USING GIN(metadata);
-- Vector similarity search index
CREATE INDEX idx_memori_mem_embedding ON memori_memories USING ivfflat (embedding vector_cosine_ops);
```

#### 2.1.3 `memori_entities` - Extracted Entities

```sql
CREATE TABLE memori_entities (
    id SERIAL PRIMARY KEY,
    entity_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    user_id VARCHAR(255),

    -- Entity Information
    entity_name VARCHAR(500) NOT NULL,
    entity_type VARCHAR(100),  -- 'table', 'column', 'database', 'user', 'concept'

    -- Associated Data Source
    data_source_id INTEGER REFERENCES data_sources(id) ON DELETE SET NULL,

    -- Entity Properties
    properties JSONB DEFAULT '{}',
    description TEXT,

    -- Statistics
    mention_count INTEGER DEFAULT 1,
    importance_score FLOAT DEFAULT 0.5,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_memori_entity_unique ON memori_entities(user_id, entity_name, entity_type);
CREATE INDEX idx_memori_entity_datasource ON memori_entities(data_source_id);
CREATE INDEX idx_memori_entity_type ON memori_entities(entity_type);
CREATE INDEX idx_memori_entity_props ON memori_entities USING GIN(properties);
```

#### 2.1.4 `memori_relationships` - Entity Relationships

```sql
CREATE TABLE memori_relationships (
    id SERIAL PRIMARY KEY,
    relationship_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    user_id VARCHAR(255),

    -- Relationship Endpoints
    source_entity_id UUID REFERENCES memori_entities(entity_id) ON DELETE CASCADE,
    target_entity_id UUID REFERENCES memori_entities(entity_id) ON DELETE CASCADE,

    -- Relationship Details
    relationship_type VARCHAR(100),  -- 'joins_with', 'filters_by', 'aggregates', 'related_to'
    strength FLOAT DEFAULT 0.5,  -- 0.0 to 1.0

    -- Context
    context TEXT,
    metadata JSONB DEFAULT '{}',

    usage_count INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_memori_rel_source ON memori_relationships(source_entity_id);
CREATE INDEX idx_memori_rel_target ON memori_relationships(target_entity_id);
CREATE INDEX idx_memori_rel_type ON memori_relationships(relationship_type);
CREATE INDEX idx_memori_rel_user ON memori_relationships(user_id);
```

#### 2.1.5 `memori_rules` - User Preferences and Business Rules

```sql
CREATE TABLE memori_rules (
    id SERIAL PRIMARY KEY,
    rule_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    user_id VARCHAR(255),
    data_source_id INTEGER REFERENCES data_sources(id) ON DELETE CASCADE,

    -- Rule Definition
    rule_name VARCHAR(255) NOT NULL,
    rule_type VARCHAR(50),  -- 'preference', 'constraint', 'transformation', 'validation'
    rule_content TEXT NOT NULL,

    -- Applicability
    conditions JSONB,  -- Conditions when rule applies
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,

    -- Usage Statistics
    application_count INTEGER DEFAULT 0,
    last_applied_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_memori_rules_user ON memori_rules(user_id);
CREATE INDEX idx_memori_rules_datasource ON memori_rules(data_source_id);
CREATE INDEX idx_memori_rules_type ON memori_rules(rule_type);
CREATE INDEX idx_memori_rules_active ON memori_rules(is_active);
```

#### 2.1.6 `memori_query_patterns` - Historical Query Analytics

```sql
CREATE TABLE memori_query_patterns (
    id SERIAL PRIMARY KEY,
    pattern_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    user_id VARCHAR(255),
    conversation_id UUID REFERENCES memori_conversations(conversation_id) ON DELETE SET NULL,
    data_source_id INTEGER REFERENCES data_sources(id) ON DELETE CASCADE,

    -- Query Information
    natural_language_query TEXT NOT NULL,
    generated_sql TEXT,
    query_intent VARCHAR(100),  -- 'select', 'aggregate', 'join', 'filter', 'group_by'

    -- Performance Metrics
    execution_time_ms INTEGER,
    result_row_count INTEGER,
    was_successful BOOLEAN DEFAULT TRUE,
    error_message TEXT,

    -- Pattern Recognition
    query_signature VARCHAR(500),  -- Normalized query pattern for deduplication
    tables_used TEXT[],
    columns_used TEXT[],

    -- Feedback and Learning
    user_satisfaction_score INTEGER,  -- 1-5 rating
    was_modified BOOLEAN DEFAULT FALSE,
    modification_notes TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_memori_qp_user ON memori_query_patterns(user_id);
CREATE INDEX idx_memori_qp_datasource ON memori_query_patterns(data_source_id);
CREATE INDEX idx_memori_qp_intent ON memori_query_patterns(query_intent);
CREATE INDEX idx_memori_qp_signature ON memori_query_patterns(query_signature);
CREATE INDEX idx_memori_qp_tables ON memori_query_patterns USING GIN(tables_used);
```

### 2.2 Database Extensions Required

```sql
-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgvector for semantic search (embeddings)
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable full-text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

---

## 3. Code Architecture

### 3.1 Directory Structure

```
backend/
├── src/
│   ├── api/
│   │   ├── datasources.py
│   │   ├── file_uploads.py
│   │   ├── file_preview.py
│   │   ├── memory.py                    # NEW: Memory management endpoints
│   │   └── conversations.py             # NEW: Conversation management
│   │
│   ├── models/
│   │   ├── datasource.py
│   │   ├── file_upload.py
│   │   ├── memory.py                    # NEW: Memori ORM models
│   │   ├── conversation.py              # NEW: Conversation ORM model
│   │   ├── entity.py                    # NEW: Entity ORM model
│   │   ├── relationship.py              # NEW: Relationship ORM model
│   │   ├── rule.py                      # NEW: Rule ORM model
│   │   └── query_pattern.py             # NEW: Query pattern ORM model
│   │
│   ├── services/
│   │   ├── datasource_service.py
│   │   ├── encryption.py
│   │   ├── claude/                      # NEW: Claude integration package
│   │   │   ├── __init__.py
│   │   │   ├── client.py                # Claude API client
│   │   │   ├── memori_client.py         # Memori-enabled Claude client
│   │   │   └── prompt_builder.py        # Context-aware prompt construction
│   │   │
│   │   ├── memori/                      # NEW: Memori service package
│   │   │   ├── __init__.py
│   │   │   ├── memory_manager.py        # Core memory management
│   │   │   ├── conversation_manager.py  # Conversation lifecycle
│   │   │   ├── entity_extractor.py      # Entity recognition
│   │   │   ├── relationship_mapper.py   # Relationship detection
│   │   │   ├── rule_engine.py           # Business rule application
│   │   │   ├── embedding_service.py     # Vector embedding generation
│   │   │   └── search_service.py        # Semantic memory search
│   │   │
│   │   └── text2sql/                    # NEW: Enhanced Text2SQL service
│   │       ├── __init__.py
│   │       ├── query_generator.py       # SQL generation with context
│   │       ├── query_optimizer.py       # Query optimization
│   │       └── pattern_analyzer.py      # Query pattern learning
│   │
│   ├── schemas/                          # NEW: Pydantic schemas
│   │   ├── memory.py
│   │   ├── conversation.py
│   │   └── query.py
│   │
│   ├── core/
│   │   ├── config.py                    # Configuration management
│   │   ├── security.py                  # Security utilities
│   │   └── dependencies.py              # FastAPI dependencies
│   │
│   ├── db/
│   │   ├── base.py
│   │   ├── config.py
│   │   └── session.py
│   │
│   └── main.py
│
├── migrations/
│   └── versions/
│       ├── 000_add_data_sources_table.py
│       ├── 001_add_file_uploads_table.py
│       ├── 002_add_file_metadata_table.py
│       ├── 003_add_memori_conversations.py    # NEW
│       ├── 004_add_memori_memories.py         # NEW
│       ├── 005_add_memori_entities.py         # NEW
│       ├── 006_add_memori_relationships.py    # NEW
│       ├── 007_add_memori_rules.py            # NEW
│       └── 008_add_memori_query_patterns.py   # NEW
│
├── tests/
│   ├── integration/
│   │   ├── test_memory_api.py           # NEW
│   │   └── test_claude_integration.py   # NEW
│   └── unit/
│       ├── test_memory_service.py       # NEW
│       └── test_entity_extraction.py    # NEW
│
└── pyproject.toml
```

### 3.2 Core Module Designs

#### 3.2.1 Memory Manager Service (`services/memori/memory_manager.py`)

```python
"""
Core memory management service integrating with Memori.

Responsibilities:
- Store and retrieve memories with semantic search
- Manage memory lifecycle (short-term to long-term promotion)
- Handle memory importance scoring
- Provide context-aware memory retrieval
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from pgvector.sqlalchemy import Vector

from src.models.memory import Memory, MemoryType
from src.services.memori.embedding_service import EmbeddingService


class MemoryManager:
    """
    Manages the complete lifecycle of memories in the Memori system.
    """

    def __init__(self, session: AsyncSession, user_id: str):
        self.session = session
        self.user_id = user_id
        self.embedding_service = EmbeddingService()

    async def store_memory(
        self,
        content: str,
        memory_type: MemoryType,
        conversation_id: UUID,
        importance_score: float = 0.5,
        context_tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        expires_at: Optional[datetime] = None
    ) -> Memory:
        """
        Store a new memory with semantic embedding.

        Args:
            content: The memory content (text)
            memory_type: Type of memory (short_term, long_term, rule, entity)
            conversation_id: Associated conversation
            importance_score: Initial importance (0.0-1.0)
            context_tags: Tags for categorical filtering
            metadata: Additional structured metadata
            expires_at: Optional expiration for short-term memories

        Returns:
            Memory: The created memory object
        """
        # Generate semantic embedding
        embedding = await self.embedding_service.generate_embedding(content)

        # Extract entities from content
        entities = await self._extract_entities(content)

        memory = Memory(
            user_id=self.user_id,
            conversation_id=conversation_id,
            content=content,
            memory_type=memory_type,
            embedding=embedding,
            importance_score=importance_score,
            context_tags=context_tags or [],
            related_entities=entities,
            metadata=metadata or {},
            expires_at=expires_at
        )

        self.session.add(memory)
        await self.session.commit()
        await self.session.refresh(memory)

        return memory

    async def retrieve_relevant_memories(
        self,
        query: str,
        conversation_id: Optional[UUID] = None,
        limit: int = 10,
        min_similarity: float = 0.7,
        memory_types: Optional[List[MemoryType]] = None,
        include_archived: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Retrieve memories using semantic similarity search.

        Args:
            query: The search query
            conversation_id: Optional conversation scope
            limit: Maximum number of memories to return
            min_similarity: Minimum cosine similarity threshold
            memory_types: Filter by memory types
            include_archived: Whether to include archived memories

        Returns:
            List of memories with similarity scores
        """
        # Generate query embedding
        query_embedding = await self.embedding_service.generate_embedding(query)

        # Build base query with vector similarity
        stmt = select(
            Memory,
            Memory.embedding.cosine_distance(query_embedding).label('distance')
        ).where(
            and_(
                Memory.user_id == self.user_id,
                Memory.is_archived == False if not include_archived else True,
                or_(
                    Memory.expires_at.is_(None),
                    Memory.expires_at > datetime.utcnow()
                )
            )
        )

        # Apply filters
        if conversation_id:
            stmt = stmt.where(Memory.conversation_id == conversation_id)

        if memory_types:
            stmt = stmt.where(Memory.memory_type.in_(memory_types))

        # Order by similarity and limit
        stmt = stmt.order_by('distance').limit(limit)

        result = await self.session.execute(stmt)
        memories = result.all()

        # Filter by minimum similarity and format results
        relevant_memories = []
        for memory, distance in memories:
            similarity = 1 - distance  # Convert distance to similarity
            if similarity >= min_similarity:
                await self._update_access_stats(memory)
                relevant_memories.append({
                    'memory': memory,
                    'similarity': similarity,
                    'content': memory.content,
                    'importance': memory.importance_score,
                    'tags': memory.context_tags,
                    'created_at': memory.created_at
                })

        return relevant_memories

    async def promote_to_long_term(self, memory_id: UUID) -> Memory:
        """
        Promote a short-term memory to long-term storage.

        Criteria for promotion:
        - High access count
        - High importance score
        - Referenced in multiple conversations
        """
        stmt = select(Memory).where(Memory.memory_id == memory_id)
        result = await self.session.execute(stmt)
        memory = result.scalar_one_or_none()

        if not memory:
            raise ValueError(f"Memory {memory_id} not found")

        memory.memory_type = MemoryType.LONG_TERM
        memory.expires_at = None  # Remove expiration
        memory.importance_score = min(1.0, memory.importance_score + 0.1)
        memory.updated_at = datetime.utcnow()

        await self.session.commit()
        return memory

    async def archive_old_memories(self, days_threshold: int = 30) -> int:
        """
        Archive memories older than threshold with low importance.

        Returns:
            Number of archived memories
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)

        stmt = select(Memory).where(
            and_(
                Memory.user_id == self.user_id,
                Memory.created_at < cutoff_date,
                Memory.importance_score < 0.3,
                Memory.access_count < 2,
                Memory.is_archived == False
            )
        )

        result = await self.session.execute(stmt)
        memories = result.scalars().all()

        for memory in memories:
            memory.is_archived = True
            memory.updated_at = datetime.utcnow()

        await self.session.commit()
        return len(memories)

    async def _update_access_stats(self, memory: Memory) -> None:
        """Update memory access statistics."""
        memory.access_count += 1
        memory.last_accessed_at = datetime.utcnow()
        # Boost importance slightly on access
        memory.importance_score = min(1.0, memory.importance_score + 0.01)
        await self.session.commit()

    async def _extract_entities(self, content: str) -> List[str]:
        """Extract entity names from content (placeholder for NER)."""
        # TODO: Implement with spaCy or Claude API entity extraction
        return []
```

#### 3.2.2 Claude API Client with Memori (`services/claude/memori_client.py`)

```python
"""
Claude API client with Memori context injection.

Integrates memory retrieval into Claude API calls for context-aware responses.
"""

import anthropic
from typing import List, Dict, Any, Optional
from uuid import UUID

from src.services.memori.memory_manager import MemoryManager
from src.services.memori.rule_engine import RuleEngine
from src.core.config import get_settings


class MemoriClaudeClient:
    """
    Enhanced Claude client with automatic memory context injection.
    """

    def __init__(self, user_id: str, session):
        self.settings = get_settings()
        self.client = anthropic.Anthropic(api_key=self.settings.ANTHROPIC_API_KEY)
        self.memory_manager = MemoryManager(session, user_id)
        self.rule_engine = RuleEngine(session, user_id)
        self.user_id = user_id

    async def generate_sql(
        self,
        natural_query: str,
        conversation_id: UUID,
        data_source_id: int,
        schema_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate SQL from natural language with memory-enhanced context.

        Args:
            natural_query: User's natural language query
            conversation_id: Current conversation ID
            data_source_id: Target data source
            schema_context: Database schema information

        Returns:
            Dict containing generated SQL and metadata
        """
        # 1. Retrieve relevant memories
        relevant_memories = await self.memory_manager.retrieve_relevant_memories(
            query=natural_query,
            conversation_id=conversation_id,
            limit=5,
            min_similarity=0.75
        )

        # 2. Get applicable rules
        applicable_rules = await self.rule_engine.get_applicable_rules(
            data_source_id=data_source_id,
            context={'query': natural_query}
        )

        # 3. Build enhanced prompt with context
        system_prompt = self._build_system_prompt(
            schema_context=schema_context,
            memories=relevant_memories,
            rules=applicable_rules
        )

        # 4. Call Claude API
        response = await self._call_claude_api(
            system_prompt=system_prompt,
            user_message=natural_query
        )

        # 5. Store interaction as memory
        await self.memory_manager.store_memory(
            content=f"Query: {natural_query}\nSQL: {response['sql']}",
            memory_type='short_term',
            conversation_id=conversation_id,
            importance_score=0.6,
            context_tags=['sql_generation', 'query'],
            metadata={
                'data_source_id': data_source_id,
                'intent': response.get('intent')
            }
        )

        return response

    def _build_system_prompt(
        self,
        schema_context: Dict[str, Any],
        memories: List[Dict[str, Any]],
        rules: List[Dict[str, Any]]
    ) -> str:
        """
        Build comprehensive system prompt with context injection.
        """
        prompt_parts = [
            "You are an expert SQL query generator for data analysis.",
            "\n## Database Schema\n",
            self._format_schema(schema_context),
        ]

        if memories:
            prompt_parts.extend([
                "\n## Relevant Historical Context\n",
                "Previous interactions and learned patterns:\n",
                self._format_memories(memories)
            ])

        if rules:
            prompt_parts.extend([
                "\n## User Preferences and Business Rules\n",
                self._format_rules(rules)
            ])

        prompt_parts.extend([
            "\n## Instructions\n",
            "- Generate syntactically correct SQL for the given database",
            "- Apply user preferences and business rules",
            "- Use historical patterns for similar queries",
            "- Explain your reasoning briefly",
            "- Return JSON format: {\"sql\": \"...\", \"explanation\": \"...\", \"intent\": \"...\"}"
        ])

        return "\n".join(prompt_parts)

    def _format_schema(self, schema: Dict[str, Any]) -> str:
        """Format database schema for prompt."""
        # Implementation details...
        pass

    def _format_memories(self, memories: List[Dict[str, Any]]) -> str:
        """Format relevant memories for prompt."""
        formatted = []
        for mem in memories:
            formatted.append(
                f"- [{mem['similarity']:.2f}] {mem['content'][:200]}"
            )
        return "\n".join(formatted)

    def _format_rules(self, rules: List[Dict[str, Any]]) -> str:
        """Format business rules for prompt."""
        formatted = []
        for rule in rules:
            formatted.append(f"- [{rule['type']}] {rule['content']}")
        return "\n".join(formatted)

    async def _call_claude_api(
        self,
        system_prompt: str,
        user_message: str
    ) -> Dict[str, Any]:
        """
        Execute Claude API call with structured output.
        """
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=2048,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )

            # Parse JSON response
            content = response.content[0].text
            # Parse and validate JSON...

            return {
                'sql': '...',  # Extracted from response
                'explanation': '...',
                'intent': '...',
                'raw_response': content
            }
        except Exception as e:
            raise RuntimeError(f"Claude API error: {str(e)}")
```

#### 3.2.3 API Endpoints (`api/memory.py`)

```python
"""
Memory management API endpoints.

Provides REST API for memory operations, conversation management,
and context retrieval.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_async_session
from src.schemas.memory import (
    MemoryCreate, MemoryResponse, MemorySearchRequest,
    ConversationResponse, ConversationCreate
)
from src.services.memori.memory_manager import MemoryManager
from src.services.memori.conversation_manager import ConversationManager
from src.core.dependencies import get_current_user


router = APIRouter(prefix="/api/memories", tags=["Memory Management"])


@router.post("/", response_model=MemoryResponse)
async def create_memory(
    memory_data: MemoryCreate,
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user)
):
    """
    Create a new memory entry.

    Stores content with semantic embedding for later retrieval.
    """
    manager = MemoryManager(session, user_id)

    memory = await manager.store_memory(
        content=memory_data.content,
        memory_type=memory_data.memory_type,
        conversation_id=memory_data.conversation_id,
        importance_score=memory_data.importance_score,
        context_tags=memory_data.context_tags,
        metadata=memory_data.metadata
    )

    return MemoryResponse.from_orm(memory)


@router.post("/search", response_model=List[MemoryResponse])
async def search_memories(
    search_request: MemorySearchRequest,
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user)
):
    """
    Search memories using semantic similarity.

    Returns memories ranked by relevance to the search query.
    """
    manager = MemoryManager(session, user_id)

    memories = await manager.retrieve_relevant_memories(
        query=search_request.query,
        conversation_id=search_request.conversation_id,
        limit=search_request.limit,
        min_similarity=search_request.min_similarity,
        memory_types=search_request.memory_types
    )

    return [
        MemoryResponse(
            **mem['memory'].__dict__,
            similarity_score=mem['similarity']
        )
        for mem in memories
    ]


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    conversation_data: ConversationCreate,
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user)
):
    """
    Create a new conversation session.
    """
    manager = ConversationManager(session, user_id)

    conversation = await manager.create_conversation(
        title=conversation_data.title,
        data_source_id=conversation_data.data_source_id,
        metadata=conversation_data.metadata
    )

    return ConversationResponse.from_orm(conversation)


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user)
):
    """
    Retrieve a conversation by ID with associated memories.
    """
    manager = ConversationManager(session, user_id)

    conversation = await manager.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return ConversationResponse.from_orm(conversation)


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user)
):
    """
    Delete a conversation and all associated memories.
    """
    manager = ConversationManager(session, user_id)

    success = await manager.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {"status": "success", "message": "Conversation deleted"}


@router.post("/maintenance/archive")
async def archive_old_memories(
    days_threshold: int = Query(30, ge=1, le=365),
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user)
):
    """
    Archive old, low-importance memories.

    Maintenance endpoint to clean up stale memories.
    """
    manager = MemoryManager(session, user_id)

    archived_count = await manager.archive_old_memories(days_threshold)

    return {
        "status": "success",
        "archived_count": archived_count,
        "threshold_days": days_threshold
    }
```

---

## 4. Configuration Management

### 4.1 Environment Variables (`backend/.env`)

```bash
# Existing configurations
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/text2sql

# Claude API
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Memori Configuration
MEMORI_ENABLED=true
MEMORI_EMBEDDING_MODEL=text-embedding-ada-002  # OpenAI for embeddings
MEMORI_EMBEDDING_DIMENSIONS=1536

# Memory Management
MEMORY_SHORT_TERM_EXPIRY_DAYS=7
MEMORY_ARCHIVE_THRESHOLD_DAYS=30
MEMORY_MAX_CONTEXT_MEMORIES=10
MEMORY_MIN_SIMILARITY_THRESHOLD=0.70

# Semantic Search
EMBEDDING_BATCH_SIZE=100
EMBEDDING_CACHE_TTL=3600

# Multi-tenancy (if applicable)
ENABLE_MULTI_TENANT=true
TENANT_ISOLATION_LEVEL=strict  # strict, relaxed
```

### 4.2 Settings Class (`core/config.py`)

```python
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Claude API
    ANTHROPIC_API_KEY: str

    # Memori
    MEMORI_ENABLED: bool = True
    MEMORI_EMBEDDING_MODEL: str = "text-embedding-ada-002"
    MEMORI_EMBEDDING_DIMENSIONS: int = 1536

    # Memory management
    MEMORY_SHORT_TERM_EXPIRY_DAYS: int = 7
    MEMORY_ARCHIVE_THRESHOLD_DAYS: int = 30
    MEMORY_MAX_CONTEXT_MEMORIES: int = 10
    MEMORY_MIN_SIMILARITY_THRESHOLD: float = 0.70

    # Semantic search
    EMBEDDING_BATCH_SIZE: int = 100
    EMBEDDING_CACHE_TTL: int = 3600

    # Multi-tenancy
    ENABLE_MULTI_TENANT: bool = True
    TENANT_ISOLATION_LEVEL: str = "strict"

    class Config:
        env_file = ".env"
        case_sensitive = True


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
```

---

## 5. Implementation Roadmap

### Phase 1: Database Foundation (Week 1)

**Tasks:**
1. Install pgvector extension on PostgreSQL
2. Create Alembic migrations for all Memori tables
3. Implement ORM models for all Memori entities
4. Write database initialization scripts
5. Create test fixtures for development

**Deliverables:**
- All 6 migration files
- 6 ORM model files
- Database setup documentation

### Phase 2: Core Memory Services (Week 2)

**Tasks:**
1. Implement `MemoryManager` service
2. Implement `EmbeddingService` for vector generation
3. Implement `ConversationManager` service
4. Implement `EntityExtractor` service
5. Write unit tests for all services

**Deliverables:**
- 5 service modules
- 90%+ test coverage
- Service integration tests

### Phase 3: Claude Integration (Week 3)

**Tasks:**
1. Implement `MemoriClaudeClient`
2. Implement `PromptBuilder` with context injection
3. Implement `RuleEngine` for business rules
4. Create Text2SQL query generator with memory
5. Integration testing with Claude API

**Deliverables:**
- Claude integration module
- Enhanced Text2SQL generator
- API integration tests

### Phase 4: API Development (Week 4)

**Tasks:**
1. Implement memory management endpoints
2. Implement conversation endpoints
3. Implement search and retrieval endpoints
4. Add authentication and authorization
5. API documentation (OpenAPI/Swagger)

**Deliverables:**
- Complete REST API
- API documentation
- Postman/Thunder Client collection

### Phase 5: Production Readiness (Week 5)

**Tasks:**
1. Performance optimization (query tuning, caching)
2. Security hardening (input validation, rate limiting)
3. Monitoring and logging setup
4. Error handling and recovery
5. Load testing and benchmarking

**Deliverables:**
- Performance benchmarks
- Security audit report
- Monitoring dashboards
- Deployment guide

---

## 6. Performance Optimization Strategies

### 6.1 Database Optimization

**Indexing Strategy:**
```sql
-- Vector search optimization
CREATE INDEX CONCURRENTLY idx_memori_mem_embedding_hnsw
ON memori_memories USING hnsw (embedding vector_cosine_ops);

-- Partitioning for large datasets
CREATE TABLE memori_memories_2024_q1
PARTITION OF memori_memories
FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');

-- Materialized views for analytics
CREATE MATERIALIZED VIEW memori_popular_entities AS
SELECT entity_name, entity_type, COUNT(*) as mention_count
FROM memori_entities
GROUP BY entity_name, entity_type
ORDER BY mention_count DESC;
```

**Query Optimization:**
- Use connection pooling (already configured in `db/config.py`)
- Implement query result caching with Redis
- Batch embedding generation for multiple memories
- Use prepared statements for frequent queries

### 6.2 Caching Strategy

```python
# Redis caching for embeddings and frequent queries
from redis import asyncio as aioredis

class MemoryCacheService:
    def __init__(self):
        self.redis = aioredis.from_url("redis://localhost:6379")

    async def cache_embedding(self, text: str, embedding: List[float]):
        cache_key = f"emb:{hash(text)}"
        await self.redis.setex(
            cache_key,
            3600,  # 1 hour TTL
            json.dumps(embedding)
        )

    async def get_cached_embedding(self, text: str) -> Optional[List[float]]:
        cache_key = f"emb:{hash(text)}"
        cached = await self.redis.get(cache_key)
        return json.loads(cached) if cached else None
```

### 6.3 Embedding Generation Optimization

```python
# Batch embedding generation
class BatchEmbeddingService:
    async def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """Generate embeddings in batches for efficiency."""
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = await self._call_embedding_api(batch)
            embeddings.extend(batch_embeddings)

        return embeddings
```

---

## 7. Security Considerations

### 7.1 Data Isolation (Multi-tenancy)

```python
# Enforce user_id filtering at ORM level
class UserScopedQuery:
    """Automatically filter queries by user_id."""

    @staticmethod
    def filter_by_user(query, user_id: str):
        return query.where(Memory.user_id == user_id)

# Row-level security in PostgreSQL
ALTER TABLE memori_memories ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_isolation_policy ON memori_memories
    USING (user_id = current_setting('app.current_user_id')::text);
```

### 7.2 API Security

```python
# Rate limiting
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/search")
@limiter.limit("10/minute")
async def search_memories(...):
    # Implementation
    pass

# Input validation
from pydantic import BaseModel, validator, Field

class MemoryCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)

    @validator('content')
    def sanitize_content(cls, v):
        # Remove potential SQL injection or XSS content
        return bleach.clean(v)
```

### 7.3 Sensitive Data Protection

```python
# Encrypt sensitive memory content
class SensitiveMemoryManager(MemoryManager):
    async def store_sensitive_memory(self, content: str, **kwargs):
        # Encrypt before storing
        encrypted_content = self.cipher.encrypt(content)
        return await super().store_memory(
            content=encrypted_content,
            metadata={**kwargs.get('metadata', {}), 'encrypted': True}
        )
```

### 7.4 API Key Management

```python
# Secure API key storage and rotation
class APIKeyManager:
    async def rotate_claude_key(self):
        """Implement key rotation without downtime."""
        # Use AWS Secrets Manager or HashiCorp Vault
        pass

    async def validate_api_key(self, key: str) -> bool:
        """Validate API key before usage."""
        # Check key format, expiration, permissions
        pass
```

---

## 8. Monitoring and Observability

### 8.1 Logging Strategy

```python
import structlog

logger = structlog.get_logger()

class MemoryManagerInstrumented(MemoryManager):
    async def store_memory(self, content: str, **kwargs):
        logger.info(
            "memory.store",
            user_id=self.user_id,
            memory_type=kwargs.get('memory_type'),
            content_length=len(content)
        )

        try:
            memory = await super().store_memory(content, **kwargs)
            logger.info("memory.store.success", memory_id=str(memory.memory_id))
            return memory
        except Exception as e:
            logger.error(
                "memory.store.failed",
                error=str(e),
                error_type=type(e).__name__
            )
            raise
```

### 8.2 Metrics Collection

```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
memory_store_counter = Counter(
    'memori_memory_stored_total',
    'Total memories stored',
    ['memory_type', 'user_id']
)

memory_search_duration = Histogram(
    'memori_search_duration_seconds',
    'Time spent on memory search',
    ['user_id']
)

active_conversations = Gauge(
    'memori_active_conversations',
    'Number of active conversations'
)

# Use in code
@memory_search_duration.time()
async def retrieve_relevant_memories(self, ...):
    # Implementation
    pass
```

### 8.3 Health Checks

```python
@router.get("/health/memori")
async def memori_health_check(
    session: AsyncSession = Depends(get_async_session)
):
    """
    Comprehensive health check for Memori services.
    """
    checks = {}

    # Database connectivity
    try:
        await session.execute(text("SELECT 1"))
        checks['database'] = 'healthy'
    except Exception as e:
        checks['database'] = f'unhealthy: {str(e)}'

    # pgvector extension
    try:
        await session.execute(text("SELECT * FROM pg_extension WHERE extname='vector'"))
        checks['pgvector'] = 'healthy'
    except Exception:
        checks['pgvector'] = 'unhealthy'

    # Claude API
    try:
        # Test API key validity
        checks['claude_api'] = 'healthy'
    except Exception as e:
        checks['claude_api'] = f'unhealthy: {str(e)}'

    # Embedding service
    try:
        # Test embedding generation
        checks['embedding_service'] = 'healthy'
    except Exception as e:
        checks['embedding_service'] = f'unhealthy: {str(e)}'

    overall_healthy = all(v == 'healthy' for v in checks.values())

    return {
        'status': 'healthy' if overall_healthy else 'degraded',
        'checks': checks
    }
```

---

## 9. Testing Strategy

### 9.1 Unit Tests

```python
# tests/unit/test_memory_manager.py
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_store_memory():
    """Test memory storage with embedding generation."""
    session = AsyncMock()
    manager = MemoryManager(session, user_id="test_user")

    with patch.object(manager.embedding_service, 'generate_embedding') as mock_embed:
        mock_embed.return_value = [0.1] * 1536

        memory = await manager.store_memory(
            content="Test memory content",
            memory_type=MemoryType.SHORT_TERM,
            conversation_id=UUID('...')
        )

        assert memory.content == "Test memory content"
        assert memory.user_id == "test_user"
        mock_embed.assert_called_once()

@pytest.mark.asyncio
async def test_semantic_search():
    """Test semantic similarity search."""
    # Implementation
    pass
```

### 9.2 Integration Tests

```python
# tests/integration/test_claude_memori_integration.py
import pytest

@pytest.mark.asyncio
async def test_sql_generation_with_memory_context(
    test_db_session,
    claude_client,
    sample_conversation
):
    """Test SQL generation enriched with memory context."""
    # Store some historical context
    await memory_manager.store_memory(
        content="User prefers using aliases for all tables",
        memory_type=MemoryType.RULE,
        conversation_id=sample_conversation.id
    )

    # Generate SQL
    result = await claude_client.generate_sql(
        natural_query="Show me all users",
        conversation_id=sample_conversation.id,
        data_source_id=1,
        schema_context={'tables': [...]}
    )

    # Verify rule was applied
    assert 'AS' in result['sql']  # Aliases used
    assert result['explanation']  # Has explanation
```

### 9.3 Performance Tests

```python
# tests/performance/test_memory_search_performance.py
import pytest
from time import time

@pytest.mark.benchmark
async def test_search_performance_with_large_memory_base(
    test_db_session,
    memory_manager
):
    """Benchmark search with 10,000 memories."""
    # Seed database with 10k memories
    for i in range(10000):
        await memory_manager.store_memory(...)

    start = time()
    results = await memory_manager.retrieve_relevant_memories(
        query="test query",
        limit=10
    )
    duration = time() - start

    assert duration < 0.5  # Must complete in < 500ms
    assert len(results) == 10
```

---

## 10. Deployment Considerations

### 10.1 Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.12-slim

# Install system dependencies including pgvector
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-dev

# Copy application
COPY . .

CMD ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: text2sql
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql+asyncpg://admin:secure_password@postgres:5432/text2sql
      REDIS_URL: redis://redis:6379
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app

volumes:
  postgres_data:
```

### 10.2 Production Checklist

- [ ] Enable SSL/TLS for database connections
- [ ] Configure connection pooling limits
- [ ] Set up automated database backups
- [ ] Enable query logging for debugging
- [ ] Configure rate limiting on API endpoints
- [ ] Set up monitoring with Prometheus/Grafana
- [ ] Configure log aggregation (ELK or CloudWatch)
- [ ] Implement circuit breakers for external APIs
- [ ] Set up API key rotation schedule
- [ ] Configure CORS policies
- [ ] Enable gzip compression for responses
- [ ] Set up CDN for static assets
- [ ] Configure auto-scaling policies
- [ ] Implement graceful shutdown handlers
- [ ] Set up disaster recovery procedures

---

## 11. Cost Estimation

### 11.1 Infrastructure Costs (Monthly, AWS)

| Component | Configuration | Estimated Cost |
|-----------|--------------|----------------|
| RDS PostgreSQL | db.t3.medium (2vCPU, 4GB) | $60-80 |
| ElastiCache Redis | cache.t3.micro | $15-20 |
| EC2/ECS | t3.medium x2 instances | $60-80 |
| Load Balancer | Application LB | $20-25 |
| Storage (EBS) | 100GB SSD | $10-15 |
| **Total Infrastructure** | | **$165-220/month** |

### 11.2 API Costs

| Service | Usage | Estimated Cost |
|---------|-------|----------------|
| Anthropic Claude | 1M tokens/day | $30-100/month |
| OpenAI Embeddings | 100k embeddings/day | $10-30/month |
| **Total API Costs** | | **$40-130/month** |

**Total Estimated Cost: $205-350/month** (for moderate usage)

---

## 12. FAQ and Troubleshooting

### Q1: How does Memori handle memory conflicts?

**A:** Memori uses importance scoring and recency to resolve conflicts. Newer memories with higher importance scores take precedence. The system also implements memory consolidation to merge similar memories.

### Q2: What happens if the embedding service is down?

**A:** The system falls back to keyword-based search using PostgreSQL full-text search. Memories are queued for embedding generation once the service recovers.

### Q3: How to migrate existing conversation history?

**A:** Use the provided migration script:
```bash
poetry run python scripts/migrate_conversation_history.py --source=legacy_db --target=memori
```

### Q4: How to scale for high traffic?

**A:**
1. Enable read replicas for PostgreSQL
2. Implement Redis caching for frequent queries
3. Use Celery for async embedding generation
4. Deploy multiple backend instances behind load balancer

### Q5: How to debug slow memory searches?

**A:**
```sql
-- Analyze query performance
EXPLAIN ANALYZE
SELECT * FROM memori_memories
WHERE embedding <-> '[...]' < 0.3
LIMIT 10;

-- Check index usage
SELECT * FROM pg_stat_user_indexes
WHERE tablename = 'memori_memories';
```

---

## 13. Next Steps

### Immediate Actions (This Week)

1. **Review and approve this architecture document**
2. **Set up development environment with pgvector**
3. **Create initial database migrations**
4. **Start implementing core MemoryManager service**

### Short-term Goals (Next 2 Weeks)

1. Complete Phase 1 (Database Foundation)
2. Start Phase 2 (Core Memory Services)
3. Set up CI/CD pipeline for testing
4. Create development documentation

### Long-term Goals (Next 2 Months)

1. Complete all 5 implementation phases
2. Conduct comprehensive testing
3. Deploy to staging environment
4. Gather user feedback and iterate
5. Production deployment with monitoring

---

## 14. References and Resources

### Documentation
- [Memori GitHub Repository](https://github.com/GibsonAI/Memori)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)

### Similar Implementations
- LangChain Memory Module
- ChromaDB for semantic search
- Pinecone vector database patterns

### Tools and Libraries
- **pgvector**: PostgreSQL extension for vector similarity search
- **Anthropic SDK**: Official Python client for Claude
- **SQLAlchemy 2.0**: Modern async ORM
- **Alembic**: Database migrations
- **Pydantic**: Data validation
- **pytest-asyncio**: Async testing

---

## Appendix A: Dependency Updates

Add to `pyproject.toml`:

```toml
[tool.poetry.dependencies]
python = "^3.12"
# Existing dependencies...
anthropic = "^0.18.0"  # Claude API
pgvector = "^0.2.4"    # PostgreSQL vector extension
openai = "^1.12.0"     # For embedding generation
redis = "^5.0.1"       # Caching
celery = "^5.3.4"      # Async task processing
prometheus-client = "^0.19.0"  # Metrics
structlog = "^24.1.0"  # Structured logging
slowapi = "^0.1.9"     # Rate limiting
bleach = "^6.1.0"      # Input sanitization
```

---

## Appendix B: Migration Example

```python
# migrations/versions/003_add_memori_conversations.py
"""Add memori conversations table

Revision ID: 003
Revises: 002
Create Date: 2024-11-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'memori_conversations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('conversation_id', UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('user_id', sa.String(255)),
        sa.Column('data_source_id', sa.Integer(), sa.ForeignKey('data_sources.id', ondelete='SET NULL')),
        sa.Column('title', sa.String(500)),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )

    # Create indexes
    op.create_index('idx_memori_conv_user', 'memori_conversations', ['user_id'])
    op.create_index('idx_memori_conv_datasource', 'memori_conversations', ['data_source_id'])
    op.create_index('idx_memori_conv_active', 'memori_conversations', ['is_active'])
    op.create_index('idx_memori_conv_metadata', 'memori_conversations', ['metadata'], postgresql_using='gin')


def downgrade():
    op.drop_table('memori_conversations')
```

---

**Document Version:** 1.0
**Last Updated:** 2025-11-11
**Author:** Backend Architecture Team
**Status:** Awaiting Approval


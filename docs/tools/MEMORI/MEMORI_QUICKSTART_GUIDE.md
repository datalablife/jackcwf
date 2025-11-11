# Memori Integration Quick-Start Guide

## Overview

This guide provides step-by-step instructions to integrate Memori into your Text2SQL project. Follow these steps to get started quickly.

---

## Prerequisites

### System Requirements
- Python 3.12+
- PostgreSQL 16+ with pgvector extension
- Redis 7+ (for caching)
- 8GB+ RAM recommended
- Anthropic Claude API key

### Required Knowledge
- FastAPI framework basics
- SQLAlchemy ORM
- Async/await patterns in Python
- Basic PostgreSQL administration

---

## Step-by-Step Implementation

### Step 1: Install Dependencies

```bash
cd backend

# Add required dependencies
poetry add anthropic pgvector openai redis celery prometheus-client structlog slowapi bleach

# Install development dependencies
poetry add --group dev pytest-benchmark

# Update dependencies
poetry lock
poetry install
```

### Step 2: Enable pgvector Extension

Connect to your PostgreSQL database:

```bash
psql -U your_user -d text2sql
```

Enable the extension:

```sql
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Verify installation
SELECT * FROM pg_extension WHERE extname IN ('vector', 'uuid-ossp', 'pg_trgm');
```

### Step 3: Update Environment Variables

Edit `backend/.env`:

```bash
# Existing configuration
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/text2sql

# Add Memori configuration
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Memori settings
MEMORI_ENABLED=true
MEMORI_EMBEDDING_MODEL=text-embedding-ada-002
MEMORI_EMBEDDING_DIMENSIONS=1536

# Memory management
MEMORY_SHORT_TERM_EXPIRY_DAYS=7
MEMORY_ARCHIVE_THRESHOLD_DAYS=30
MEMORY_MAX_CONTEXT_MEMORIES=10
MEMORY_MIN_SIMILARITY_THRESHOLD=0.70

# OpenAI (for embeddings)
OPENAI_API_KEY=sk-your-openai-key-here

# Redis (optional, for caching)
REDIS_URL=redis://localhost:6379/0

# Performance
EMBEDDING_BATCH_SIZE=100
EMBEDDING_CACHE_TTL=3600
```

### Step 4: Create Database Migrations

Create migration files in `backend/migrations/versions/`:

#### Migration 003: Conversations Table

```bash
cd backend
poetry run alembic revision -m "add_memori_conversations"
```

Copy the following content to the generated migration file:

```python
"""Add memori conversations table

Revision ID: 003_add_memori_conversations
Revises: 002
Create Date: 2024-11-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '003'
down_revision = '002'


def upgrade():
    op.create_table(
        'memori_conversations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('conversation_id', UUID(as_uuid=True), nullable=False, unique=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.String(255)),
        sa.Column('data_source_id', sa.Integer(), sa.ForeignKey('data_sources.id', ondelete='SET NULL')),
        sa.Column('title', sa.String(500)),
        sa.Column('metadata', JSONB, server_default='{}'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )

    op.create_index('idx_memori_conv_user', 'memori_conversations', ['user_id'])
    op.create_index('idx_memori_conv_datasource', 'memori_conversations', ['data_source_id'])
    op.create_index('idx_memori_conv_active', 'memori_conversations', ['is_active'])
    op.create_index('idx_memori_conv_metadata', 'memori_conversations', ['metadata'], postgresql_using='gin')


def downgrade():
    op.drop_table('memori_conversations')
```

#### Migration 004: Memories Table

```bash
poetry run alembic revision -m "add_memori_memories"
```

```python
"""Add memori memories table

Revision ID: 004_add_memori_memories
Revises: 003
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from pgvector.sqlalchemy import Vector

revision = '004'
down_revision = '003'


def upgrade():
    op.create_table(
        'memori_memories',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('memory_id', UUID(as_uuid=True), nullable=False, unique=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('conversation_id', UUID(as_uuid=True), sa.ForeignKey('memori_conversations.conversation_id', ondelete='CASCADE')),
        sa.Column('user_id', sa.String(255)),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('memory_type', sa.String(50), nullable=False),
        sa.Column('embedding', Vector(1536)),  # OpenAI ada-002 dimensions
        sa.Column('importance_score', sa.Float(), server_default='0.5'),
        sa.Column('access_count', sa.Integer(), server_default='0'),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True)),
        sa.Column('context_tags', ARRAY(sa.Text()), server_default='{}'),
        sa.Column('related_entities', ARRAY(sa.Text()), server_default='{}'),
        sa.Column('metadata', JSONB, server_default='{}'),
        sa.Column('expires_at', sa.DateTime(timezone=True)),
        sa.Column('is_archived', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )

    op.create_index('idx_memori_mem_conv', 'memori_memories', ['conversation_id'])
    op.create_index('idx_memori_mem_user', 'memori_memories', ['user_id'])
    op.create_index('idx_memori_mem_type', 'memori_memories', ['memory_type'])
    op.create_index('idx_memori_mem_importance', 'memori_memories', [sa.text('importance_score DESC')])
    op.create_index('idx_memori_mem_tags', 'memori_memories', ['context_tags'], postgresql_using='gin')
    op.create_index('idx_memori_mem_entities', 'memori_memories', ['related_entities'], postgresql_using='gin')
    op.create_index('idx_memori_mem_metadata', 'memori_memories', ['metadata'], postgresql_using='gin')

    # Vector similarity search index (HNSW for better performance)
    op.execute('CREATE INDEX idx_memori_mem_embedding ON memori_memories USING hnsw (embedding vector_cosine_ops)')


def downgrade():
    op.drop_table('memori_memories')
```

#### Run Migrations

```bash
# Apply all migrations
poetry run alembic upgrade head

# Verify tables created
psql -U your_user -d text2sql -c "\dt memori_*"
```

### Step 5: Create Core Models

Create `backend/src/models/memory.py`:

```python
"""
Memory ORM models for Memori integration.
"""
from enum import Enum
from sqlalchemy import Column, String, Text, Float, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from pgvector.sqlalchemy import Vector
from src.db.base import BaseModel


class MemoryType(str, Enum):
    """Types of memories in the system."""
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    RULE = "rule"
    ENTITY = "entity"
    RELATIONSHIP = "relationship"


class Memory(BaseModel):
    """
    Core memory storage model.

    Stores conversation context with semantic embeddings for intelligent retrieval.
    """
    __tablename__ = "memori_memories"

    memory_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('memori_conversations.conversation_id', ondelete='CASCADE'))
    user_id = Column(String(255), nullable=False, index=True)

    content = Column(Text, nullable=False)
    memory_type = Column(String(50), nullable=False, index=True)

    # Vector embedding for semantic search
    embedding = Column(Vector(1536))

    # Importance and usage metrics
    importance_score = Column(Float, default=0.5)
    access_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime(timezone=True))

    # Contextual metadata
    context_tags = Column(ARRAY(Text), default=[])
    related_entities = Column(ARRAY(Text), default=[])
    metadata = Column(JSONB, default={})

    # Lifecycle
    expires_at = Column(DateTime(timezone=True))
    is_archived = Column(Boolean, default=False)

    def __repr__(self):
        return f"<Memory {self.memory_id} type={self.memory_type} user={self.user_id}>"
```

Create `backend/src/models/conversation.py`:

```python
"""
Conversation ORM model for grouping related memories.
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from src.db.base import BaseModel


class Conversation(BaseModel):
    """
    Conversation session model.

    Groups related memories and provides context isolation.
    """
    __tablename__ = "memori_conversations"

    conversation_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    user_id = Column(String(255), index=True)
    data_source_id = Column(Integer, ForeignKey('data_sources.id', ondelete='SET NULL'))

    title = Column(String(500))
    metadata = Column(JSONB, default={})

    is_active = Column(Boolean, default=True)
    last_activity_at = Column(DateTime(timezone=True))

    # Relationships
    memories = relationship("Memory", backref="conversation", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Conversation {self.conversation_id} title={self.title}>"
```

Update `backend/src/models/__init__.py`:

```python
# Add to existing imports
from .memory import Memory, MemoryType
from .conversation import Conversation

# Add to __all__
__all__ = [
    # ... existing exports
    "Memory",
    "MemoryType",
    "Conversation",
]
```

### Step 6: Implement Core Services

Create `backend/src/services/memori/__init__.py`:

```python
"""
Memori service package for memory management.
"""
from .memory_manager import MemoryManager
from .conversation_manager import ConversationManager
from .embedding_service import EmbeddingService

__all__ = [
    "MemoryManager",
    "ConversationManager",
    "EmbeddingService",
]
```

Create `backend/src/services/memori/embedding_service.py`:

```python
"""
Embedding generation service using OpenAI API.
"""
import openai
from typing import List
from src.core.config import get_settings


class EmbeddingService:
    """
    Generate semantic embeddings for text content.
    """

    def __init__(self):
        self.settings = get_settings()
        openai.api_key = self.settings.OPENAI_API_KEY
        self.model = self.settings.MEMORI_EMBEDDING_MODEL

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for given text.

        Args:
            text: Input text to embed

        Returns:
            List of floats representing the embedding vector
        """
        try:
            response = await openai.Embedding.acreate(
                model=self.model,
                input=text
            )
            return response['data'][0]['embedding']
        except Exception as e:
            raise RuntimeError(f"Failed to generate embedding: {str(e)}")

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.

        More efficient for bulk operations.
        """
        try:
            response = await openai.Embedding.acreate(
                model=self.model,
                input=texts
            )
            return [item['embedding'] for item in response['data']]
        except Exception as e:
            raise RuntimeError(f"Failed to generate batch embeddings: {str(e)}")
```

Create a minimal `backend/src/services/memori/memory_manager.py`:

```python
"""
Core memory management service.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from src.models.memory import Memory, MemoryType
from src.services.memori.embedding_service import EmbeddingService


class MemoryManager:
    """
    Manages memory storage and retrieval with semantic search.
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
        metadata: Optional[Dict[str, Any]] = None
    ) -> Memory:
        """
        Store a new memory with semantic embedding.
        """
        # Generate embedding
        embedding = await self.embedding_service.generate_embedding(content)

        memory = Memory(
            user_id=self.user_id,
            conversation_id=conversation_id,
            content=content,
            memory_type=memory_type.value,
            embedding=embedding,
            importance_score=importance_score,
            context_tags=context_tags or [],
            metadata=metadata or {}
        )

        self.session.add(memory)
        await self.session.commit()
        await self.session.refresh(memory)

        return memory

    async def retrieve_relevant_memories(
        self,
        query: str,
        conversation_id: Optional[UUID] = None,
        limit: int = 10
    ) -> List[Memory]:
        """
        Retrieve memories using semantic similarity search.
        """
        # Generate query embedding
        query_embedding = await self.embedding_service.generate_embedding(query)

        # Build query with vector similarity
        stmt = select(Memory).where(
            Memory.user_id == self.user_id
        ).order_by(
            Memory.embedding.cosine_distance(query_embedding)
        ).limit(limit)

        if conversation_id:
            stmt = stmt.where(Memory.conversation_id == conversation_id)

        result = await self.session.execute(stmt)
        return result.scalars().all()
```

### Step 7: Create API Endpoints

Create `backend/src/api/memory.py`:

```python
"""
Memory management API endpoints.
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from src.db import get_async_session
from src.services.memori.memory_manager import MemoryManager
from src.models.memory import MemoryType


router = APIRouter(prefix="/api/memories", tags=["Memory Management"])


class MemoryCreateRequest(BaseModel):
    content: str
    memory_type: MemoryType
    conversation_id: UUID
    importance_score: float = 0.5
    context_tags: List[str] = []


class MemorySearchRequest(BaseModel):
    query: str
    conversation_id: UUID = None
    limit: int = 10


@router.post("/")
async def create_memory(
    request: MemoryCreateRequest,
    session: AsyncSession = Depends(get_async_session),
    user_id: str = "default_user"  # TODO: Get from auth
):
    """Create a new memory."""
    manager = MemoryManager(session, user_id)

    memory = await manager.store_memory(
        content=request.content,
        memory_type=request.memory_type,
        conversation_id=request.conversation_id,
        importance_score=request.importance_score,
        context_tags=request.context_tags
    )

    return {
        "memory_id": str(memory.memory_id),
        "content": memory.content,
        "memory_type": memory.memory_type,
        "created_at": memory.created_at.isoformat()
    }


@router.post("/search")
async def search_memories(
    request: MemorySearchRequest,
    session: AsyncSession = Depends(get_async_session),
    user_id: str = "default_user"
):
    """Search memories using semantic similarity."""
    manager = MemoryManager(session, user_id)

    memories = await manager.retrieve_relevant_memories(
        query=request.query,
        conversation_id=request.conversation_id,
        limit=request.limit
    )

    return {
        "results": [
            {
                "memory_id": str(m.memory_id),
                "content": m.content,
                "memory_type": m.memory_type,
                "importance_score": m.importance_score,
                "created_at": m.created_at.isoformat()
            }
            for m in memories
        ]
    }
```

Register the router in `backend/src/main.py`:

```python
# Add import
from src.api import memory

# Add to create_app()
def create_app() -> FastAPI:
    # ... existing code ...

    # Include routers
    app.include_router(datasources.router)
    app.include_router(file_uploads.router)
    app.include_router(file_preview.router)
    app.include_router(memory.router)  # NEW

    # ... rest of code ...
```

### Step 8: Test the Integration

Create a test script `backend/test_memori_integration.py`:

```python
"""
Quick test script for Memori integration.
"""
import asyncio
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.models.conversation import Conversation
from src.services.memori.memory_manager import MemoryManager
from src.models.memory import MemoryType


async def test_memori():
    # Create database session
    engine = create_async_engine("postgresql+asyncpg://user:password@localhost/text2sql")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Create conversation
        conversation = Conversation(
            conversation_id=uuid4(),
            user_id="test_user",
            title="Test Conversation"
        )
        session.add(conversation)
        await session.commit()

        print(f"Created conversation: {conversation.conversation_id}")

        # Create memory manager
        manager = MemoryManager(session, user_id="test_user")

        # Store some memories
        memory1 = await manager.store_memory(
            content="User prefers using table aliases in SQL queries",
            memory_type=MemoryType.RULE,
            conversation_id=conversation.conversation_id,
            importance_score=0.8,
            context_tags=["preference", "sql"]
        )
        print(f"Stored memory 1: {memory1.memory_id}")

        memory2 = await manager.store_memory(
            content="The customers table has columns: id, name, email, created_at",
            memory_type=MemoryType.ENTITY,
            conversation_id=conversation.conversation_id,
            importance_score=0.7,
            context_tags=["schema", "table"]
        )
        print(f"Stored memory 2: {memory2.memory_id}")

        # Search for relevant memories
        print("\nSearching for 'SQL query preferences'...")
        results = await manager.retrieve_relevant_memories(
            query="SQL query preferences",
            conversation_id=conversation.conversation_id,
            limit=5
        )

        print(f"Found {len(results)} relevant memories:")
        for mem in results:
            print(f"  - [{mem.memory_type}] {mem.content[:100]}")

        print("\n✓ Memori integration test completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_memori())
```

Run the test:

```bash
cd backend
poetry run python test_memori_integration.py
```

### Step 9: Test via API

Start the server:

```bash
poetry run uvicorn src.main:app --reload --port 8000
```

Test with curl:

```bash
# Create a conversation first (you'll need to implement this endpoint)
CONV_ID=$(uuidgen)

# Store a memory
curl -X POST http://localhost:8000/api/memories/ \
  -H "Content-Type: application/json" \
  -d "{
    \"content\": \"User prefers using JOINs instead of subqueries\",
    \"memory_type\": \"rule\",
    \"conversation_id\": \"$CONV_ID\",
    \"importance_score\": 0.8,
    \"context_tags\": [\"preference\", \"sql\"]
  }"

# Search memories
curl -X POST http://localhost:8000/api/memories/search \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"How does the user prefer SQL queries?\",
    \"conversation_id\": \"$CONV_ID\",
    \"limit\": 5
  }"
```

---

## Common Issues and Solutions

### Issue 1: pgvector Extension Not Found

**Error:** `extension "vector" is not available`

**Solution:**
```bash
# On Ubuntu/Debian
sudo apt-get install postgresql-16-pgvector

# On macOS with Homebrew
brew install pgvector

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### Issue 2: Embedding API Errors

**Error:** `Failed to generate embedding: Unauthorized`

**Solution:**
- Verify `OPENAI_API_KEY` in `.env` file
- Check API key has sufficient credits
- Test API key: `curl https://api.openai.com/v1/models -H "Authorization: Bearer YOUR_KEY"`

### Issue 3: Slow Vector Search

**Error:** Searches taking > 1 second

**Solution:**
```sql
-- Check if HNSW index exists
SELECT * FROM pg_indexes WHERE tablename = 'memori_memories';

-- Recreate index if missing
CREATE INDEX CONCURRENTLY idx_memori_mem_embedding_hnsw
ON memori_memories USING hnsw (embedding vector_cosine_ops);

-- Analyze table
ANALYZE memori_memories;
```

### Issue 4: Memory Not Retrieved

**Error:** Semantic search returns no results

**Solution:**
- Check embedding dimensions match (1536 for OpenAI ada-002)
- Verify embeddings are being stored: `SELECT COUNT(*) FROM memori_memories WHERE embedding IS NOT NULL;`
- Lower similarity threshold in search parameters

---

## Next Steps

After completing this quick-start:

1. **Add Authentication**: Implement user authentication to replace hardcoded `user_id`
2. **Enhance Services**: Add entity extraction, relationship mapping, and rule engine
3. **Integrate with Claude**: Implement the full Claude API client with context injection
4. **Add Caching**: Set up Redis for embedding and query caching
5. **Monitoring**: Add Prometheus metrics and structured logging
6. **Testing**: Write comprehensive unit and integration tests

---

## Verification Checklist

- [ ] pgvector extension installed and enabled
- [ ] All dependencies installed (`poetry install`)
- [ ] Environment variables configured
- [ ] Database migrations applied successfully
- [ ] Models imported without errors
- [ ] API server starts without errors
- [ ] Test script executes successfully
- [ ] API endpoints respond correctly
- [ ] Vector search returns relevant results
- [ ] Memory storage and retrieval works

---

## Support and Resources

- **Architecture Document**: See `MEMORI_INTEGRATION_ARCHITECTURE.md` for full details
- **API Documentation**: Visit `http://localhost:8000/docs` when server is running
- **PostgreSQL pgvector**: https://github.com/pgvector/pgvector
- **OpenAI Embeddings**: https://platform.openai.com/docs/guides/embeddings
- **Anthropic Claude**: https://docs.anthropic.com/

---

**Last Updated:** 2025-11-11
**Version:** 1.0
**Status:** Ready for Implementation

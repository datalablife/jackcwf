# AI Performance Optimization - Quick Start Guide

**Goal**: Reduce LangChain RAG latency from 850ms to 400ms (53% improvement) in 2 weeks
**Investment**: 32 hours
**ROI**: 5/5 stars

---

## Phase 1: Semantic Caching (Week 1)

### Day 1-2: Setup (4 hours)

**Task 1.1: Apply Database Migration** (30 min)
```bash
cd /mnt/d/工作区/云开发/working

# Load environment
set -a && source .env && set +a

# Apply migration
psql -h 47.79.87.199 -U jackcwf888 -d postgres \
  -f src/db/migrations/001_add_semantic_cache.sql

# Verify
psql -h 47.79.87.199 -U jackcwf888 -d postgres \
  -c "SELECT * FROM cache_analytics;"
```

Expected output:
```
 total_entries | total_hits | avg_hits_per_entry | ...
---------------+------------+--------------------+-----
             0 |          0 |                  0 | ...
```

**Task 1.2: Install Dependencies** (30 min)
```bash
# Add to requirements.txt
echo "asyncpg>=0.29.0" >> requirements.txt

# Install
pip install -r requirements.txt
```

**Task 1.3: Update FastAPI Initialization** (3 hours)

Edit `/mnt/d/工作区/云开发/working/src/main.py`:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
import asyncpg
import os
from src.services.semantic_cache import SemanticCacheService, set_cache_service
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan with cache initialization."""

    # Startup
    logger.info("Initializing database connection pool...")
    app.state.db_pool = await asyncpg.create_pool(
        os.getenv("DATABASE_URL"),
        min_size=5,
        max_size=20,
        command_timeout=60,
        max_inactive_connection_lifetime=300
    )

    logger.info("Initializing semantic cache service...")
    cache_service = SemanticCacheService(app.state.db_pool)
    init_success = await cache_service.initialize()

    if init_success:
        set_cache_service(cache_service)
        logger.info("✅ Semantic cache initialized successfully")
    else:
        logger.warning("⚠️ Semantic cache initialization failed - running without cache")

    yield

    # Shutdown
    logger.info("Closing database connection pool...")
    await app.state.db_pool.close()
    logger.info("✅ Shutdown complete")


# Update FastAPI app initialization
app = FastAPI(
    title="LangChain RAG API",
    version="1.0.0",
    lifespan=lifespan  # Add this line
)
```

**Checkpoint 1**: Test server startup
```bash
python src/main.py

# Expected log output:
# INFO: Initializing database connection pool...
# INFO: Initializing semantic cache service...
# INFO: ✅ Semantic cache initialized successfully
# INFO: Application startup complete
```

---

### Day 3-5: Integration (8 hours)

**Task 2.1: Create Cache-Aware RAG Service** (4 hours)

Create `/mnt/d/工作区/云开发/working/src/services/cached_rag.py`:

```python
"""RAG service with semantic caching."""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chat_models import ChatAnthropic
from src.services.semantic_cache import get_cache_service, Document

logger = logging.getLogger(__name__)


@dataclass
class RAGResponse:
    """RAG response with metadata."""
    response_text: str
    cached: bool
    latency_ms: float
    cache_distance: Optional[float] = None
    context_docs: Optional[List[Document]] = None


class CachedRAGService:
    """RAG service with semantic caching."""

    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small"
        )
        self.llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            temperature=0.7,
            max_tokens=2048
        )

    async def query(
        self,
        user_query: str,
        enable_cache: bool = True
    ) -> RAGResponse:
        """
        Execute RAG query with semantic caching.

        Args:
            user_query: User's natural language query
            enable_cache: Whether to use cache (for A/B testing)

        Returns:
            RAGResponse with answer and metadata
        """
        import time
        start_time = time.time()

        # Step 1: Encode query
        query_embedding = await self.embeddings.aembed_query(user_query)
        encoding_time = time.time()
        logger.debug(f"Query encoding: {(encoding_time - start_time) * 1000:.2f}ms")

        # Step 2: Retrieve context documents
        context_docs = await self._search_documents(query_embedding, limit=5)
        search_time = time.time()
        logger.debug(f"Vector search: {(search_time - encoding_time) * 1000:.2f}ms")

        # Step 3: Check semantic cache
        if enable_cache:
            cache_service = get_cache_service()
            if cache_service:
                cached_response = await cache_service.get_cached_response(
                    query_embedding=query_embedding,
                    context_docs=context_docs,
                    model_name="claude-3-5-sonnet-20241022"
                )
                cache_time = time.time()
                logger.debug(f"Cache lookup: {(cache_time - search_time) * 1000:.2f}ms")

                if cached_response:
                    total_latency = (time.time() - start_time) * 1000
                    logger.info(
                        f"Cache HIT: {total_latency:.2f}ms "
                        f"(saved {550:.0f}ms of LLM time)"
                    )

                    return RAGResponse(
                        response_text=cached_response.response_text,
                        cached=True,
                        latency_ms=total_latency,
                        cache_distance=cached_response.distance,
                        context_docs=context_docs
                    )

        # Step 4: Generate new response (cache miss)
        prompt = self._build_prompt(user_query, context_docs)
        response = await self.llm.ainvoke(prompt)
        generation_time = time.time()
        logger.debug(f"LLM generation: {(generation_time - search_time) * 1000:.2f}ms")

        # Step 5: Cache for future queries
        if enable_cache:
            cache_service = get_cache_service()
            if cache_service:
                await cache_service.cache_response(
                    query_text=user_query,
                    query_embedding=query_embedding,
                    response_text=response.content,
                    context_docs=context_docs,
                    model_name="claude-3-5-sonnet-20241022",
                    metadata={
                        "generation_time_ms": (generation_time - search_time) * 1000,
                        "total_latency_ms": (time.time() - start_time) * 1000
                    }
                )

        total_latency = (time.time() - start_time) * 1000
        logger.info(f"Cache MISS: {total_latency:.2f}ms (response cached)")

        return RAGResponse(
            response_text=response.content,
            cached=False,
            latency_ms=total_latency,
            context_docs=context_docs
        )

    async def _search_documents(
        self,
        query_embedding: List[float],
        limit: int = 5
    ) -> List[Document]:
        """Search for relevant documents using Lantern vector index."""
        # TODO: Replace with your actual database query
        # This is a placeholder - implement your vector search here
        from src.db.base import get_db_connection

        async with get_db_connection() as conn:
            results = await conn.fetch("""
                SELECT id, content, metadata
                FROM documents
                WHERE deleted_at IS NULL
                ORDER BY embedding <-> $1
                LIMIT $2
            """, query_embedding, limit)

            return [
                Document(
                    id=row['id'],
                    content=row['content'],
                    metadata=row['metadata']
                )
                for row in results
            ]

    def _build_prompt(self, query: str, docs: List[Document]) -> str:
        """Build LLM prompt with context documents."""
        context = "\n\n".join([
            f"Document {i+1}:\n{doc.content}"
            for i, doc in enumerate(docs)
        ])

        return f"""You are a helpful AI assistant with access to a knowledge base.
Use the following documents to answer the user's question. If the answer is not
in the documents, say so clearly.

Context Documents:
{context}

User Question: {query}

Answer:"""


# Singleton instance
_rag_service: Optional[CachedRAGService] = None


def get_rag_service() -> CachedRAGService:
    """Get global RAG service instance."""
    global _rag_service
    if _rag_service is None:
        _rag_service = CachedRAGService()
    return _rag_service
```

**Task 2.2: Update API Endpoint** (2 hours)

Edit `/mnt/d/工作区/云开发/working/src/api/conversation_routes.py`:

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.services.cached_rag import get_rag_service

router = APIRouter(prefix="/api/v1", tags=["conversation"])


class ChatRequest(BaseModel):
    message: str
    enable_cache: bool = True  # Allow disabling for A/B testing


class ChatResponse(BaseModel):
    response: str
    cached: bool
    latency_ms: float
    cache_distance: Optional[float] = None


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Chat endpoint with semantic caching.

    Performance:
    - Cache hit: ~300ms (65% faster)
    - Cache miss: ~850ms (first time, then cached)
    """
    try:
        rag_service = get_rag_service()
        result = await rag_service.query(
            user_query=request.message,
            enable_cache=request.enable_cache
        )

        return ChatResponse(
            response=result.response_text,
            cached=result.cached,
            latency_ms=result.latency_ms,
            cache_distance=result.cache_distance
        )

    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

**Task 2.3: Add Cache Management Endpoints** (2 hours)

Create `/mnt/d/工作区/云开发/working/src/api/cache_admin_routes.py`:

```python
"""Cache administration endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from src.services.semantic_cache import get_cache_service

router = APIRouter(prefix="/api/admin/cache", tags=["admin"])


@router.get("/stats")
async def cache_stats():
    """Get cache performance statistics."""
    cache_service = get_cache_service()
    if not cache_service:
        raise HTTPException(status_code=503, detail="Cache not initialized")

    stats = await cache_service.get_cache_stats()
    return {
        "status": "healthy",
        "metrics": stats
    }


class InvalidateRequest(BaseModel):
    query_id: Optional[int] = None
    model_name: Optional[str] = None
    older_than_hours: Optional[int] = None


@router.post("/invalidate")
async def invalidate_cache(request: InvalidateRequest):
    """Invalidate cache entries."""
    cache_service = get_cache_service()
    if not cache_service:
        raise HTTPException(status_code=503, detail="Cache not initialized")

    count = await cache_service.invalidate_cache(
        query_id=request.query_id,
        model_name=request.model_name,
        older_than_hours=request.older_than_hours
    )

    return {
        "status": "success",
        "entries_deleted": count
    }
```

Register routes in `src/main.py`:
```python
from src.api import cache_admin_routes

app.include_router(cache_admin_routes.router)
```

**Checkpoint 2**: Test cache integration
```bash
# Start server
python src/main.py

# Test chat endpoint (cache miss)
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is machine learning?"}'

# Response:
# {
#   "response": "Machine learning is...",
#   "cached": false,
#   "latency_ms": 850.5
# }

# Test again (cache hit)
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is machine learning?"}'

# Response:
# {
#   "response": "Machine learning is...",
#   "cached": true,
#   "latency_ms": 305.2,
#   "cache_distance": 0.0
# }

# Check cache stats
curl http://localhost:8000/api/admin/cache/stats
```

---

### Day 6-7: Monitoring & Testing (8 hours)

**Task 3.1: Add Prometheus Metrics** (3 hours)

Create `/mnt/d/工作区/云开发/working/src/infrastructure/cache_metrics.py`:

```python
"""Prometheus metrics for cache monitoring."""

from prometheus_client import Counter, Histogram, Gauge

# Cache hit/miss counters
cache_hits = Counter(
    'llm_cache_hits_total',
    'Total number of cache hits'
)

cache_misses = Counter(
    'llm_cache_misses_total',
    'Total number of cache misses'
)

# Latency histograms
cache_hit_latency = Histogram(
    'llm_cache_hit_latency_ms',
    'Latency for cache hits in milliseconds',
    buckets=[50, 100, 200, 300, 500]
)

cache_miss_latency = Histogram(
    'llm_cache_miss_latency_ms',
    'Latency for cache misses in milliseconds',
    buckets=[200, 500, 1000, 2000, 5000]
)

# Cache statistics
cache_size = Gauge(
    'llm_cache_size_entries',
    'Total number of cached entries'
)

cache_hit_rate = Gauge(
    'llm_cache_hit_rate',
    'Cache hit rate (0-1)'
)


# Instrument RAG service
def record_cache_hit(latency_ms: float):
    """Record cache hit metric."""
    cache_hits.inc()
    cache_hit_latency.observe(latency_ms)


def record_cache_miss(latency_ms: float):
    """Record cache miss metric."""
    cache_misses.inc()
    cache_miss_latency.observe(latency_ms)


async def update_cache_gauges():
    """Update cache size and hit rate gauges."""
    from src.services.semantic_cache import get_cache_service

    cache_service = get_cache_service()
    if cache_service:
        stats = await cache_service.get_cache_stats()
        cache_size.set(stats.get('total_entries', 0))
        cache_hit_rate.set(stats.get('hit_rate', 0))
```

Update `CachedRAGService.query()` to record metrics:
```python
from src.infrastructure.cache_metrics import record_cache_hit, record_cache_miss

# In query() method:
if cached_response:
    record_cache_hit(total_latency)
    # ...
else:
    record_cache_miss(total_latency)
    # ...
```

**Task 3.2: Create Dashboard** (2 hours)

Create Grafana dashboard JSON at `/mnt/d/工作区/云开发/working/monitoring/grafana_cache_dashboard.json`:

```json
{
  "dashboard": {
    "title": "LLM Cache Performance",
    "panels": [
      {
        "title": "Cache Hit Rate",
        "targets": [
          {
            "expr": "llm_cache_hit_rate"
          }
        ]
      },
      {
        "title": "Cache Hit vs Miss",
        "targets": [
          {
            "expr": "rate(llm_cache_hits_total[5m])",
            "legendFormat": "Hits"
          },
          {
            "expr": "rate(llm_cache_misses_total[5m])",
            "legendFormat": "Misses"
          }
        ]
      },
      {
        "title": "Latency Distribution",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(llm_cache_hit_latency_ms_bucket[5m]))",
            "legendFormat": "p95 Cache Hit"
          },
          {
            "expr": "histogram_quantile(0.95, rate(llm_cache_miss_latency_ms_bucket[5m]))",
            "legendFormat": "p95 Cache Miss"
          }
        ]
      }
    ]
  }
}
```

**Task 3.3: Load Testing** (3 hours)

Create `/mnt/d/工作区/云开发/working/tests/load_test_cache.py`:

```python
"""Load test for cache performance."""

from locust import HttpUser, task, between
import random

QUERIES = [
    "What is machine learning?",
    "Explain neural networks",
    "How does RAG work?",
    "What is semantic search?",
    "Define vector embeddings"
]


class CacheLoadTest(HttpUser):
    wait_time = between(1, 3)

    @task(7)  # 70% repeated queries (cache hits)
    def repeated_query(self):
        """Simulate repeated queries that should hit cache."""
        query = random.choice(QUERIES[:3])  # Only use first 3
        self.client.post("/api/v1/chat", json={"message": query})

    @task(3)  # 30% unique queries (cache misses)
    def unique_query(self):
        """Simulate unique queries that miss cache."""
        query = f"{random.choice(QUERIES)} {random.randint(1, 1000)}"
        self.client.post("/api/v1/chat", json={"message": query})


# Run test:
# locust -f tests/load_test_cache.py --host=http://localhost:8000 --users 10 --spawn-rate 2
```

Run load test and verify:
```bash
# Terminal 1: Start server
python src/main.py

# Terminal 2: Run load test
locust -f tests/load_test_cache.py --host=http://localhost:8000 --users 10 --spawn-rate 2 --run-time 5m

# Expected results:
# - Cache hit rate: 40-60%
# - Average latency: ~450ms (mix of hits and misses)
# - P95 latency: <800ms
```

**Checkpoint 3**: Validate performance improvement
```bash
# Check cache stats after load test
curl http://localhost:8000/api/admin/cache/stats

# Expected output:
# {
#   "status": "healthy",
#   "metrics": {
#     "total_entries": 50-100,
#     "total_hits": 200-400,
#     "hit_rate": 0.4-0.6,
#     "avg_hits_per_entry": 4-8
#   }
# }
```

---

## Phase 2: Claude Prompt Caching (Week 2)

### Day 8-10: Claude Prompt Caching (8 hours)

**Task 4.1: Update Anthropic SDK** (1 hour)
```bash
pip install --upgrade anthropic
```

**Task 4.2: Implement Prompt Caching** (5 hours)

Update `CachedRAGService._build_prompt()` in `src/services/cached_rag.py`:

```python
from anthropic import AsyncAnthropic

class CachedRAGService:
    def __init__(self):
        self.client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        # Remove self.llm = ChatAnthropic(...)

    async def _generate_response(
        self,
        query: str,
        context_docs: List[Document]
    ) -> str:
        """Generate response with Claude prompt caching."""

        # Build system prompt with cache control
        system_instruction = """You are an expert AI assistant with access to a comprehensive knowledge base.

Your responsibilities:
1. Answer questions accurately using the provided context
2. Cite specific documents when making claims
3. Admit when you don't know something
4. Provide clear, concise answers

If the answer isn't in the context, say: "I don't have enough information to answer that question based on the provided documents."
"""

        # Format context documents
        context_text = "\n\n".join([
            f"--- Document {i+1} (ID: {doc.id}) ---\n{doc.content}"
            for i, doc in enumerate(context_docs)
        ])

        # Build cached system message
        system = [
            {
                "type": "text",
                "text": system_instruction,
                "cache_control": {"type": "ephemeral"}  # Cache system prompt
            },
            {
                "type": "text",
                "text": f"Knowledge Base:\n\n{context_text}",
                "cache_control": {"type": "ephemeral"}  # Cache context docs
            }
        ]

        # Make request with cached context
        response = await self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            temperature=0.7,
            system=system,  # Cached system prompt
            messages=[
                {
                    "role": "user",
                    "content": query  # Only this changes per query
                }
            ]
        )

        # Log cache performance
        usage = response.usage
        logger.info(
            f"Claude API usage: "
            f"input={usage.input_tokens} "
            f"cache_creation={getattr(usage, 'cache_creation_input_tokens', 0)} "
            f"cache_read={getattr(usage, 'cache_read_input_tokens', 0)}"
        )

        return response.content[0].text
```

Update `query()` method to use new generation:
```python
async def query(self, user_query: str, enable_cache: bool = True) -> RAGResponse:
    # ... existing code ...

    # Step 4: Generate new response with prompt caching
    response_text = await self._generate_response(user_query, context_docs)
    generation_time = time.time()

    # ... rest of method ...
```

**Task 4.3: Test Prompt Caching** (2 hours)

```python
# tests/test_prompt_cache.py
import pytest
from src.services.cached_rag import get_rag_service

@pytest.mark.asyncio
async def test_prompt_cache_effectiveness():
    """Test that prompt caching reduces latency."""
    rag_service = get_rag_service()

    # First query: cold cache (should create cache)
    result1 = await rag_service.query("What is AI?", enable_cache=False)
    latency1 = result1.latency_ms

    # Second query: warm cache (should read from cache)
    result2 = await rag_service.query("What is machine learning?", enable_cache=False)
    latency2 = result2.latency_ms

    # Prompt cache should reduce latency by ~50%
    assert latency2 < latency1 * 0.8, \
        f"Expected prompt cache speedup, got {latency1}ms -> {latency2}ms"

    print(f"Prompt cache speedup: {latency1}ms -> {latency2}ms ({(1 - latency2/latency1)*100:.1f}%)")
```

---

## Success Metrics

After completing both phases, verify:

### Performance Metrics
```bash
# Run benchmark
python tests/benchmark_cache.py

# Expected results:
# ┌─────────────────┬─────────────┬──────────────┬──────────────┐
# │ Scenario        │ Baseline    │ Optimized    │ Improvement  │
# ├─────────────────┼─────────────┼──────────────┼──────────────┤
# │ Cold query      │ 850ms       │ 850ms        │ 0%           │
# │ Semantic cache  │ 850ms       │ 300ms        │ 65%          │
# │ Prompt cache    │ 550ms       │ 200ms        │ 64%          │
# │ Both caches     │ 850ms       │ 150ms        │ 82%          │
# │ Average (40% HR)│ 850ms       │ 400ms        │ 53%          │
# └─────────────────┴─────────────┴──────────────┴──────────────┘
```

### Cost Savings
```bash
# Check cost analytics
curl http://localhost:8000/api/admin/cache/cost-report

# Expected output:
# {
#   "baseline_cost_per_day": 135.00,
#   "optimized_cost_per_day": 54.00,
#   "savings_per_day": 81.00,
#   "savings_per_month": 2430.00,
#   "roi_days": 2.5  # Days to recover 20h implementation cost
# }
```

### Cache Health
```bash
# Monitor cache performance
curl http://localhost:8000/api/admin/cache/stats

# Healthy metrics:
# - hit_rate: 0.35-0.60 (35-60%)
# - avg_hits_per_entry: >3
# - entries_last_24h: >50
# - p95_latency_cache_hit: <400ms
# - p95_latency_cache_miss: <1000ms
```

---

## Troubleshooting

### Issue: Cache not initializing
```bash
# Check database connection
psql -h 47.79.87.199 -U jackcwf888 -d postgres -c "SELECT 1;"

# Check if table exists
psql -h 47.79.87.199 -U jackcwf888 -d postgres -c "SELECT COUNT(*) FROM llm_response_cache;"

# Check logs
tail -f logs/app.log | grep cache
```

### Issue: Low cache hit rate (<20%)
```bash
# Diagnose similarity threshold
psql -h 47.79.87.199 -U jackcwf888 -d postgres <<EOF
SELECT
    query_text,
    hit_count,
    created_at
FROM llm_response_cache
ORDER BY hit_count DESC
LIMIT 10;
EOF

# If hit_count is consistently 0, increase threshold in:
# src/services/semantic_cache.py
# SIMILARITY_THRESHOLD = 0.08  # More lenient
```

---

## Next Steps

After completing Phase 1 & 2 (53% improvement):

**Week 3-4: Additional Optimizations**
- Concurrent processing (+90% batch throughput)
- ONNX embeddings (+10% latency, -100% embedding cost)
- Hybrid search (+20% quality, reduces follow-up queries)

**Expected Final Performance**:
- Average latency: 200ms (76% improvement from baseline)
- Cost per query: $0.0008 (80% reduction)
- Throughput: 10+ concurrent queries/sec

---

**Status**: Ready to implement
**Last Updated**: 2025-11-18
**Estimated Completion**: 2 weeks (32 hours)

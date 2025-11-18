"""Prometheus metrics for semantic cache monitoring."""

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry

# Create a shared registry for all cache metrics
cache_registry = CollectorRegistry()

# ============================================================================
# Cache Hit/Miss Counters
# ============================================================================

llm_cache_hits_total = Counter(
    name="llm_cache_hits_total",
    documentation="Total number of cache hits in semantic cache",
    labelnames=["model", "cache_type"],
    registry=cache_registry,
)

llm_cache_misses_total = Counter(
    name="llm_cache_misses_total",
    documentation="Total number of cache misses in semantic cache",
    labelnames=["model", "cache_type"],
    registry=cache_registry,
)

# ============================================================================
# Latency Histograms
# ============================================================================

llm_cache_hit_latency_ms = Histogram(
    name="llm_cache_hit_latency_ms",
    documentation="Latency of cache hits in milliseconds",
    labelnames=["model"],
    buckets=(10, 50, 100, 200, 300, 400, 500, 750, 1000),
    registry=cache_registry,
)

llm_cache_miss_latency_ms = Histogram(
    name="llm_cache_miss_latency_ms",
    documentation="Latency of cache misses (full RAG pipeline) in milliseconds",
    labelnames=["model"],
    buckets=(100, 250, 500, 750, 1000, 1500, 2000, 3000, 5000),
    registry=cache_registry,
)

# ============================================================================
# Cache Status Gauges
# ============================================================================

llm_cache_size_entries = Gauge(
    name="llm_cache_size_entries",
    documentation="Current number of entries in semantic cache",
    labelnames=["model"],
    registry=cache_registry,
)

llm_cache_hit_rate = Gauge(
    name="llm_cache_hit_rate",
    documentation="Cache hit rate as a percentage (0-100)",
    labelnames=["model"],
    registry=cache_registry,
)

llm_cache_table_size_bytes = Gauge(
    name="llm_cache_table_size_bytes",
    documentation="Total size of cache table in bytes",
    labelnames=["model"],
    registry=cache_registry,
)

# ============================================================================
# Query Metrics
# ============================================================================

llm_query_latency_ms = Histogram(
    name="llm_query_latency_ms",
    documentation="Total RAG query latency in milliseconds",
    labelnames=["model", "cached"],
    buckets=(50, 150, 300, 500, 750, 1000, 1500, 2000, 3000, 5000),
    registry=cache_registry,
)

llm_embedding_latency_ms = Histogram(
    name="llm_embedding_latency_ms",
    documentation="Query embedding generation latency in milliseconds",
    labelnames=["model"],
    buckets=(10, 25, 50, 100, 150, 200, 300),
    registry=cache_registry,
)

llm_vector_search_latency_ms = Histogram(
    name="llm_vector_search_latency_ms",
    documentation="Vector similarity search latency in milliseconds",
    labelnames=["model"],
    buckets=(5, 10, 25, 50, 100, 150, 200, 300),
    registry=cache_registry,
)

llm_generation_latency_ms = Histogram(
    name="llm_generation_latency_ms",
    documentation="LLM response generation latency in milliseconds",
    labelnames=["model"],
    buckets=(100, 250, 500, 750, 1000, 1500, 2000, 3000, 5000, 7500, 10000),
    registry=cache_registry,
)

# ============================================================================
# Cache Efficiency Metrics
# ============================================================================

llm_cache_distance = Histogram(
    name="llm_cache_distance",
    documentation="Semantic similarity distance of cached responses (0-1 normalized)",
    labelnames=["model"],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2, 0.3, 0.5, 1.0),
    registry=cache_registry,
)

llm_cached_responses_served = Counter(
    name="llm_cached_responses_served",
    documentation="Number of responses served from cache (avoiding LLM calls)",
    labelnames=["model"],
    registry=cache_registry,
)

# ============================================================================
# Metric Recording Functions
# ============================================================================

def record_cache_hit(model_name: str, latency_ms: float, cache_distance: float = None):
    """Record a cache hit event."""
    llm_cache_hits_total.labels(model=model_name, cache_type="semantic").inc()
    llm_cache_hit_latency_ms.labels(model=model_name).observe(latency_ms)
    llm_query_latency_ms.labels(model=model_name, cached="true").observe(latency_ms)
    llm_cached_responses_served.labels(model=model_name).inc()

    if cache_distance is not None:
        llm_cache_distance.labels(model=model_name).observe(cache_distance)


def record_cache_miss(
    model_name: str,
    total_latency_ms: float,
    embedding_latency_ms: float,
    search_latency_ms: float,
    generation_latency_ms: float,
):
    """Record a cache miss event with detailed latency breakdown."""
    llm_cache_misses_total.labels(model=model_name, cache_type="semantic").inc()
    llm_cache_miss_latency_ms.labels(model=model_name).observe(total_latency_ms)
    llm_query_latency_ms.labels(model=model_name, cached="false").observe(total_latency_ms)

    # Record component latencies
    llm_embedding_latency_ms.labels(model=model_name).observe(embedding_latency_ms)
    llm_vector_search_latency_ms.labels(model=model_name).observe(search_latency_ms)
    llm_generation_latency_ms.labels(model=model_name).observe(generation_latency_ms)


def update_cache_stats(model_name: str, total_entries: int, hit_rate: float, table_size_bytes: int):
    """Update cache statistics gauges."""
    llm_cache_size_entries.labels(model=model_name).set(total_entries)
    llm_cache_hit_rate.labels(model=model_name).set(hit_rate * 100)  # Convert to percentage
    llm_cache_table_size_bytes.labels(model=model_name).set(table_size_bytes)


def get_metrics_summary(model_name: str) -> dict:
    """Get current cache metrics summary."""
    return {
        "model": model_name,
        "hits": llm_cache_hits_total.labels(model=model_name, cache_type="semantic")._value.get(),
        "misses": llm_cache_misses_total.labels(model=model_name, cache_type="semantic")._value.get(),
        "cache_entries": llm_cache_size_entries.labels(model=model_name)._value.get(),
        "hit_rate": llm_cache_hit_rate.labels(model=model_name)._value.get(),
    }

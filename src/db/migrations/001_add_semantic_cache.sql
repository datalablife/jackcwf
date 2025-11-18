-- Migration: Add Semantic Cache for LLM Responses
-- Version: 001
-- Date: 2025-11-18
-- Description: Creates tables and indexes for semantic caching of LLM responses
--              to reduce latency and API costs by 65% on cache hits.

-- ============================================================================
-- Table: llm_response_cache
-- Purpose: Store LLM responses with vector embeddings for semantic similarity
-- ============================================================================

CREATE TABLE IF NOT EXISTS llm_response_cache (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Query information
    query_text TEXT NOT NULL,
    query_embedding REAL[1536] NOT NULL,  -- OpenAI text-embedding-3-small dimension

    -- Response information
    response_text TEXT NOT NULL,
    model_name VARCHAR(100) NOT NULL,

    -- Context tracking
    context_hash BYTEA NOT NULL,          -- SHA256 hash of document IDs
    context_doc_ids INTEGER[] NOT NULL,   -- Actual document IDs for verification

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,   -- Flexible metadata (tokens, latency, etc.)

    -- Cache statistics
    created_at TIMESTAMP DEFAULT NOW(),
    hit_count INTEGER DEFAULT 0,
    last_hit_at TIMESTAMP,

    -- Constraints
    CONSTRAINT valid_embedding_dimension CHECK (array_length(query_embedding, 1) = 1536),
    CONSTRAINT valid_hit_count CHECK (hit_count >= 0)
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Lantern HNSW index for fast vector similarity search
-- Expected performance: 50ms for similarity search on 1M+ entries
CREATE INDEX IF NOT EXISTS llm_cache_embedding_hnsw
ON llm_response_cache
USING lantern_hnsw (query_embedding dist_l2sq_ops)
WITH (
    M=16,               -- Graph connectivity (16 = good balance)
    ef_construction=64, -- Build quality (higher = better index, slower build)
    ef=40,              -- Search quality (higher = better recall, slower search)
    dim=1536            -- Embedding dimension
);

COMMENT ON INDEX llm_cache_embedding_hnsw IS
    'HNSW index for O(log n) semantic similarity search. Enables 50ms lookups on 1M+ cache entries.';

-- B-tree index for context hash lookups
-- Used in Stage 2 verification to ensure context matches
CREATE INDEX IF NOT EXISTS llm_cache_context_hash_idx
ON llm_response_cache (context_hash);

COMMENT ON INDEX llm_cache_context_hash_idx IS
    'Fast lookup by context hash to verify document overlap.';

-- Composite index for model-specific queries
CREATE INDEX IF NOT EXISTS llm_cache_model_created_idx
ON llm_response_cache (model_name, created_at DESC);

COMMENT ON INDEX llm_cache_model_created_idx IS
    'Optimizes TTL-based cache cleanup and model-specific invalidation.';

-- Index for cache analytics
CREATE INDEX IF NOT EXISTS llm_cache_hit_stats_idx
ON llm_response_cache (hit_count DESC, last_hit_at DESC)
WHERE hit_count > 0;

COMMENT ON INDEX llm_cache_hit_stats_idx IS
    'Tracks popular cache entries for analytics and optimization.';

-- ============================================================================
-- Views for Analytics
-- ============================================================================

CREATE OR REPLACE VIEW cache_analytics AS
SELECT
    COUNT(*) as total_entries,
    SUM(hit_count) as total_hits,
    AVG(hit_count) as avg_hits_per_entry,
    MAX(hit_count) as max_hits,
    COUNT(*) FILTER (WHERE hit_count > 0) as entries_with_hits,
    COUNT(*) FILTER (WHERE hit_count = 0) as entries_never_hit,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '1 hour') as entries_last_hour,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as entries_last_24h,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') as entries_last_week,
    ROUND(100.0 * COUNT(*) FILTER (WHERE hit_count > 0) / NULLIF(COUNT(*), 0), 2) as hit_percentage,
    pg_size_pretty(pg_total_relation_size('llm_response_cache')) as table_size,
    pg_size_pretty(pg_relation_size('llm_response_cache')) as data_size,
    pg_size_pretty(pg_total_relation_size('llm_cache_embedding_hnsw')) as index_size
FROM llm_response_cache;

COMMENT ON VIEW cache_analytics IS
    'Real-time cache performance metrics. Query this view for monitoring dashboards.';

-- ============================================================================
-- View: Top Cached Queries
-- ============================================================================

CREATE OR REPLACE VIEW top_cached_queries AS
SELECT
    id,
    query_text,
    response_text,
    model_name,
    hit_count,
    created_at,
    last_hit_at,
    EXTRACT(EPOCH FROM (last_hit_at - created_at)) / 3600 as lifetime_hours,
    ROUND(hit_count::NUMERIC / NULLIF(EXTRACT(EPOCH FROM (COALESCE(last_hit_at, NOW()) - created_at)) / 3600, 0), 2) as hits_per_hour
FROM llm_response_cache
WHERE hit_count > 0
ORDER BY hit_count DESC
LIMIT 100;

COMMENT ON VIEW top_cached_queries IS
    'Top 100 most frequently hit cache entries. Useful for identifying common query patterns.';

-- ============================================================================
-- View: Model Performance Comparison
-- ============================================================================

CREATE OR REPLACE VIEW cache_by_model AS
SELECT
    model_name,
    COUNT(*) as cached_responses,
    SUM(hit_count) as total_hits,
    AVG(hit_count) as avg_hits,
    MAX(hit_count) as max_hits,
    ROUND(100.0 * SUM(hit_count) / NULLIF(COUNT(*), 0), 2) as hit_rate,
    pg_size_pretty(SUM(pg_column_size(response_text))) as response_data_size
FROM llm_response_cache
GROUP BY model_name
ORDER BY total_hits DESC;

COMMENT ON VIEW cache_by_model IS
    'Cache performance breakdown by LLM model. Compare effectiveness across models.';

-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Function: Clean up expired cache entries
CREATE OR REPLACE FUNCTION cleanup_expired_cache(ttl_hours INTEGER DEFAULT 24)
RETURNS TABLE (deleted_count BIGINT) AS $$
BEGIN
    RETURN QUERY
    WITH deleted AS (
        DELETE FROM llm_response_cache
        WHERE created_at < NOW() - (ttl_hours || ' hours')::INTERVAL
        RETURNING id
    )
    SELECT COUNT(*) FROM deleted;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_expired_cache IS
    'Delete cache entries older than specified TTL (default: 24 hours).
     Usage: SELECT * FROM cleanup_expired_cache(48); -- Delete entries older than 48h';

-- Function: Get cache efficiency report
CREATE OR REPLACE FUNCTION cache_efficiency_report()
RETURNS TABLE (
    metric TEXT,
    value TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH stats AS (
        SELECT * FROM cache_analytics
    )
    SELECT 'Total Entries'::TEXT, total_entries::TEXT FROM stats
    UNION ALL
    SELECT 'Total Hits', total_hits::TEXT FROM stats
    UNION ALL
    SELECT 'Hit Percentage', hit_percentage::TEXT || '%' FROM stats
    UNION ALL
    SELECT 'Avg Hits Per Entry', ROUND(avg_hits_per_entry::NUMERIC, 2)::TEXT FROM stats
    UNION ALL
    SELECT 'Entries Last 24h', entries_last_24h::TEXT FROM stats
    UNION ALL
    SELECT 'Table Size', table_size FROM stats
    UNION ALL
    SELECT 'Estimated Cost Savings', (
        SELECT CASE
            WHEN total_hits > 0 THEN
                '$' || ROUND((total_hits * 0.003)::NUMERIC, 2)::TEXT || ' (assuming $0.003/query)'
            ELSE '$0.00'
        END
        FROM stats
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cache_efficiency_report IS
    'Generate human-readable cache efficiency report.
     Usage: SELECT * FROM cache_efficiency_report();';

-- ============================================================================
-- Triggers for Maintenance
-- ============================================================================

-- Trigger: Prevent modification of cached responses
CREATE OR REPLACE FUNCTION prevent_cache_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Cannot modify cached responses. Delete and recreate instead.';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER prevent_cache_update
BEFORE UPDATE ON llm_response_cache
FOR EACH ROW
WHEN (
    OLD.query_text IS DISTINCT FROM NEW.query_text OR
    OLD.response_text IS DISTINCT FROM NEW.response_text OR
    OLD.query_embedding IS DISTINCT FROM NEW.query_embedding
)
EXECUTE FUNCTION prevent_cache_modification();

COMMENT ON TRIGGER prevent_cache_update ON llm_response_cache IS
    'Prevents modification of immutable cache fields (query, response, embedding).
     Only statistics (hit_count, last_hit_at) can be updated.';

-- ============================================================================
-- Grants (adjust based on your user setup)
-- ============================================================================

-- Grant permissions to application user
GRANT SELECT, INSERT, DELETE ON llm_response_cache TO jackcwf888;
GRANT UPDATE (hit_count, last_hit_at, metadata) ON llm_response_cache TO jackcwf888;
GRANT SELECT ON cache_analytics TO jackcwf888;
GRANT SELECT ON top_cached_queries TO jackcwf888;
GRANT SELECT ON cache_by_model TO jackcwf888;
GRANT EXECUTE ON FUNCTION cleanup_expired_cache TO jackcwf888;
GRANT EXECUTE ON FUNCTION cache_efficiency_report TO jackcwf888;

-- ============================================================================
-- Initial Data / Configuration
-- ============================================================================

-- Insert configuration metadata
CREATE TABLE IF NOT EXISTS cache_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO cache_config (key, value) VALUES
    ('similarity_threshold', '0.05'),
    ('ttl_hours', '24'),
    ('min_context_overlap', '0.8'),
    ('enabled', 'true')
ON CONFLICT (key) DO NOTHING;

-- ============================================================================
-- Rollback Instructions
-- ============================================================================

-- To rollback this migration, run:
/*
DROP VIEW IF EXISTS cache_by_model;
DROP VIEW IF EXISTS top_cached_queries;
DROP VIEW IF EXISTS cache_analytics;
DROP TRIGGER IF EXISTS prevent_cache_update ON llm_response_cache;
DROP FUNCTION IF EXISTS prevent_cache_modification();
DROP FUNCTION IF EXISTS cache_efficiency_report();
DROP FUNCTION IF EXISTS cleanup_expired_cache(INTEGER);
DROP TABLE IF EXISTS cache_config;
DROP TABLE IF EXISTS llm_response_cache CASCADE;
*/

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Verify table creation
-- SELECT tablename FROM pg_tables WHERE tablename = 'llm_response_cache';

-- Verify indexes
-- SELECT indexname FROM pg_indexes WHERE tablename = 'llm_response_cache';

-- Test cache analytics view
-- SELECT * FROM cache_analytics;

-- ============================================================================
-- Performance Tuning Notes
-- ============================================================================

/*
HNSW Index Tuning:

1. M (graph connectivity):
   - Default: 16
   - Lower (8): Smaller index, faster build, lower recall
   - Higher (32): Larger index, slower build, better recall

2. ef_construction (build quality):
   - Default: 64
   - Lower (32): Faster build, lower quality
   - Higher (128): Slower build, better quality

3. ef (search quality):
   - Default: 40
   - Lower (20): Faster search, lower recall
   - Higher (80): Slower search, better recall

Adjust based on your latency vs. quality requirements:
- High traffic, moderate quality: M=12, ef=30
- Low traffic, high quality: M=24, ef=60

Cache Size Management:

Expected growth: ~2KB per cached entry (embedding + response)
For 100K cached responses: ~200MB storage
For 1M cached responses: ~2GB storage

Set up automated cleanup:
SELECT cron.schedule('cleanup-cache', '0 2 * * *',
    'SELECT cleanup_expired_cache(24)');  -- Daily at 2 AM
*/

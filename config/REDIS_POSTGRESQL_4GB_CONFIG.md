# Redis 4GB 内存轻量版配置
# 预期内存占用：256MB
# 缓存策略：LRU 自动驱逐

# 在 Docker Compose 中使用以下命令启动：
# docker run -d \
#   --name redis-cache \
#   --restart unless-stopped \
#   -p 6379:6379 \
#   -v redis-data:/data \
#   redis:7-alpine \
#   redis-server \
#     --maxmemory 256mb \
#     --maxmemory-policy allkeys-lru \
#     --save 900 1 \
#     --save 300 10 \
#     --save 60 10000 \
#     --appendonly yes \
#     --appendfsync everysec \
#     --loglevel notice

# 或者使用 redis.conf 配置文件：

# Redis 内存配置
maxmemory 268435456               # 256MB（必须设置）
maxmemory-policy allkeys-lru      # 超过内存时删除最少使用的键

# 持久化配置（权衡性能和可靠性）
save 900 1                         # 15分钟内至少 1 个键改变，保存一次
save 300 10                        # 5分钟内至少 10 个键改变，保存一次
save 60 10000                      # 1分钟内至少 10000 个键改变，保存一次

appendonly yes                     # 启用 AOF 持久化（更安全）
appendfsync everysec              # 每秒 fsync 一次（平衡性能和安全）
no-appendfsync-on-rewrite no       # 禁用 rewrite 时 fsync

# AOF 重写配置
auto-aof-rewrite-percentage 100    # 当 AOF 文件大小是原来 100% 时重写
auto-aof-rewrite-min-size 64mb     # AOF 文件最小 64MB 才能重写

# 键过期策略
timeout 0                          # 不关闭空闲连接
tcp-keepalive 300                  # TCP 保活

# 慢查询日志
slowlog-log-slower-than 10000      # 10ms 以上的命令记录
slowlog-max-len 128                # 保留最多 128 条记录

# 日志级别
loglevel notice                    # info/notice/warning

# 其他优化
databases 1                        # 4GB 内存只用 1 个数据库（默认 16 个）
hz 10                              # 后台任务频率（默认 10，可降低到 5）

# ============================================
# PostgreSQL 4GB 内存轻量版配置
# 预期内存占用：500-800MB（可调整）
# ============================================

# 使用以下环境变量或 postgresql.conf 配置：

# 内存配置（4GB 服务器）
shared_buffers = 256MB             # 仅 6% of RAM（vs 推荐 25%）
effective_cache_size = 1GB         # 仅 25% of RAM（让 OS 缓存处理）
work_mem = 8MB                     # 单个排序/哈希操作的内存
maintenance_work_mem = 64MB        # 维护操作（VACUUM、CREATE INDEX）

# 连接池配置
max_connections = 50               # 降低到 50（默认 100）
reserved_connections = 3           # 保留 3 个管理连接

# 查询优化
random_page_cost = 1.1             # SSD 优化（默认 4 for HDD）
effective_io_concurrency = 200     # SSD 并发 IO

# 日志配置（仅关键日志）
log_min_duration_statement = 1000   # 记录超过 1s 的查询
log_statement = 'none'             # 不记录所有 SQL
log_duration = off                 # 关闭所有查询时间记录

# WAL 配置（权衡安全和性能）
wal_buffers = 16MB                 # WAL 缓冲
checkpoint_completion_target = 0.9 # 充分利用检查点时间
wal_level = minimal                # 基本 WAL 日志

# 禁用不需要的功能
ssl = off                          # 禁用 SSL（性能）
shared_preload_libraries = ''      # 不加载额外模块

# ============================================
# 性能指标和监控
# ============================================

# 创建指标收集脚本（python）
import asyncpg
import time

async def collect_postgresql_metrics():
    """收集 PostgreSQL 性能指标"""
    conn = await asyncpg.connect('postgresql://user:pass@localhost/db')

    try:
        # 1. 连接数
        connections = await conn.fetchval(
            'SELECT count(*) FROM pg_stat_activity'
        )

        # 2. 缓冲命中率
        hit_rate = await conn.fetchval("""
            SELECT
              ROUND(heap_blks_hit::float / (heap_blks_hit + heap_blks_read), 4) * 100
            FROM pg_statio_user_tables
            LIMIT 1
        """)

        # 3. 慢查询
        slow_queries = await conn.fetch("""
            SELECT query, mean_exec_time
            FROM pg_stat_statements
            WHERE mean_exec_time > 1000  -- >1s
            ORDER BY mean_exec_time DESC
            LIMIT 5
        """)

        # 4. 表大小
        table_size = await conn.fetchval("""
            SELECT sum(pg_total_relation_size(schemaname||'.'||tablename))::bigint
            FROM pg_tables
            WHERE schemaname = 'public'
        """)

        return {
            'connections': connections,
            'buffer_hit_rate': hit_rate,
            'slow_queries': slow_queries,
            'total_size': table_size
        }

    finally:
        await conn.close()

# ============================================
# 优化建议（针对 4GB）
# ============================================

# 1. 使用连接池
#    - 使用 pgBouncer（轻量级连接池）
#    - 减少实际连接数（从 50 降到 20）
#    - 共享连接重用

# 2. 定期维护
#    - VACUUM 每天一次
#    - ANALYZE 每周一次
#    - REINDEX 每月一次

# 3. 监控关键指标
#    - 连接数 > 40 → 告警
#    - 缓冲命中率 < 99% → 优化查询
#    - 慢查询 > 1s → 添加索引

# 4. 禁用不必要的功能
#    - 禁用 SSL（除非需要）
#    - 禁用日志（仅记录慢查询）
#    - 禁用 full_page_writes（如果有 RAID）

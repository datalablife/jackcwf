# 轻量级日志收集方案（替代 ELK）
# 针对 4GB 内存优化，完全无需 Elasticsearch、Logstash、Kibana
# 预期成本：0 额外内存占用

# 方案说明：
# 1. 本地日志文件 + logrotate（自动轮转）
# 2. Docker 容器日志驱动（json-file）
# 3. Loki 轻量级日志聚合（可选，仅 50MB）

# ============================================
# 方案 A: 本地日志文件 + 脚本分析（最简单）
# ============================================

# Docker Compose 日志配置
# 在 docker-compose.ha.yml 或 docker-compose.monitoring.yml 中添加：

version: '3.8'
services:
  fastapi-backend:
    # ... 其他配置 ...
    logging:
      driver: json-file
      options:
        max-size: "100m"        # 单个日志文件最大 100MB
        max-file: "5"           # 保留 5 个日志文件
        labels: "service=fastapi"
    environment:
      - LOG_LEVEL=INFO
      - LOG_FORMAT=json

  nginx:
    # ... 其他配置 ...
    logging:
      driver: json-file
      options:
        max-size: "50m"
        max-file: "3"
        labels: "service=nginx"

# logrotate 配置（在服务器上）
# 文件：/etc/logrotate.d/langchain-ai

/var/log/langchain-ai/*.log {
    daily                    # 每天轮转
    rotate 7                 # 保留 7 天
    missingok                # 文件不存在也不报错
    notifempty               # 空文件不轮转
    compress                 # 压缩旧日志
    delaycompress            # 延迟压缩
    postrotate
        # 轮转后重启相关服务
        docker ps -q --filter "label=service=fastapi" | xargs -r docker kill -s HUP
    endscript
}

# ============================================
# 方案 B: Grafana Loki（轻量级日志聚合）
# 仅 50-100MB，替代整个 ELK 栈
# ============================================

# docker-compose-loki.yml
version: '3.8'

services:
  loki:
    image: grafana/loki:latest
    container_name: loki
    restart: unless-stopped
    ports:
      - "3100:3100"
    volumes:
      - ./loki-config.yml:/etc/loki/local-config.yml
      - loki-data:/loki
    command: -config.file=/etc/loki/local-config.yml
    environment:
      - TZ=UTC
    # 内存限制
    deploy:
      resources:
        limits:
          memory: 100M
        reservations:
          memory: 50M

  promtail:  # Loki 日志采集器
    image: grafana/promtail:latest
    container_name: promtail
    restart: unless-stopped
    volumes:
      - /var/log:/var/log:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock
      - ./promtail-config.yml:/etc/promtail/config.yml
    command: -config.file=/etc/promtail/config.yml
    # 内存限制
    deploy:
      resources:
        limits:
          memory: 50M
        reservations:
          memory: 25M

volumes:
  loki-data:
    driver: local

# loki-config.yml
auth_enabled: false

ingester:
  chunk_idle_period: 3m
  chunk_retain_period: 1m
  max_chunk_age: 1h
  max_streams_limit_per_user: 10000

limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h
  ingestion_rate_mb: 10
  ingestion_burst_size_mb: 20

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema:
        version: v11
        index:
          prefix: index_
          period: 24h

server:
  http_listen_port: 3100
  log_level: info

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/index
    cache_location: /loki/boltdb-cache
    shared_store: filesystem
  filesystem:
    directory: /loki/chunks

chunk_store_config:
  max_look_back_period: 0s

table_manager:
  retention_deletes_enabled: false
  retention_period: 0s

# promtail-config.yml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

scrape_configs:
  - job_name: fastapi
    static_configs:
      - targets:
          - localhost
        labels:
          job: fastapi
          service: langchain-ai
    pipeline_stages:
      - json:
          expressions:
            timestamp: timestamp
            level: level
            message: message
      - timestamp:
          format: "RFC3339Nano"
          source: timestamp
      - labels:
          level:
          service:

  - job_name: nginx
    static_configs:
      - targets:
          - localhost
        labels:
          job: nginx
          service: webserver
    pipeline_stages:
      - regex:
          expression: '(?P<remote_addr>\S*) - (?P<remote_user>\S*) \[(?P<timestamp>[\w:/]+\s[+\-]\d{4})\] "(?P<method>\S+)(?: +(?P<path>(?:(?:[^"]*)?)*) +\S*)?" (?P<status>\S*) (?P<bytes_sent>\S*)'

  - job_name: syslog
    static_configs:
      - targets:
          - localhost
        labels:
          job: syslog
          service: system
    pipeline_stages:
      - regex:
          expression: '(?P<timestamp>.{15}) (?P<hostname>\S*) (?P<process>\S*): (?P<message>.*)'

# ============================================
# 在 Grafana 中添加 Loki 数据源
# ============================================

# 在 grafana/provisioning/datasources/datasources.yml 中添加：

- name: Loki
  type: loki
  access: proxy
  url: http://loki:3100
  isDefault: false
  editable: true
  jsonData:
    maxLines: 1000

# 性能对比

# ELK 栈（原方案）:
# - Elasticsearch: 1-2GB
# - Logstash: 256-512MB
# - Kibana: 256-512MB
# - 总计: 1.5-2.5GB（不适合 4GB）

# Loki 轻量版（推荐）:
# - Loki: 50-100MB
# - Promtail: 25-50MB
# - 总计: 75-150MB（节省 90%+）

# 本地日志（最轻量）:
# - 总计: 0MB（仅磁盘日志文件）
# - logrotate 自动管理

# 推荐方案：
# 1. 如果不需要日志搜索功能 → 本地日志文件 + logrotate
# 2. 如果需要日志搜索 → Loki 轻量版（仅 100MB）
# 3. 不要使用 ELK（太重，1.5GB+）

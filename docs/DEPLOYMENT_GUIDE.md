"""
# LangChain AI Conversation System - Production Deployment Guide

## Executive Summary

This guide provides comprehensive instructions for deploying the LangChain AI Conversation System
to production. The system includes:

- **REST API Layer** (17 endpoints + 1 WebSocket)
- **Streaming Support** (Server-Sent Events with NDJSON format)
- **Circuit Breaker Protection** (Fault tolerance and graceful degradation)
- **Comprehensive Monitoring** (Health checks, metrics, performance tracking)
- **Middleware Stack** (Authentication, memory injection, content moderation, audit logging)
- **RAG Pipeline** (Document processing, vector search, semantic retrieval)
- **LangChain Agent** (Multi-tool orchestration, parallel execution)

---

## Pre-Deployment Checklist

### Environment Requirements

- **Python**: 3.10+
- **PostgreSQL**: 14+ with pgvector extension
- **Redis**: 6+ (optional, for caching)
- **System Resources**:
  - CPU: 4+ cores
  - Memory: 8+ GB
  - Disk: 50+ GB for documents/indexes

### Infrastructure Setup

#### 1. Database Setup

```bash
# Install PostgreSQL with pgvector
# macOS
brew install postgresql
brew services start postgresql

# Ubuntu
sudo apt-get install postgresql postgresql-contrib
sudo -u postgres psql

# Create database
CREATE DATABASE langchain_ai;
CREATE EXTENSION vector;
```

#### 2. Environment Configuration

Create `.env.production` file:

```env
# Application
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/langchain_ai
DATABASE_ECHO=false
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# LLM Configuration
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
LANGCHAIN_API_KEY=...

# Security
JWT_SECRET=your-very-secure-secret-key-min-32-chars
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Performance
HEALTH_CHECK_TIMEOUT_MS=2000
API_TIMEOUT_MS=30000
STREAMING_BUFFER_SIZE=100

# Circuit Breaker
CIRCUIT_BREAKER_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT=60

# Monitoring
ENABLE_MONITORING=true
MONITORING_INTERVAL_SECONDS=10
METRICS_PORT=8001
```

#### 3. Database Migrations

```bash
# Apply migrations
python -m alembic upgrade head

# Verify database schema
psql langchain_ai -c "\\dt"
```

### Code Quality Checks

```bash
# Type checking
mypy src --strict

# Linting
flake8 src
pylint src

# Security scanning
bandit -r src

# Testing
pytest tests -v --cov=src
```

---

## Deployment Architectures

### Single Server Deployment

```
┌─────────────────────────────────┐
│   Reverse Proxy (Nginx)          │
│   - HTTPS termination            │
│   - Rate limiting                │
│   - Load balancing               │
└──────────────┬──────────────────┘
               │
┌──────────────┴──────────────────┐
│   FastAPI Application (gunicorn) │
│   - 4 worker processes           │
│   - Circuit breakers             │
│   - Health checks                │
└──────────────┬──────────────────┘
               │
       ┌───────┴────────┬─────────┐
       │                │         │
    ┌──▼──┐       ┌─────▼──┐  ┌──▼──┐
    │  DB │       │ Redis  │  │ LLM │
    └─────┘       └────────┘  └─────┘
```

### Load Balanced Deployment

```
                    ┌──────────────────┐
                    │  Load Balancer   │
                    │  (AWS ALB/NLB)   │
                    └────────┬─────────┘
                    │
        ┌───────────┼────────────┐
        │           │            │
    ┌───▼──┐   ┌───▼──┐    ┌───▼──┐
    │  App │   │  App │    │  App │
    │   #1 │   │  #2  │    │  #3  │
    └───┬──┘   └───┬──┘    └───┬──┘
        │          │           │
        └──────────┼───────────┘
                   │
        ┌──────────┴────────────┐
        │                       │
    ┌───▼──────┐          ┌────▼────┐
    │ RDS DB   │          │ Redis   │
    │ (Primary)│          │ Cluster │
    └───┬──────┘          └─────────┘
        │
    ┌───▼──────────────┐
    │ DB Replica (RO)  │
    └──────────────────┘
```

---

## Deployment Steps

### Step 1: Prepare Application

```bash
# Clone repository
git clone <repo-url>
cd langchain-ai-conversation

# Install dependencies
pip install -r requirements.txt

# Collect static files (if applicable)
python manage.py collectstatic --noinput
```

### Step 2: Run Database Migrations

```bash
# Apply database schema
python -m alembic upgrade head

# Seed initial data
python scripts/seed_database.py
```

### Step 3: Build Docker Image

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \\
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 4: Deploy with Docker Compose

```yaml
# docker-compose.prod.yml
version: "3.8"

services:
  db:
    image: postgres:14-alpine
    environment:
      POSTGRES_DB: langchain_ai
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  app:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - JWT_SECRET=${JWT_SECRET}
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
```

### Step 5: Start Application

```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# Verify deployment
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f app
```

---

## Health Checks and Monitoring

### Health Check Endpoints

```bash
# Liveness probe (is application running?)
curl http://localhost:8000/health

# Readiness probe (is application ready to serve?)
curl http://localhost:8000/health/ready

# Detailed status
curl http://localhost:8000/health/detailed

# Streaming health
curl http://localhost:8000/api/v1/health/stream
```

### Kubernetes Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: langchain-ai-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: langchain-ai-api
  template:
    metadata:
      labels:
        app: langchain-ai-api
    spec:
      containers:
      - name: api
        image: langchain-ai:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: langchain-secrets
              key: database-url
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 20
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "500m"
          limits:
            memory: "512Mi"
            cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: langchain-ai-api
spec:
  selector:
    app: langchain-ai-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

---

## Monitoring and Logging

### Prometheus Metrics

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'langchain-api'
    static_configs:
      - targets: ['localhost:8001']
```

### Structured Logging

```python
# src/infrastructure/logging.py
import logging
import json

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'request_id': getattr(record, 'request_id', None),
        }
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_data)
```

### Key Metrics to Monitor

```
- api_request_duration_ms (histogram)
  * Labels: endpoint, method, status
  * Target: P99 < 2000ms

- circuit_breaker_state (gauge)
  * Labels: breaker_name, state
  * Target: state = 0 (CLOSED)

- active_connections (gauge)
  * Target: < max_connections

- database_query_duration_ms (histogram)
  * Target: P99 < 500ms

- memory_usage_mb (gauge)
  * Target: < max_memory_mb

- error_rate_percent (gauge)
  * Target: < 0.1%
```

---

## Troubleshooting Guide

### Common Issues

#### 1. Database Connection Errors

```bash
# Check database connectivity
psql -h localhost -U user -d langchain_ai -c "SELECT 1"

# View connection pool stats
curl http://localhost:8001/metrics | grep postgres

# Fix: Increase pool size in .env
DATABASE_POOL_SIZE=30
DATABASE_MAX_OVERFLOW=20
```

#### 2. High Memory Usage

```bash
# Check memory leaks
docker stats --no-stream

# Review circuit breaker metrics
curl http://localhost:8000/api/v1/circuit-breaker-status

# Fix: Restart application or scale horizontally
```

#### 3. Slow API Responses

```bash
# Identify slow endpoints
curl http://localhost:8000/api/v1/metrics/endpoints

# Check database performance
EXPLAIN ANALYZE SELECT * FROM conversations ...

# Fix: Add indexes, optimize queries, scale vertically
```

#### 4. Circuit Breaker Stuck Open

```bash
# Check circuit breaker status
curl http://localhost:8001/metrics | grep circuit_breaker

# Manual reset
curl -X POST http://localhost:8000/admin/circuit-breaker/reset

# Fix: Address underlying service issue
```

---

## Backup and Recovery

### Database Backups

```bash
# Daily backup
0 2 * * * pg_dump langchain_ai | gzip > /backups/langchain_$(date +%Y%m%d).sql.gz

# Recovery
gunzip < /backups/langchain_20240101.sql.gz | psql langchain_ai
```

### Vector Index Recovery

```bash
# Rebuild vector indexes
python scripts/rebuild_vector_indexes.py

# Verify index health
curl http://localhost:8000/admin/vector-index-health
```

---

## Performance Tuning

### Database Optimization

```sql
-- Add missing indexes
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_embeddings_document_id ON embeddings(document_id);

-- Enable HNSW index for vectors
CREATE INDEX idx_embeddings_vector ON embeddings USING hnsw (embedding vector_cosine_ops);

-- Analyze query performance
ANALYZE;
```

### Application Tuning

```python
# Increase worker processes for CPU-bound work
# gunicorn config
workers = 4 * cpu_count()
worker_class = "uvicorn.workers.UvicornWorker"
keepalive = 65

# Connection pooling
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 10
```

### Network Optimization

```nginx
# nginx.conf
http {
    # Gzip compression
    gzip on;
    gzip_types text/plain application/json;
    gzip_min_length 1000;

    # Keep-alive
    keepalive_timeout 65;
    keepalive_requests 100;

    # Upstream connection pooling
    upstream api {
        keepalive 32;
        server localhost:8000;
        server localhost:8001;
    }
}
```

---

## Security Hardening

### HTTPS/TLS Configuration

```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# Update nginx.conf
server {
    listen 443 ssl;
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
}
```

### Rate Limiting

```python
# src/middleware/rate_limit_middleware.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/v1/conversations")
@limiter.limit("100/minute")
async def list_conversations(...):
    ...
```

### JWT Token Rotation

```python
# Implement token refresh mechanism
@app.post("/auth/refresh")
async def refresh_token(refresh_token: str):
    # Validate refresh token
    # Generate new access token
    # Invalidate old token
    pass
```

---

## Rollback Procedure

```bash
# Tag current version as rollback point
git tag -a rollback/v1.2.3 -m "Production deployment v1.2.3"

# Revert to previous version
git checkout rollback/v1.2.1

# Restart application
docker-compose -f docker-compose.prod.yml up -d --build

# Verify health
curl http://localhost:8000/health
```

---

## Post-Deployment Validation

```bash
#!/bin/bash
# validate_deployment.sh

echo "Validating deployment..."

# 1. Health checks
echo "✓ Checking health endpoints..."
curl -f http://localhost:8000/health || exit 1
curl -f http://localhost:8000/health/ready || exit 1

# 2. Database connectivity
echo "✓ Checking database..."
curl -f http://localhost:8000/admin/db-status || exit 1

# 3. API endpoints
echo "✓ Testing API endpoints..."
curl -f -H "Authorization: Bearer $TEST_TOKEN" http://localhost:8000/api/v1/conversations || exit 1

# 4. Streaming
echo "✓ Testing streaming endpoint..."
curl -f -H "Authorization: Bearer $TEST_TOKEN" http://localhost:8000/api/v1/health/stream || exit 1

# 5. Performance benchmark
echo "✓ Running performance benchmark..."
python tests/test_story33_performance.py || exit 1

echo "✅ All validations passed!"
```

---

## Support and Escalation

### Issues to Monitor

1. **Critical** (Page immediately):
   - Health check failing (all 3 endpoints down)
   - Error rate > 1%
   - API response P99 > 5000ms
   - Database unavailable

2. **High** (Within 1 hour):
   - Memory usage > 90%
   - CPU usage > 80% sustained
   - Circuit breaker open > 5 minutes
   - Error rate > 0.1%

3. **Medium** (Within 4 hours):
   - API response P99 > 2000ms
   - Slow database queries
   - High connection count

### Contact and Escalation

```
Level 1: On-Call Engineer (Slack #langchain-incidents)
Level 2: SRE Team (PagerDuty)
Level 3: Engineering Manager (Executive escalation)
```

---

## Conclusion

The LangChain AI Conversation System is now deployed and ready for production traffic.
Monitor health metrics continuously and follow the troubleshooting guide for any issues.

For questions or support: engineering@company.com
"""

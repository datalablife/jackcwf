# Financial RAG System - Deployment & Monitoring Quick Reference

**Production Readiness Checklist**

---

## SECTION 1: ENVIRONMENT SETUP

### Development Environment

```bash
# 1. Create Python environment
python3.11 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# Key packages:
# - langchain==1.0.0
# - langchain-anthropic==0.1.0
# - langchain-openai==0.1.0
# - langgraph==0.1.0
# - pinecone-client==3.0.0
# - fastapi==0.104.0
# - psycopg2-binary==2.9.0
# - redis==5.0.0
# - pydantic==2.0.0

# 3. Configure environment
cp .env.example .env
# Fill in:
# ANTHROPIC_API_KEY=sk-ant-...
# OPENAI_API_KEY=sk-...
# PINECONE_API_KEY=...
# DATABASE_URL=postgresql://localhost/financial_rag
# REDIS_URL=redis://localhost:6379
```

### Database Initialization

```bash
# Create PostgreSQL database
createdb financial_rag

# Initialize checkpoint and cost tables
python -c "from src.storage.checkpoint import CheckpointManager; CheckpointManager('$DATABASE_URL')._init_db()"
python -c "from src.storage.cost_db import CostDatabase; CostDatabase('$DATABASE_URL')._init_db()"

# Apply migrations
alembic upgrade head
```

### Vector Database Setup

```bash
# Initialize Pinecone index (100K documents, 1536-dim embeddings)
from pinecone import Pinecone

pc = Pinecone(api_key="YOUR_API_KEY")

# Create serverless index
index = pc.create_index(
    name="financial-documents",
    dimension=1536,
    metric="cosine",
    spec={
        "serverless": {
            "cloud": "aws",
            "region": "us-east-1"
        }
    }
)

# Index documents with metadata
# Add ~100K financial documents with metadata:
# {
#     "company": "AAPL",
#     "ticker": "AAPL",
#     "doc_type": "10-K",
#     "date": "2024-01-15",
#     "source": "SEC Edgar"
# }
```

---

## SECTION 2: LOCAL DEVELOPMENT

### Start Services

```bash
# Terminal 1: PostgreSQL
docker run -d \
  --name postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  postgres:15-alpine

# Terminal 2: Redis
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:7-alpine

# Terminal 3: FastAPI server
uvicorn src.api.main:app --reload --port 8000

# Terminal 4: Monitor logs
tail -f logs/app.log
```

### Test Agent Creation

```python
# test_agent_local.py

from src.agent.create_financial_agent import FinancialRAGAgent
from src.models import UserContext, UserTier
from src.storage.checkpoint import CheckpointManager
from src.storage.cost_db import CostDatabase

# Initialize components
checkpoint_mgr = CheckpointManager("postgresql://localhost/financial_rag")
cost_db = CostDatabase("postgresql://localhost/financial_rag")

user_context = UserContext(
    user_id="test_user",
    tier=UserTier.PRO,
    email="test@example.com",
    role="analyst",
)

# Create agent
agent_factory = FinancialRAGAgent(
    checkpoint_manager=checkpoint_mgr,
    cost_db=cost_db,
    vector_store=None,  # Mock for testing
    user_context=user_context,
)

agent = agent_factory.create()

# Test query
response = agent.invoke({
    "input": "What is Apple's P/E ratio trend?",
    "conversation_id": "conv_123",
})

print(response)
```

---

## SECTION 3: PRODUCTION DEPLOYMENT

### Docker Build & Deploy

```dockerfile
# Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY .env .env

# Run migrations on startup
CMD ["sh", "-c", "alembic upgrade head && uvicorn src.api.main:app --host 0.0.0.0 --port 8000"]
```

### Kubernetes Deployment

```yaml
# k8s/deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: financial-rag-api
  namespace: default

spec:
  replicas: 3

  selector:
    matchLabels:
      app: financial-rag-api

  template:
    metadata:
      labels:
        app: financial-rag-api
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"

    spec:
      containers:
      - name: api
        image: financial-rag:latest
        imagePullPolicy: IfNotPresent

        ports:
        - containerPort: 8000
          name: http

        env:
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-keys
              key: anthropic-key

        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-config
              key: postgres-url

        - name: REDIS_URL
          value: "redis://redis-service:6379"

        - name: PINECONE_API_KEY
          valueFrom:
            secretKeyRef:
              name: vector-db
              key: pinecone-key

        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5

        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5

        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
          limits:
            cpu: "2000m"
            memory: "2Gi"

---
apiVersion: v1
kind: Service
metadata:
  name: financial-rag-service
  namespace: default

spec:
  type: LoadBalancer
  selector:
    app: financial-rag-api

  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
```

### Scaling Configuration

```yaml
# k8s/autoscaling.yaml

apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: financial-rag-hpa

spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: financial-rag-api

  minReplicas: 3
  maxReplicas: 10

  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70

  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80

  behavior:
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15

    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
```

---

## SECTION 4: MONITORING & OBSERVABILITY

### LangSmith Dashboard Setup

```python
# src/monitoring/langsmith_setup.py

from langsmith import Client

client = Client()

# Create project
project = client.create_project(
    project_name="financial-rag-production"
)

# Configure feedback labels
client.create_feedback_type(
    project_name="financial-rag-production",
    feedback_key="accuracy",
    description="Is the analysis accurate?",
    feedback_type="binary"
)

client.create_feedback_type(
    project_name="financial-rag-production",
    feedback_key="cost_efficiency",
    description="Was the query cost-efficient?",
    feedback_type="numeric"
)

# Configure tracing tags
# - user_id: User identifier
# - conversation_id: Conversation session
# - provider: LLM provider used
# - query_complexity: Complexity level
# - cost_usd: Query cost
# - latency_ms: Response time
```

### Prometheus Metrics

```python
# src/monitoring/prometheus.py

from prometheus_client import Counter, Histogram, Gauge

# Counters
query_counter = Counter(
    'rag_queries_total',
    'Total queries',
    ['provider', 'user_tier', 'status']
)

token_counter = Counter(
    'rag_tokens_total',
    'Total tokens used',
    ['provider', 'type']  # type: input or output
)

cost_counter = Counter(
    'rag_cost_usd_total',
    'Total cost in USD',
    ['provider', 'user_tier']
)

# Histograms
latency_histogram = Histogram(
    'rag_query_latency_seconds',
    'Query latency',
    ['provider'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0)
)

token_histogram = Histogram(
    'rag_tokens_per_query',
    'Tokens per query',
    ['provider'],
    buckets=(100, 300, 500, 1000, 2000, 5000)
)

# Gauges
active_conversations = Gauge(
    'rag_active_conversations',
    'Active conversations'
)

cache_size = Gauge(
    'rag_cache_size_bytes',
    'Cache size in bytes'
)
```

### Grafana Dashboard Definition

```json
{
  "dashboard": {
    "title": "Financial RAG System",
    "panels": [
      {
        "title": "Query Volume",
        "targets": [
          {
            "expr": "rate(rag_queries_total[5m])",
            "legendFormat": "{{provider}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Average Latency (P95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rag_query_latency_seconds)",
            "legendFormat": "{{provider}}"
          }
        ]
      },
      {
        "title": "Daily Cost",
        "targets": [
          {
            "expr": "increase(rag_cost_usd_total[1d])",
            "legendFormat": "{{provider}}"
          }
        ]
      },
      {
        "title": "Token Usage",
        "targets": [
          {
            "expr": "rate(rag_tokens_total[5m])",
            "legendFormat": "{{provider}} - {{type}}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(rag_queries_total{status=\"error\"}[5m]) / rate(rag_queries_total[5m])",
            "legendFormat": "Error Rate"
          }
        ]
      },
      {
        "title": "Cache Hit Rate",
        "targets": [
          {
            "expr": "rate(cache_hits[5m]) / rate(cache_requests[5m])",
            "legendFormat": "Hit Rate"
          }
        ]
      }
    ]
  }
}
```

---

## SECTION 5: ALERTING RULES

### Alert Configuration (alert.rules.yml)

```yaml
groups:
- name: financial-rag-alerts
  rules:

  # Performance SLOs
  - alert: HighQueryLatency
    expr: histogram_quantile(0.95, rag_query_latency_seconds) > 5
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "Query latency {{ $value }}s exceeds 5s threshold"
      action: "Check vector DB, LLM provider status"

  - alert: ErrorRateSpike
    expr: rate(rag_queries_total{status="error"}[5m]) > 0.01
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Error rate {{ $value | humanizePercentage }} exceeds 1%"
      action: "Page on-call engineer immediately"

  # Cost SLOs
  - alert: DailyCostOverage
    expr: increase(rag_cost_usd_total[1d]) > 100
    for: 1h
    labels:
      severity: warning
    annotations:
      summary: "Daily cost ${{ $value }} exceeds $100 threshold"
      action: "Review recent queries, check for cost spikes"

  - alert: UserBudgetAlmost
    expr: user_tokens_remaining / user_tokens_allocated < 0.1
    for: 0m
    labels:
      severity: info
    annotations:
      summary: "User {{ $labels.user_id }} at 90% token budget"
      action: "Suggest upgrade or cost optimization"

  # Infrastructure
  - alert: VectorDBLatency
    expr: vector_search_latency_p95_ms > 2000
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Vector DB latency {{ $value }}ms exceeds 2s"
      action: "Scale Pinecone index, enable caching"

  - alert: PostgresConnectionPoolExhausted
    expr: postgres_connection_usage > 0.9
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Database connection pool 90% exhausted"
      action: "Increase pool size, investigate long queries"

  - alert: ProviderOutage
    expr: rate(rag_queries_total{provider="claude", status="error"}[5m]) > 0.05
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "Claude API outage detected"
      action: "Failover to GPT-4, notify Anthropic support"

  # PII Detection
  - alert: PIIDetectionFailure
    expr: pii_detection_confidence < 0.8
    for: 0m
    labels:
      severity: critical
    annotations:
      summary: "PII detection confidence below threshold"
      action: "Fallback to conservative masking, investigate"
```

---

## SECTION 6: COST TRACKING DASHBOARD

### User Cost Report Query

```sql
-- View user costs for current month
SELECT
    user_id,
    COUNT(*) as query_count,
    SUM(input_tokens + output_tokens) as total_tokens,
    SUM(cost_usd) as total_cost,
    AVG(latency_ms) as avg_latency_ms,
    SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END)::float / COUNT(*) as cache_hit_rate
FROM query_costs
WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE)
GROUP BY user_id
ORDER BY total_cost DESC;

-- View costs by provider
SELECT
    provider,
    SUM(cost_usd) as total_cost,
    SUM(input_tokens + output_tokens) as total_tokens,
    COUNT(*) as query_count,
    AVG(cost_usd) as avg_cost_per_query
FROM query_costs
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY provider;

-- Identify expensive queries
SELECT
    query_id,
    user_id,
    provider,
    input_tokens + output_tokens as total_tokens,
    cost_usd,
    latency_ms,
    created_at
FROM query_costs
WHERE created_at >= NOW() - INTERVAL '24 hours'
ORDER BY cost_usd DESC
LIMIT 20;
```

### Cost Optimization Report

```python
# src/monitoring/cost_report.py

def generate_cost_report(days=7):
    """Generate cost optimization report"""

    costs_by_provider = db.query("""
        SELECT provider, SUM(cost_usd) as cost
        FROM query_costs
        WHERE created_at >= NOW() - INTERVAL '%s days'
        GROUP BY provider
    """, (days,))

    cache_metrics = db.query("""
        SELECT
            COUNT(*) as total_queries,
            SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END) as cache_hits,
            SUM(CASE WHEN cache_hit THEN cost_usd ELSE 0 END) as cache_saved_cost
        FROM query_costs
        WHERE created_at >= NOW() - INTERVAL '%s days'
    """, (days,))

    print(f"Cost Report (Last {days} days)")
    print(f"================================")
    print(f"\nProvider Breakdown:")
    for provider, cost in costs_by_provider:
        print(f"  {provider}: ${cost:.2f}")

    total_cost = sum(cost for _, cost in costs_by_provider)
    cache_hit_rate = cache_metrics[0]['cache_hits'] / cache_metrics[0]['total_queries']

    print(f"\nTotal Cost: ${total_cost:.2f}")
    print(f"Cache Hit Rate: {cache_hit_rate:.1%}")
    print(f"Savings from Cache: ${cache_metrics[0]['cache_saved_cost']:.2f}")

    potential_savings = total_cost * 0.3  # 30% optimization potential
    print(f"\nOptimization Potential: ${potential_savings:.2f}")
```

---

## SECTION 7: INCIDENT RESPONSE PROCEDURES

### Response Playbook

```markdown
## Incident: High Error Rate

**Detection:** Alert triggered when error_rate > 1% for 5 minutes

**Immediate Actions (0-5 min):**
1. Check LangSmith dashboard for error patterns
2. Identify affected queries (provider, query_type, user_tier)
3. Check vector DB status (Pinecone)
4. Check LLM provider status (Anthropic, OpenAI)
5. Review database connection pool utilization

**Root Cause Analysis (5-30 min):**
- Error logs: `grep ERROR logs/app.log | tail -100`
- Provider errors: Check API status pages
- Database errors: Check PostgreSQL slow query log
- Vector DB errors: Check Pinecone metrics

**Mitigation (5-15 min):**
- If LLM outage: Enable failover to secondary provider
- If vector DB timeout: Enable caching, reduce k
- If database pool exhausted: Scale connection pool
- If code issue: Rollback to last known good version

**Recovery (15+ min):**
- Clear cache if needed: `redis-cli FLUSHALL`
- Increase monitoring frequency
- Notify users of service recovery
- Post-incident review within 24h

---

## Incident: High Latency

**Detection:** P95 latency > 5s for 10 minutes

**Immediate Actions:**
1. Check which provider is slow (Claude vs GPT-4)
2. Check vector DB latency
3. Check LLM provider rate limits
4. Check database query performance

**Mitigation:**
- Scale vector DB read replicas
- Reduce context window size
- Enable more aggressive caching
- Route to faster provider

---

## Incident: Cost Spike

**Detection:** Daily cost > $100 (threshold)

**Immediate Actions:**
1. Check query volume and average cost/query
2. Identify expensive query patterns
3. Check for cache misses
4. Review provider costs

**Mitigation:**
- Temporarily reduce context size
- Enable stricter caching
- Route to cheaper provider
- Check for malicious/automated queries
```

---

## SECTION 8: RUNBOOK & OPERATIONAL GUIDES

### Daily Operations Checklist

```markdown
## Daily Standup

### 1. Health Check (5 min)
- [ ] API uptime: 99.9%?
- [ ] Error rate: < 0.5%?
- [ ] P95 latency: < 5s?
- [ ] Vector DB: responsive?
- [ ] Database: normal connections?

### 2. Cost Review (5 min)
- [ ] Yesterday's cost: $XXX
- [ ] Average per query: $0.05?
- [ ] Top 10 expensive queries: reviewed?
- [ ] Cache hit rate: > 40%?

### 3. Recent Incidents (10 min)
- [ ] Any alerts triggered?
- [ ] Any customer reports?
- [ ] Performance regressions?
- [ ] Capacity concerns?

### 4. Planned Actions
- [ ] DB maintenance scheduled?
- [ ] Vector DB reindex needed?
- [ ] Dependencies to update?
```

### Scale Verification Commands

```bash
# Check API capacity
kubectl get pods -l app=financial-rag-api
kubectl top pods -l app=financial-rag-api

# Monitor active connections
psql -c "SELECT count(*) FROM pg_stat_activity WHERE datname = 'financial_rag';"

# Vector DB status
curl "https://api.pinecone.io/indexes/financial-documents" \
  -H "Api-Key: $PINECONE_API_KEY"

# Check cache size
redis-cli INFO memory

# Monitor query performance
tail -f logs/app.log | grep "latency_ms"
```

---

## SECTION 9: DISASTER RECOVERY

### Backup Strategy

```bash
# Automatic PostgreSQL backup (daily)
pg_dump financial_rag > backups/financial_rag_$(date +%Y%m%d).sql

# Restore from backup
psql financial_rag < backups/financial_rag_20241116.sql

# Pinecone index backup (document metadata)
curl "https://api.pinecone.io/indexes/financial-documents/vectors/fetch" \
  -H "Api-Key: $PINECONE_API_KEY" > backups/pinecone_vectors.json

# LangGraph checkpoint export
SELECT * FROM checkpoints WHERE created_at < NOW() - INTERVAL '30 days'
→ Export to S3 for archival
```

### Rollback Procedure

```bash
# 1. Stop current deployment
kubectl set image deployment/financial-rag-api \
  financial-rag-api=financial-rag:v1.5.0-backup

# 2. Wait for pods to restart
kubectl rollout status deployment/financial-rag-api

# 3. Verify health
curl http://localhost:8000/health

# 4. Check error logs
kubectl logs -l app=financial-rag-api --tail=100

# 5. If needed, restore database
psql financial_rag < backups/financial_rag_20241116.sql
```

---

## FINAL CHECKLIST: PRODUCTION READINESS

- [ ] LangSmith project configured with proper tagging
- [ ] Cost tracking database tested at scale (100K+ queries)
- [ ] Vector DB handles 100K documents with <2s latency
- [ ] All 6 middleware hooks tested and traced
- [ ] PII detection/masking verified on sensitive data
- [ ] Token counting accurate per provider (Claude, GPT-4)
- [ ] Failover mechanisms tested (provider outage simulation)
- [ ] Rate limiting rules in place
- [ ] Budget enforcement working (queries blocked at 100%)
- [ ] Streaming responses work with interruption handling
- [ ] Prometheus metrics exported properly
- [ ] Grafana dashboards operational
- [ ] Alerting rules triggering correctly
- [ ] Backup/restore procedures documented and tested
- [ ] On-call rotation established
- [ ] Customer communication plans for incidents
- [ ] Load testing completed (100 concurrent queries)
- [ ] Security audit passed (API keys, encryption, PII)

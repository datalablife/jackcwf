# Monitoring and Observability Stack - Deployment Guide

## Overview

This guide covers the deployment of a comprehensive monitoring and observability system for the LangChain AI application, including:

- **Prometheus**: Metrics collection and alerting
- **Grafana**: Metrics visualization and dashboards
- **Elasticsearch**: Log storage and search
- **Logstash**: Log collection and parsing
- **Kibana**: Log visualization and analytics
- **AlertManager**: Alert routing and management

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   FastAPI    │  │    Nginx     │  │  Frontend    │      │
│  │   (Backend)  │  │ (Proxy)      │  │  (React)     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘      │
│         │                 │                                  │
└─────────┼─────────────────┼──────────────────────────────────┘
          │                 │
          │ /metrics        │ logs
          ▼                 ▼
┌─────────────────────────────────────────────────────────────┐
│                  Monitoring Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Prometheus  │  │   Logstash   │  │ AlertManager │      │
│  │  (Metrics)   │  │ (Log Parser) │  │  (Alerts)    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼──────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                  Storage Layer                               │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │  Prometheus  │  │ Elasticsearch│                         │
│  │   TSDB       │  │  (Indices)   │                         │
│  └──────┬───────┘  └──────┬───────┘                         │
└─────────┼──────────────────┼──────────────────────────────────┘
          │                  │
          ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│              Visualization Layer                             │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │   Grafana    │  │    Kibana    │                         │
│  │ (Dashboards) │  │  (Log View)  │                         │
│  └──────────────┘  └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **Docker and Docker Compose** installed
2. **Coolify** deployment platform (or standalone Docker)
3. **Minimum System Requirements**:
   - CPU: 4 cores
   - RAM: 8GB (16GB recommended)
   - Disk: 50GB free space

## Quick Start (Local Development)

### Step 1: Clone Configuration

All monitoring configurations are in the `monitoring/` directory:

```bash
monitoring/
├── prometheus/
│   ├── prometheus.yml
│   ├── alerts.yml
│   └── recording_rules.yml
├── grafana/
│   ├── provisioning/
│   └── dashboards/
├── alertmanager/
│   ├── alertmanager.yml
│   └── templates/
├── logstash/
│   ├── logstash.conf
│   └── patterns/
├── elasticsearch/
│   └── elasticsearch.yml
└── kibana/
    └── kibana.yml
```

### Step 2: Configure Environment Variables

Create `.env.monitoring` file:

```bash
# Grafana
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=your_secure_password

# AlertManager
SMTP_PASSWORD=your_smtp_password
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Application
ENVIRONMENT=production
HOSTNAME=langchain-ai-prod

# Elasticsearch
ES_JAVA_OPTS=-Xms1g -Xmx1g

# Logstash
LS_JAVA_OPTS=-Xms512m -Xmx512m
ELASTICSEARCH_HOSTS=http://elasticsearch:9200
```

### Step 3: Start Monitoring Stack

```bash
# Start all services
docker-compose -f docker-compose.monitoring.yml --env-file .env.monitoring up -d

# Verify services are running
docker-compose -f docker-compose.monitoring.yml ps

# View logs
docker-compose -f docker-compose.monitoring.yml logs -f
```

### Step 4: Access Dashboards

- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Kibana**: http://localhost:5601
- **AlertManager**: http://localhost:9093
- **Elasticsearch**: http://localhost:9200

### Step 5: Verify Metrics Collection

1. Check Prometheus targets: http://localhost:9090/targets
2. Verify FastAPI metrics: http://localhost:8000/metrics
3. Check Grafana dashboard: http://localhost:3001/d/application-overview

## Production Deployment (Coolify)

### Option 1: Integrated Deployment (Recommended)

Deploy monitoring stack alongside your application:

1. **Update Main Application**:

```yaml
# Add to your main docker-compose.yml
networks:
  app-network:
    name: app-network
    driver: bridge
```

2. **Deploy Monitoring Stack**:

```bash
# On Coolify server
cd /var/lib/coolify/applications/your-app-id
docker-compose -f docker-compose.monitoring.yml --env-file .env.monitoring up -d
```

3. **Configure Traefik Routes** (in Coolify UI):

```
prometheus.yourdomain.com -> prometheus:9090
grafana.yourdomain.com -> grafana:3000
kibana.yourdomain.com -> kibana:5601
```

### Option 2: Separate Coolify Services

Deploy each component as a separate Coolify service:

1. **Prometheus Service**:
   - Type: Docker Compose
   - Repository: Use `monitoring/prometheus/` files
   - Port: 9090
   - Volume: `/prometheus` for data persistence

2. **Grafana Service**:
   - Type: Docker Compose
   - Port: 3000
   - Volume: `/var/lib/grafana` for data persistence

3. **Elasticsearch Service**:
   - Type: Docker Compose
   - Port: 9200
   - Volume: `/usr/share/elasticsearch/data` (at least 50GB)

4. **Logstash Service**:
   - Type: Docker Compose
   - Port: 5044
   - Mount application log directory: `/var/log/app`

5. **Kibana Service**:
   - Type: Docker Compose
   - Port: 5601
   - Link to Elasticsearch

## Configuration Details

### Prometheus Metrics

Your FastAPI application already exposes metrics at `/metrics`:

```python
# Available metrics:
- llm_cache_hits_total
- llm_cache_misses_total
- llm_cache_hit_latency_ms
- llm_query_latency_ms
- llm_generation_latency_ms
- llm_cache_size_entries
- llm_cache_hit_rate
```

### Alert Rules

Key alerts configured in `prometheus/alerts.yml`:

1. **Critical Alerts**:
   - ServiceDown (2min)
   - CriticalAPILatency (P95 > 5s)
   - CriticalCPUUsage (> 90%)
   - CriticalMemoryUsage (> 90%)

2. **Warning Alerts**:
   - HighAPILatency (P95 > 3s)
   - HighErrorRate (> 5%)
   - LowCacheHitRate (< 30%)
   - HighCPUUsage (> 80%)

### Log Collection

Logstash collects logs from:

1. **FastAPI Backend**: `/var/log/app/backend.log`
2. **Nginx Access**: `/var/log/app/nginx_access.log`
3. **Nginx Error**: `/var/log/app/nginx_error.log`
4. **Health Monitor**: `/var/log/app/health_monitor.log`

Logs are indexed in Elasticsearch as:
- `langchain-ai-YYYY.MM.DD` (all logs)
- `langchain-ai-errors-YYYY.MM.DD` (errors only)
- `langchain-ai-performance-YYYY.MM.DD` (slow requests)

## Grafana Dashboards

Pre-configured dashboard: **LangChain AI - Application Overview**

Panels include:
1. System Health Overview
2. Cache Hit Rate
3. API P95 Latency
4. Request Rate
5. CPU/Memory Usage
6. API Latency Over Time
7. Cache Performance
8. Component Latency Breakdown
9. Error Rate
10. Resource Utilization Trends
11. Cost Savings
12. SLA Compliance

## Kibana Setup

### Initial Configuration

1. **Create Index Pattern**:
   - Go to Stack Management > Index Patterns
   - Pattern: `langchain-ai-*`
   - Time field: `@timestamp`

2. **Import Dashboards**:
   - Go to Stack Management > Saved Objects
   - Import from `monitoring/kibana/dashboards/` (if created)

3. **Common Searches**:

```
# All errors
level: "ERROR"

# Slow requests (> 3s)
duration_ms: >3000

# Cache misses
cache_hit: false

# 5xx errors
status: [500 TO 599]

# Specific endpoint
endpoint: "/api/v1/conversations/*/chat"
```

## Alert Notification Setup

### Email Notifications

Configure in `monitoring/alertmanager/alertmanager.yml`:

```yaml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@yourdomain.com'
  smtp_auth_username: 'alerts@yourdomain.com'
  smtp_auth_password: '${SMTP_PASSWORD}'
```

### Slack Notifications

1. Create Slack incoming webhook
2. Set `SLACK_WEBHOOK_URL` in `.env.monitoring`
3. Configure channels in alertmanager.yml:
   - `#alerts-critical` - Critical alerts
   - `#backend-alerts` - Backend issues
   - `#ops-alerts` - Infrastructure issues

### PagerDuty Integration (Optional)

Uncomment in `alertmanager.yml`:

```yaml
pagerduty_configs:
  - service_key: '${PAGERDUTY_SERVICE_KEY}'
```

## Maintenance and Operations

### Daily Tasks

1. **Check Dashboard**: Review Grafana dashboard for anomalies
2. **Review Alerts**: Check AlertManager for firing alerts
3. **Log Analysis**: Search Kibana for errors and warnings

### Weekly Tasks

1. **Performance Review**: Analyze latency trends
2. **Cache Optimization**: Review cache hit rates
3. **Capacity Planning**: Check resource utilization trends

### Monthly Tasks

1. **Index Cleanup**: Delete old Elasticsearch indices
2. **Alert Tuning**: Adjust alert thresholds based on trends
3. **Cost Analysis**: Review cache savings and resource costs

### Cleanup Commands

```bash
# Delete old Elasticsearch indices (> 30 days)
curl -X DELETE "localhost:9200/langchain-ai-2024.01.*"

# Clean Prometheus data (restart with retention)
docker-compose -f docker-compose.monitoring.yml restart prometheus

# Backup Grafana dashboards
docker exec grafana grafana-cli admin export-dashboard > backup.json
```

## Troubleshooting

### Prometheus Not Scraping Metrics

1. Check FastAPI `/metrics` endpoint: `curl http://localhost:8000/metrics`
2. Verify Prometheus targets: http://localhost:9090/targets
3. Check network connectivity: `docker network inspect app-network`

### Logstash Not Receiving Logs

1. Check log file permissions: `ls -la /var/log/app/`
2. Verify Logstash pipeline: http://localhost:9600/_node/stats
3. Check Elasticsearch connection: `curl http://localhost:9200/_cluster/health`

### High Memory Usage

1. Reduce Elasticsearch heap: `ES_JAVA_OPTS=-Xms512m -Xmx512m`
2. Limit Logstash threads: Set `pipeline.workers: 2` in logstash.yml
3. Decrease Prometheus retention: `--storage.tsdb.retention.time=15d`

### Alerts Not Firing

1. Check AlertManager status: http://localhost:9093/#/status
2. Verify alert rules: http://localhost:9090/rules
3. Test alert: `curl -X POST http://localhost:9093/api/v1/alerts`

## Performance Optimization

### Elasticsearch Optimization

```bash
# Increase refresh interval (better write performance)
curl -X PUT "localhost:9200/langchain-ai-*/_settings" -H 'Content-Type: application/json' -d'
{
  "index": {
    "refresh_interval": "30s"
  }
}'

# Force merge old indices (reduce disk usage)
curl -X POST "localhost:9200/langchain-ai-2024.01.*/_forcemerge?max_num_segments=1"
```

### Prometheus Optimization

1. Use recording rules for complex queries
2. Reduce scrape frequency for less critical metrics
3. Enable remote write for long-term storage

### Grafana Optimization

1. Set reasonable dashboard refresh intervals (30s+)
2. Use variables for dynamic dashboards
3. Limit query time ranges for heavy queries

## Security Best Practices

1. **Enable Authentication**:
   - Grafana: Change default password
   - Elasticsearch: Enable X-Pack security
   - Kibana: Configure authentication

2. **Network Security**:
   - Use internal networks for inter-service communication
   - Expose only necessary ports via Traefik
   - Enable HTTPS for public endpoints

3. **Access Control**:
   - Create read-only Grafana users for team members
   - Restrict Elasticsearch write access
   - Use API keys for external integrations

## Cost Monitoring

Monitor infrastructure costs using Grafana dashboard:

- **Cache Savings**: Estimated USD saved by caching
- **Request Volume**: Total requests per hour/day
- **Resource Usage**: CPU/Memory/Disk trends

## Support and Resources

- **Documentation**: See `docs/` directory
- **Grafana Dashboards**: https://grafana.com/grafana/dashboards/
- **Prometheus Docs**: https://prometheus.io/docs/
- **ELK Stack**: https://www.elastic.co/guide/

## Next Steps

1. ✅ Deploy monitoring stack
2. ✅ Configure alert notifications
3. ✅ Create custom Grafana dashboards
4. ✅ Set up log retention policies
5. ✅ Configure backup strategies
6. ✅ Train team on dashboard usage
7. ✅ Document incident response procedures

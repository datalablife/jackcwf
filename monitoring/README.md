# Monitoring and Observability Stack

Complete monitoring and observability solution for the LangChain AI application.

## Quick Reference

### Service Endpoints

| Service | Port | URL | Credentials |
|---------|------|-----|-------------|
| Grafana | 3001 | http://localhost:3001 | admin/admin (change on first login) |
| Prometheus | 9090 | http://localhost:9090 | None |
| Kibana | 5601 | http://localhost:5601 | None |
| Elasticsearch | 9200 | http://localhost:9200 | None |
| AlertManager | 9093 | http://localhost:9093 | None |
| Logstash | 5044 | TCP input | None |

### Quick Start

```bash
# 1. Copy environment file
cp .env.monitoring.example .env.monitoring

# 2. Edit configuration (set passwords, webhook URLs)
nano .env.monitoring

# 3. Deploy monitoring stack
./scripts/monitoring/deploy-monitoring.sh deploy

# 4. Verify services
./scripts/monitoring/deploy-monitoring.sh verify
```

### Common Operations

```bash
# View logs
docker-compose -f docker-compose.monitoring.yml logs -f [service]

# Restart service
docker-compose -f docker-compose.monitoring.yml restart [service]

# Stop all services
./scripts/monitoring/deploy-monitoring.sh stop

# Check service status
./scripts/monitoring/deploy-monitoring.sh status

# Clean up everything
./scripts/monitoring/deploy-monitoring.sh clean
```

## Key Features

### Prometheus Metrics

- **Cache Performance**: Hit rate, latency, size
- **API Performance**: Request rate, latency (P50/P95/P99), error rate
- **LLM Operations**: Generation latency, embedding latency, token usage
- **System Resources**: CPU, memory, disk, open files
- **Database**: Vector search latency, connection pool usage

### Alert Rules

#### Critical (2-5 min)
- Service Down
- CPU/Memory > 90%
- API Latency P95 > 5s

#### Warning (5-10 min)
- CPU/Memory > 80%
- Cache Hit Rate < 30%
- API Latency P95 > 3s
- Error Rate > 5%

### Log Collection

**Sources**:
- FastAPI backend logs (JSON structured)
- Nginx access logs
- Nginx error logs
- Health monitor logs

**Indices**:
- `langchain-ai-*` - All logs
- `langchain-ai-errors-*` - Errors only
- `langchain-ai-performance-*` - Slow requests (>3s)

### Grafana Dashboards

**Pre-configured Dashboard**: LangChain AI - Application Overview

**Key Panels**:
1. System health indicators
2. Cache performance metrics
3. API latency graphs
4. Resource utilization
5. Error rate tracking
6. Cost savings calculations
7. SLA compliance monitoring

## Architecture Overview

```
┌─────────────────┐
│   Application   │
│    (FastAPI)    │
│   /metrics      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│   Prometheus    │────▶│  AlertManager   │
│  (Scrape 15s)   │     │   (Routing)     │
└────────┬────────┘     └────────┬────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│    Grafana      │     │ Email/Slack     │
│  (Dashboards)   │     │   (Alerts)      │
└─────────────────┘     └─────────────────┘

┌─────────────────┐
│  App Logs       │
│  (JSON/Text)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Logstash     │
│   (Parse/Tag)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Elasticsearch   │
│  (Index/Store)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     Kibana      │
│  (Log Search)   │
└─────────────────┘
```

## Configuration Files

### Prometheus
- `monitoring/prometheus/prometheus.yml` - Main config
- `monitoring/prometheus/alerts.yml` - Alert rules
- `monitoring/prometheus/recording_rules.yml` - Recording rules

### Grafana
- `monitoring/grafana/provisioning/datasources/` - Data sources
- `monitoring/grafana/provisioning/dashboards/` - Dashboard config
- `monitoring/grafana/dashboards/` - Dashboard JSON files

### AlertManager
- `monitoring/alertmanager/alertmanager.yml` - Alert routing
- `monitoring/alertmanager/templates/` - Notification templates

### ELK Stack
- `monitoring/elasticsearch/elasticsearch.yml` - ES config
- `monitoring/logstash/logstash.conf` - Pipeline config
- `monitoring/logstash/patterns/` - Grok patterns
- `monitoring/kibana/kibana.yml` - Kibana config

## Performance Tuning

### For Low Resources (< 8GB RAM)

```yaml
# In .env.monitoring
ES_JAVA_OPTS=-Xms512m -Xmx512m
LS_JAVA_OPTS=-Xms256m -Xmx256m
PROMETHEUS_RETENTION_TIME=7d
```

### For High Traffic (> 1000 req/s)

```yaml
# In .env.monitoring
ES_JAVA_OPTS=-Xms2g -Xmx2g
LS_JAVA_OPTS=-Xms1g -Xmx1g
LOGSTASH_PIPELINE_WORKERS=4
PROMETHEUS_SCRAPE_INTERVAL=10s
```

## Troubleshooting

### Prometheus Not Collecting Metrics

```bash
# Check FastAPI metrics endpoint
curl http://localhost:8000/metrics

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq

# View Prometheus logs
docker-compose -f docker-compose.monitoring.yml logs prometheus
```

### Elasticsearch Out of Memory

```bash
# Reduce heap size
export ES_JAVA_OPTS="-Xms512m -Xmx512m"

# Delete old indices
curl -X DELETE "localhost:9200/langchain-ai-2024.01.*"

# Check cluster health
curl http://localhost:9200/_cluster/health?pretty
```

### Logstash Not Processing Logs

```bash
# Check pipeline status
curl http://localhost:9600/_node/stats/pipelines?pretty

# View Logstash logs
docker-compose -f docker-compose.monitoring.yml logs logstash

# Test Grok patterns
# Use Kibana Dev Tools -> Grok Debugger
```

### Grafana Dashboard Not Loading

```bash
# Check Grafana logs
docker-compose -f docker-compose.monitoring.yml logs grafana

# Verify Prometheus datasource
curl http://localhost:3001/api/datasources | jq

# Restart Grafana
docker-compose -f docker-compose.monitoring.yml restart grafana
```

## Security Hardening

### Production Checklist

- [ ] Change default Grafana password
- [ ] Enable Elasticsearch X-Pack security
- [ ] Configure SSL/TLS for all services
- [ ] Restrict network access (internal only)
- [ ] Enable authentication for Prometheus
- [ ] Use secrets management for credentials
- [ ] Set up firewall rules
- [ ] Enable audit logging

### Example: Enable Basic Auth

```yaml
# In prometheus.yml
basic_auth:
  username: prometheus
  password: ${PROMETHEUS_PASSWORD}

# In grafana provisioning
jsonData:
  basicAuth: true
  basicAuthUser: prometheus
```

## Backup and Recovery

### Backup Grafana Dashboards

```bash
# Export all dashboards
docker exec grafana grafana-cli admin export-dashboard > backup.json

# Import dashboard
# Grafana UI -> Dashboards -> Import -> Upload JSON
```

### Backup Prometheus Data

```bash
# Create snapshot
docker exec prometheus promtool tsdb snapshot /prometheus

# Copy to backup location
docker cp prometheus:/prometheus/snapshots/latest ./backup/
```

### Backup Elasticsearch Indices

```bash
# Create snapshot repository
curl -X PUT "localhost:9200/_snapshot/backup" -H 'Content-Type: application/json' -d'
{
  "type": "fs",
  "settings": {
    "location": "/backup"
  }
}'

# Create snapshot
curl -X PUT "localhost:9200/_snapshot/backup/snapshot_1?wait_for_completion=true"
```

## Maintenance Schedule

### Daily
- Check Grafana dashboard for anomalies
- Review critical alerts
- Monitor disk space usage

### Weekly
- Review alert thresholds
- Analyze performance trends
- Check for slow queries in Kibana

### Monthly
- Delete old Elasticsearch indices
- Review and optimize alert rules
- Update dashboard based on feedback
- Review capacity planning metrics

## Advanced Features

### Custom Metrics

Add custom metrics in FastAPI:

```python
from prometheus_client import Counter, Histogram

# Define custom metric
custom_requests = Counter(
    'custom_requests_total',
    'Total custom requests',
    ['endpoint', 'status']
)

# Record metric
custom_requests.labels(endpoint='/api/custom', status='success').inc()
```

### Custom Grok Patterns

Add patterns in `monitoring/logstash/patterns/`:

```
# Custom pattern
MY_PATTERN %{DATA:field1} - %{NUMBER:field2}
```

### Alert Silencing

```bash
# Silence alert for 2 hours
curl -X POST http://localhost:9093/api/v1/silences \
  -H 'Content-Type: application/json' \
  -d '{
    "matchers": [{"name": "alertname", "value": "HighAPILatency"}],
    "startsAt": "2024-01-01T00:00:00Z",
    "endsAt": "2024-01-01T02:00:00Z",
    "comment": "Planned maintenance"
  }'
```

## Resources

- [Full Deployment Guide](../docs/deployment/MONITORING_DEPLOYMENT_GUIDE.md)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Elasticsearch Guide](https://www.elastic.co/guide/)
- [AlertManager Guide](https://prometheus.io/docs/alerting/latest/alertmanager/)

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review service logs
3. Consult official documentation
4. Open an issue in the repository

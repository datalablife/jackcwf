# High-Availability Deployment - Complete Solution

This document provides a comprehensive overview of the high-availability deployment architecture for the Jackcwf AI Conversation Platform.

## Quick Links

- [Deployment Guide](../../docs/deployment/HA_DEPLOYMENT_GUIDE.md) - Detailed step-by-step guide
- [Docker Compose Setup](#docker-compose-deployment) - Simple multi-replica deployment
- [Kubernetes Setup](#kubernetes-deployment) - Production-grade auto-scaling
- [Monitoring Stack](#monitoring-and-observability) - Prometheus + Grafana

---

## Architecture Summary

### Single Container Architecture (Current)

```
┌──────────────────────────────────────┐
│  Docker Container                     │
│                                      │
│  ┌────────────────────────────────┐ │
│  │  Supervisor                    │ │
│  │                                │ │
│  │  ├─ Nginx (port 80)           │ │
│  │  │   - Frontend (React)       │ │
│  │  │   - Reverse proxy to API   │ │
│  │  │                            │ │
│  │  ├─ FastAPI (port 8000)       │ │
│  │  │   - Backend API            │ │
│  │  │   - 2 Uvicorn workers      │ │
│  │  │                            │ │
│  │  └─ Health Monitor            │ │
│  └────────────────────────────────┘ │
└──────────────────────────────────────┘
```

### High-Availability Architecture (New)

```
                    Internet
                       │
                       ▼
              ┌────────────────┐
              │  Load Balancer │
              │   (Traefik)    │
              └────────┬───────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
    ┌───────┐      ┌───────┐      ┌───────┐
    │ Pod 1 │      │ Pod 2 │      │ Pod 3 │
    │       │      │       │      │       │
    │ Nginx │      │ Nginx │      │ Nginx │
    │   +   │      │   +   │      │   +   │
    │FastAPI│      │FastAPI│      │FastAPI│
    └───┬───┘      └───┬───┘      └───┬───┘
        │              │              │
        └──────────────┼──────────────┘
                       │
                       ▼
              ┌────────────────┐
              │   PostgreSQL   │
              │   (External)   │
              └────────────────┘
```

---

## Files Overview

### Docker Compose Deployment

```
deployment/
├── docker-compose.ha.yml           # Main HA configuration (3 replicas + Traefik)
├── traefik/
│   ├── traefik.yml                # Traefik static configuration
│   └── dynamic/
│       └── dynamic.yml            # Traefik dynamic configuration (middlewares)
├── scripts/
│   ├── deploy-ha.sh               # Deployment automation script
│   └── health-check.sh            # Health monitoring script
└── monitoring/
    ├── docker-compose.monitoring.yml  # Prometheus + Grafana stack
    ├── prometheus/
    │   ├── prometheus.yml         # Prometheus configuration
    │   └── rules/
    │       └── alerts.yml         # Alerting rules
    ├── alertmanager/
    │   └── alertmanager.yml       # Alert routing configuration
    └── grafana/
        └── provisioning/          # Grafana dashboards
```

### Kubernetes Deployment

```
deployment/
└── kubernetes/
    └── all-in-one.yml             # Complete K8s manifests
        ├── Namespace
        ├── ConfigMap
        ├── Secret
        ├── Deployment (3-10 replicas)
        ├── Service (ClusterIP)
        ├── HPA (Horizontal Pod Autoscaler)
        ├── Ingress (NGINX)
        ├── PodDisruptionBudget
        └── ServiceMonitor (Prometheus)
```

---

## Quick Start

### Option 1: Docker Compose (Recommended for Development)

```bash
# 1. Build image
docker build -t jackcwf-backend:latest .

# 2. Deploy with 3 replicas
./deployment/scripts/deploy-ha.sh --platform docker-compose --replicas 3

# 3. Verify deployment
./deployment/scripts/health-check.sh --platform docker-compose

# 4. Access application
curl http://localhost/health
```

**Pros:**
- Simple setup (1 command)
- Fast deployment (< 2 minutes)
- Good for development and small production

**Cons:**
- Manual scaling only
- No advanced features (auto-healing, auto-scaling)

---

### Option 2: Kubernetes (Recommended for Production)

```bash
# 1. Update secrets in all-in-one.yml
nano deployment/kubernetes/all-in-one.yml

# 2. Deploy to Kubernetes
kubectl apply -f deployment/kubernetes/all-in-one.yml

# 3. Verify deployment
kubectl get pods -n jackcwf
kubectl get hpa -n jackcwf

# 4. Access application
kubectl port-forward -n jackcwf svc/jackcwf-backend-service 8080:80
curl http://localhost:8080/health
```

**Pros:**
- Auto-scaling (HPA)
- Self-healing
- Rolling updates with zero downtime
- Advanced features (PDB, resource quotas)

**Cons:**
- Complex setup
- Requires Kubernetes cluster
- Steeper learning curve

---

## Key Features

### 1. Load Balancing

**Traefik (Docker Compose):**
- Automatic service discovery
- Health checks
- Sticky sessions (optional)
- SSL termination
- Dashboard at http://localhost:8080

**NGINX Ingress (Kubernetes):**
- Advanced routing rules
- Rate limiting
- CORS configuration
- Let's Encrypt integration

### 2. Auto-Scaling

**Kubernetes HPA:**
```yaml
minReplicas: 3
maxReplicas: 10
metrics:
  - CPU: 70%
  - Memory: 80%
```

**Manual Scaling (Docker Compose):**
```bash
docker-compose -f deployment/docker-compose.ha.yml up -d --scale web=5
```

### 3. Health Checks

**Health Endpoint:**
```bash
curl http://localhost/health

# Response:
{
  "status": "healthy",
  "timestamp": "2025-11-21T10:00:00Z"
}
```

**Automated Monitoring:**
```bash
# Continuous monitoring
./deployment/scripts/health-check.sh --continuous --platform docker-compose
```

### 4. Rolling Updates

**Docker Compose:**
```bash
# Zero-downtime update
docker build -t jackcwf-backend:latest .
docker-compose -f deployment/docker-compose.ha.yml up -d
```

**Kubernetes:**
```bash
# Rolling update strategy
kubectl set image deployment/jackcwf-backend jackcwf-backend=jackcwf-backend:v2 -n jackcwf
kubectl rollout status deployment/jackcwf-backend -n jackcwf
```

### 5. Resource Limits

**Per Replica:**
```yaml
resources:
  requests:
    cpu: 500m
    memory: 512Mi
  limits:
    cpu: 2000m
    memory: 2Gi
```

---

## Monitoring Stack

### Prometheus + Grafana + AlertManager

```bash
# Deploy monitoring stack
docker-compose -f deployment/monitoring/docker-compose.monitoring.yml up -d

# Access dashboards
# Prometheus: http://localhost:9090
# Grafana:    http://localhost:3001 (admin/admin)
# AlertManager: http://localhost:9093
```

### Metrics Available

- **Application Metrics**
  - HTTP request rate
  - Response time (P50, P95, P99)
  - Error rate
  - Cache hit ratio

- **Infrastructure Metrics**
  - CPU usage
  - Memory usage
  - Disk usage
  - Network I/O

- **Container Metrics**
  - Container CPU/Memory
  - Restart count
  - Health status

- **Business Metrics**
  - User activity
  - LLM API costs
  - Database query performance

### Alert Rules

See `/deployment/monitoring/prometheus/rules/alerts.yml` for 25+ alert rules including:

- Service down
- High error rate
- High latency
- Resource exhaustion
- Database issues
- Cache performance

---

## Configuration Reference

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# LLM APIs
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key

# Application
UVICORN_WORKERS=2              # Workers per replica
GRACEFUL_SHUTDOWN_TIMEOUT=30   # Seconds

# Monitoring
ENABLE_MONITORING=true
MONITORING_INTERVAL_SECONDS=10

# Health Check
HEALTH_CHECK_TIMEOUT_MS=2000
```

### Traefik Labels (Docker Compose)

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.app.rule=Host(`jackcwf.com`)"
  - "traefik.http.services.app.loadbalancer.server.port=80"
  - "traefik.http.services.app.loadbalancer.sticky.cookie=true"
  - "traefik.http.services.app.loadbalancer.healthcheck.path=/health"
```

### Kubernetes Annotations

```yaml
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "80"
  prometheus.io/path: "/metrics"
```

---

## Performance Tuning

### Small Deployment (< 100 users)

```yaml
replicas: 2
resources:
  requests: { cpu: 250m, memory: 256Mi }
  limits: { cpu: 1000m, memory: 1Gi }
```

### Medium Deployment (100-1000 users)

```yaml
replicas: 3
resources:
  requests: { cpu: 500m, memory: 512Mi }
  limits: { cpu: 2000m, memory: 2Gi }
```

### Large Deployment (1000+ users)

```yaml
replicas: 5-10 (auto-scale)
resources:
  requests: { cpu: 1000m, memory: 1Gi }
  limits: { cpu: 4000m, memory: 4Gi }
```

---

## Troubleshooting

### Check Container Status

```bash
# Docker Compose
docker-compose -f deployment/docker-compose.ha.yml ps
docker-compose -f deployment/docker-compose.ha.yml logs -f web

# Kubernetes
kubectl get pods -n jackcwf
kubectl logs -f <pod-name> -n jackcwf
kubectl describe pod <pod-name> -n jackcwf
```

### Common Issues

**1. Containers Not Starting**
```bash
# Check logs
docker logs <container-id>

# Check environment variables
docker exec <container-id> env
```

**2. Database Connection Errors**
```bash
# Test connectivity
docker run --rm postgres:15 psql $DATABASE_URL -c "SELECT 1"
```

**3. Load Balancer Not Working**
```bash
# Check Traefik dashboard
http://localhost:8080

# Verify health endpoint
curl http://localhost/health
```

---

## Deployment Checklist

- [ ] Review and update `.env` file
- [ ] Build Docker image
- [ ] Test single container deployment
- [ ] Deploy HA stack (3 replicas)
- [ ] Verify health checks
- [ ] Deploy monitoring stack
- [ ] Configure alerts
- [ ] Set up backups
- [ ] Document rollback procedure
- [ ] Load test deployment

---

## Security Best Practices

1. **Use Secrets Management**
   - Kubernetes Secrets
   - Docker Secrets
   - Vault integration

2. **Enable HTTPS**
   - Let's Encrypt certificates
   - Traefik SSL termination

3. **Network Isolation**
   - Private networks
   - Firewall rules

4. **Resource Limits**
   - CPU/Memory limits
   - Rate limiting

5. **Regular Updates**
   - Security patches
   - Dependency updates

---

## Cost Optimization

1. **Right-Size Replicas**
   - Monitor actual usage
   - Adjust HPA settings
   - Scale down during off-peak

2. **Use Spot Instances**
   - For non-critical workloads
   - Kubernetes node affinity

3. **Optimize Images**
   - Multi-stage builds
   - Slim base images
   - Layer caching

---

## Next Steps

1. **Setup CI/CD**
   - Automate builds
   - Deploy on Git push
   - Automated testing

2. **Add Caching**
   - Deploy Redis
   - Semantic caching
   - API response caching

3. **Implement Backups**
   - Database backups
   - Configuration backups
   - Disaster recovery plan

4. **Advanced Monitoring**
   - Custom dashboards
   - Business metrics
   - Cost tracking

---

## Support

For detailed guides, see:
- [Complete Deployment Guide](../../docs/deployment/HA_DEPLOYMENT_GUIDE.md)
- [Monitoring Setup Guide](./monitoring/README.md)
- [Troubleshooting Guide](../../docs/deployment/DEPLOYMENT_RECOVERY_GUIDE.md)

---

**Document Version:** 1.0
**Last Updated:** 2025-11-21
**Author:** Claude (DevOps Agent)

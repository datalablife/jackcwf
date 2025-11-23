# High-Availability Deployment Guide

Complete guide for deploying the Jackcwf AI Conversation Platform with high availability, load balancing, and auto-scaling.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Deployment Options](#deployment-options)
3. [Quick Start](#quick-start)
4. [Docker Compose Deployment](#docker-compose-deployment)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [Docker Swarm Deployment](#docker-swarm-deployment)
7. [Load Balancing Configuration](#load-balancing-configuration)
8. [Auto-Scaling](#auto-scaling)
9. [Monitoring and Health Checks](#monitoring-and-health-checks)
10. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

### High-Level Architecture

```
                                  ┌──────────────────┐
                                  │   Users/Clients  │
                                  └────────┬─────────┘
                                           │
                                           ▼
                              ┌────────────────────────┐
                              │   Load Balancer        │
                              │   (Traefik/NGINX)      │
                              └────────┬───────────────┘
                                       │
                 ┌─────────────────────┼─────────────────────┐
                 │                     │                     │
                 ▼                     ▼                     ▼
         ┌───────────────┐    ┌───────────────┐    ┌───────────────┐
         │  Backend Pod  │    │  Backend Pod  │    │  Backend Pod  │
         │  (Replica 1)  │    │  (Replica 2)  │    │  (Replica 3)  │
         │               │    │               │    │               │
         │  - Nginx      │    │  - Nginx      │    │  - Nginx      │
         │  - FastAPI    │    │  - FastAPI    │    │  - FastAPI    │
         │  - Supervisor │    │  - Supervisor │    │  - Supervisor │
         └───────┬───────┘    └───────┬───────┘    └───────┬───────┘
                 │                     │                     │
                 └─────────────────────┼─────────────────────┘
                                       │
                                       ▼
                          ┌────────────────────────┐
                          │   PostgreSQL Database   │
                          │   (Coolify External)    │
                          │   47.79.87.199:5432    │
                          └────────────────────────┘
```

### Key Components

1. **Load Balancer (Traefik/NGINX)**
   - Routes traffic to backend replicas
   - Health checking
   - Sticky sessions (optional)
   - SSL termination

2. **Backend Replicas (3+)**
   - Stateless FastAPI application
   - Each replica contains:
     - Nginx (port 80) - Serves frontend + proxies API
     - FastAPI (port 8000) - Backend API
     - Supervisor - Process management

3. **External Database**
   - Coolify-managed PostgreSQL + pgvector
   - Shared across all replicas
   - No state stored in containers

---

## Deployment Options

| Platform | Complexity | Scalability | Best For |
|----------|-----------|-------------|----------|
| **Docker Compose** | Low | Manual scaling | Development, small production |
| **Kubernetes** | High | Auto-scaling (HPA) | Large production, enterprise |
| **Docker Swarm** | Medium | Manual scaling | Mid-size production |

---

## Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+ (for Docker Compose deployment)
- kubectl 1.24+ (for Kubernetes deployment)
- 4GB+ RAM, 2+ CPU cores

### 1. Clone Repository

```bash
cd /mnt/d/工作区/云开发/working
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your database credentials and API keys
nano .env
```

Required variables:
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@47.79.87.199:5432/postgres
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
```

### 3. Build Docker Image

```bash
docker build -t jackcwf-backend:latest .
```

### 4. Deploy

Choose your platform:

```bash
# Docker Compose (recommended for quick start)
./deployment/scripts/deploy-ha.sh --platform docker-compose --replicas 3

# Kubernetes (for production)
./deployment/scripts/deploy-ha.sh --platform kubernetes --build

# Docker Swarm
./deployment/scripts/deploy-ha.sh --platform swarm --replicas 3
```

### 5. Verify Deployment

```bash
# Check health
./deployment/scripts/health-check.sh --platform docker-compose

# Access application
curl http://localhost/health
```

---

## Docker Compose Deployment

### Architecture

```
┌─────────────────────────────────────────────────────┐
│ Docker Compose Network (app-network)               │
│                                                     │
│  ┌──────────────┐                                  │
│  │   Traefik    │ :80, :443, :8080 (dashboard)    │
│  └──────┬───────┘                                  │
│         │                                           │
│  ┌──────┴───────────────────────┐                 │
│  │                               │                 │
│  ▼                               ▼                 │
│  web-1 (replica 1)    web-2 (replica 2)           │
│  web-3 (replica 3)                                │
└─────────────────────────────────────────────────────┘
```

### Step-by-Step Deployment

#### 1. Review Configuration

```bash
cat deployment/docker-compose.ha.yml
```

Key settings:
- **Replicas**: `deploy.replicas: 3`
- **Health check**: Every 30s
- **Resource limits**: 2 CPU, 2GB RAM per replica
- **Sticky sessions**: Enabled via Traefik labels

#### 2. Deploy Stack

```bash
cd /mnt/d/工作区/云开发/working

# Start with 3 replicas
docker-compose -f deployment/docker-compose.ha.yml up -d --scale web=3

# Or use deployment script
./deployment/scripts/deploy-ha.sh --platform docker-compose --replicas 3
```

#### 3. Verify Containers

```bash
docker-compose -f deployment/docker-compose.ha.yml ps

# Expected output:
# NAME                STATUS      PORTS
# jackcwf-traefik    running     0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
# working-web-1      running     80/tcp
# working-web-2      running     80/tcp
# working-web-3      running     80/tcp
```

#### 4. Check Traefik Dashboard

```bash
# Access dashboard at http://localhost:8080
# Default credentials: admin / change_me
```

#### 5. Test Load Balancing

```bash
# Make multiple requests and observe round-robin distribution
for i in {1..10}; do
  curl -s http://localhost/api/v1/health | jq .
  sleep 1
done
```

#### 6. Monitor Logs

```bash
# All services
docker-compose -f deployment/docker-compose.ha.yml logs -f

# Specific service
docker-compose -f deployment/docker-compose.ha.yml logs -f web

# Traefik only
docker-compose -f deployment/docker-compose.ha.yml logs -f traefik
```

### Scaling Replicas

```bash
# Scale up to 5 replicas
docker-compose -f deployment/docker-compose.ha.yml up -d --scale web=5

# Scale down to 2 replicas
docker-compose -f deployment/docker-compose.ha.yml up -d --scale web=2

# Check status
docker-compose -f deployment/docker-compose.ha.yml ps
```

### Updating Application

```bash
# 1. Build new image
docker build -t jackcwf-backend:latest .

# 2. Rolling update (zero downtime)
docker-compose -f deployment/docker-compose.ha.yml up -d --scale web=3 --no-recreate

# 3. Restart one replica at a time
for i in 1 2 3; do
  docker-compose -f deployment/docker-compose.ha.yml restart web
  sleep 30  # Wait for health check
done
```

### Stopping Deployment

```bash
# Stop all services
docker-compose -f deployment/docker-compose.ha.yml down

# Stop and remove volumes
docker-compose -f deployment/docker-compose.ha.yml down -v
```

---

## Kubernetes Deployment

### Architecture

```
┌─────────────────────────────────────────────────────┐
│ Kubernetes Cluster                                   │
│                                                     │
│  ┌──────────────┐                                  │
│  │   Ingress    │ (NGINX/Traefik)                  │
│  └──────┬───────┘                                  │
│         │                                           │
│  ┌──────▼───────────────┐                          │
│  │   Service (LoadBalancer/ClusterIP)              │
│  └──────┬───────────────┘                          │
│         │                                           │
│  ┌──────▼───────────────────────────────┐         │
│  │   Deployment (jackcwf-backend)       │         │
│  │   - Replicas: 3 (min), 10 (max)      │         │
│  │   - HPA: CPU/Memory based             │         │
│  │   - Rolling update strategy           │         │
│  │                                       │         │
│  │   ┌─────────┐  ┌─────────┐  ┌─────────┐      │
│  │   │ Pod 1   │  │ Pod 2   │  │ Pod 3   │      │
│  │   └─────────┘  └─────────┘  └─────────┘      │
│  └───────────────────────────────────────────┘   │
│                                                     │
│  ┌──────────────────────────────────┐             │
│  │ HPA (Auto-scaling)                │             │
│  │ - Target CPU: 70%                 │             │
│  │ - Target Memory: 80%              │             │
│  └──────────────────────────────────┘             │
└─────────────────────────────────────────────────────┘
```

### Prerequisites

```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Verify
kubectl version --client

# Configure kubeconfig (example for local cluster)
# For cloud providers (GKE, EKS, AKS), use their CLI tools
```

### Step-by-Step Deployment

#### 1. Review Kubernetes Manifests

```bash
cat deployment/kubernetes/all-in-one.yml
```

Key resources:
- **Namespace**: `jackcwf`
- **Deployment**: 3 replicas (min), 10 replicas (max)
- **Service**: ClusterIP with sticky sessions
- **HPA**: Auto-scales based on CPU/Memory
- **Ingress**: NGINX Ingress Controller
- **PodDisruptionBudget**: Ensures 2+ pods always available

#### 2. Update Secrets

```bash
# Encode secrets to base64
echo -n 'postgresql+asyncpg://user:pass@host:5432/db' | base64
echo -n 'your-openai-api-key' | base64

# Edit secret section in all-in-one.yml
nano deployment/kubernetes/all-in-one.yml
```

#### 3. Deploy to Kubernetes

```bash
# Apply all manifests
kubectl apply -f deployment/kubernetes/all-in-one.yml

# Or use deployment script
./deployment/scripts/deploy-ha.sh --platform kubernetes --build
```

#### 4. Verify Deployment

```bash
# Check namespace
kubectl get namespace jackcwf

# Check all resources
kubectl get all -n jackcwf

# Check pods
kubectl get pods -n jackcwf -l app=jackcwf-backend

# Check deployment status
kubectl rollout status deployment/jackcwf-backend -n jackcwf
```

#### 5. Check HPA Status

```bash
kubectl get hpa jackcwf-backend-hpa -n jackcwf

# Expected output:
# NAME                  REFERENCE                     TARGETS         MINPODS   MAXPODS   REPLICAS
# jackcwf-backend-hpa   Deployment/jackcwf-backend   15%/70%, 20%/80%   3         10        3
```

#### 6. Access Application

```bash
# Port forward for local testing
kubectl port-forward -n jackcwf svc/jackcwf-backend-service 8080:80

# Access at http://localhost:8080

# Or configure Ingress DNS
# Add to /etc/hosts: <INGRESS_IP> jackcwf.com
```

### Scaling

```bash
# Manual scaling
kubectl scale deployment/jackcwf-backend --replicas=5 -n jackcwf

# Check HPA metrics
kubectl top pods -n jackcwf
kubectl describe hpa jackcwf-backend-hpa -n jackcwf

# Test auto-scaling by generating load
kubectl run -i --tty load-generator --rm --image=busybox --restart=Never -- /bin/sh
# Inside container:
while true; do wget -q -O- http://jackcwf-backend-service.jackcwf.svc.cluster.local/api/v1/health; done
```

### Updating Application

```bash
# 1. Build and push new image
docker build -t your-registry/jackcwf-backend:v2 .
docker push your-registry/jackcwf-backend:v2

# 2. Update deployment
kubectl set image deployment/jackcwf-backend jackcwf-backend=your-registry/jackcwf-backend:v2 -n jackcwf

# 3. Monitor rollout
kubectl rollout status deployment/jackcwf-backend -n jackcwf

# 4. Rollback if needed
kubectl rollout undo deployment/jackcwf-backend -n jackcwf
```

### Monitoring

```bash
# View logs
kubectl logs -f -l app=jackcwf-backend -n jackcwf

# Describe pod for events
kubectl describe pod <pod-name> -n jackcwf

# Execute command in pod
kubectl exec -it <pod-name> -n jackcwf -- bash

# Check resource usage
kubectl top pods -n jackcwf
kubectl top nodes
```

### Cleanup

```bash
# Delete all resources
kubectl delete -f deployment/kubernetes/all-in-one.yml

# Or delete namespace (removes everything)
kubectl delete namespace jackcwf
```

---

## Load Balancing Configuration

### Session Affinity (Sticky Sessions)

**When to Use:**
- WebSocket connections
- User sessions with local state
- Long-running operations

**Docker Compose (Traefik):**

```yaml
labels:
  - "traefik.http.services.jackcwf-backend.loadbalancer.sticky.cookie=true"
  - "traefik.http.services.jackcwf-backend.loadbalancer.sticky.cookie.name=jackcwf_session"
```

**Kubernetes (Ingress):**

```yaml
annotations:
  nginx.ingress.kubernetes.io/affinity: "cookie"
  nginx.ingress.kubernetes.io/session-cookie-name: "jackcwf_session"
```

### Health Check Configuration

All platforms check `/health` endpoint:

```bash
curl http://localhost/health

# Response:
{
  "status": "healthy",
  "timestamp": "2025-11-21T10:00:00Z",
  "message": "Service is running"
}
```

### Load Balancing Algorithms

**Round Robin (default):**
- Distributes requests evenly
- Best for stateless applications

**Least Connections:**
- Routes to replica with fewest active connections
- Good for long-running requests

**IP Hash:**
- Routes based on client IP
- Provides session affinity without cookies

---

## Auto-Scaling

### Kubernetes HPA (Horizontal Pod Autoscaler)

#### CPU-based Scaling

```yaml
metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70  # Scale up if CPU > 70%
```

#### Memory-based Scaling

```yaml
metrics:
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80  # Scale up if memory > 80%
```

#### Custom Metrics (Prometheus)

```yaml
metrics:
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
```

### Testing Auto-Scaling

```bash
# 1. Monitor HPA
watch kubectl get hpa jackcwf-backend-hpa -n jackcwf

# 2. Generate load
kubectl run -i --tty load-generator --rm --image=busybox --restart=Never -- /bin/sh
while true; do wget -q -O- http://jackcwf-backend-service/api/v1/health; done

# 3. Observe scaling
# HPA will scale up replicas when CPU > 70%
# HPA will scale down after 5 minutes of low usage
```

### Docker Compose Manual Scaling

```bash
# Scale up during peak hours
docker-compose -f deployment/docker-compose.ha.yml up -d --scale web=5

# Scale down during off-peak
docker-compose -f deployment/docker-compose.ha.yml up -d --scale web=2
```

---

## Monitoring and Health Checks

### Health Check Script

```bash
# Check all replicas
./deployment/scripts/health-check.sh --platform docker-compose

# Continuous monitoring
./deployment/scripts/health-check.sh --platform docker-compose --continuous

# Verbose output
./deployment/scripts/health-check.sh --platform docker-compose --verbose
```

### Prometheus Metrics

Access metrics endpoint:

```bash
curl http://localhost/metrics

# Metrics include:
# - http_requests_total
# - http_request_duration_seconds
# - cache_hit_ratio
# - database_connection_pool_size
```

### Log Aggregation

**Docker Compose:**

```bash
# View logs from all replicas
docker-compose -f deployment/docker-compose.ha.yml logs -f web

# Filter by service
docker-compose -f deployment/docker-compose.ha.yml logs -f backend
```

**Kubernetes:**

```bash
# All pods
kubectl logs -f -l app=jackcwf-backend -n jackcwf

# Specific pod
kubectl logs -f <pod-name> -n jackcwf

# Previous container (if crashed)
kubectl logs --previous <pod-name> -n jackcwf
```

---

## Troubleshooting

### Common Issues

#### 1. Containers Not Starting

**Symptoms:**
- Containers exit immediately
- Health checks fail

**Diagnosis:**

```bash
# Docker Compose
docker-compose -f deployment/docker-compose.ha.yml ps
docker-compose -f deployment/docker-compose.ha.yml logs web

# Kubernetes
kubectl get pods -n jackcwf
kubectl describe pod <pod-name> -n jackcwf
kubectl logs <pod-name> -n jackcwf
```

**Solutions:**
- Check `.env` file configuration
- Verify database connectivity
- Review Docker image build logs

#### 2. Database Connection Errors

**Symptoms:**
- Backend API returns 500 errors
- Logs show database connection failures

**Diagnosis:**

```bash
# Test database connectivity
docker run --rm -it postgres:15 psql postgresql://user:pass@47.79.87.199:5432/postgres -c "SELECT 1"
```

**Solutions:**
- Verify `DATABASE_URL` in `.env`
- Check firewall rules (port 5432)
- Ensure Coolify PostgreSQL is running

#### 3. Load Balancer Not Distributing Traffic

**Symptoms:**
- All requests go to one replica
- Some replicas idle

**Diagnosis:**

```bash
# Check Traefik dashboard
# Access http://localhost:8080

# Check service health
./deployment/scripts/health-check.sh --platform docker-compose --verbose
```

**Solutions:**
- Verify health check endpoint `/health`
- Check Traefik labels in docker-compose.yml
- Review sticky session configuration

#### 4. Out of Memory Errors

**Symptoms:**
- Containers crash with OOMKilled
- Slow response times

**Diagnosis:**

```bash
# Docker Compose
docker stats

# Kubernetes
kubectl top pods -n jackcwf
```

**Solutions:**
- Increase memory limits in configuration
- Reduce `UVICORN_WORKERS` count
- Scale horizontally (more replicas) instead of vertically

#### 5. Slow Performance

**Symptoms:**
- High latency (> 1s)
- Low throughput

**Diagnosis:**

```bash
# Check resource usage
docker stats  # Docker Compose
kubectl top pods -n jackcwf  # Kubernetes

# Check database connection pool
curl http://localhost/api/v1/admin/cache/stats
```

**Solutions:**
- Increase connection pool size
- Enable semantic caching
- Scale up replicas
- Optimize database queries

---

## Performance Tuning

### Recommended Settings

#### Small Deployment (< 100 users)

```yaml
replicas: 2
resources:
  requests:
    cpu: 250m
    memory: 256Mi
  limits:
    cpu: 1000m
    memory: 1Gi
```

#### Medium Deployment (100-1000 users)

```yaml
replicas: 3
resources:
  requests:
    cpu: 500m
    memory: 512Mi
  limits:
    cpu: 2000m
    memory: 2Gi
```

#### Large Deployment (1000+ users)

```yaml
replicas: 5-10 (auto-scale)
resources:
  requests:
    cpu: 1000m
    memory: 1Gi
  limits:
    cpu: 4000m
    memory: 4Gi
```

### Connection Pool Tuning

Edit `.env`:

```bash
# Database connection pool (per replica)
DB_POOL_MIN_SIZE=5
DB_POOL_MAX_SIZE=20

# Uvicorn workers (per replica)
UVICORN_WORKERS=2  # Recommended: CPU cores - 1
```

---

## Security Best Practices

1. **Use Secrets Management**
   - Never commit `.env` to Git
   - Use Kubernetes Secrets or Docker Secrets
   - Rotate API keys regularly

2. **Enable HTTPS**
   - Configure SSL certificates
   - Use Let's Encrypt for free certs
   - Redirect HTTP to HTTPS

3. **Network Isolation**
   - Use private networks for internal services
   - Expose only necessary ports
   - Use firewall rules

4. **Resource Limits**
   - Set CPU/memory limits
   - Prevent resource exhaustion
   - Use namespaces for isolation

---

## Cost Optimization

### Right-Sizing Replicas

```bash
# Monitor actual usage
kubectl top pods -n jackcwf

# Adjust HPA settings
kubectl edit hpa jackcwf-backend-hpa -n jackcwf

# Reduce min replicas during off-peak
minReplicas: 2  # Instead of 3
```

### Spot Instances (Cloud)

For Kubernetes on cloud providers:

```yaml
# Use node affinity to prefer spot instances
affinity:
  nodeAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        preference:
          matchExpressions:
            - key: cloud.google.com/gke-preemptible
              operator: In
              values:
                - "true"
```

---

## Next Steps

1. **Setup Monitoring**
   - Deploy Prometheus + Grafana
   - Configure alerting rules
   - Create custom dashboards

2. **Implement CI/CD**
   - Automate builds
   - Auto-deploy on Git push
   - Rollback on failure

3. **Add Caching Layer**
   - Deploy Redis
   - Configure semantic caching
   - Cache API responses

4. **Setup Backup**
   - Database backups
   - Disaster recovery plan
   - Regular restore testing

---

## Support

For issues or questions:

1. Check logs: `./deployment/scripts/health-check.sh --verbose`
2. Review troubleshooting section
3. Open GitHub issue with logs

---

**Document Version:** 1.0
**Last Updated:** 2025-11-21
**Author:** Claude (DevOps Agent)

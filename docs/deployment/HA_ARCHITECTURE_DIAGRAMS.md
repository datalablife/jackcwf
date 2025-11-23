# High-Availability Architecture Diagrams

Visual reference for the HA deployment architecture.

---

## Table of Contents

1. [Current Single-Container Architecture](#current-single-container-architecture)
2. [Docker Compose HA Architecture](#docker-compose-ha-architecture)
3. [Kubernetes HA Architecture](#kubernetes-ha-architecture)
4. [Load Balancing Flow](#load-balancing-flow)
5. [Auto-Scaling Behavior](#auto-scaling-behavior-kubernetes)
6. [Monitoring Stack Architecture](#monitoring-stack-architecture)
7. [Request Flow Diagram](#request-flow-diagram)

---

## Current Single-Container Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User / Client                         │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP Request
                       ▼
        ┌──────────────────────────────────┐
        │     Docker Container             │
        │                                  │
        │  ┌────────────────────────────┐ │
        │  │     Supervisor             │ │
        │  │                            │ │
        │  │  ┌──────────────────────┐ │ │
        │  │  │ Nginx (Port 80)      │ │ │
        │  │  │  - Serves Frontend   │ │ │
        │  │  │  - Reverse Proxy     │ │ │
        │  │  └──────────┬───────────┘ │ │
        │  │             │              │ │
        │  │             ▼              │ │
        │  │  ┌──────────────────────┐ │ │
        │  │  │ FastAPI (Port 8000)  │ │ │
        │  │  │  - 2 Uvicorn Workers │ │ │
        │  │  │  - Backend API       │ │ │
        │  │  └──────────┬───────────┘ │ │
        │  │             │              │ │
        │  │  ┌──────────▼───────────┐ │ │
        │  │  │ Health Monitor       │ │ │
        │  │  │  - Python Script     │ │ │
        │  │  └──────────────────────┘ │ │
        │  └────────────────────────────┘ │
        └──────────────────┬───────────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │   PostgreSQL DB      │
                │   (Coolify External) │
                │   47.79.87.199:5432  │
                └──────────────────────┘

Limitations:
❌ Single point of failure
❌ No load balancing
❌ Limited capacity
❌ Manual scaling only
❌ Downtime during updates
```

---

## Docker Compose HA Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Users / Clients                       │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP/HTTPS
                       ▼
        ┌──────────────────────────────────┐
        │   Traefik Load Balancer          │
        │   (Port 80, 443, 8080)          │
        │                                  │
        │   Features:                      │
        │   ✓ Auto service discovery       │
        │   ✓ Health checks                │
        │   ✓ Sticky sessions              │
        │   ✓ SSL termination              │
        │   ✓ Metrics (Prometheus)         │
        └──────────┬───────────────────────┘
                   │
   ┌───────────────┼───────────────┐
   │               │               │
   ▼               ▼               ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Web-1    │  │ Web-2    │  │ Web-3    │
│ Replica  │  │ Replica  │  │ Replica  │
│          │  │          │  │          │
│ Nginx    │  │ Nginx    │  │ Nginx    │
│   +      │  │   +      │  │   +      │
│ FastAPI  │  │ FastAPI  │  │ FastAPI  │
│   +      │  │   +      │  │   +      │
│ Monitor  │  │ Monitor  │  │ Monitor  │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │
     └─────────────┼─────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │   PostgreSQL DB      │
        │   (Coolify External) │
        │   47.79.87.199:5432  │
        └──────────────────────┘

┌─────────────────────────────────────┐
│  Shared Volumes                     │
├─────────────────────────────────────┤
│  - app-logs:/var/log/app           │
│  - supervisor-logs:/var/log/super  │
│  - traefik-logs:/var/log/traefik   │
└─────────────────────────────────────┘

Benefits:
✅ No single point of failure
✅ Automatic load balancing
✅ Easy horizontal scaling
✅ Zero-downtime updates
✅ Health-based routing
✅ 3x capacity (or more)
```

---

## Kubernetes HA Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Internet                             │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────┐
        │     NGINX Ingress Controller      │
        │   (nginx.ingress.kubernetes.io)   │
        │                                   │
        │   Features:                       │
        │   ✓ SSL/TLS termination          │
        │   ✓ Rate limiting                │
        │   ✓ CORS handling                │
        │   ✓ Session affinity             │
        └──────────┬────────────────────────┘
                   │
                   ▼
        ┌──────────────────────────────────┐
        │   Service (ClusterIP)             │
        │   jackcwf-backend-service         │
        │                                   │
        │   Session Affinity: ClientIP      │
        │   Timeout: 3600s                  │
        └──────────┬────────────────────────┘
                   │
   ┌───────────────┼───────────────┐
   │               │               │
   ▼               ▼               ▼
┌──────────┐  ┌──────────┐  ┌──────────┐     ┌──────────┐
│ Pod 1    │  │ Pod 2    │  │ Pod 3    │ ... │ Pod 10   │
│          │  │          │  │          │     │ (HPA)    │
│ Init:    │  │ Init:    │  │ Init:    │     │          │
│ DB Mig   │  │ DB Mig   │  │ DB Mig   │     │          │
│          │  │          │  │          │     │          │
│ Main:    │  │ Main:    │  │ Main:    │     │ Main:    │
│ Backend  │  │ Backend  │  │ Backend  │     │ Backend  │
│ (Port80) │  │ (Port80) │  │ (Port80) │     │ (Port80) │
│          │  │          │  │          │     │          │
│ Probes:  │  │ Probes:  │  │ Probes:  │     │ Probes:  │
│ ✓ Live   │  │ ✓ Live   │  │ ✓ Live   │     │ ✓ Live   │
│ ✓ Ready  │  │ ✓ Ready  │  │ ✓ Ready  │     │ ✓ Ready  │
│ ✓ Start  │  │ ✓ Start  │  │ ✓ Start  │     │ ✓ Start  │
└────┬─────┘  └────┬─────┘  └────┬─────┘     └────┬─────┘
     │             │             │                 │
     └─────────────┼─────────────┴─────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │   PostgreSQL DB      │
        │   (External)         │
        │   47.79.87.199:5432  │
        └──────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Kubernetes Resources                                    │
├─────────────────────────────────────────────────────────┤
│  Namespace: jackcwf                                     │
│  Deployment: jackcwf-backend (replicas: 3)             │
│  HPA: jackcwf-backend-hpa (min: 3, max: 10)           │
│  Service: jackcwf-backend-service (ClusterIP)          │
│  Ingress: jackcwf-backend-ingress                      │
│  PodDisruptionBudget: min 2 pods available             │
│  ServiceMonitor: Prometheus scraping                    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  HPA Behavior                                            │
├─────────────────────────────────────────────────────────┤
│  Scale Up:                                              │
│    - Immediate (0s stabilization)                       │
│    - 100% increase OR +4 pods max                       │
│    - Every 15s                                          │
│                                                         │
│  Scale Down:                                            │
│    - 5 min stabilization                                │
│    - 50% decrease OR -2 pods max                        │
│    - Every 60s                                          │
└─────────────────────────────────────────────────────────┘

Benefits:
✅ Auto-scaling (3-10 pods)
✅ Self-healing
✅ Rolling updates
✅ Resource quotas
✅ Pod anti-affinity
✅ Graceful shutdown
✅ Production-grade
```

---

## Load Balancing Flow

### Round-Robin Algorithm (Default)

```
Request 1 → Traefik → Web-1 ✓
Request 2 → Traefik → Web-2 ✓
Request 3 → Traefik → Web-3 ✓
Request 4 → Traefik → Web-1 ✓ (cycle repeats)
Request 5 → Traefik → Web-2 ✓
Request 6 → Traefik → Web-3 ✓

Distribution: 33% / 33% / 34%
```

### Sticky Sessions (Session Affinity)

```
User A (Cookie: session_123)
  Request 1 → Traefik → Web-2 ✓ (initial)
  Request 2 → Traefik → Web-2 ✓ (sticky)
  Request 3 → Traefik → Web-2 ✓ (sticky)

User B (Cookie: session_456)
  Request 1 → Traefik → Web-1 ✓ (initial)
  Request 2 → Traefik → Web-1 ✓ (sticky)
  Request 3 → Traefik → Web-1 ✓ (sticky)

User C (Cookie: session_789)
  Request 1 → Traefik → Web-3 ✓ (initial)
  Request 2 → Traefik → Web-3 ✓ (sticky)

Same user → Same backend (until session expires)
```

### Health Check Behavior

```
Time: 0s
  Web-1: Healthy ✓
  Web-2: Healthy ✓
  Web-3: Healthy ✓
  Traffic: [Web-1, Web-2, Web-3]

Time: 30s (Health check)
  Web-1: Healthy ✓
  Web-2: UNHEALTHY ✗ (health endpoint returns 500)
  Web-3: Healthy ✓
  Traffic: [Web-1, Web-3] (Web-2 removed from pool)

Time: 60s (Health check)
  Web-1: Healthy ✓
  Web-2: Healthy ✓ (recovered)
  Web-3: Healthy ✓
  Traffic: [Web-1, Web-2, Web-3] (Web-2 re-added)

Automatic failover and recovery
```

---

## Auto-Scaling Behavior (Kubernetes)

### CPU-Based Scaling

```
Timeline:

09:00 - Normal load (30% CPU)
        [Pod-1] [Pod-2] [Pod-3]
        HPA: 3 replicas (min)

10:00 - Traffic spike (80% CPU) ⚠️
        [Pod-1] [Pod-2] [Pod-3]
        HPA: Scaling up...

10:00:15 - Scaled up (60% CPU)
           [Pod-1] [Pod-2] [Pod-3] [Pod-4] [Pod-5] [Pod-6]
           HPA: 6 replicas

11:00 - Traffic normalizes (40% CPU)
        [Pod-1] [Pod-2] [Pod-3] [Pod-4] [Pod-5] [Pod-6]
        HPA: Waiting 5 min stabilization...

11:05 - Scale down (40% CPU)
        [Pod-1] [Pod-2] [Pod-3] [Pod-4]
        HPA: 4 replicas

11:10 - Continue scale down (35% CPU)
        [Pod-1] [Pod-2] [Pod-3]
        HPA: 3 replicas (min reached)
```

### Memory-Based Scaling

```
Current Memory Usage:

Pod-1: 1.6 GB / 2 GB = 80% ⚠️
Pod-2: 1.5 GB / 2 GB = 75%
Pod-3: 1.7 GB / 2 GB = 85% ⚠️

Average: 80% (threshold: 80%)

HPA Decision: SCALE UP
Action: Add 3 pods (100% increase)

After Scaling:

Pod-1: 800 MB / 2 GB = 40% ✓
Pod-2: 750 MB / 2 GB = 38% ✓
Pod-3: 850 MB / 2 GB = 43% ✓
Pod-4: 800 MB / 2 GB = 40% ✓
Pod-5: 750 MB / 2 GB = 38% ✓
Pod-6: 850 MB / 2 GB = 43% ✓

Average: 40% ✓
```

---

## Monitoring Stack Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Monitoring Stack                       │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
┌────────────────┐           ┌────────────────┐
│   Prometheus   │           │    Grafana     │
│   (Port 9090)  │◄─────────│  (Port 3001)   │
│                │  Query    │                │
│  - Scrapes     │           │  - Dashboards  │
│  - Stores      │           │  - Alerts      │
│  - Alerts      │           │  - Visualization│
└────┬───────────┘           └────────────────┘
     │
     │ Scrape (every 15-30s)
     │
     ├──────────────────────┬──────────────────┐
     │                      │                  │
     ▼                      ▼                  ▼
┌──────────┐        ┌──────────┐      ┌──────────┐
│ Backend  │        │ Node     │      │ cAdvisor │
│ Replicas │        │ Exporter │      │ (Port    │
│ (Port80) │        │ (Port    │      │ 8080)    │
│          │        │ 9100)    │      │          │
│ /metrics │        │          │      │ Container│
│ endpoint │        │ Host     │      │ Metrics  │
└──────────┘        │ Metrics  │      └──────────┘
                    └──────────┘

     │
     │ Alert Rules
     ▼
┌────────────────┐
│ AlertManager   │
│ (Port 9093)    │
│                │
│ Routes to:     │
│  - Slack       │
│  - Email       │
│  - PagerDuty   │
│  - Webhook     │
└────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Metrics Flow                                            │
├─────────────────────────────────────────────────────────┤
│  1. Application exposes /metrics (Prometheus format)     │
│  2. Prometheus scrapes metrics every 30s                 │
│  3. Prometheus stores time-series data (15 days)         │
│  4. Prometheus evaluates alert rules every 30s           │
│  5. Grafana queries Prometheus for dashboards            │
│  6. AlertManager routes alerts to notification channels  │
└─────────────────────────────────────────────────────────┘
```

---

## Request Flow Diagram

### Successful Request Flow

```
1. User Request
   │
   ▼
   http://jackcwf.com/api/v1/chat
   │
   ▼
2. DNS Resolution
   │
   ▼
   Load Balancer IP
   │
   ▼
3. Traefik/Ingress
   │ - Check health
   │ - Check session cookie
   │ - Select backend
   ▼
4. Backend Replica (e.g., Web-2)
   │
   ▼
5. Nginx (Port 80)
   │ - Check path
   │ - Proxy to FastAPI
   ▼
6. FastAPI (Port 8000)
   │ - Authentication
   │ - Rate limiting
   │ - Business logic
   ▼
7. Database Query
   │
   ▼
   PostgreSQL (47.79.87.199:5432)
   │
   ▼
8. Response
   │
   ▼
   FastAPI → Nginx → Traefik → User
   │
   ▼
9. Metrics Collection
   │
   ▼
   Prometheus scrapes /metrics

Total Time: ~200ms (P50)
```

### Failure Recovery Flow

```
Scenario: Web-2 crashes during request

1. User Request → Traefik → Web-2
   │
   ▼
2. Web-2 Health Check FAILS (timeout)
   │
   ▼
3. Traefik removes Web-2 from pool
   │ - Marks as unhealthy
   │ - Stops routing traffic
   ▼
4. Retry Request → Traefik → Web-1
   │ (automatic failover)
   ▼
5. Web-1 processes request successfully
   │
   ▼
6. Response to User (200 OK)
   │ - User doesn't notice failure
   │ - Seamless failover
   ▼
7. Kubernetes/Docker restarts Web-2
   │ (self-healing)
   ▼
8. Web-2 Health Check PASSES
   │
   ▼
9. Traefik re-adds Web-2 to pool
   │
   ▼
10. Normal operation resumed

Downtime for user: 0 seconds
Downtime for Web-2: ~30-60 seconds (self-healing)
```

---

## Deployment Topology

### Development Environment

```
┌────────────────────────────────────┐
│ Developer Laptop                   │
│                                    │
│  Docker Compose                    │
│  ├─ Traefik (1 instance)          │
│  ├─ Backend (2 replicas)          │
│  └─ PostgreSQL (local)            │
│                                    │
│  Resources: 4 CPU, 8 GB RAM       │
└────────────────────────────────────┘

Purpose: Local development and testing
```

### Staging Environment

```
┌────────────────────────────────────┐
│ Cloud VM (e.g., AWS EC2)          │
│                                    │
│  Docker Compose                    │
│  ├─ Traefik (1 instance)          │
│  ├─ Backend (3 replicas)          │
│  └─ PostgreSQL (RDS)              │
│                                    │
│  Resources: 8 CPU, 16 GB RAM      │
└────────────────────────────────────┘

Purpose: Pre-production testing
```

### Production Environment (Docker Compose)

```
┌────────────────────────────────────┐
│ Cloud VM (e.g., AWS EC2, GCP)     │
│                                    │
│  Docker Compose                    │
│  ├─ Traefik (1 instance)          │
│  └─ Backend (3-5 replicas)        │
│                                    │
│  Resources: 16 CPU, 32 GB RAM     │
└────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│ Managed PostgreSQL                 │
│ (AWS RDS / GCP Cloud SQL)         │
└────────────────────────────────────┘

Purpose: Small to medium production
```

### Production Environment (Kubernetes)

```
┌─────────────────────────────────────────────────────────┐
│ Kubernetes Cluster (e.g., GKE, EKS, AKS)              │
│                                                         │
│  Control Plane                                          │
│  ├─ API Server                                         │
│  ├─ Scheduler                                          │
│  └─ Controller Manager                                 │
│                                                         │
│  Worker Nodes (3+)                                     │
│  ├─ Node 1 (8 CPU, 16 GB)                            │
│  │   ├─ Backend Pod 1                                │
│  │   └─ Backend Pod 2                                │
│  │                                                     │
│  ├─ Node 2 (8 CPU, 16 GB)                            │
│  │   ├─ Backend Pod 3                                │
│  │   └─ Backend Pod 4                                │
│  │                                                     │
│  └─ Node 3 (8 CPU, 16 GB)                            │
│      ├─ Backend Pod 5                                │
│      └─ Backend Pod 6 (+ up to 4 more via HPA)      │
│                                                         │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Managed PostgreSQL                  │
│ (AWS RDS / GCP Cloud SQL)          │
└─────────────────────────────────────┘

Purpose: Large-scale production with auto-scaling
```

---

## Summary

This architecture provides:

1. **Redundancy:** Multiple replicas eliminate single point of failure
2. **Scalability:** Horizontal scaling (manual or automatic)
3. **Reliability:** Health checks and automatic failover
4. **Observability:** Comprehensive monitoring and alerting
5. **Flexibility:** Multiple deployment options for any scale

Choose the architecture that best fits your requirements:
- **Docker Compose:** Simple, fast, good for dev and small production
- **Kubernetes:** Complex, powerful, best for large production

---

**Document Version:** 1.0
**Last Updated:** 2025-11-21

# Coolify Deployment Guide

Comprehensive guide for deploying the Data Management System (FastAPI + React) on Coolify.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Coolify Setup](#coolify-setup)
5. [Application Configuration](#application-configuration)
6. [Deployment Process](#deployment-process)
7. [Environment Management](#environment-management)
8. [Monitoring and Maintenance](#monitoring-and-maintenance)
9. [Troubleshooting](#troubleshooting)

---

## Overview

This application is deployed as a containerized application on Coolify, a self-hosted deployment platform. The deployment uses:

- **Multi-stage Docker build** for optimized image size
- **FastAPI** backend running in production mode with Uvicorn
- **React** frontend served as static assets
- **PostgreSQL** database (managed separately on pgvctor.jackcwf.com)
- **Graceful shutdown** handling for zero-downtime deployments

### Key Architecture Decisions

1. **Single Container Deployment**: Both backend and frontend run in a single container
   - Frontend assets are pre-built and served by the backend
   - Simplifies Coolify configuration and resource management
   - Single health check endpoint

2. **Optimal Worker Calculation**: Workers automatically calculated based on CPU cores
   - Formula: `workers = (cpu_cores * 2) + 1`
   - Capped between 2 (minimum) and 8 (maximum)
   - Can be overridden via `BACKEND_WORKERS` environment variable

3. **Database Migrations**: Automatically run on container startup
   - Ensures schema consistency across deployments
   - No manual migration step required

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Coolify Platform                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          Docker Container (Application)                  │  │
│  │                                                            │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  Uvicorn Server (FastAPI Backend)                 │  │  │
│  │  │  - Port 8000                                       │  │  │
│  │  │  - Multiple Workers (auto-calculated)            │  │  │
│  │  │  - /health endpoint for health checks            │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │                                                            │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  Static Asset Server (React Frontend)             │  │  │
│  │  │  - Built with Vite                               │  │  │
│  │  │  - Served from backend `/` endpoint             │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │                                                            │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  Entrypoint Script (/app/entrypoint.sh)           │  │  │
│  │  │  - PID 1 process in container                     │  │  │
│  │  │  - Handles SIGTERM for graceful shutdown         │  │  │
│  │  │  - Runs database migrations                       │  │  │
│  │  │  - Environment validation                         │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  External Dependencies:                                          │
│  - PostgreSQL Database (pgvctor.jackcwf.com:5432)              │
│  - Environment Variables (from Coolify)                         │
│  - Domain/SSL (handled by Coolify)                             │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### Coolify Requirements

- Coolify instance running (v3.x or later recommended)
- Docker runtime available on Coolify host
- PostgreSQL database accessible (external or managed)
- 512MB minimum RAM (recommended 1GB+)
- 2GB minimum disk space

### Git Repository

- Application code in GitHub repository
- Public or private access configured in Coolify

### Database

- PostgreSQL database already created
- Database user with appropriate permissions
- Connection string in format: `postgresql+asyncpg://user:password@host:port/database`

---

## Coolify Setup

### Step 1: Create New Project

1. Log in to Coolify dashboard
2. Click "Create New Project"
3. Set project name: "Data Management System"
4. Set project description: "FastAPI + React application"

### Step 2: Add Application

1. In project dashboard, click "Create New Service"
2. Select "GitHub" as source
3. Authenticate with GitHub
4. Select repository: `datalablife/jackcwf`

### Step 3: Configure Build Settings

**Build Configuration:**
- Dockerfile location: `./Dockerfile.prod`
- Build context: Root directory (`.`)

**Build Arguments:**
```
PYTHON_VERSION=3.12-slim
NODE_VERSION=20-alpine
```

### Step 4: Configure Runtime

**Ports:**
- Container port: `8000`
- Exposed port: Same or custom (Coolify will handle)

**Health Check:**
- Path: `/health`
- Port: `8000`
- Interval: `30s`
- Timeout: `10s`
- Success threshold: `1`
- Failure threshold: `3`

**Resource Limits:**
- Memory: 1GB (recommended)
- CPU: 1 core (or more if available)

---

## Application Configuration

### Environment Variables

Set these in Coolify's environment variable management:

#### Required Variables

```env
# Database Configuration
DATABASE_URL=postgresql+asyncpg://user:password@pgvctor.jackcwf.com:5432/data_management_prod

# Application Configuration
ENVIRONMENT=production
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1

# Backend Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
BACKEND_WORKERS=auto  # or specific number (2-8)

# Logging Configuration
LOG_LEVEL=WARNING  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

#### Optional Variables

```env
# Database Connection Pool
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_POOL_RECYCLE=3600

# CORS Configuration
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Security
SECURE_COOKIE=true
CORS_STRICT=true

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

### Domain Configuration

1. In Coolify project settings, add domain binding
2. Configure SSL (Coolify can auto-generate with Let's Encrypt)
3. Point DNS to Coolify IP address

**DNS Entry:**
```
yourdomain.com  A  <COOLIFY_IP_ADDRESS>
```

---

## Deployment Process

### Initial Deployment

1. **Coolify builds the image:**
   - Clones repository
   - Executes `Dockerfile.prod`
   - Multi-stage build process (optimized for production)
   - Frontend: Builds React app with Vite
   - Backend: Installs Python dependencies
   - Final image: ~500-700MB (optimized)

2. **Container startup:**
   - Entrypoint script runs as PID 1
   - Validates environment variables
   - Checks database connectivity (10 retries with exponential backoff)
   - Executes database migrations (alembic upgrade head)
   - Starts Uvicorn with optimal worker count
   - Health check begins (after 60-second grace period)

3. **Verification:**
   - Wait for health check to pass
   - Check application logs
   - Verify API endpoints are responding
   - Test frontend is accessible

### Zero-Downtime Deployments

When deploying updates:

1. Coolify creates a new container with updated code
2. Old container receives SIGTERM signal (graceful shutdown)
3. New container starts health checks
4. Once new container is healthy, traffic switches
5. Old container terminates after cleanup (30-second timeout)

**Key: No manual steps required - Coolify handles orchestration**

### Manual Deployment Trigger

To redeploy without code changes:
1. In Coolify, click "Redeploy"
2. Choose "Use existing image" or "Rebuild"
3. Coolify handles the rest

---

## Environment Management

### Secrets and Sensitive Data

**Important:** Never commit secrets to GitHub!

In Coolify, use the "Secrets" feature for:
- `DATABASE_URL`
- API keys
- Authentication tokens
- SSL certificates

Coolify will inject these as environment variables at runtime.

### Configuration Files

The application reads environment variables from:
1. Coolify injected variables (highest priority)
2. `scripts/config/prod.env` file (fallback, included in image)

**Note:** Coolify variables override `prod.env` values.

### Updating Configuration

1. In Coolify dashboard, edit environment variables
2. Trigger redeployment
3. Changes take effect immediately (with container restart)

---

## Monitoring and Maintenance

### Log Viewing

**Real-time logs:**
```bash
# In Coolify dashboard
- Click application
- Select "Logs" tab
- View live container output
```

**Log Levels:**
- `DEBUG`: Detailed development information
- `INFO`: General informational messages
- `WARNING`: Warning messages (recommended for production)
- `ERROR`: Error messages
- `CRITICAL`: Critical failures

### Performance Monitoring

**Container Metrics (Coolify provides):**
- CPU usage
- Memory usage
- Network I/O
- Container uptime

**Application Health:**
- `/health` endpoint returns current health status
- Health check runs every 30 seconds
- Container automatically restarted if 3 consecutive checks fail

### Database Maintenance

**Backups:**
1. Configure external database backups (pgvctor.jackcwf.com)
2. Use PostgreSQL backup tools (pg_dump)
3. Schedule automatic backups

**Connection Pool:**
- Configured for production use (pool_size=20, max_overflow=40)
- Automatic connection recycling every 3600 seconds
- Failover to new connection if stale

### Storage and Cleanup

**Container Storage:**
- Application files: ~600MB (in image)
- Temporary files: Cleaned up on exit
- Logs: Streamed to stdout (no disk usage)

**Keep Clean:**
- Don't store files in container
- Use external storage (S3, etc.) for user uploads
- Database for persistent data

---

## Troubleshooting

### Container Won't Start

**Check Startup Logs:**
```
1. Go to Coolify dashboard
2. Click application → Logs
3. Look for error messages in first 30 seconds
```

**Common Issues:**

1. **Database Connection Failed**
   - Error: `Failed to connect to database after 10 attempts`
   - Check: `DATABASE_URL` is correct
   - Check: Database server is running and accessible
   - Check: Firewall allows connections
   - Solution: Fix `DATABASE_URL` and redeploy

2. **Missing Environment Variables**
   - Error: `Required environment variable not set: DATABASE_URL`
   - Check: All required variables are set in Coolify
   - Solution: Add missing variables and redeploy

3. **Python Dependency Issues**
   - Error: `Failed to install Poetry dependencies`
   - Check: `pyproject.toml` in `backend/` directory
   - Check: All dependencies are compatible
   - Solution: Fix `pyproject.toml` and push new code

4. **Build Fails**
   - Error: `Docker build failed`
   - Check: `Dockerfile.prod` syntax
   - Check: All source files are present
   - Check: Disk space on Coolify host
   - Solution: Check build logs and fix issues

### Health Check Failing

**Check Logs:**
```
Logs show: "HEALTHCHECK [unhealthy]"
```

**Diagnose:**
1. Application is running but `/health` endpoint not responding
2. Database connection lost
3. Application crashed after startup

**Solutions:**
1. Check application logs for errors
2. Verify database connectivity
3. Increase health check timeout (if needed)
4. Review recent code changes

### High Memory/CPU Usage

**Causes:**
- Too many Uvicorn workers for available resources
- Memory leak in application code
- Database queries too heavy
- Slow clients holding connections

**Solutions:**
```bash
# Reduce worker count
BACKEND_WORKERS=2  # Instead of auto-calculated

# Monitor connection pool
# Check DB_POOL_SIZE (shouldn't exceed available connections)

# Review application logs for slow queries
LOG_LEVEL=INFO  # Enable debug logging temporarily
```

### Database Migrations Failing

**Error:** `Database migrations failed`

**Check:**
1. Migration scripts in `backend/migrations/` directory
2. Database connectivity and permissions
3. Migration compatibility with current schema

**Solution:**
```bash
# Connect to database directly
psql postgresql://user:password@pgvctor.jackcwf.com:5432/data_management_prod

# Manually check migration status
# If needed, manually run/fix migrations
```

### Graceful Shutdown Issues

**Container not shutting down cleanly (timeout after 30s):**

1. Application not handling SIGTERM properly
2. Database connections not closing
3. Background tasks not completing

**Check:**
- Look for SIGTERM handling in application code
- Ensure database connections have timeout
- Review logs for "shutdown" messages

---

## Manual Container Management

### SSH into Coolify Host (if needed)

```bash
ssh user@coolify-host

# View running containers
docker ps | grep data-management

# View container logs
docker logs <container-id>

# Inspect container
docker inspect <container-id>

# Stop/restart container
docker stop <container-id>
docker restart <container-id>
```

### Local Testing Before Deployment

**Build image locally:**
```bash
docker build -f Dockerfile.prod -t data-management:test .
```

**Run locally:**
```bash
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql+asyncpg://user:pass@db:5432/test" \
  -e BACKEND_WORKERS=2 \
  data-management:test
```

---

## Best Practices

### Deployment Strategy

1. **Test Locally First**
   - Build and test Docker image locally
   - Verify environment variables
   - Test database migrations

2. **Staged Rollout**
   - Deploy to test environment first
   - Verify functionality
   - Then deploy to production

3. **Backup Before Updates**
   - Backup database before deployment
   - Keep previous image available for rollback
   - Document changes

4. **Monitor After Deployment**
   - Watch logs for first 5 minutes
   - Verify health checks passing
   - Check application functionality

### Security Best Practices

1. **Secrets Management**
   - Use Coolify Secrets feature
   - Never commit secrets to GitHub
   - Rotate secrets periodically

2. **Database Security**
   - Use strong passwords
   - Limit database user permissions
   - Use SSL/TLS for connections

3. **Network Security**
   - Enable HTTPS/SSL
   - Configure CORS appropriately
   - Use rate limiting

4. **Application Updates**
   - Keep dependencies updated
   - Monitor security advisories
   - Test before production deployment

---

## Support and Resources

- **Coolify Documentation:** https://coolify.io/docs
- **FastAPI Documentation:** https://fastapi.tiangolo.com
- **PostgreSQL Documentation:** https://www.postgresql.org/docs
- **Docker Documentation:** https://docs.docker.com

For issues specific to this application:
- Check application logs
- Review `UNIFIED_STARTUP_SOLUTION_ANALYSIS.md` for architecture
- Check GitHub issues repository

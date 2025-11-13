# Production Dockerfile for FastAPI Backend + React Frontend
# Optimized for containerized deployment on Coolify with proper signal handling
# Multi-stage build for minimal final image size

# =============================================================================
# Build Arguments
# =============================================================================
ARG PYTHON_VERSION=3.12-slim
ARG NODE_VERSION=20-alpine

# =============================================================================
# Stage 1: Frontend Build
# Builds React application with Vite
# =============================================================================
FROM node:${NODE_VERSION} AS frontend-builder

LABEL stage=frontend-build

WORKDIR /build/frontend

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci --prefer-offline --no-audit

# Copy source code
COPY frontend .

# Build React application
RUN npm run build

# =============================================================================
# Stage 2: Backend Dependencies
# Installs Python dependencies using Poetry
# =============================================================================
FROM python:${PYTHON_VERSION} AS backend-builder

LABEL stage=backend-build

WORKDIR /build/backend

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy dependency files
COPY backend/pyproject.toml backend/poetry.lock ./

# Install Python dependencies
RUN poetry config virtualenvs.in-project true && \
    poetry install --no-dev --no-interaction --no-ansi

# =============================================================================
# Stage 3: Final Production Image
# Combines frontend built assets and backend runtime
# =============================================================================
FROM python:${PYTHON_VERSION}

LABEL maintainer="Cloud Dev Team"
LABEL description="Production container for FastAPI + React application"

# Set working directory
WORKDIR /app

# ============================================================================
# System Setup and Environment
# ============================================================================

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Python environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app:$PYTHONPATH \
    PATH="/app/.venv/bin:$PATH"

# Application environment
ENV APP_ENV=production \
    ENVIRONMENT=production

# ============================================================================
# Copy Application Files
# ============================================================================

# Copy backend virtual environment from builder
COPY --from=backend-builder /build/backend/.venv /app/.venv

# Copy backend source code
COPY backend/src /app/backend/src
COPY backend/migrations /app/backend/migrations
COPY backend/alembic.ini /app/backend/
COPY backend/pyproject.toml backend/poetry.lock /app/backend/

# Copy frontend built assets
COPY --from=frontend-builder /build/frontend/dist /app/frontend/dist

# Copy scripts directory
COPY scripts /app/scripts

# Copy container entrypoint and helper scripts
COPY scripts/container/entrypoint.sh /app/entrypoint.sh
COPY scripts/lib /app/scripts/lib
COPY scripts/config /app/scripts/config

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# ============================================================================
# Health Check Configuration
# ============================================================================

# Health check for container orchestration systems
# - interval: Check every 30 seconds
# - timeout: Wait 10 seconds for response
# - start-period: Wait 60 seconds before first check (allows migration time)
# - retries: Fail after 3 consecutive failures
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# ============================================================================
# Port Exposure
# ============================================================================

# Backend API port
EXPOSE 8000

# ============================================================================
# Container Runtime Configuration
# ============================================================================

# Use entrypoint script for proper initialization and signal handling
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command (can be overridden)
CMD ["start"]

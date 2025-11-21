# Multi-stage Docker build
# Supports Supervisor process management with integrated frontend/backend services

# ============================================
# Stage 1: Build Backend Dependencies
# ============================================
FROM python:3.12-slim AS backend-builder

WORKDIR /build

# Install build tools
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files AND source code for editable install
COPY pyproject.toml pyproject.toml
COPY README.md README.md
COPY src/ src/

# Install dependencies using uv (faster than pip)
RUN pip install uv && \
    uv pip install "." --system

# ============================================
# Stage 2: Build Frontend
# ============================================
FROM node:20-slim AS frontend-builder

WORKDIR /build

# Copy frontend files
COPY frontend/package*.json ./
RUN npm ci --legacy-peer-deps

# Copy source code
COPY frontend/ ./

# Build frontend (Vite outputs to /build/dist)
RUN npm run build

# ============================================
# Stage 3: Final Production Image
# ============================================
FROM python:3.12-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    nodejs npm \
    supervisor \
    nginx \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ============================================
# Copy Backend Dependencies and Code
# ============================================
COPY --from=backend-builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copy backend source code
COPY src/ ./src/
COPY pyproject.toml .

# ============================================
# Copy Frontend Build Result
# ============================================
COPY --from=frontend-builder /build/dist /usr/share/nginx/html
COPY frontend/package*.json frontend/

# Install serve (for production frontend)
RUN npm install -g serve

# ============================================
# Configure Supervisor
# ============================================
RUN mkdir -p /etc/supervisor/conf.d /var/log/supervisor /var/log/app

COPY docker/supervisord.conf /etc/supervisor/supervisord.conf

# ============================================
# Configure Nginx (Frontend Reverse Proxy)
# ============================================
COPY docker/nginx.conf /etc/nginx/nginx.conf

# ============================================
# Health Monitoring Scripts
# ============================================
RUN mkdir -p /app/scripts/monitor
COPY scripts/monitor/ /app/scripts/monitor/

# Make Python scripts executable (only .py files exist)
RUN chmod +x /app/scripts/monitor/*.py 2>/dev/null || true

# ============================================
# Startup Script
# ============================================
COPY docker/docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# ============================================
# Log Directories and Permissions
# ============================================
RUN mkdir -p /var/log/app /var/log/supervisor /app/logs && \
    chmod 777 /var/log/app /var/log/supervisor /app/logs

# ============================================
# Environment Variables
# ============================================
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    ENVIRONMENT=production \
    LOG_LEVEL=info

# ============================================
# Health Check Configuration
# ============================================
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health && \
        curl -f http://localhost:3000 || exit 1

# ============================================
# Expose Ports
# ============================================
EXPOSE 3000 8000

# ============================================
# Startup
# ============================================
ENTRYPOINT ["/entrypoint.sh"]
CMD ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]

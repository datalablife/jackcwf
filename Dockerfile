# Multi-stage Dockerfile for Reflex Application
# Optimized for production deployment with CI/CD

# Build arguments
ARG PYTHON_VERSION=3.12
ARG NODE_VERSION=20

# ============================================
# Stage 1: Python dependencies builder
# ============================================
FROM python:${PYTHON_VERSION}-slim as python-builder

WORKDIR /app

# Install system dependencies for Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install Python dependencies
RUN uv sync --no-dev

# ============================================
# Stage 2: Node.js frontend builder
# ============================================
FROM node:${NODE_VERSION}-slim as node-builder

WORKDIR /app

# Copy Python environment from previous stage (needed for reflex)
COPY --from=python-builder /app/.venv /app/.venv
COPY --from=python-builder /root/.cargo/bin/uv /usr/local/bin/uv

# Copy application files
COPY . .

# Initialize and build Reflex
ENV PATH="/app/.venv/bin:$PATH"
RUN python -m reflex init --loglevel warning
RUN python -m reflex export --frontend-only --loglevel info

# ============================================
# Stage 3: Production runtime
# ============================================
FROM python:${PYTHON_VERSION}-slim

# Build arguments
ARG VERSION=latest
ARG BUILD_DATE
ARG VCS_REF

# Labels
LABEL maintainer="jack@example.com"
LABEL version="${VERSION}"
LABEL description="Reflex Full-Stack Application"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${VCS_REF}"

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash appuser && \
    chown -R appuser:appuser /app

# Copy Python environment
COPY --from=python-builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy built frontend
COPY --from=node-builder --chown=appuser:appuser /app/.web /app/.web

# Copy application code
COPY --chown=appuser:appuser . .

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV REFLEX_ENV=production
ENV FRONTEND_PORT=3000
ENV BACKEND_PORT=8000

# Expose ports
EXPOSE 3000 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Switch to non-root user
USER appuser

# Start application
CMD ["python", "-m", "reflex", "run", "--env", "production"]

# Simplified Dockerfile for Reflex Application with Coolify compatibility
# This Dockerfile is optimized for Coolify deployment
# For local development, use: uv sync && uv run reflex run

ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim

WORKDIR /app

# Install system dependencies for Python packages and Node.js
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for Reflex frontend
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install Python dependencies (non-dev for production)
RUN uv sync --no-dev

# Copy application code
COPY . .

# Initialize Reflex and build frontend
ENV PATH="/app/.venv/bin:$PATH"
RUN python -m reflex init --loglevel warning && \
    python -m reflex export --frontend-only --loglevel info

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV REFLEX_ENV=production
ENV FRONTEND_PORT=3000
ENV BACKEND_PORT=8000

# Expose ports
EXPOSE 3000 8000

# Health check - extended start period for Reflex app compilation
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=5 \
    CMD curl -f http://localhost:3000/ || exit 1

# Start application
CMD ["python", "-m", "reflex", "run", "--env", "production"]

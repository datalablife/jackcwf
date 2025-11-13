# Startup System Quick Start Guide

Fast guide to using the new unified startup system for both development and production environments.

## Quick Links

- **Development?** → [Development Quick Start](#development-quick-start)
- **Production/Container?** → [Container Quick Start](#container-quick-start)
- **Want Details?** → [Full Documentation](#full-documentation)

---

## Development Quick Start

### Start Everything in One Command

```bash
cd /path/to/project
bash scripts/dev/start.sh
```

That's it! The script will:

1. ✅ Check all required commands (Python, Node, npm, poetry)
2. ✅ Verify project structure
3. ✅ Install/update backend dependencies (Python packages)
4. ✅ Install/update frontend dependencies (npm packages)
5. ✅ Check database connection
6. ✅ Start backend (FastAPI with hot reload)
7. ✅ Start frontend (React with Vite dev server)
8. ✅ Display helpful information with endpoints

### After Startup Completes

You should see:

```
════════════════════════════════════════
✨ 开发环境启动完成！
════════════════════════════════════════

📋 服务信息:

  后端 (FastAPI + Uvicorn):
    🔗 API:       http://localhost:8000
    📚 文档:      http://localhost:8000/docs
    🔍 ReDoc:     http://localhost:8000/redoc
    🌐 Host:      127.0.0.1

  前端 (React + Vite):
    🔗 应用:      http://localhost:5173
    📂 项目:      /path/to/frontend

📝 日志:
    📄 文件:      logs/development/launcher-YYYY-MM-DD.log
    👀 实时查看:  tail -f logs/development/launcher-YYYY-MM-DD.log

🔄 热重载:
    后端: 修改 backend/src 中的文件会自动重载
    前端: 修改 frontend/src 中的文件会自动刷新

⏹️  停止: 按 Ctrl+C 优雅关闭所有服务
```

### Testing the Services

**Backend API:**
```bash
curl http://localhost:8000/health
```

**Frontend:**
Open http://localhost:5173 in your browser

**API Documentation:**
Open http://localhost:8000/docs (Swagger UI)

### Development Tips

1. **Modify code while running:**
   - Backend: Change files in `backend/src` → auto-reloads (5-10 seconds)
   - Frontend: Change files in `frontend/src` → auto-refreshes (instant)

2. **View logs in real-time:**
   ```bash
   tail -f logs/development/launcher-YYYY-MM-DD.log
   ```

3. **Stop services gracefully:**
   ```
   Press Ctrl+C
   ```
   Waits up to 30 seconds for each service to shutdown cleanly

4. **Database migrations:**
   - Automatically run when backend starts
   - Check `backend/migrations/` for migration files

---

## Container Quick Start

### Build Docker Image

```bash
docker build -f Dockerfile.prod -t my-app:latest .
```

### Run Container

```bash
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql+asyncpg://user:password@db:5432/mydb" \
  -e ENVIRONMENT=production \
  my-app:latest
```

### On Coolify

1. Connect your GitHub repository to Coolify
2. Create new application
3. Set Dockerfile: `Dockerfile.prod`
4. Add environment variables (DATABASE_URL, etc.)
5. Click Deploy

That's it! Coolify handles the rest.

---

## Full Documentation

### Directory Structure

```
scripts/
├── dev/
│   └── start.sh              # Development startup script
├── container/
│   └── entrypoint.sh         # Container startup script
├── lib/                       # Shared libraries (used by both)
│   ├── ui.sh                 # Terminal UI (colors, progress bars)
│   ├── utils.sh              # System utilities
│   ├── logging.sh            # Logging system
│   └── signals.sh            # Signal handling (graceful shutdown)
└── config/                    # Environment configurations
    ├── dev.env               # Development environment
    ├── test.env              # Test environment
    └── prod.env              # Production environment
```

### Key Files

#### Development Entry Point: `scripts/dev/start.sh`

**What it does:**
- Loads development environment configuration
- Checks prerequisites (commands, directories)
- Installs/updates dependencies
- Validates database connection
- Starts backend and frontend services
- Handles graceful shutdown

**Usage:**
```bash
bash scripts/dev/start.sh
```

**Features:**
- 6-step initialization with progress
- Colored output and status indicators
- File and terminal logging
- Hot reload for both backend and frontend
- Service health checks
- Graceful shutdown on Ctrl+C

#### Container Entry Point: `scripts/container/entrypoint.sh`

**What it does:**
- Validates production environment
- Checks database connectivity (with retries)
- Runs database migrations
- Calculates optimal worker count
- Starts Uvicorn server
- Handles SIGTERM for graceful shutdown

**Usage (in Docker):**
```bash
docker run my-app:latest start        # Normal start
docker run my-app:latest health       # Health check
docker run my-app:latest migrate      # Run migrations only
docker run my-app:latest shell        # Debug shell
```

**Features:**
- PID 1 process handling
- SIGTERM signal handling
- Database migration support
- JSON logging for aggregation
- Health check endpoint
- Worker optimization

### Shared Libraries

All scripts use these shared libraries:

#### `lib/ui.sh` - Terminal UI
Provides colored output and formatted messages
```bash
print_success "Operation completed"
print_error "Something failed"
print_info "Informational message"
progress_bar 50 100  # Show progress (50 of 100)
```

#### `lib/utils.sh` - System Utilities
Provides system checks and utilities
```bash
command_exists "python"          # Check if command available
is_in_container                  # Check if running in Docker
get_cpu_cores                    # Get number of CPU cores
wait_for_port "localhost" 8000   # Wait for port to be available
wait_for_http "http://..."       # Wait for HTTP endpoint
is_process_running $PID          # Check if process alive
```

#### `lib/logging.sh` - Logging System
Provides dual-mode logging (file + stdout)
```bash
log_info "component" "Message"      # Info level
log_warning "component" "Warning"   # Warning level
log_error "component" "Error"       # Error level
setup_local_logging "dev" "logs"    # Setup for dev (file + stdout)
setup_container_logging             # Setup for container (stdout only)
```

#### `lib/signals.sh` - Signal Handling
Provides graceful shutdown
```bash
setup_signal_handlers              # Register signal handlers
register_backend_pid $pid          # Register process for cleanup
graceful_shutdown                  # Graceful shutdown sequence
```

### Configuration Files

#### Development (`scripts/config/dev.env`)
```env
ENVIRONMENT=development
DATABASE_URL=postgresql://...dev
BACKEND_PORT=8000
BACKEND_HOST=127.0.0.1
BACKEND_WORKERS=1
BACKEND_RELOAD=true
DEBUG=true
LOG_LEVEL=DEBUG
FRONTEND_PORT=5173
```

#### Production (`scripts/config/prod.env`)
```env
ENVIRONMENT=production
BACKEND_PORT=8000
BACKEND_HOST=0.0.0.0
BACKEND_WORKERS=auto              # Auto-calculated (2-8)
BACKEND_RELOAD=false
DEBUG=false
LOG_LEVEL=WARNING
DB_POOL_SIZE=20
ENABLE_METRICS=true
CORS_STRICT=true
```

### Docker Configuration

#### Multi-stage Dockerfile (`Dockerfile.prod`)

**Stages:**
1. **frontend-builder**: Builds React app with Vite
2. **backend-builder**: Installs Python dependencies
3. **application**: Final production image combining both

**Optimizations:**
- Multi-stage reduces final image size
- Only production dependencies included
- Minimal base images (python:3.12-slim, node:20-alpine)
- Shared library caching

**Building:**
```bash
docker build -f Dockerfile.prod -t app:latest .
```

#### .dockerignore
Excludes unnecessary files from Docker build:
- Development files (.git, node_modules, .venv)
- Test files and coverage reports
- IDE configuration
- Documentation (except scripts)
- Logs and temporary files

---

## Common Tasks

### Restart Services (Development)

```bash
# Kill existing process
pkill -f "uvicorn"
pkill -f "npm run dev"

# Start fresh
bash scripts/dev/start.sh
```

### Check Service Status

```bash
# Backend health
curl http://localhost:8000/health

# Frontend
curl http://localhost:5173

# Backend logs (if separate terminal)
tail -f logs/development/launcher-*.log
```

### Run Database Migrations Only

```bash
# Development
cd backend
source .venv/bin/activate
alembic upgrade head

# Container
docker run app:latest migrate
```

### Debug Container

```bash
# Start shell in container
docker run -it app:latest shell

# Inside shell:
ls -la /app                    # Check directory structure
python -c "import fastapi"     # Check dependencies
curl http://localhost:8000     # Test endpoint
```

### View Application Logs

```bash
# Development (file + terminal)
tail -f logs/development/launcher-*.log

# Container
docker logs <container-id>

# Container real-time
docker logs -f <container-id>
```

### Check Port Usage

```bash
# See what's using port 8000
lsof -i :8000

# See what's using port 5173
lsof -i :5173
```

---

## Troubleshooting

### "Command not found: python3"
```bash
# Solution: Install Python 3.12
# Ubuntu/Debian:
sudo apt-get install python3.12 python3.12-venv

# macOS:
brew install python@3.12
```

### "Backend failed to start"
```bash
# Check if port 8000 is already in use
lsof -i :8000

# Check database connection
psql $DATABASE_URL -c "SELECT 1"

# Check backend logs
tail -f logs/development/launcher-*.log
```

### "Frontend failed to start"
```bash
# Check if port 5173 is already in use
lsof -i :5173

# Check Node.js version
node --version  # Should be v20+

# Try clearing node_modules
rm -rf frontend/node_modules
npm install --prefix frontend
```

### "Database connection failed"
```bash
# Check DATABASE_URL is set
echo $DATABASE_URL

# Check database is running
pg_isready -h pgvctor.jackcwf.com -p 5432

# Test connection manually
psql postgresql://user:pass@pgvctor.jackcwf.com:5432/dbname
```

### "Docker build fails"
```bash
# Check Dockerfile syntax
docker build -f Dockerfile.prod --dry-run .

# Build with more verbose output
docker build -f Dockerfile.prod --progress=plain .

# Check available disk space
df -h

# Check Docker daemon is running
docker ps
```

---

## Environment Variables

### Required for Development
- `DATABASE_URL` - PostgreSQL connection string

### Required for Production/Container
- `DATABASE_URL` - PostgreSQL connection string
- `ENVIRONMENT` - Should be "production"

### Optional but Recommended
- `BACKEND_WORKERS` - Number of Uvicorn workers (default: auto)
- `LOG_LEVEL` - DEBUG/INFO/WARNING/ERROR/CRITICAL (default: WARNING)
- `CORS_ORIGINS` - Comma-separated allowed origins

### All Available Variables
See `scripts/config/dev.env` and `scripts/config/prod.env` for complete list

---

## Performance Tips

1. **Development Startup Time**
   - First run: 2-3 minutes (installs dependencies)
   - Subsequent runs: 30 seconds
   - Rebuild frontend assets on changes (seconds)

2. **Production Optimization**
   - Image size: ~600-800MB
   - Container startup: 10-20 seconds
   - Health check grace period: 60 seconds
   - Worker count: Automatically optimized

3. **Database Performance**
   - Connection pooling: 20 connections (production)
   - Connection timeout: 10 seconds
   - Pool recycle: 3600 seconds

---

## Additional Resources

- **Architecture Document:** `UNIFIED_STARTUP_SOLUTION_ANALYSIS.md`
- **Coolify Guide:** `COOLIFY_DEPLOYMENT_GUIDE.md`
- **Project Root:** See `scripts/` directory structure

---

## Support

For issues or questions:
1. Check the full documentation files
2. Review application logs
3. Test each component individually
4. Check GitHub issues repository

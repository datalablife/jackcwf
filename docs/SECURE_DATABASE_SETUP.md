# Secure PostgreSQL Database Setup Guide

This guide provides comprehensive instructions for securely setting up PostgreSQL database connectivity in the LangChain AI Analyzer application.

## Table of Contents

1. [Security Principles](#security-principles)
2. [Initial Setup](#initial-setup)
3. [Environment Variables](#environment-variables)
4. [Configuration by Environment](#configuration-by-environment)
5. [Troubleshooting](#troubleshooting)
6. [Security Best Practices](#security-best-practices)
7. [Production Checklist](#production-checklist)

---

## Security Principles

The application follows strict security principles to prevent credential exposure:

### Core Rules

1. **NO Hardcoded Credentials**
   - All sensitive information must come from environment variables
   - Default values in code must NEVER contain actual credentials
   - The `.env` file must NEVER be committed to version control

2. **Environment-Based Configuration**
   - Development, staging, and production use different configurations
   - Each environment has its own `.env` file
   - `.env.example` serves as a template without sensitive values

3. **Fail-Fast Validation**
   - Application fails immediately if required configuration is missing
   - Clear error messages guide users to fix configuration
   - Configuration validation runs before any database operations

4. **Secure Error Handling**
   - Error messages never expose credentials or sensitive details
   - Only connection status is logged, not connection parameters
   - Stack traces are sanitized in production

---

## Initial Setup

### Step 1: Copy the Environment Template

Create your `.env` file from the provided template:

```bash
# Development setup
cp .env.example .env

# Staging setup
cp .env.example .env.staging

# Production setup
cp .env.example .env.prod
```

### Step 2: Edit .env with Your Credentials

Open `.env` in your text editor and fill in all `your_*` placeholders with your actual values:

```bash
# REQUIRED - must be set for database to work
DATABASE_URL=postgresql+asyncpg://username:password@host:5432/dbname
POSTGRES_HOST=your_host
POSTGRES_PORT=5432
POSTGRES_USER=your_username
POSTGRES_DB=your_database_name
ENCRYPTION_KEY=your-encryption-key
```

### Step 3: Verify .gitignore Configuration

Ensure `.env` files are ignored by Git:

```bash
# Check that .env is in .gitignore
grep "\.env" .gitignore

# If not already there, .env patterns should include:
# .env
# .env.local
# .env.*.local
# .env.prod
# .env.staging
```

### Step 4: Validate Configuration

Use the validation script to verify your setup:

```bash
# Check development configuration
python scripts/validate_env.py --environment=development

# Check with strict validation (including optional vars)
python scripts/validate_env.py --environment=development --strict

# Check staging configuration
python scripts/validate_env.py --environment=staging

# Check production configuration
python scripts/validate_env.py --environment=production
```

---

## Environment Variables

### Required Variables

All of these MUST be set for the application to function:

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | Async PostgreSQL connection string | `postgresql+asyncpg://user:pass@host:5432/db` |
| `POSTGRES_HOST` | PostgreSQL server hostname | `localhost` or `db.example.com` |
| `POSTGRES_PORT` | PostgreSQL port number | `5432` |
| `POSTGRES_USER` | PostgreSQL username | `postgres` |
| `POSTGRES_DB` | PostgreSQL database name | `langchain_ai` |
| `ENCRYPTION_KEY` | 256-bit encryption key for sensitive data | Generated key (see below) |

### Generating a Secure Encryption Key

```bash
# Python 3
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Or in a Python shell
import secrets
print(secrets.token_urlsafe(32))
```

Copy the output to your `.env` as:
```
ENCRYPTION_KEY=<paste-generated-key-here>
```

### Optional Variables

These are recommended but have sensible defaults:

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_CONNECTION_TIMEOUT` | `10` | Connection timeout in seconds |
| `DB_COMMAND_TIMEOUT` | `60` | Command timeout in seconds |
| `SQL_ECHO` | `false` | Enable SQL query logging (development only) |
| `DEBUG` | `true` | Debug mode (development only) |
| `LOG_LEVEL` | `INFO` | Logging verbosity level |

---

## Configuration by Environment

### Development Environment

**Purpose**: Local development with relaxed security for rapid iteration

**Setup**:
```bash
# 1. Copy template
cp .env.example .env

# 2. Configure for local development
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/langchain_ai
```

**Characteristics**:
- SQL echo enabled for debugging
- Verbose logging
- Local database (usually)
- Relaxed validation

**Run validation**:
```bash
python scripts/validate_env.py --environment=development
```

### Staging Environment

**Purpose**: Pre-production testing with security closer to production

**Setup**:
```bash
# 1. Copy template
cp .env.example .env.staging

# 2. Configure for staging
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=WARNING
DATABASE_URL=postgresql+asyncpg://staging_user:staging_password@staging.example.com:5432/langchain_ai_staging
```

**Characteristics**:
- Matches production structure
- Real database on staging server
- Security validations enforced
- Limited logging

**Run validation**:
```bash
python scripts/validate_env.py --environment=staging
```

### Production Environment

**Purpose**: Live application with maximum security

**Setup**:
```bash
# 1. Copy template
cp .env.example .env.prod

# 2. Configure for production
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=ERROR
DATABASE_URL=postgresql+asyncpg://prod_user:prod_password@prod.example.com:5432/langchain_ai
ENCRYPTION_KEY=<strong-production-key>
```

**Critical Requirements**:
- Never store `.env.prod` locally - use secrets management service
- Use AWS Secrets Manager, GCP Secret Manager, Azure Key Vault, or similar
- Rotate credentials regularly
- Enable SSL/TLS for database connections
- Use strong, unique passwords
- Implement access controls and monitoring

**Run strict validation**:
```bash
python scripts/validate_env.py --environment=production --strict
```

---

## Using Different Configurations

### Method 1: Environment-Specific .env Files

```bash
# Development
export ENV_FILE=.env
python -m src.main

# Staging
export ENV_FILE=.env.staging
python -m src.main

# Production (using secrets service)
# Set environment variables from your secrets manager
python -m src.main
```

### Method 2: Docker Deployment

Create environment-specific Docker configurations:

```dockerfile
# Dockerfile.prod
FROM python:3.12
WORKDIR /app

# Set production environment
ENV ENVIRONMENT=production

# Copy requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . .

# Validate configuration before starting
RUN python scripts/validate_env.py --environment=production --strict || exit 1

# Start application
CMD ["python", "-m", "src.main"]
```

Build and run:
```bash
docker build -f Dockerfile.prod -t langchain-ai:prod .
docker run \
  -e DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/db" \
  -e POSTGRES_HOST="host" \
  -e POSTGRES_PORT="5432" \
  -e POSTGRES_USER="user" \
  -e POSTGRES_DB="dbname" \
  -e ENCRYPTION_KEY="your-key" \
  langchain-ai:prod
```

### Method 3: Kubernetes Secrets

Create a secret from your `.env`:

```bash
# Create secret from .env.prod
kubectl create secret generic langchain-db-credentials \
  --from-env-file=.env.prod \
  -n langchain-ai

# Use in deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: langchain-ai
spec:
  template:
    spec:
      containers:
      - name: app
        image: langchain-ai:prod
        envFrom:
        - secretRef:
            name: langchain-db-credentials
```

---

## Troubleshooting

### "Missing required environment variable: DATABASE_URL"

**Problem**: The DATABASE_URL environment variable is not set

**Solution**:
1. Verify `.env` file exists: `ls -la .env`
2. Check if file is readable: `file .env`
3. Verify variable is set: `grep DATABASE_URL .env`
4. Load environment: `source .env` (bash/zsh)
5. Re-run validation: `python scripts/validate_env.py`

### "Connection refused" at Database Setup

**Problem**: Cannot connect to the PostgreSQL server

**Solution**:
1. Verify host is accessible: `ping <POSTGRES_HOST>`
2. Check port is open: `telnet <POSTGRES_HOST> <POSTGRES_PORT>`
3. Verify credentials are correct
4. Check PostgreSQL service is running
5. Look at error logs: Check PostgreSQL server logs

### "Authentication failed"

**Problem**: Wrong username or password

**Solution**:
1. Verify credentials in `.env`:
   ```bash
   grep -E "POSTGRES_USER|DATABASE_URL" .env
   ```
2. Check PostgreSQL user exists:
   ```bash
   psql -h <host> -U postgres -l
   ```
3. Try connecting directly:
   ```bash
   psql "postgresql://user:password@host:5432/dbname"
   ```
4. Reset password if needed
5. Update `.env` with correct credentials

### "pgvector extension not found"

**Problem**: pgvector extension is not installed on the database

**Solution**:
1. Connect to PostgreSQL as admin:
   ```bash
   psql -h <host> -U postgres -d <database>
   ```
2. Install pgvector extension:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
3. Verify installation:
   ```sql
   SELECT * FROM pg_extension WHERE extname = 'vector';
   ```
4. If not available, contact your database provider

### "Insufficient permissions"

**Problem**: Database user doesn't have required permissions

**Solution**:
1. Connect as admin user
2. Grant permissions:
   ```sql
   GRANT ALL PRIVILEGES ON DATABASE <dbname> TO <username>;
   GRANT ALL PRIVILEGES ON SCHEMA public TO <username>;
   GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO <username>;
   GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO <username>;
   ```

---

## Security Best Practices

### 1. Credential Management

- **Never hardcode credentials** - Always use environment variables
- **Rotate credentials regularly** - Every 90 days minimum
- **Use strong passwords** - At least 16 characters, mixed case, numbers, symbols
- **Generate encryption keys securely** - Use `secrets.token_urlsafe()` or OS-level crypto
- **Store separately** - Keep .env in a secure location, never in version control

### 2. Version Control

```bash
# Verify .env is in .gitignore
echo ".env" >> .gitignore
echo ".env.local" >> .gitignore
echo ".env.*.local" >> .gitignore

# Check if .env was already committed (CRITICAL IF TRUE)
git log --all -S "DATABASE_URL" --oneline

# If found, the repository is compromised - rotate ALL credentials immediately
```

### 3. Application Security

**In src/db/config.py**:
- Credentials validated on startup
- Missing credentials raise errors before database operations
- No credentials in log messages
- SQL echo disabled in production

**In src/db/setup_remote_db.py**:
- Only logs non-sensitive connection information
- Validates configuration before connecting
- Provides helpful error messages
- Never exposes passwords in output

### 4. Database Security

```bash
# Use SSL/TLS for connections
postgresql+asyncpg://user:pass@host:5432/db?sslmode=require

# Create limited-privilege database user
CREATE USER app_user WITH PASSWORD 'strong_password';
GRANT CONNECT ON DATABASE app_db TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;

# Enable query logging for audit
log_statement = 'all'
log_min_duration_statement = 0
```

### 5. Environment Variable Security

```bash
# Don't put credentials in shell history
export HISTCONTROL=ignorespace  # Won't log lines starting with space
 export MY_SECRET=secret_value    # Space prevents logging

# Mask sensitive data in logs
def log_safe_url(url: str) -> str:
    """Return URL with password masked"""
    return url.replace(password, "***REDACTED***")

# Don't print environment
# BAD: os.system("env")
# GOOD: only read specific variables
```

### 6. Monitoring & Alerting

```bash
# Monitor for failed connection attempts
grep "Connection failed" /var/log/postgresql/postgresql.log

# Alert on unauthorized access attempts
grep "authentication failed" /var/log/postgresql/postgresql.log

# Check for credential exposure in logs
grep -r "password\|secret\|key" logs/ --exclude-dir=.git
```

---

## Production Checklist

Before deploying to production, verify all of the following:

### Security

- [ ] No credentials committed to any branch (check git history)
- [ ] `.env` files are in `.gitignore`
- [ ] All passwords are strong (16+ characters, mixed case, numbers, symbols)
- [ ] Encryption keys generated securely using `secrets` module
- [ ] Database credentials rotated from development values
- [ ] SSL/TLS enabled for all database connections
- [ ] Database user has minimal required permissions
- [ ] No SQL echo or debug logging in production

### Configuration

- [ ] `ENVIRONMENT=production` is set
- [ ] `DEBUG=false` is set
- [ ] `LOG_LEVEL=ERROR` is set
- [ ] All required environment variables are defined
- [ ] Database connection validated before deployment
- [ ] pgvector extension installed and working
- [ ] Database backups are configured
- [ ] Connection pooling is tuned for expected load

### Monitoring

- [ ] Error tracking configured (Sentry or similar)
- [ ] Database query logging enabled
- [ ] Connection pool monitoring active
- [ ] Failed authentication logging enabled
- [ ] Backup verification scheduled

### Documentation

- [ ] Team knows how to rotate credentials
- [ ] Runbooks documented for common issues
- [ ] Emergency procedures documented
- [ ] Contact list for database administrators

### Testing

- [ ] Connection validation script passes: `python scripts/validate_env.py --environment=production --strict`
- [ ] Database setup script completes successfully
- [ ] All database queries verified to work
- [ ] Load testing completed
- [ ] Failover tested (if applicable)

---

## Quick Reference

### Validation Script

```bash
# Full validation for current environment
python scripts/validate_env.py

# Strict validation (includes optional checks)
python scripts/validate_env.py --strict

# Validate specific environment
python scripts/validate_env.py --environment=production
```

### Generate Encryption Key

```bash
python -c "import secrets; print('ENCRYPTION_KEY=' + secrets.token_urlsafe(32))"
```

### Test Database Connection

```bash
# Using psql
psql "postgresql://user:password@host:5432/database"

# Using Python
python -c "
from src.db.config import engine
import asyncio
asyncio.run(engine.connect())
print('Connected!')
"
```

### View Current Configuration (safe)

```bash
# Shows which variables are set (not values)
python scripts/validate_env.py --strict

# Or manually check
grep "^[^#]" .env | cut -d= -f1 | sort
```

### Reset to Example Config

```bash
# Start over with template
rm .env
cp .env.example .env
nano .env  # Edit with your values
```

---

## Support

For issues or questions:

1. Check the [Troubleshooting](#troubleshooting) section above
2. Review error messages - they include helpful guidance
3. Consult [docs/README.md](../README.md) for general setup
4. Check application logs: `tail -f logs/app.log`
5. Contact your database administrator

For security incidents or credential exposure:
1. **Immediately rotate credentials**
2. **Check git history** for exposure: `git log --all -p -- .env | head -50`
3. **Revoke old credentials** from the database
4. **Audit access logs** for unauthorized access
5. **Notify team** of the incident

---

**Last Updated**: 2024-11-18
**Security Level**: Critical Infrastructure
**Review Date**: Quarterly

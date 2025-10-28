# CI/CD Pipeline Documentation

Complete guide to the GitHub Actions CI/CD pipelines for the Reflex full-stack application.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Workflows](#workflows)
- [Setup Instructions](#setup-instructions)
- [Deployment Process](#deployment-process)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Overview

This project implements a comprehensive CI/CD system using GitHub Actions, designed specifically for a Reflex full-stack application deployed via Coolify.

### Key Features

- **Automated Testing**: Unit, integration, and E2E tests
- **Code Quality**: Linting, formatting, and type checking
- **Security Scanning**: Dependency scanning, SAST, container security
- **Multi-Environment Deployment**: Development, staging, production
- **Health Monitoring**: Automated health checks and smoke tests
- **Rollback Capability**: Automated rollback on deployment failure

### Technology Stack

- **CI/CD Platform**: GitHub Actions
- **Package Manager**: uv (Python)
- **Framework**: Reflex 0.8.16
- **Deployment Target**: Coolify (self-hosted)
- **Container Registry**: GitHub Container Registry (ghcr.io)

## Architecture

### Workflow Structure

```
.github/workflows/
├── ci.yml           # Main CI pipeline (tests, linting, build)
├── cd.yml           # Continuous deployment pipeline
├── security.yml     # Security scanning
└── pre-commit.yml   # Pre-commit validation
```

### Pipeline Flow

```
┌─────────────────┐
│   Code Push     │
└────────┬────────┘
         │
         ├──────────────────┬──────────────────┬──────────────────┐
         ▼                  ▼                  ▼                  ▼
  ┌─────────────┐    ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
  │  Pre-commit │    │     CI      │   │  Security   │   │ Dependabot  │
  │   Checks    │    │  Pipeline   │   │   Scans     │   │   Updates   │
  └──────┬──────┘    └──────┬──────┘   └─────────────┘   └─────────────┘
         │                  │
         └────────┬─────────┘
                  ▼
         ┌─────────────────┐
         │   All Checks    │
         │     Pass?       │
         └────────┬────────┘
                  │ Yes
                  ▼
         ┌─────────────────┐
         │  Build Docker   │
         │     Image       │
         └────────┬────────┘
                  │
         ┌────────┴────────┬────────────┬─────────────┐
         ▼                 ▼            ▼             ▼
  ┌─────────────┐   ┌─────────────┐   ┌──────────┐   ┌──────────┐
  │ Development │   │   Staging   │   │Production│   │ Rollback │
  │   Deploy    │   │   Deploy    │   │  Deploy  │   │ (if fail)│
  └──────┬──────┘   └──────┬──────┘   └────┬─────┘   └──────────┘
         │                 │               │
         └────────┬────────┴───────┬───────┘
                  ▼                ▼
         ┌─────────────────┐  ┌─────────────────┐
         │ Health Checks   │  │  Smoke Tests    │
         └─────────────────┘  └─────────────────┘
```

## Workflows

### 1. CI Pipeline (`ci.yml`)

**Triggers**:
- Push to `main`, `develop`, `feature/**`, `bugfix/**`
- Pull requests to `main`, `develop`
- Manual dispatch

**Jobs**:

#### Setup
- Installs Python 3.12, Node.js 20, and uv
- Caches dependencies for faster builds

#### Lint
- Black (code formatting)
- isort (import sorting)
- flake8 (style guide enforcement)
- pylint (code analysis)

#### Type Check
- mypy (static type checking)

#### Test
- Unit tests with PostgreSQL and Redis services
- Integration tests
- Coverage reporting to Codecov
- Test artifacts uploaded

#### Build
- Reflex application build
- Frontend export
- Build artifacts archived

#### CI Summary
- Aggregates all job results
- Fails if any critical job fails

**Configuration**:
```yaml
env:
  PYTHON_VERSION: '3.12'
  NODE_VERSION: '20'
  UV_VERSION: '0.9.2'
  FRONTEND_PORT: 3000
  BACKEND_PORT: 8000
```

### 2. CD Pipeline (`cd.yml`)

**Triggers**:
- Push to `main` (auto-deploy to staging)
- Manual dispatch with environment selection

**Jobs**:

#### Pre-Deploy
- Determines target environment
- Generates version tag (format: `YYYYMMDD-HHMMSS-githash`)
- Validates branch restrictions

#### Test (Optional)
- Runs critical tests before deployment
- Can be skipped via workflow input

#### Build Image
- Builds Docker image with multi-stage build
- Pushes to GitHub Container Registry
- Tags: `latest`, `main-sha`, version tag

#### Deploy Development
- Automatic deployment
- No approval required
- URL: https://dev.jackcwf.com

#### Deploy Staging
- Triggered on push to main
- No approval required
- URL: https://staging.jackcwf.com

#### Deploy Production
- Requires manual approval
- Creates backup before deployment
- URL: https://jackcwf.com
- Automatic rollback on failure

#### Post-Deploy
- 5-minute health monitoring
- Generates deployment report

**Environment Variables**:
```bash
# Required GitHub Secrets
COOLIFY_API_TOKEN          # Coolify API token
COOLIFY_DEV_APP_UUID       # Development app UUID
COOLIFY_STAGING_APP_UUID   # Staging app UUID
COOLIFY_PROD_APP_UUID      # Production app UUID
```

### 3. Security Pipeline (`security.yml`)

**Triggers**:
- Push to `main`, `develop`
- Pull requests
- Weekly schedule (Mondays at 9 AM UTC)
- Manual dispatch

**Jobs**:

#### Python Security
- pip-audit (dependency vulnerabilities)
- Safety (known security issues)

#### SAST
- Bandit (Python security linter)
- Severity: Medium+
- Confidence: Medium+

#### Secret Scan
- TruffleHog (verified secrets)
- Gitleaks (hardcoded secrets)

#### Container Scan
- Trivy (vulnerability scanner)
- SARIF format for GitHub Security tab

#### CodeQL
- Advanced semantic code analysis
- Python and JavaScript
- Security-extended queries

#### Dependency Review (PRs only)
- Reviews dependency changes
- Fails on moderate+ severity
- Blocks GPL/AGPL licenses

### 4. Pre-commit Pipeline (`pre-commit.yml`)

**Triggers**:
- Pull requests (opened, synchronized, reopened)
- Push to `feature/**`, `bugfix/**`, `hotfix/**`

**Jobs**:

#### Quick Checks
- Commit message format validation
- Large file detection (>5MB)
- TODO/FIXME comment detection
- Python syntax validation

#### Format Check
- Black formatting
- isort import order
- Auto-fix suggestions on failure

#### Static Analysis
- flake8 linting

#### Fast Tests
- Unit tests only
- 10-second timeout per test
- Excludes slow tests

#### Security Quick
- Quick Bandit scan
- Hardcoded secret pattern detection

## Setup Instructions

### 1. GitHub Repository Setup

#### Create Environments

Navigate to **Settings → Environments** and create:

1. **development**
   - No protection rules
   - Secrets: `COOLIFY_DEV_APP_UUID`

2. **staging**
   - Optional: Required reviewers
   - Secrets: `COOLIFY_STAGING_APP_UUID`

3. **production**
   - Required reviewers: Add team leads
   - Wait timer: 5 minutes (optional)
   - Secrets: `COOLIFY_PROD_APP_UUID`

#### Configure Secrets

Navigate to **Settings → Secrets and variables → Actions**

**Repository Secrets**:
```bash
COOLIFY_API_TOKEN=2|xxxxx...
COOLIFY_URL=https://coolpanel.jackcwf.com
```

**Environment Secrets**:
```bash
# development environment
COOLIFY_DEV_APP_UUID=your-dev-app-uuid

# staging environment
COOLIFY_STAGING_APP_UUID=your-staging-app-uuid

# production environment
COOLIFY_PROD_APP_UUID=your-prod-app-uuid
```

#### Get Coolify Credentials

```bash
# Install Coolify CLI
curl -fsSL https://raw.githubusercontent.com/coollabsio/coolify-cli/main/scripts/install.sh | bash

# Configure context
coolify context add myapp https://coolpanel.jackcwf.com '<your-api-token>'

# List applications to get UUIDs
coolify app list --format json

# Get specific app UUID
coolify app get <app-name> --format json | jq -r '.uuid'
```

### 2. Enable GitHub Actions

1. Go to **Settings → Actions → General**
2. Set **Actions permissions** to "Allow all actions and reusable workflows"
3. Set **Workflow permissions** to "Read and write permissions"
4. Enable "Allow GitHub Actions to create and approve pull requests"

### 3. Configure Branch Protection

Navigate to **Settings → Branches → Branch protection rules**

**For `main` branch**:
- ☑ Require a pull request before merging
  - Required approvals: 1
  - Dismiss stale reviews
- ☑ Require status checks to pass before merging
  - Required checks:
    - `CI Summary`
    - `Lint and Format Check`
    - `Type Checking`
    - `Run Tests`
- ☑ Require conversation resolution before merging
- ☑ Include administrators (optional)

**For `develop` branch**:
- ☑ Require status checks to pass before merging
  - Required checks:
    - `Pre-commit Summary`

### 4. Enable Dependabot

Dependabot is automatically configured via `.github/dependabot.yml`

To enable:
1. Go to **Settings → Code security and analysis**
2. Enable "Dependabot alerts"
3. Enable "Dependabot security updates"
4. Enable "Dependabot version updates"

### 5. Local Development Setup

```bash
# Clone repository
git clone https://github.com/datalablife/jackcwf.git
cd jackcwf

# Install dependencies
uv sync --all-extras

# Copy environment template
cp .env.example .env
# Edit .env with your values

# Run pre-commit checks locally
./scripts/ci/pre-commit-local.sh

# Start development server
uv run reflex run
```

## Deployment Process

### Automatic Deployment

#### Development
```bash
# Push to any branch triggers CI
git push origin feature/my-feature

# Merge to develop deploys to development
git checkout develop
git merge feature/my-feature
git push origin develop
```

#### Staging
```bash
# Push to main deploys to staging
git checkout main
git merge develop
git push origin main
```

#### Production
```bash
# Use GitHub UI for manual approval
# 1. Go to Actions → CD workflow run
# 2. Review deployment
# 3. Click "Review deployments"
# 4. Select "production" environment
# 5. Click "Approve and deploy"
```

### Manual Deployment

```bash
# Go to Actions → CD workflow
# Click "Run workflow"
# Select:
#   - Branch: main
#   - Environment: production
#   - Skip tests: false
# Click "Run workflow"
```

### Rollback

#### Automatic Rollback
Production deployments automatically rollback if:
- Health checks fail
- Smoke tests fail
- Deployment times out

#### Manual Rollback

**Via GitHub Actions**:
```bash
# Go to Actions
# Find the last successful deployment
# Click "Re-run jobs"
```

**Via Script**:
```bash
# SSH to server or run locally
./scripts/deploy/rollback.sh production

# Or rollback to specific version
./scripts/deploy/rollback.sh production 20231027-154532-abc1234
```

**Via Coolify CLI**:
```bash
# List deployments
coolify app get <app-uuid> --format json | jq '.deployments'

# Rollback to previous deployment
coolify app rollback <app-uuid> --to <deployment-id>
```

## Troubleshooting

### CI Pipeline Failures

#### Tests Failing

```bash
# Run tests locally
uv run pytest tests/ -v

# Run specific test
uv run pytest tests/unit/test_example.py -v

# Check database connection
psql -h localhost -U testuser -d testdb
```

#### Build Failures

```bash
# Clean and rebuild
rm -rf .web/
uv run reflex init
uv run reflex export --frontend-only

# Check Node.js version
node --version  # Should be 20.x

# Clear npm cache
rm -rf .web/node_modules
rm -rf ~/.npm
```

#### Dependency Issues

```bash
# Sync dependencies
uv sync --all-extras

# Update lock file
uv lock --upgrade

# Check for conflicts
uv pip list
```

### CD Pipeline Failures

#### Coolify Connection Issues

```bash
# Verify API token
export COOLIFY_TOKEN='your-token'
curl -H "Authorization: Bearer $COOLIFY_TOKEN" \
  https://coolpanel.jackcwf.com/api/v1/health

# Check app UUID
coolify app get <app-uuid>

# Verify context
coolify context list
coolify context verify
```

#### Deployment Timeout

```bash
# Check Coolify logs
coolify app logs <app-uuid> --tail 100

# Check deployment status
coolify app get <app-uuid> --format json | jq '.status'

# Manual deployment trigger
./scripts/deploy/deploy-coolify.sh production <version>
```

#### Health Check Failures

```bash
# Run health checks manually
./scripts/deploy/health-check.sh https://jackcwf.com

# Check application logs
coolify app logs <app-uuid> --tail 100 --follow

# Check container status
docker ps -a | grep <app-name>
```

### Security Scan Issues

#### False Positives

Update `.github/workflows/security.yml`:

```yaml
# For Bandit
bandit -r working/ --skip B101,B601

# For Trivy
trivy image --severity HIGH,CRITICAL
```

#### Dependency Vulnerabilities

```bash
# Check vulnerabilities
uv pip install pip-audit
uv run pip-audit

# Update specific package
uv add package@latest

# Pin to safe version
# Edit pyproject.toml:
package = "==1.2.3"  # safe version
```

### Environment Issues

#### Missing Secrets

```bash
# List secrets (names only)
gh secret list

# Set secret
gh secret set SECRET_NAME --body "secret-value"

# Set from file
gh secret set SECRET_NAME < secret.txt
```

#### Port Conflicts

```bash
# Check port usage
lsof -i :3000
lsof -i :8000

# Kill process
kill -9 <PID>

# Use different ports
export FRONTEND_PORT=3001
export BACKEND_PORT=8001
```

## Best Practices

### Commit Messages

Follow conventional commits:

```bash
feat(auth): add two-factor authentication
fix(api): handle null pointer in user service
docs(readme): update installation instructions
chore(deps): update reflex to 0.8.16
test(api): add integration tests for auth
ci(workflow): add deployment approval step
```

### Branch Strategy

```
main (production)
  ↑
develop (staging)
  ↑
feature/xxx (development)
```

### Pull Request Workflow

1. Create feature branch from `develop`
2. Make changes and commit
3. Push and create PR to `develop`
4. Pre-commit checks run automatically
5. Request review
6. Merge after approval
7. Auto-deploy to development

### Testing Strategy

**Unit Tests** (fast, isolated):
```python
def test_user_creation():
    user = User(name="Test")
    assert user.name == "Test"
```

**Integration Tests** (with database):
```python
def test_user_api(db):
    response = client.post("/users", json={"name": "Test"})
    assert response.status_code == 201
```

**E2E Tests** (full application):
```python
def test_user_signup_flow(browser):
    browser.goto("/signup")
    browser.fill("name", "Test")
    browser.click("Submit")
    assert browser.url == "/dashboard"
```

### Deployment Checklist

Before production deployment:

- [ ] All tests pass
- [ ] Code review completed
- [ ] Security scan passed
- [ ] Documentation updated
- [ ] Database migrations prepared
- [ ] Environment variables configured
- [ ] Backup created
- [ ] Rollback plan ready
- [ ] Monitoring configured
- [ ] Team notified

After deployment:

- [ ] Health checks pass
- [ ] Smoke tests pass
- [ ] Response times acceptable
- [ ] No error spikes in logs
- [ ] Key features working
- [ ] Rollback tested (optional)

### Monitoring

**Key Metrics**:
- Response time (target: <2s)
- Error rate (target: <1%)
- CPU usage (target: <80%)
- Memory usage (monitor for leaks)
- Database connections

**Tools**:
- Coolify built-in monitoring
- Application logs
- Health endpoints
- Custom metrics endpoint

## Additional Resources

### Documentation

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Reflex Documentation](https://reflex.dev/docs)
- [Coolify Documentation](https://coolify.io/docs)
- [uv Documentation](https://docs.astral.sh/uv/)

### Scripts

All scripts are located in `/mnt/d/工作区/云开发/working/scripts/deploy/`:

- `deploy-coolify.sh` - Coolify deployment
- `health-check.sh` - Health monitoring
- `smoke-tests.sh` - Post-deployment tests
- `rollback.sh` - Rollback automation
- `backup.sh` - Backup creation
- `monitor-metrics.sh` - Metrics collection

### Support

For issues or questions:

1. Check this documentation
2. Review GitHub Actions logs
3. Check Coolify deployment logs
4. Review application logs
5. Contact DevOps team

---

**Last Updated**: 2025-10-28
**Version**: 1.0.0
**Maintainer**: jack@example.com

# CI/CD Quick Start Guide

Get your CI/CD pipeline up and running in 10 minutes.

## Prerequisites

- GitHub repository: `datalablife/jackcwf`
- Coolify instance: `https://coolpanel.jackcwf.com`
- Coolify API token
- Admin access to GitHub repository

## Step 1: Get Coolify Credentials (2 min)

### Get API Token

1. Log in to Coolify: https://coolpanel.jackcwf.com
2. Go to **Security → API Tokens**
3. Click **Create Token**
4. Copy the token (starts with `2|`)

### Get Application UUIDs

```bash
# Install Coolify CLI
curl -fsSL https://raw.githubusercontent.com/coollabsio/coolify-cli/main/scripts/install.sh | bash

# Add context
coolify context add myapp https://coolpanel.jackcwf.com '2|your-token-here'

# List apps and copy UUIDs
coolify app list --format json | jq '.[] | {name, uuid}'
```

You should have 3 UUIDs:
- Development app UUID
- Staging app UUID
- Production app UUID

## Step 2: Configure GitHub Secrets (3 min)

### Navigate to Secrets

1. Go to your repo: https://github.com/datalablife/jackcwf
2. Click **Settings → Secrets and variables → Actions**

### Add Repository Secrets

Click **New repository secret** for each:

| Name | Value |
|------|-------|
| `COOLIFY_API_TOKEN` | `2\|your-full-token-here` |
| `COOLIFY_URL` | `https://coolpanel.jackcwf.com` |

### Create Environments and Add Secrets

#### Create Development Environment

1. Go to **Settings → Environments**
2. Click **New environment**
3. Name: `development`
4. Click **Add secret**
5. Name: `COOLIFY_DEV_APP_UUID`, Value: `your-dev-uuid`

#### Create Staging Environment

1. Click **New environment**
2. Name: `staging`
3. Add secret:
   - Name: `COOLIFY_STAGING_APP_UUID`
   - Value: `your-staging-uuid`

#### Create Production Environment

1. Click **New environment**
2. Name: `production`
3. **Required reviewers**: Add yourself
4. **Wait timer**: 5 minutes (optional)
5. Add secret:
   - Name: `COOLIFY_PROD_APP_UUID`
   - Value: `your-prod-uuid`

## Step 3: Enable GitHub Actions (1 min)

1. Go to **Settings → Actions → General**
2. Set **Actions permissions**: "Allow all actions and reusable workflows"
3. Set **Workflow permissions**: "Read and write permissions"
4. Check "Allow GitHub Actions to create and approve pull requests"
5. Click **Save**

## Step 4: Configure Branch Protection (2 min)

### Protect Main Branch

1. Go to **Settings → Branches**
2. Click **Add rule**
3. Branch name pattern: `main`
4. Check:
   - ☑ Require a pull request before merging
     - Required approvals: 1
   - ☑ Require status checks to pass before merging
     - Search and add: `CI Summary`
   - ☑ Require conversation resolution before merging
5. Click **Create**

### Protect Develop Branch (Optional)

1. Click **Add rule**
2. Branch name pattern: `develop`
3. Check:
   - ☑ Require status checks to pass before merging
     - Search and add: `Pre-commit Summary`
4. Click **Create**

## Step 5: Enable Dependabot (1 min)

1. Go to **Settings → Code security and analysis**
2. Click **Enable** for:
   - Dependabot alerts
   - Dependabot security updates
   - Dependabot version updates

## Step 6: Test the Pipeline (1 min)

### Push Code to Trigger CI

```bash
# Make a small change
echo "# CI/CD Test" >> README.md

# Commit and push
git add README.md
git commit -m "test: trigger CI pipeline"
git push origin main
```

### Watch the Workflow

1. Go to **Actions** tab
2. You should see workflows running:
   - ✓ CI - Continuous Integration
   - ✓ Security Scanning
   - ✓ CD - Continuous Deployment (if on main)

### Check Deployment

If pushed to `main`:
- ✓ Staging deploys automatically
- ✓ Check: https://staging.jackcwf.com

## Verification Checklist

After setup, verify:

- [ ] ✓ Repository secrets configured
- [ ] ✓ Environment secrets configured
- [ ] ✓ GitHub Actions enabled
- [ ] ✓ Branch protection active
- [ ] ✓ Dependabot enabled
- [ ] ✓ CI workflow runs successfully
- [ ] ✓ CD workflow deploys to staging
- [ ] ✓ Health checks pass

## Next Steps

### Deploy to Production

1. Go to **Actions → CD workflow**
2. Click **Run workflow**
3. Select:
   - Branch: `main`
   - Environment: `production`
4. Click **Run workflow**
5. Review and approve the deployment
6. Monitor: https://jackcwf.com

### Create Your First Feature

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes
# ... code changes ...

# Commit and push
git add .
git commit -m "feat: add my feature"
git push origin feature/my-feature

# Create PR on GitHub
# Pre-commit checks run automatically
# Request review and merge
```

### Monitor Your Application

```bash
# Install monitoring script
cd scripts/deploy

# Run health checks
./health-check.sh https://jackcwf.com

# Run smoke tests
./smoke-tests.sh https://jackcwf.com

# Monitor metrics
./monitor-metrics.sh https://jackcwf.com
```

## Common Issues

### Issue: Coolify API 401 Unauthorized

**Solution**:
```bash
# Verify token format (must have | character)
echo "$COOLIFY_API_TOKEN"  # Should be: 2|xxxxx

# Re-add token with single quotes
coolify context add myapp https://coolpanel.jackcwf.com '2|xxxxx' --force
```

### Issue: Workflow Not Running

**Solution**:
1. Check **Actions → General** settings
2. Verify permissions are set correctly
3. Check if Actions are enabled for the repository

### Issue: Deployment Fails

**Solution**:
```bash
# Check Coolify app status
coolify app get <app-uuid>

# Check logs
coolify app logs <app-uuid> --tail 100

# Run manual health check
./scripts/deploy/health-check.sh https://your-url.com
```

### Issue: Environment Secret Not Found

**Solution**:
1. Go to **Settings → Environments → [environment name]**
2. Verify secret name matches exactly (case-sensitive)
3. Click secret to view (value is hidden but name shows)
4. Re-add if necessary

## Getting Help

- **Documentation**: `/mnt/d/工作区/云开发/working/docs/deployment/ci-cd.md`
- **Workflow Files**: `/mnt/d/工作区/云开发/working/.github/workflows/`
- **Scripts**: `/mnt/d/工作区/云开发/working/scripts/deploy/`
- **Support**: Create an issue on GitHub

## Summary

You've successfully set up:

✅ CI Pipeline - Automated testing and quality checks
✅ CD Pipeline - Multi-environment deployment
✅ Security Scanning - Vulnerability detection
✅ Branch Protection - Code review enforcement
✅ Dependabot - Automated dependency updates

**Total Time**: ~10 minutes
**Status**: Production Ready 🚀

---

**Next**: Read the [full CI/CD documentation](./ci-cd.md) for advanced features and troubleshooting.

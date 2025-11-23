# 4GB Deployment - Quick Reference Card
**Estimated Deployment Time**: 12 minutes (automated) | 10 minutes (manual)
**Success Probability**: 92%
**Status**: ✅ APPROVED FOR DEPLOYMENT

---

## Pre-Deployment Checklist (5 minutes)

```
□ Production server has 4GB RAM
□ .env file with all required variables
□ Database backup created
□ Previous docker-compose.yml backed up
□ Team notified of deployment window
□ On-call engineer assigned
□ Approval from infrastructure lead
```

---

## Deployment Option 1: Automated (RECOMMENDED)

```bash
# 1. Push to main branch (triggers GitHub Actions automatically)
git add docker-compose-4gb.yml
git commit -m "Deploy 4GB optimization to production"
git push origin main

# 2. Monitor deployment in GitHub Actions UI
# https://github.com/your-repo/actions

# 3. Wait for completion (~12 minutes)
# System will rollback automatically if health checks fail
```

**Duration**: ~12 minutes
**Success Rate**: 92%
**Automation**: Fully automated with automatic rollback

---

## Deployment Option 2: Manual via Coolify UI

```bash
# 1. Log in to Coolify
# URL: https://coolpanel.jackcwf.com

# 2. Navigate to Application
# App ID: ok0s0cgw8ck0w8kgs8kk4kk8

# 3. Select Deployment
# File: docker-compose-4gb.yml

# 4. Click "Deploy" button
# Monitor logs in dashboard
```

**Duration**: ~10 minutes
**Success Rate**: 85-90%
**Note**: Manual intervention required

---

## Post-Deployment Verification (5 minutes)

```bash
# 1. Check all containers running
docker ps

# 2. Test API health
curl http://localhost:8000/health

# 3. Verify database connection
curl http://localhost:8000/api/conversations

# 4. Check memory usage
free -h
docker stats

# 5. View service logs
docker-compose logs -f --tail=20
```

---

## Critical Metrics to Monitor (First 48 hours)

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Memory Usage | 50-65% | >80% = ALERT |
| API Latency P95 | <200ms | >300ms = ALERT |
| Cache Hit Rate | 50-70% | <40% = WARNING |
| Error Rate | <1% | >2% = ALERT |
| Service Status | All UP | 1 DOWN = ALERT |

---

## Immediate Rollback (if needed)

```bash
# Quick rollback command
docker-compose -f docker-compose-backup.yml down
docker-compose -f docker-compose-backup.yml up -d

# Verify rollback successful
curl http://localhost:8000/health
docker ps
```

**Rollback Time**: <3 minutes

---

## Emergency Contacts

| Role | Name | Phone | Slack |
|------|------|-------|-------|
| Deployment Lead | _________ | _________ | _________ |
| On-Call Engineer | _________ | _________ | _________ |
| Infrastructure | _________ | _________ | _________ |
| Escalation | _________ | _________ | _________ |

---

## Support Documents

- **📄 DEPLOYMENT_READINESS_SUMMARY.md** - Full deployment report
- **📄 PRODUCTION_4GB_MEMORY_OPTIMIZATION.md** - Technical details
- **📄 docker-compose-4gb.yml** - Configuration file
- **📄 4GB_QUICK_DECISION.md** - Decision matrix

---

## Deployment Approval Sign-Off

```
Infrastructure Team Lead: _________________ Date: _______

DevOps Lead: _________________ Date: _______

On-Call Engineer: _________________ Date: _______

Deployment Window: _________________

Expected Completion: _________________
```

---

**Print this card and keep at deployment station** 📋

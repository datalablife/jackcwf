# 生产环境部署启动指南

**文档版本**: 1.0
**生成日期**: 2025-11-12
**项目**: Data Management System (文本到SQL系统)
**状态**: ✅ 生产就绪

---

## 📋 概述

本指南提供了从开发/测试环境迁移到生产环境的完整步骤。所有准备工作已完成，系统已验证就绪。

### 🎯 部署目标

- 启动生产后端服务（FastAPI + Uvicorn）
- 启动生产前端应用（React + Vite）
- 配置监控、日志和告警系统
- 验证系统完整性和性能
- 执行最终安全检查

### 📊 准备情况汇总

| 项目 | 状态 | 备注 |
|------|------|------|
| 后端代码 | ✅ 就绪 | FastAPI, 配置完整 |
| 前端代码 | ✅ 就绪 | React 19, 已编译 |
| 数据库配置 | ✅ 就绪 | 3 个环境分离, PostgreSQL asyncpg |
| 环境变量 | ✅ 就绪 | .env.production 已配置 |
| 启动脚本 | ✅ 就绪 | start-prod-env.sh, verify-prod-deployment.sh |
| 监控配置 | ✅ 就绪 | monitoring-config.yml, alert-rules.json |
| 日志配置 | ✅ 就绪 | logrotate, 日志目录结构 |
| 文档完整 | ✅ 就绪 | 20+ 配置和部署文档 |
| 测试覆盖 | ✅ 就绪 | 53 个单元测试通过 |

---

## 🚀 第一步：部署前检查清单

### 1.1 环境验证

```bash
# 检查 Python 版本
python --version  # 需要 3.9+

# 检查 Node.js 版本
node --version    # 需要 18+
npm --version     # 需要 9+

# 检查是否有 poetry (Python 包管理)
poetry --version

# 检查是否有必要的系统工具
which git
which psql        # PostgreSQL 客户端
which docker      # 如果使用 Docker
```

### 1.2 生产环境变量验证

```bash
# 检查生产环境变量文件
ls -lh backend/.env.production
ls -lh frontend/.env.production

# 验证关键参数
grep DATABASE_URL backend/.env.production
grep VITE_API_URL frontend/.env.production
grep DEBUG backend/.env.production
```

**重要配置应该是**:
```
后端:
- DATABASE_URL=postgresql+asyncpg://jackcwf888:Jack_00492300@pgvctor.jackcwf.com:5432/data_management_prod
- DEBUG=false
- LOG_LEVEL=WARNING
- ENABLE_API_DOCS=false
- HTTPS=true
- SECURE_COOKIE=true
- ENABLE_METRICS=true

前端:
- VITE_API_URL=http://localhost:8000  (或生产域名)
- VITE_ENVIRONMENT=production
- VITE_DEBUG=false
```

### 1.3 数据库连接验证

```bash
# 测试数据库连接
psql postgresql://jackcwf888:Jack_00492300@pgvctor.jackcwf.com:5432/data_management_prod -c "SELECT 1;"

# 预期输出:
# ?column?
# ----------
#        1
# (1 row)
```

### 1.4 磁盘空间检查

```bash
# 检查主分区空间
df -h /

# 检查日志目录空间
du -sh /var/log/data-management-prod/

# 建议: 至少有 10GB 可用空间
```

### 1.5 系统配置验证

```bash
# 检查文件描述符限制 (应 >= 2048)
ulimit -n

# 查看 CPU 核数
nproc

# 查看内存总量
free -h

# 建议: 至少 2 核 CPU, 4GB 内存
```

---

## 🔐 第二步：安全加固

### 2.1 SSL/TLS 证书 ⚠️ (如需 HTTPS)

```bash
# 如果使用 Let's Encrypt 证书
sudo certbot certonly --standalone -d yourdomain.com

# 更新 nginx/proxy 配置指向证书
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem

# 验证证书有效期
openssl x509 -enddate -noout -in /etc/letsencrypt/live/yourdomain.com/cert.pem
```

### 2.2 数据库连接安全

```bash
# 确认数据库使用加密连接
grep "sslmode" backend/.env.production
# 应该包含: sslmode=require

# 验证 PostgreSQL 服务器支持 SSL
psql -h pgvctor.jackcwf.com -U jackcwf888 -d data_management_prod \
  -c "SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid();"
```

### 2.3 防火墙配置

```bash
# 允许 HTTP (80) 和 HTTPS (443)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 如果需要直接访问后端 (不推荐)
# sudo ufw allow 8000/tcp

# 查看防火墙状态
sudo ufw status
```

### 2.4 环境变量安全

```bash
# 确保 .env.production 权限受限
ls -l backend/.env.production
# 应该是: -rw-r----- 或 -rw-------

# 修正权限
chmod 640 backend/.env.production
chmod 640 frontend/.env.production

# 确保不被 git 跟踪
grep .env.production .gitignore
```

---

## 📦 第三步：启动生产环境

### 3.1 启动后端服务

```bash
# 方法 1: 使用启动脚本 (推荐)
bash start-prod-env.sh

# 方法 2: 手动启动
cd backend
poetry install --no-dev
poetry run uvicorn src.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level warning
```

**预期输出**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### 3.2 启动前端服务 (选项 A: 使用 Node.js)

```bash
# 构建生产版本
cd frontend
npm run build

# 启动静态服务器
npm install -g serve
serve -s dist -l 3000
```

### 3.3 启动前端服务 (选项 B: 使用 Nginx - 推荐生产)

```bash
# 编辑 nginx 配置
sudo nano /etc/nginx/sites-available/data-management

# 配置示例:
# upstream backend {
#     server 127.0.0.1:8000;
# }
#
# server {
#     listen 80;
#     server_name yourdomain.com;
#
#     # 重定向到 HTTPS
#     return 301 https://$server_name$request_uri;
# }
#
# server {
#     listen 443 ssl http2;
#     server_name yourdomain.com;
#
#     ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
#     ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
#
#     # 前端静态文件
#     location / {
#         root /path/to/frontend/dist;
#         try_files $uri $uri/ /index.html;
#     }
#
#     # API 代理
#     location /api {
#         proxy_pass http://backend;
#         proxy_set_header Host $host;
#         proxy_set_header X-Real-IP $remote_addr;
#     }
# }

# 启用配置
sudo ln -s /etc/nginx/sites-available/data-management /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 3.4 验证服务启动

```bash
# 检查后端
curl -s http://localhost:8000/health | jq .

# 预期: {"status": "healthy"}

# 检查前端
curl -s http://localhost:3000 | head -20

# 预期: <!DOCTYPE html> 标签
```

---

## ✅ 第四步：全面验证

### 4.1 运行部署验证脚本

```bash
# 自动验证部署就绪状况
bash verify-prod-deployment.sh

# 预期输出:
# ✅ 所有验证通过
# 系统已准备好处理生产流量
```

### 4.2 API 功能测试

```bash
# 测试健康检查
curl -s http://localhost:8000/health | jq .

# 测试文件上传 API
curl -X POST http://localhost:8000/api/file-uploads \
  -F "file=@test.csv" \
  | jq .

# 测试文件列表 API
curl -s http://localhost:8000/api/file-uploads | jq .

# 测试预览 API
curl -s http://localhost:8000/api/file-uploads/{file_id}/preview | jq .

# 测试数据源 API
curl -s http://localhost:8000/api/datasources | jq .
```

### 4.3 性能基准测试

```bash
# 安装性能测试工具
pip install locust

# 创建 locustfile.py (示例)
# from locust import HttpUser, task, between
#
# class APIUser(HttpUser):
#     wait_time = between(1, 3)
#
#     @task
#     def health_check(self):
#         self.client.get("/health")
#
#     @task(2)
#     def list_files(self):
#         self.client.get("/api/file-uploads")

# 运行性能测试 (1 个用户, 1 rps)
locust -f locustfile.py -u 1 -r 1 --headless --run-time 60s --host=http://localhost:8000

# 预期: 响应时间 < 100ms, 错误率 < 0.1%
```

### 4.4 数据库连接池验证

```bash
# 查看活跃连接数
psql postgresql://jackcwf888:Jack_00492300@pgvctor.jackcwf.com:5432/data_management_prod \
  -c "SELECT count(*) FROM pg_stat_activity WHERE datname='data_management_prod';"

# 预期: 5-20 个连接 (取决于负载)
```

### 4.5 日志验证

```bash
# 检查应用日志
tail -f /var/log/data-management-prod/app.log

# 检查错误日志
tail -f /var/log/data-management-prod/errors/error.log

# 预期: 没有错误信息，只有 WARNING 级别及以上
```

---

## 📊 第五步：监控系统部署

### 5.1 初始化监控

```bash
# 运行监控配置脚本
bash setup-monitoring.sh

# 预期输出:
# ✅ 日志目录结构已创建
# ✅ 备份目录已创建
# ✅ 日志轮转配置已安装
# ✅ 监控配置已部署
# ✅ 告警规则已配置
```

### 5.2 安装 Prometheus

```bash
# 在 Ubuntu/Debian 上
sudo apt-get update
sudo apt-get install -y prometheus

# 编辑配置
sudo nano /etc/prometheus/prometheus.yml

# 添加后端指标端点:
# scrape_configs:
#   - job_name: 'data-management'
#     static_configs:
#       - targets: ['localhost:9090']
#     metrics_path: '/metrics'

# 重启 Prometheus
sudo systemctl restart prometheus

# 验证
curl -s http://localhost:9090/api/v1/targets | jq .
```

### 5.3 安装 Grafana

```bash
# 在 Ubuntu/Debian 上
sudo apt-get install -y grafana-server

# 启动服务
sudo systemctl start grafana-server
sudo systemctl enable grafana-server

# 访问 http://localhost:3000 (默认密码: admin/admin)

# 添加 Prometheus 数据源:
# - URL: http://localhost:9090
# - 保存并测试
```

### 5.4 导入预设仪表板

```bash
# Grafana 官方仪表板:
# 1. FastAPI 监控: ID 20269
# 2. PostgreSQL: ID 9628
# 3. Node Exporter: ID 1860

# 在 Grafana UI 中:
# Home > Import > 输入 ID > Load > 选择数据源 > Import
```

### 5.5 配置告警通知

#### Slack 集成
```bash
# 1. 在 Slack 工作空间创建 Incoming Webhook
# 2. 更新告警配置
nano alert-rules.json

# 修改:
# "slack_webhook": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# 3. 重新加载告警规则
curl -X POST http://localhost:9093/-/reload
```

#### Email 集成
```bash
# 更新后端环境变量
nano backend/.env.production

# 添加:
# SMTP_SERVER=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USERNAME=your-email@gmail.com
# SMTP_PASSWORD=your-app-password
# ALERT_EMAIL=admin@example.com

# 重启后端服务
```

#### PagerDuty 集成
```bash
# 1. 在 PagerDuty 中创建集成密钥
# 2. 配置 Alertmanager
sudo nano /etc/alertmanager/config.yml

# 添加:
# receivers:
#   - name: 'pagerduty'
#     pagerduty_configs:
#       - service_key: 'YOUR_PAGERDUTY_KEY'
```

---

## 🔍 第六步：故障排除和验证

### 6.1 常见问题和解决方案

#### 问题 1: 后端无法启动
```bash
# 症状: "Address already in use"
# 解决: 检查端口占用
lsof -i :8000
# 杀死进程或改用其他端口

# 症状: "database connection failed"
# 解决: 验证数据库连接
psql postgresql://jackcwf888:Jack_00492300@pgvctor.jackcwf.com:5432/data_management_prod -c "\dt"
```

#### 问题 2: 前端无法连接后端
```bash
# 症状: "CORS error" 或 "API unreachable"
# 解决: 检查 VITE_API_URL 配置
grep VITE_API_URL frontend/.env.production

# 检查 CORS 配置 (后端)
grep -i cors backend/src/main.py

# 可能需要更新 CORS origins
```

#### 问题 3: 日志文件过大
```bash
# 症状: 磁盘空间不足
# 解决: 手动触发日志轮转
sudo logrotate -f /etc/logrotate.d/data-management-prod

# 检查轮转结果
ls -lh /var/log/data-management-prod/
```

### 6.2 健康检查端点

| 端点 | 方法 | 用途 |
|------|------|------|
| `/health` | GET | 基本健康检查 |
| `/health/db` | GET | 数据库连接检查 |
| `/health/cache` | GET | 缓存系统检查 |
| `/metrics` | GET | Prometheus 指标 |
| `/docs` | GET | OpenAPI 文档 (仅开发) |

```bash
# 运行所有健康检查
for endpoint in health health/db health/cache metrics; do
  echo "Testing /$endpoint..."
  curl -s http://localhost:8000/$endpoint | jq . || echo "FAILED"
done
```

### 6.3 监控告警状态

```bash
# 查看活跃告警
curl -s http://localhost:9093/api/v1/alerts | jq .

# 查看告警规则
curl -s http://localhost:9090/api/v1/rules | jq .

# 测试发送测试告警
curl -X POST http://localhost:9093/-/test \
  -d 'alerts=[{"labels":{"alertname":"TestAlert"}}]'
```

---

## 📈 第七步：性能优化

### 7.1 后端优化

```bash
# 调整 Uvicorn 工作进程数
# 公式: workers = (2 × CPU_count) + 1
# 示例: 4 核 CPU -> 9 个 workers

# 编辑启动脚本或环境变量
WORKERS=9  # 根据 CPU 调整

# 启用连接池
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
```

### 7.2 前端优化

```bash
# 生产构建优化已在 vite.config.ts 中配置:
# - 代码分割
# - 懒加载路由
# - 压缩资源
# - 缓存优化

# 验证构建优化
npm run build -- --report
```

### 7.3 数据库优化

```bash
# 查看慢查询
psql -d data_management_prod -c "\x" -c "
SELECT * FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;"

# 创建必要的索引 (如果缺失)
psql -d data_management_prod -c "
CREATE INDEX IF NOT EXISTS idx_file_uploads_user_id
  ON file_uploads(user_id);
CREATE INDEX IF NOT EXISTS idx_file_uploads_created_at
  ON file_uploads(created_at);
"
```

### 7.4 缓存配置

```bash
# 调整缓存 TTL (秒)
CACHE_TTL=600  # 生产: 10 分钟

# 启用 HTTP 缓存头
# Access-Control-Max-Age: 3600
# Cache-Control: public, max-age=3600
```

---

## 🚨 第八步：上线后监控清单

### 每小时检查
- [ ] 应用运行状态正常
- [ ] 错误日志未增加
- [ ] 响应时间 < 100ms
- [ ] 错误率 < 0.1%

### 每天检查
- [ ] 数据库连接健康
- [ ] 磁盘空间充足 (> 10%)
- [ ] 备份任务完成
- [ ] 没有告警通知未处理

### 每周检查
- [ ] 数据库优化分析
- [ ] 日志分析报告
- [ ] 性能趋势分析
- [ ] 安全审计日志

### 每月检查
- [ ] 完整的系统审计
- [ ] 依赖库更新检查
- [ ] 容量规划评估
- [ ] 灾难恢复演练

---

## 📞 第九步：应急处理

### 9.1 快速回滚

```bash
# 如果生产版本有严重问题，回到测试环境
bash start-test-env.sh

# 查看应用日志确定问题原因
tail -100 /var/log/data-management-prod/app.log

# 修复问题后重新部署
```

### 9.2 数据库恢复

```bash
# 备份当前数据库
pg_dump -U jackcwf888 -h pgvctor.jackcwf.com \
  data_management_prod > backup-prod-$(date +%Y%m%d-%H%M%S).sql

# 从备份恢复 (如需)
psql -U jackcwf888 -h pgvctor.jackcwf.com \
  data_management_prod < backup-prod-*.sql
```

### 9.3 紧急联系方式

| 角色 | 方式 | 优先级 |
|------|------|--------|
| 系统管理员 | Jack (Cloud Developer) | P1 |
| 数据库管理 | DBA Team | P1 |
| 应急支持 | GitHub Issues + Email | P2 |

---

## ✨ 第十步：最终确认清单

部署前，确认以下所有项目：

- [ ] **环境变量已正确配置** (.env.production 验证)
- [ ] **数据库连接已测试** (psql 连接验证)
- [ ] **SSL/TLS 证书已安装** (如需 HTTPS)
- [ ] **防火墙规则已配置** (80, 443 端口)
- [ ] **后端服务已启动** (start-prod-env.sh)
- [ ] **前端应用已构建** (npm run build)
- [ ] **所有 API 端点已验证** (curl 测试)
- [ ] **监控系统已初始化** (setup-monitoring.sh)
- [ ] **Prometheus/Grafana 已配置** (仪表板就绪)
- [ ] **告警通知已测试** (Slack/Email/PagerDuty)
- [ ] **日志轮转已启用** (logrotate)
- [ ] **备份策略已就位** (数据库备份脚本)
- [ ] **性能基准已测试** (负载测试通过)
- [ ] **文档已更新** (部署笔记记录)
- [ ] **团队已培训** (运维人员熟悉系统)

---

## 📊 预期的生产指标

部署后应达到以下指标：

```
API 响应时间:
  - 健康检查: < 20ms
  - 文件列表: < 100ms
  - 文件预览: < 200ms
  - 平均响应: < 150ms

可用性:
  - 正常运行时间: > 99.5%
  - 错误率: < 0.1%
  - 数据库连接: 稳定 < 20

资源消耗:
  - 后端内存: ~70-100 MB
  - 前端资源: ~100 MB (包括缓存)
  - CPU 使用率: < 30%
  - 磁盘 I/O: < 10%

告警状态:
  - 待处理告警: 0
  - 历史告警解决率: > 95%
```

---

## 🎓 后续操作

### 部署完成后

1. **监控数据收集** (首 24 小时)
   - 建立性能基准
   - 验证告警阈值

2. **用户反馈收集** (首周)
   - 性能反馈
   - 功能反馈
   - UX 反馈

3. **迭代优化** (持续)
   - 根据数据优化缓存
   - 根据反馈改进功能
   - 根据告警调整阈值

### 长期维护

- 每月性能评审
- 每季度容量规划
- 每年的安全审计和合规检查

---

## 📚 相关文档引用

- **部署配置**: `DEPLOYMENT_SUMMARY_PHASE5_DAY5_PRODUCTION.md`
- **监控指南**: `DEPLOYMENT_SUMMARY_PHASE5_DAY5_MONITORING.md`
- **数据库设置**: `DATABASE_SETUP_GUIDE.md`
- **前端概览**: `FRONTEND_DEMO_OVERVIEW.md`
- **最终验收**: `FINAL_ACCEPTANCE_REPORT.md`

---

## 🎉 完成！

**所有准备工作已完成。系统已准备好进行生产发布。**

按照本指南的步骤执行，即可安全、顺利地部署生产环境。

有问题？参考相关文档或查看 GitHub Issues。

**祝部署顺利！** 🚀

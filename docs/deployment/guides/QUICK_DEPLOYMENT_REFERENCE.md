# 快速部署参考卡

**适用于**: 生产环境快速部署
**使用时机**: 已完成所有准备工作，需要快速执行部署
**估计时间**: 15-30 分钟

---

## 🚀 超快速部署流程 (5 步)

### 步骤 1: 验证环境 (2 分钟)

```bash
# 快速检查所有必要条件
echo "=== 环境检查 ===" && \
python --version && \
node --version && \
poetry --version && \
grep DATABASE_URL backend/.env.production | grep "data_management_prod" && \
echo "✅ 环境检查通过"
```

### 步骤 2: 启动后端 (1 分钟)

```bash
# 一键启动生产后端
bash start-prod-env.sh
# 等待 "Application startup complete" 消息
```

### 步骤 3: 启动前端 (2 分钟)

```bash
# 构建并启动前端
cd frontend && npm run build && npm install -g serve && serve -s dist -l 3000 &
cd ..
```

### 步骤 4: 验证启动 (1 分钟)

```bash
# 验证所有服务就绪
curl -s http://localhost:8000/health | jq .status && \
curl -s http://localhost:3000 | grep "<!DOCTYPE" > /dev/null && \
echo "✅ 所有服务已启动"
```

### 步骤 5: 初始化监控 (1 分钟)

```bash
# 配置监控和日志
bash setup-monitoring.sh
echo "✅ 监控系统已初始化"
```

---

## 🔑 关键配置一览

### 数据库连接
```
主机: pgvctor.jackcwf.com
用户: jackcwf888
数据库: data_management_prod
驱动: postgresql+asyncpg
```

### 服务端口
```
后端 API:      localhost:8000
前端应用:      localhost:3000
Prometheus:    localhost:9090 (可选)
Grafana:       localhost:3000 (如安装)
```

### 关键文件位置
```
后端配置:      backend/.env.production
前端配置:      frontend/.env.production
日志目录:      /var/log/data-management-prod/
监控配置:      /etc/data-management-prod/
```

---

## ⚡ 常用命令速查

| 任务 | 命令 |
|------|------|
| 启动后端 | `bash start-prod-env.sh` |
| 启动前端 | `cd frontend && npm run build && serve -s dist -l 3000` |
| 验证部署 | `bash verify-prod-deployment.sh` |
| 初始化监控 | `bash setup-monitoring.sh` |
| 查看后端日志 | `tail -f /var/log/data-management-prod/app.log` |
| 查看错误日志 | `tail -f /var/log/data-management-prod/errors/error.log` |
| 测试 API | `curl -s http://localhost:8000/health \| jq .` |
| 健康检查 | `curl -s http://localhost:8000/health \| jq .` |
| 数据库检查 | `psql postgresql://... -c "SELECT 1;"` |
| 性能检查 | `curl -s http://localhost:8000/metrics` |

---

## 🆘 快速故障排除

| 症状 | 原因 | 解决 |
|------|------|------|
| "Address already in use" | 端口被占用 | `lsof -i :8000` 查看并杀死进程 |
| "Database connection failed" | DB 连接问题 | `psql postgresql://...` 测试连接 |
| "CORS error" | 跨域问题 | 检查 VITE_API_URL 配置 |
| "API timeout" | 响应慢 | 检查数据库负载: `psql ... -c "SELECT count(*) FROM pg_stat_activity"` |
| "Disk space low" | 日志过大 | `sudo logrotate -f /etc/logrotate.d/data-management-prod` |
| "High memory usage" | 内存泄漏 | 重启服务: `pkill -f uvicorn` |

---

## ✅ 部署验收清单 (打钩)

部署完成后逐项验证:

- [ ] 后端服务运行 (port 8000)
- [ ] 前端应用加载 (port 3000)
- [ ] API `/health` 响应正常
- [ ] 文件上传功能工作
- [ ] 文件预览功能工作
- [ ] 数据库连接正常
- [ ] 日志文件生成
- [ ] 监控指标可用
- [ ] 告警系统初始化
- [ ] 无错误日志

---

## 📊 部署后必检项 (首小时)

```bash
# 1. 检查进程状态
ps aux | grep uvicorn    # 后端
ps aux | grep "serve"    # 前端

# 2. 检查监听端口
netstat -tlnp | grep -E "8000|3000"

# 3. 检查日志输出
ls -lh /var/log/data-management-prod/

# 4. 检查数据库连接
curl http://localhost:8000/health/db | jq .

# 5. 检查系统资源
free -h && df -h / && top -b -n 1 | head -20
```

---

## 🎯 性能验证

```bash
# 快速性能测试
for i in {1..5}; do
  echo "Request $i:"
  time curl -s http://localhost:8000/api/file-uploads | jq '.[] | .id' | head -5
done

# 预期: 每次请求 < 200ms
```

---

## 🔔 监控命令

```bash
# 查看实时指标
watch 'curl -s http://localhost:8000/metrics | grep "^# TYPE"'

# 查看告警状态
curl -s http://localhost:9093/api/v1/alerts | jq '.data[] | .labels.alertname'

# 查看活跃连接
psql postgresql://... -c "SELECT count(*) as active_connections FROM pg_stat_activity WHERE datname='data_management_prod';"
```

---

## 📱 移动版本验证

```bash
# 测试响应式设计
curl -s http://localhost:3000 | grep -o "width=device-width"

# 应输出: width=device-width (表示支持移动)
```

---

## 🔐 安全性快速检查

```bash
# 检查 API 文档是否禁用 (生产应禁用)
curl -s http://localhost:8000/docs | head -1
# 应返回: 404 Not Found

# 检查 DEBUG 模式
grep "DEBUG=false" backend/.env.production
# 应找到: DEBUG=false

# 检查 HTTPS 配置
grep "HTTPS=true" backend/.env.production
# 应找到: HTTPS=true
```

---

## 💾 备份验证

```bash
# 创建部署时刻的数据库备份
pg_dump -U jackcwf888 -h pgvctor.jackcwf.com data_management_prod > \
  /var/backups/data-management-prod/backup-$(date +%Y%m%d-%H%M%S).sql

# 验证备份
ls -lh /var/backups/data-management-prod/
# 应显示: 最新备份文件
```

---

## 📞 需要帮助？

1. **查看详细指南**: `PRODUCTION_LAUNCH_GUIDE.md`
2. **查看部署文档**: `docs/deployment/DEPLOYMENT_SUMMARY_*.md`
3. **查看故障排除**: `PRODUCTION_LAUNCH_GUIDE.md` 第六步
4. **查看监控指南**: `DEPLOYMENT_SUMMARY_PHASE5_DAY5_MONITORING.md`

---

## 🚀 预期结果

成功部署后:

```
✅ 后端运行在 http://localhost:8000
✅ 前端运行在 http://localhost:3000
✅ API 响应时间 < 100ms
✅ 错误率 < 0.1%
✅ 监控系统就绪
✅ 日志系统就绪
✅ 告警系统就绪
✅ 准备接收生产流量
```

---

**祝部署顺利！** 🎉

最后更新: 2025-11-12

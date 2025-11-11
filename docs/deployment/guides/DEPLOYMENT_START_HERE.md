# 🚀 生产部署快速入门

**欢迎！** 本文件是您部署本项目到生产环境的起点。

**项目**: Data Management System (数据文件管理系统)
**状态**: ✅ 生产就绪
**最后更新**: 2025-11-12

---

## 📖 快速导航

根据您的需求选择相应的文档:

### 我是第一次接触本项目

👉 **开始这里**: [QUICK_DEPLOYMENT_REFERENCE.md](./QUICK_DEPLOYMENT_REFERENCE.md)
- ⏱️ 5 分钟快速了解
- 📋 关键配置一览
- ⚡ 常用命令速查
- 🆘 常见问题解决

### 我想了解部署的整个过程

👉 **读这个**: [PRODUCTION_LAUNCH_GUIDE.md](./PRODUCTION_LAUNCH_GUIDE.md)
- 📋 10 步完整流程
- 🔐 安全加固指南
- ✅ 详细验证清单
- 📊 预期性能指标

### 我需要了解系统的准备情况

👉 **查看**: [FINAL_DEPLOYMENT_READINESS_REPORT.md](./FINAL_DEPLOYMENT_READINESS_REPORT.md)
- 📈 完整的准备情况评估
- 🧪 测试覆盖情况
- 🛡️ 安全配置验证
- 💼 风险评估和缓解措施

### 我需要技术细节信息

👉 **查阅**:
- [FRONTEND_DEMO_OVERVIEW.md](./FRONTEND_DEMO_OVERVIEW.md) - 前端架构和页面设计
- [docs/guides/operations/DATABASE_SETUP_GUIDE.md](./docs/guides/operations/DATABASE_SETUP_GUIDE.md) - 数据库配置详解
- [docs/deployment/DEPLOYMENT_SUMMARY_PHASE5_DAY5_PRODUCTION.md](./docs/deployment/DEPLOYMENT_SUMMARY_PHASE5_DAY5_PRODUCTION.md) - 生产部署详解

### 我需要部署后进行验证

👉 **执行这个**:
```bash
bash verify-prod-system.sh
```

脚本会自动验证:
- ✅ 环境变量配置
- ✅ 服务状态
- ✅ 数据库连接
- ✅ API 端点
- ✅ 系统资源
- ✅ 监控配置
- ✅ 安全设置
- ✅ 备份配置

---

## ⚡ 超快速 5 步部署

如果您已有经验，只需 5 步快速启动:

### 1️⃣ 验证环境
```bash
python --version && node --version && poetry --version
```

### 2️⃣ 启动后端
```bash
bash start-prod-env.sh
# 等待 "Application startup complete"
```

### 3️⃣ 启动前端
```bash
cd frontend && npm run build && serve -s dist -l 3000 &
```

### 4️⃣ 快速验证
```bash
curl -s http://localhost:8000/health | jq .
curl -s http://localhost:3000 | grep "<!DOCTYPE"
```

### 5️⃣ 初始化监控
```bash
bash setup-monitoring.sh
```

✅ **完成！** 您的系统现已运行。

---

## 📚 完整文档清单

### 部署指南 (3 个)
| 文件 | 用途 | 阅读时间 |
|------|------|---------|
| [PRODUCTION_LAUNCH_GUIDE.md](./PRODUCTION_LAUNCH_GUIDE.md) | 完整 10 步部署指南 | 30 分钟 |
| [QUICK_DEPLOYMENT_REFERENCE.md](./QUICK_DEPLOYMENT_REFERENCE.md) | 快速参考卡 | 5 分钟 |
| [FINAL_DEPLOYMENT_READINESS_REPORT.md](./FINAL_DEPLOYMENT_READINESS_REPORT.md) | 完整准备情况评估 | 20 分钟 |

### 技术文档 (4 个)
| 文件 | 用途 | 位置 |
|------|------|------|
| [FRONTEND_DEMO_OVERVIEW.md](./FRONTEND_DEMO_OVERVIEW.md) | 前端架构和演示 | 项目根目录 |
| [DATABASE_SETUP_GUIDE.md](./docs/guides/operations/DATABASE_SETUP_GUIDE.md) | 数据库详细配置 | docs/guides/operations/ |
| [PERFORMANCE_SECURITY_GUIDE.md](./docs/guides/operations/PERFORMANCE_SECURITY_GUIDE.md) | 性能和安全指南 | docs/guides/operations/ |
| [START_HERE.md](./docs/guides/developer/START_HERE.md) | 开发快速入门 | docs/guides/developer/ |

### 阶段总结 (5 个)
| 文件 | 覆盖范围 | 位置 |
|------|---------|------|
| [DEPLOYMENT_SUMMARY_PHASE5_DAY3.md](./docs/deployment/DEPLOYMENT_SUMMARY_PHASE5_DAY3.md) | T083 开发环境 | docs/deployment/ |
| [DEPLOYMENT_SUMMARY_PHASE5_DAY4_TEST_ENV.md](./docs/deployment/DEPLOYMENT_SUMMARY_PHASE5_DAY4_TEST_ENV.md) | T084 测试环境 | docs/deployment/ |
| [DEPLOYMENT_SUMMARY_PHASE5_DAY5_PRODUCTION.md](./docs/deployment/DEPLOYMENT_SUMMARY_PHASE5_DAY5_PRODUCTION.md) | T085 生产环境 | docs/deployment/ |
| [DEPLOYMENT_SUMMARY_PHASE5_DAY5_MONITORING.md](./docs/deployment/DEPLOYMENT_SUMMARY_PHASE5_DAY5_MONITORING.md) | T086 监控系统 | docs/deployment/ |
| [SERVICE_STARTUP_TEST_REPORT.md](./docs/deployment/SERVICE_STARTUP_TEST_REPORT.md) | 启动验证报告 | docs/deployment/ |

### 验收报告 (2 个)
| 文件 | 内容 | 位置 |
|------|------|------|
| [FINAL_ACCEPTANCE_REPORT.md](./docs/deployment/FINAL_ACCEPTANCE_REPORT.md) | 完整验收报告 | docs/deployment/ |
| [PROJECT_COMPLETION_SUMMARY.txt](./docs/deployment/PROJECT_COMPLETION_SUMMARY.txt) | 项目完成总结 | docs/deployment/ |

### 部署脚本 (4 个)
| 脚本 | 功能 | 权限 |
|------|------|------|
| `start-prod-env.sh` | 启动生产后端 | ✅ 可执行 |
| `verify-prod-deployment.sh` | 部署前验证 | ✅ 可执行 |
| `setup-monitoring.sh` | 初始化监控 | ✅ 可执行 |
| `verify-prod-system.sh` | 部署后完整验证 | ✅ 可执行 |

### 配置文件 (6 个)
| 文件 | 环境 | 状态 |
|------|------|------|
| `backend/.env.production` | 后端生产 | ✅ 已配置 |
| `frontend/.env.production` | 前端生产 | ✅ 已配置 |
| `monitoring-config.yml` | 监控框架 | ✅ 已配置 |
| `alert-rules.json` | 告警规则 | ✅ 已配置 |
| `logrotate-config` | 日志轮转 | ✅ 已配置 |

---

## 🔑 关键信息速查

### 数据库连接信息
```
主机: pgvctor.jackcwf.com
用户: jackcwf888
数据库: data_management_prod
驱动: postgresql+asyncpg
```

### 服务端口
```
后端 API:      http://localhost:8000
前端应用:      http://localhost:3000
Prometheus:    http://localhost:9090 (可选)
Grafana:       http://localhost:3000 (如安装)
```

### 关键目录
```
日志:           /var/log/data-management-prod/
备份:           /var/backups/data-management-prod/
监控配置:       /etc/data-management-prod/
项目根目录:     当前目录
```

---

## ✅ 部署前检查清单

在启动部署前，请确认以下项目:

### 环境准备
- [ ] Python 3.9+ 已安装
- [ ] Node.js 18+ 已安装
- [ ] Poetry 已安装
- [ ] PostgreSQL 命令行工具已安装

### 配置准备
- [ ] `backend/.env.production` 已配置
- [ ] `frontend/.env.production` 已配置
- [ ] 数据库凭证已验证
- [ ] SSL/TLS 证书已准备 (如需 HTTPS)

### 系统准备
- [ ] 磁盘空间 > 10GB
- [ ] 内存 > 4GB
- [ ] CPU 核数 >= 2
- [ ] 防火墙已配置 (80, 443 端口)

### 备份准备
- [ ] 数据库备份目录已创建
- [ ] 备份脚本已准备
- [ ] 恢复计划已制定

---

## 🎯 典型部署流程

### 场景 1: 首次部署到生产环境

**推荐步骤**:
1. 阅读 [PRODUCTION_LAUNCH_GUIDE.md](./PRODUCTION_LAUNCH_GUIDE.md) 第 1-3 步
2. 执行 `bash verify-prod-deployment.sh`
3. 执行部署前检查清单
4. 按照指南的步骤启动服务
5. 执行 `bash verify-prod-system.sh` 验证

**预计时间**: 1-2 小时

### 场景 2: 已有旧版本，要更新升级

**推荐步骤**:
1. 创建当前环境的完整备份
2. 停止旧版本服务
3. 按照 [PRODUCTION_LAUNCH_GUIDE.md](./PRODUCTION_LAUNCH_GUIDE.md) 的步骤启动新版本
4. 运行全面验证测试
5. 监控 24 小时后确认正常

**预计时间**: 2-3 小时

### 场景 3: 紧急回滚

**如需快速回滚**:
```bash
# 1. 停止当前服务
pkill -f uvicorn
pkill -f serve

# 2. 恢复备份
psql ... < backup-prod-latest.sql

# 3. 启动旧版本或测试版本
bash start-test-env.sh

# 4. 立即通知团队和用户
```

---

## 🆘 需要帮助？

### 常见问题快速解答

**Q: 启动时报 "Address already in use"**
```bash
# A: 端口被占用，查找并杀死进程
lsof -i :8000
kill -9 <PID>
```

**Q: 数据库连接失败**
```bash
# A: 测试数据库连接
psql postgresql://jackcwf888:Jack_00492300@pgvctor.jackcwf.com:5432/data_management_prod -c "SELECT 1;"
```

**Q: 前端无法连接后端**
```bash
# A: 检查 VITE_API_URL 配置
grep VITE_API_URL frontend/.env.production
```

**Q: 服务启动很慢**
```bash
# A: 检查数据库和网络连接状况
curl -s http://localhost:8000/health/db | jq .
```

### 更详细的故障排除

查看以下文档的第 6 步 (故障排除和验证):
- [PRODUCTION_LAUNCH_GUIDE.md](./PRODUCTION_LAUNCH_GUIDE.md#第六步故障排除和验证)
- [QUICK_DEPLOYMENT_REFERENCE.md](./QUICK_DEPLOYMENT_REFERENCE.md#-快速故障排除)

### 获取技术支持

1. 检查相关文档的故障排除章节
2. 查看应用日志: `tail -f /var/log/data-management-prod/app.log`
3. 检查错误日志: `tail -f /var/log/data-management-prod/errors/error.log`
4. 创建 GitHub Issue 报告问题
5. 联系项目负责人 (Jack)

---

## 📊 预期结果

成功部署后，您应该看到:

```
✅ 后端服务运行在 http://localhost:8000
✅ 前端应用运行在 http://localhost:3000
✅ API /health 返回 {"status": "healthy"}
✅ 前端首页正常加载
✅ 所有 API 端点可访问
✅ 监控系统就绪
✅ 日志正常生成
✅ 没有错误消息
```

如果发现任何异常，请立即参考故障排除章节。

---

## 🎓 部署后步骤

### 立即 (部署完成后)
- [ ] 运行 `verify-prod-system.sh` 验证所有系统
- [ ] 查看应用日志确认没有错误
- [ ] 测试主要功能 (文件上传、预览等)
- [ ] 通知团队和利益相关者

### 首 24 小时
- [ ] 持续监控系统运行
- [ ] 收集性能基准数据
- [ ] 验证告警系统正常工作
- [ ] 收集用户反馈

### 首周
- [ ] 分析监控数据
- [ ] 进行性能优化
- [ ] 调整告警阈值
- [ ] 更新文档

### 持续 (长期)
- [ ] 每天检查日志和告警
- [ ] 每周进行备份验证
- [ ] 每月进行性能评估
- [ ] 每季度进行容量规划

---

## 📞 联系信息

**项目负责人**: Jack (Cloud Developer)
**项目状态**: ✅ Production Ready
**最后更新**: 2025-11-12

有问题或建议? 创建 GitHub Issue 或直接联系项目负责人。

---

## 🚀 准备好了吗？

选择您需要的文档开始:

1. **新手**: → [QUICK_DEPLOYMENT_REFERENCE.md](./QUICK_DEPLOYMENT_REFERENCE.md)
2. **详细步骤**: → [PRODUCTION_LAUNCH_GUIDE.md](./PRODUCTION_LAUNCH_GUIDE.md)
3. **完整评估**: → [FINAL_DEPLOYMENT_READINESS_REPORT.md](./FINAL_DEPLOYMENT_READINESS_REPORT.md)
4. **快速启动**: → 执行下方的 5 步部署

---

## ⚡ 立即开始 5 步部署

```bash
# 步骤 1: 验证环境
python --version && node --version && poetry --version

# 步骤 2: 启动后端
bash start-prod-env.sh

# 步骤 3: 启动前端
cd frontend && npm run build && serve -s dist -l 3000 &

# 步骤 4: 验证启动
curl -s http://localhost:8000/health | jq .
curl -s http://localhost:3000 | grep "<!DOCTYPE" && echo "✅ 前端就绪"

# 步骤 5: 初始化监控
bash setup-monitoring.sh
```

✅ **完成！您的系统现已运行！**

查看日志确认一切正常:
```bash
tail -f /var/log/data-management-prod/app.log
```

---

**祝部署顺利！** 🎉

*本文档由 Claude Code 自动生成*
*最后更新: 2025-11-12 UTC*

# 🚀 部署文件导航指南

**最后更新**: 2025-11-12
**状态**: ✅ 所有部署文件已整理到 docs/deployment/ 目录

---

## 📍 快速导航

所有部署相关的文件已从项目根目录迁移到 `docs/deployment/` 目录，以保持项目结构的整洁和有序。

### 🎯 我应该先读哪个文件？

**👉 从这里开始**: `docs/deployment/guides/DEPLOYMENT_START_HERE.md`

这是部署的入门指南，包含：
- 快速导航和文件索引
- 5 步快速部署流程
- 常见问题快速解答

---

## 📂 目录结构

```
docs/deployment/
│
├── guides/                          📘 部署启动文档 (6 个)
│   ├── DEPLOYMENT_START_HERE.md              ⭐ 首先阅读
│   ├── PRODUCTION_LAUNCH_GUIDE.md            完整 10 步指南
│   ├── QUICK_DEPLOYMENT_REFERENCE.md         快速参考卡
│   ├── FINAL_DEPLOYMENT_READINESS_REPORT.md  完整准备情况评估
│   ├── DEPLOYMENT_FILES_INVENTORY.md         文件清单索引
│   └── DEPLOYMENT_TOOLS_SUMMARY.md           工具和脚本总结
│
├── scripts/                         🚀 部署执行脚本 (11 个)
│   ├── verify-prod-system.sh                 部署后 10 项完整验证 ✨
│   ├── deployment-checklist.sh               交互式 6 阶段引导 ✨
│   ├── start-prod-env.sh                     启动生产后端
│   ├── start-test-env.sh                     启动测试环境
│   ├── verify-prod-deployment.sh             部署前 7 步验证
│   ├── setup-monitoring.sh                   初始化监控系统
│   ├── run-integration-tests.sh              运行集成测试
│   ├── performance-security-test.sh          性能和安全测试
│   ├── start.sh                              快速启动脚本
│   ├── diagnose_granian.sh                   诊断脚本
│   └── test_postgres_connection.py           数据库连接测试
│
├── config/                          ⚙️ 配置文件 (3 个)
│   ├── alert-rules.json                      15 条告警规则
│   ├── monitoring-config.yml                 监控框架配置
│   └── logrotate-config                      日志轮转配置
│
└── reports/                         📊 报告和总结 (1 个)
    └── DEPLOYMENT_COMPLETION_SUMMARY.txt     部署完成总结
```

---

## 🔍 按使用场景快速找文件

### 场景 1: 我是第一次部署

**推荐阅读顺序**:
1. `docs/deployment/guides/DEPLOYMENT_START_HERE.md` (5 分钟)
2. `docs/deployment/guides/PRODUCTION_LAUNCH_GUIDE.md` (30 分钟)
3. 执行: `bash docs/deployment/scripts/verify-prod-deployment.sh`
4. 按照指南步骤进行部署
5. 执行: `bash docs/deployment/scripts/verify-prod-system.sh`

### 场景 2: 我有部署经验，想快速启动

**快速参考**:
1. `docs/deployment/guides/QUICK_DEPLOYMENT_REFERENCE.md`
2. 执行 5 步快速部署流程
3. 运行验证脚本

### 场景 3: 我需要交互式指导

**执行**:
```bash
bash docs/deployment/scripts/deployment-checklist.sh
```
脚本会一步步引导您完成 6 个阶段的部署。

### 场景 4: 我需要了解系统准备情况

**查看**:
- `docs/deployment/guides/FINAL_DEPLOYMENT_READINESS_REPORT.md` - 完整评估
- `docs/deployment/reports/DEPLOYMENT_COMPLETION_SUMMARY.txt` - 完成总结

### 场景 5: 我需要查看所有可用文件

**查看**:
- `docs/deployment/guides/DEPLOYMENT_FILES_INVENTORY.md` - 完整文件清单

---

## 📋 脚本使用指南

### 部署前验证

```bash
# 执行部署前 7 步检查
bash docs/deployment/scripts/verify-prod-deployment.sh
```

### 启动服务

```bash
# 启动生产环境
bash docs/deployment/scripts/start-prod-env.sh

# 启动测试环境
bash docs/deployment/scripts/start-test-env.sh
```

### 部署后验证

```bash
# 执行部署后 10 项完整系统验证
bash docs/deployment/scripts/verify-prod-system.sh
```

### 初始化监控

```bash
# 配置监控、日志和告警系统
bash docs/deployment/scripts/setup-monitoring.sh
```

### 交互式部署清单

```bash
# 按步骤引导式部署 (推荐首次用户)
bash docs/deployment/scripts/deployment-checklist.sh
```

### 测试

```bash
# 运行集成测试
bash docs/deployment/scripts/run-integration-tests.sh

# 运行性能和安全测试
bash docs/deployment/scripts/performance-security-test.sh

# 测试数据库连接
python docs/deployment/scripts/test_postgres_connection.py
```

---

## ⚙️ 配置文件说明

### alert-rules.json
包含 15 条监控告警规则，覆盖：
- 响应时间告警 (3 条)
- 错误率告警 (2 条)
- 资源使用告警 (4 条)
- 数据库告警 (3 条)
- 安全告警 (2 条)
- 其他告警 (1 条)

**位置**: `docs/deployment/config/alert-rules.json`

### monitoring-config.yml
包含监控框架配置和 Grafana 仪表板定义。

**位置**: `docs/deployment/config/monitoring-config.yml`

### logrotate-config
配置日志自动轮转和压缩。

**位置**: `docs/deployment/config/logrotate-config`

---

## 🔗 关键信息速查

### 数据库连接
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

### 重要目录
```
日志:           /var/log/data-management-prod/
备份:           /var/backups/data-management-prod/
监控配置:       /etc/data-management-prod/
部署文件:       docs/deployment/
```

---

## ✅ 文件完整性检查

所有部署文件已迁移到 `docs/deployment/` 目录：

```bash
# 验证所有文件都在正确位置
ls -R docs/deployment/

# 验证脚本权限
ls -l docs/deployment/scripts/*.sh
```

---

## 🚀 快速开始

最快的方式是阅读快速入门指南，然后执行交互式部署清单：

```bash
# 1. 阅读快速入门 (5 分钟)
cat docs/deployment/guides/DEPLOYMENT_START_HERE.md

# 2. 执行交互式部署 (1-2 小时)
bash docs/deployment/scripts/deployment-checklist.sh

# 3. 完成！
```

---

## 📚 完整文档列表

### 部署启动文档
| 文件 | 用途 | 时间 |
|------|------|------|
| DEPLOYMENT_START_HERE.md | 入门指南和导航 | 5 分钟 |
| PRODUCTION_LAUNCH_GUIDE.md | 完整 10 步部署指南 | 30 分钟 |
| QUICK_DEPLOYMENT_REFERENCE.md | 快速参考和命令 | 5 分钟 |
| FINAL_DEPLOYMENT_READINESS_REPORT.md | 完整准备情况评估 | 20 分钟 |
| DEPLOYMENT_FILES_INVENTORY.md | 文件清单和索引 | 10 分钟 |
| DEPLOYMENT_TOOLS_SUMMARY.md | 工具和脚本说明 | 10 分钟 |

### 脚本文件
| 脚本 | 功能 |
|------|------|
| verify-prod-system.sh | 部署后 10 项完整验证 |
| deployment-checklist.sh | 交互式 6 阶段引导 |
| start-prod-env.sh | 启动生产后端 |
| verify-prod-deployment.sh | 部署前 7 步验证 |
| setup-monitoring.sh | 初始化监控系统 |
| 其他脚本 | 测试和诊断功能 |

---

## 🎯 建议的部署流程

### 对于首次部署的用户

```
Step 1: 阅读 DEPLOYMENT_START_HERE.md (5 分钟)
        └─ 了解全局和快速导航

Step 2: 选择部署方式:
        ├─ 快速: QUICK_DEPLOYMENT_REFERENCE.md
        ├─ 详细: PRODUCTION_LAUNCH_GUIDE.md
        └─ 指导: deployment-checklist.sh (推荐)

Step 3: 执行部署前验证
        └─ bash docs/deployment/scripts/verify-prod-deployment.sh

Step 4: 进行部署
        └─ 按照选定的文档步骤

Step 5: 执行部署后验证
        └─ bash docs/deployment/scripts/verify-prod-system.sh

总耗时: 2-3 小时
```

---

## 💡 常见问题

**Q: 脚本不在项目根目录了，怎样运行？**

A: 所有脚本已迁移到 `docs/deployment/scripts/` 目录。需要时从这个新位置运行：
```bash
bash docs/deployment/scripts/verify-prod-system.sh
```

**Q: 配置文件在哪？**

A: 配置文件已迁移到 `docs/deployment/config/` 目录：
- `alert-rules.json`
- `monitoring-config.yml`
- `logrotate-config`

**Q: 我需要快速参考**

A: 查看 `docs/deployment/guides/QUICK_DEPLOYMENT_REFERENCE.md` 或 `DEPLOYMENT_FILES_INVENTORY.md`

**Q: 我需要了解系统状态**

A: 查看 `docs/deployment/reports/DEPLOYMENT_COMPLETION_SUMMARY.txt`

---

## ✨ 项目整理成果

✅ **部署相关文件已完全整理**
- 6 个部署启动文档 → `guides/`
- 11 个部署脚本 → `scripts/`
- 3 个配置文件 → `config/`
- 1 个总结文档 → `reports/`

✅ **项目根目录现已整洁**
- 移除了所有部署相关文件
- 仅保留必要的源代码和项目文件
- 项目结构更加清晰和专业

---

## 🎓 后续开发指南

现在项目根目录已整理干净，您可以：

1. **继续功能开发** - 专注于核心业务逻辑
2. **保持根目录整洁** - 新的部署相关文件直接放入 `docs/deployment/`
3. **方便查阅** - 所有部署文件都有清晰的组织结构
4. **版本管理** - 项目的专业性和可维护性都得到提高

---

**从这里开始部署**: 👉 `docs/deployment/guides/DEPLOYMENT_START_HERE.md`

**项目整理完成！** ✨

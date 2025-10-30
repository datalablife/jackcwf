# Coolify 配置指南 - Reflex 应用部署

本文档提供在 Coolify 面板中配置 Reflex 0.8.16 应用的详细步骤。

## 前提条件

- ✓ Coolify 实例已运行（https://coolpanel.jackcwf.com）
- ✓ Git 仓库已连接到 Coolify
- ✓ 本地已更新 `nixpacks.toml`
- ✓ 已提交并推送代码到远程仓库

## 步骤 1: 应用基本设置

### 1.1 进入应用设置

1. 登录 Coolify 面板：https://coolpanel.jackcwf.com
2. 导航到项目：`datalablife/jackcwf`
3. 选择应用：`mg8c40oowo80o08o0gsw0gwc`
4. 点击 "Settings" 选项卡

### 1.2 构建配置

| 设置项 | 值 | 说明 |
|--------|-----|------|
| **Build Pack** | Nixpacks | 使用 Nixpacks 自动构建 |
| **Nixpacks File** | `nixpacks.toml` | 使用项目根目录的配置文件 |
| **Base Directory** | `/` | 项目根目录 |
| **Publish Directory** | （留空） | 不需要 |

### 1.3 Git 配置

| 设置项 | 值 |
|--------|-----|
| **Branch** | `main` |
| **Auto Deploy** | ✓ 启用（推荐） |

## 步骤 2: 环境变量配置

进入 "Environment Variables" 选项卡，添加以下变量：

### 必需的环境变量

```bash
# Python 配置
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1

# Reflex 配置
REFLEX_ENV=production
FRONTEND_PORT=3000
BACKEND_PORT=8000
```

### 可选的环境变量（调试用）

```bash
# 仅在调试时启用
REFLEX_LOGLEVEL=debug
```

**添加步骤**:
1. 点击 "+ Add" 按钮
2. 输入 Key 和 Value
3. 点击 "Save"
4. 重复直到所有变量添加完成

## 步骤 3: 端口配置

进入 "Ports" 或 "Network" 设置：

### 端口映射

| 内部端口 | 外部端口 | 协议 | 用途 |
|---------|---------|------|------|
| 3000 | 3000 | HTTP | Reflex 前端 |
| 8000 | 8000 | HTTP | Reflex 后端 API |

**配置步骤**:
1. 点击 "+ Add Port"
2. 输入内部端口：`3000`
3. 选择协议：`HTTP`
4. 点击 "Save"
5. 重复添加端口 `8000`

### FQDN（完全限定域名）

如果需要自定义域名：

```
https://yourapp.jackcwf.com
```

- 主端口：`3000`（前端）
- 确保 DNS 记录指向 Coolify 服务器

## 步骤 4: 健康检查配置

**关键**: 这是解决部署失败的核心配置！

进入 "Health Check" 设置：

### 推荐配置

| 设置项 | 值 | 说明 |
|--------|-----|------|
| **Enabled** | ✓ 启用 | 必须启用健康检查 |
| **Path** | `/` | 检查前端根路径 |
| **Port** | `3000` | 前端端口 |
| **Initial Delay** | `60` 秒 | **关键**：等待应用完全启动 |
| **Interval** | `30` 秒 | 检查间隔 |
| **Timeout** | `10` 秒 | 单次检查超时 |
| **Retries** | `5` | 失败重试次数 |

**为什么 Initial Delay 设置为 60 秒？**

Reflex 应用启动流程：
```
1. Python 虚拟环境激活       →  2-5 秒
2. 依赖模块导入              →  5-10 秒
3. Reflex 框架初始化         →  5-10 秒
4. 前端 React 编译/启动      →  15-30 秒
5. 后端 FastAPI 启动         →  5-10 秒
6. WebSocket 连接建立        →  2-5 秒
───────────────────────────────────────
总计                         →  34-70 秒
```

因此，60 秒是安全的初始延迟时间。

## 步骤 5: 资源限制配置

进入 "Resources" 设置：

### 推荐配置

| 资源 | 最小值 | 推荐值 | 说明 |
|------|--------|--------|------|
| **Memory** | 512 MB | 1 GB | Reflex 需要足够内存编译前端 |
| **CPU** | 0.5 core | 1 core | 编译时 CPU 密集 |
| **Swap** | 512 MB | 1 GB | 防止内存不足 |

**配置步骤**:
1. 勾选 "Limit Resources"
2. 设置 Memory Limit：`1024` (MB)
3. 设置 CPU Limit：`1.0`
4. 点击 "Save"

## 步骤 6: 重启策略

进入 "Advanced" 或 "Restart Policy" 设置：

| 设置项 | 值 |
|--------|-----|
| **Restart Policy** | `unless-stopped` |
| **Max Restart Attempts** | `3` |

## 步骤 7: 部署应用

### 7.1 触发部署

有两种方式触发部署：

**方式 1: 手动部署**
1. 进入应用详情页
2. 点击右上角 "Deploy" 按钮
3. 等待构建完成

**方式 2: Git Push（推荐）**
```bash
# 在本地仓库
git add .
git commit -m "fix: update Nixpacks config for Coolify deployment"
git push origin main

# Coolify 自动检测并部署
```

### 7.2 监控部署进度

1. 进入 "Deployments" 选项卡
2. 查看最新部署状态
3. 点击部署查看详细日志

### 7.3 查看构建日志

实时查看构建过程：

```
Building application...
[nixpacks] Setup phase...
[nixpacks] Install phase...
[nixpacks] Build phase...
  → Initializing Reflex...
  → Exporting frontend...
[nixpacks] Start phase...
```

### 7.4 查看运行日志

部署成功后，查看应用日志：

1. 进入 "Logs" 选项卡
2. 选择 "Application Logs"
3. 应该看到类似输出：

```
==================================================
Starting Reflex 0.8.16 Application
==================================================

Environment Information:
  Python version: 3.12.x
  Node version: 20.x.x
  Working directory: /app

Verifying Reflex installation...
  Reflex version: 0.8.16

Checking frontend compilation...
  ✓ Frontend compiled (.web directory exists)

Application Configuration:
  REFLEX_ENV: production
  FRONTEND_PORT: 3000
  BACKEND_PORT: 8000

==================================================
Starting Reflex in production mode...
==================================================

Compiling: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
App running at:
  ├─ http://0.0.0.0:8000 (backend)
  └─ http://0.0.0.0:3000 (frontend)
```

## 步骤 8: 验证部署

### 8.1 检查应用状态

在 Coolify 应用详情页，确认：

- ✓ 状态显示：`running:healthy`
- ✓ 健康检查：绿色 ✓
- ✓ 容器运行时间：> 60 秒

### 8.2 访问应用

使用浏览器访问：

- **前端**: https://yourapp.jackcwf.com 或 http://server-ip:3000
- **后端 API**: http://server-ip:8000
- **API 文档**: http://server-ip:8000/docs

### 8.3 功能测试

1. **前端测试**:
   - 打开首页
   - 测试登录功能
   - 检查页面交互

2. **后端测试**:
   ```bash
   curl http://server-ip:8000/
   ```

3. **WebSocket 测试**:
   - 检查浏览器控制台是否有 WebSocket 连接错误

## 故障排除

### 问题 1: 容器立即退出

**症状**: 状态显示 `exited:unhealthy`

**检查清单**:
- [ ] 查看构建日志，确认 `reflex export` 成功
- [ ] 查看应用日志，查找 Python 错误
- [ ] 检查环境变量是否正确设置
- [ ] 确认 `nixpacks.toml` 已推送到 Git

**解决方案**:
```bash
# 查看完整日志
coolify app logs mg8c40oowo80o08o0gsw0gwc

# 检查应用详情
coolify app get mg8c40oowo80o08o0gsw0gwc
```

### 问题 2: 健康检查失败

**症状**: 状态显示 `running:unhealthy`

**检查清单**:
- [ ] Initial Delay 是否设置为至少 60 秒？
- [ ] 端口 3000 是否可访问？
- [ ] 应用日志显示 "App running at" 消息？

**解决方案**:
1. 增加 Initial Delay 到 90 秒
2. 检查防火墙规则
3. 确认应用绑定到 `0.0.0.0` 而非 `127.0.0.1`

### 问题 3: 构建失败

**症状**: 部署卡在构建阶段

**检查清单**:
- [ ] `uv sync` 是否成功？
- [ ] Node.js 是否正确安装？
- [ ] 内存是否足够（至少 512MB）？

**解决方案**:
```bash
# 本地测试构建
docker build -t reflex-test .

# 使用 Nixpacks 本地构建
nixpacks build . --name reflex-nixpacks
```

### 问题 4: 前端 404 错误

**症状**: 访问前端显示 404

**检查清单**:
- [ ] `.web` 目录是否在构建时生成？
- [ ] `reflex export --frontend-only` 是否执行？
- [ ] 端口映射是否正确？

**解决方案**:
1. 检查构建日志，确认 export 步骤成功
2. 重新部署应用
3. 检查 Reflex 配置文件 `rxconfig.py`

## 配置检查清单

部署前确认：

- [ ] `nixpacks.toml` 已更新并推送
- [ ] 环境变量已在 Coolify 中配置
- [ ] 端口 3000 和 8000 已映射
- [ ] 健康检查 Initial Delay 设置为 60 秒
- [ ] 资源限制设置为至少 512MB 内存
- [ ] Git 仓库已连接且 Auto Deploy 启用
- [ ] 域名 DNS（如有）已配置

## 优化建议

### 1. 启用自动部署

在 Git 设置中启用 Webhook，实现：
- Push to main → 自动部署
- 部署失败 → 邮件通知

### 2. 配置监控

使用 Coolify 内置监控：
- CPU 使用率告警
- 内存使用率告警
- 健康检查失败告警

### 3. 备份策略

定期备份：
- 应用配置
- 环境变量
- 数据库（如有）

### 4. 多环境部署

创建不同环境：
- `main` 分支 → 生产环境
- `develop` 分支 → 测试环境

## 命令行快速参考

```bash
# 查看应用列表
coolify app list

# 查看应用详情
coolify app get mg8c40oowo80o08o0gsw0gwc

# 查看应用日志
coolify app logs mg8c40oowo80o08o0gsw0gwc

# 重启应用
coolify app restart mg8c40oowo80o08o0gsw0gwc

# 手动部署
coolify deploy uuid mg8c40oowo80o08o0gsw0gwc

# 查看环境变量
coolify app env list mg8c40oowo80o08o0gsw0gwc
```

## 下一步

1. **完成配置**: 按照本文档完成所有设置
2. **触发部署**: Push 代码或手动部署
3. **验证运行**: 确认应用状态为 `running:healthy`
4. **性能优化**: 监控资源使用，按需调整
5. **文档更新**: 记录任何项目特定的配置

## 相关文档

- **诊断报告**: `DEPLOYMENT_DIAGNOSIS.md` - 详细的问题分析
- **Nixpacks 配置**: `nixpacks.toml` - 构建配置文件
- **启动脚本**: `start.sh` - 应用启动逻辑
- **Reflex 配置**: `rxconfig.py` - 框架配置
- **Coolify 文档**: https://coolify.io/docs

---

**最后更新**: 2025-10-30
**维护者**: Claude Code
**应用 UUID**: mg8c40oowo80o08o0gsw0gwc

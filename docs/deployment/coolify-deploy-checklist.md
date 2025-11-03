# Coolify 部署检查清单

本文档提供部署 Reflex 应用到 Coolify 的快速检查清单。

## 部署前检查

### 1. 配置文件检查

- [ ] **nixpacks.toml** - 存在且配置正确
- [ ] **start.sh** - 存在且有执行权限 (`chmod +x start.sh`)
- [ ] **rxconfig.py** - 生产环境 API URL 配置正确
- [ ] **.gitignore** - 包含 `.venv/`, `__pycache__/` 等

### 2. 依赖检查

- [ ] **pyproject.toml** - 所有依赖已列出
- [ ] **reflex** - 版本 >= 0.8.16
- [ ] **granian** - 必须包含在依赖中
- [ ] **其他依赖** - fastapi, pydantic, uvicorn, python-socketio, python-engineio

### 3. Coolify 应用设置

- [ ] **项目和应用** - 已创建
- [ ] **Git 仓库** - 已连接并配置正确分支
- [ ] **构建包** - 设置为 `nixpacks`
- [ ] **端口** - 暴露端口 3000
- [ ] **环境变量** - 在 Coolify 中配置（如有需要）

## 部署步骤

### 方法 1: 通过 Coolify 面板

1. **进入 Coolify 面板**
   - URL: https://coolpanel.jackcwf.com
   - 导航到您的项目 → 应用

2. **触发部署**
   - 点击 "Deploy" 按钮
   - 或推送代码到 Git 仓库（如启用了自动部署）

3. **监控构建日志**
   - 查看实时构建日志
   - 检查以下阶段：
     - Setup (安装系统依赖)
     - Install (安装 Python 依赖)
     - Build (编译 Reflex 前端)
     - Start (启动应用)

### 方法 2: 通过 Coolify CLI

```bash
# 获取项目和应用 ID
coolify project list
coolify app list --project <project_id>

# 触发部署
coolify deploy <project_id> <app_id>

# 查看应用日志
coolify app logs <app_id> --follow
```

## 部署后验证

### 1. 检查应用状态

```bash
# 通过 CLI
coolify app get <app_id>

# 通过面板
# Status 应该显示为 "running"
```

### 2. 检查应用日志

**成功的日志标志**：

```
=========================================
Starting Reflex Application
=========================================
Activating virtual environment at /app/.venv
Virtual environment activated successfully

Environment Information:
----------------------------------------
Python: /app/.venv/bin/python
Reflex: /app/.venv/bin/reflex
Granian: /app/.venv/bin/granian
----------------------------------------

App running at: http://0.0.0.0:3000/
Backend running at: http://0.0.0.0:8000
Serving app at: http://0.0.0.0:8000
```

**失败的标志**：

```
ERROR: granian not found in PATH
FileNotFoundError: [Errno 2] No such file or directory: 'granian'
```

### 3. 测试应用访问

```bash
# 获取应用 FQDN (完全限定域名)
coolify app get <app_id> | grep fqdn

# 访问应用
curl https://your-app.domain.com

# 或在浏览器中打开
```

### 4. 检查前后端连接

- **前端**: https://your-app.domain.com/
- **后端 API**: https://your-app.domain.com/api/
- **健康检查**: https://your-app.domain.com/ping (如果配置了)

## 常见问题排查

### 问题 1: 构建失败

**症状**: 构建阶段报错

**检查**:
```bash
# 查看构建日志
coolify app logs <app_id>

# 常见原因：
# - Python 版本不匹配
# - 依赖安装失败
# - nixpacks.toml 语法错误
```

**解决**:
- 检查 `nixpacks.toml` 配置
- 确保所有依赖在 `pyproject.toml` 中
- 检查 Python 版本兼容性

### 问题 2: 启动失败 (granian not found)

**症状**: `FileNotFoundError: 'granian'`

**解决**: 参考 [`granian-path-fix.md`](./granian-path-fix.md)

**快速修复**:
1. 确保 `nixpacks.toml` 使用正确的启动命令
2. 或使用 `start.sh` 脚本
3. 重新部署

### 问题 3: 应用运行但无法访问

**症状**: 部署成功，但访问域名返回 502 或 504

**检查**:
```bash
# 检查应用是否真的在运行
coolify app get <app_id>

# 检查容器日志
coolify app logs <app_id>

# 检查端口是否正确暴露
# 应该暴露 3000 端口
```

**解决**:
- 确保 `rxconfig.py` 中配置了正确的 host 和 port
- 检查 Coolify 应用设置中的端口映射
- 查看 Traefik 路由配置

### 问题 4: WebSocket 连接失败

**症状**: 前端加载但实时更新不工作

**检查**:
- `rxconfig.py` 中的 `api_url` 是否正确
- WebSocket 协议是否启用 (wss://)
- Coolify/Traefik 是否支持 WebSocket

**解决**:
```python
# rxconfig.py
api_url = "https://your-app.domain.com"  # 确保使用完整 URL
```

### 问题 5: 环境变量未生效

**症状**: 应用行为不符合预期

**检查**:
```bash
# 查看应用环境变量
coolify app env list <app_id> --show-sensitive

# 进入容器检查
docker exec -it <container-id> env
```

**解决**:
- 在 Coolify 面板中设置环境变量
- 或在 `nixpacks.toml` 的 `[variables]` 中设置
- 重启应用使环境变量生效

## 回滚策略

如果部署失败或出现问题：

### 方法 1: 通过 Git 回滚

```bash
# 回滚到上一个提交
git revert HEAD
git push

# 或回滚到特定提交
git reset --hard <commit-hash>
git push --force
```

### 方法 2: 重新部署上一个版本

在 Coolify 面板中：
1. 导航到应用 → Deployments
2. 找到上一个成功的部署
3. 点击 "Redeploy"

### 方法 3: 通过 CLI

```bash
# 查看部署历史
coolify app get <app_id>

# 重新部署特定版本
coolify deploy <project_id> <app_id> --commit <commit-hash>
```

## 性能优化检查

部署成功后，考虑以下优化：

- [ ] **启用缓存** - 配置 CDN 或 Cloudflare
- [ ] **数据库连接池** - 如使用数据库
- [ ] **静态文件服务** - 使用 Nginx 或 CDN
- [ ] **日志管理** - 配置日志轮转和清理
- [ ] **监控和告警** - 设置健康检查和告警
- [ ] **备份策略** - 定期备份数据库和配置

## 相关文档

- **[Granian PATH 问题修复](./granian-path-fix.md)** - 解决 granian 找不到的问题
- **[Reflex 配置指南](../guides/developer/reflex-with-uv.md)** - Reflex 开发和部署指南
- **[Coolify CLI 指南](../../CLAUDE.md#coolify-cli-管理规则)** - Coolify CLI 使用说明

## 获取帮助

如果遇到问题：

1. **查看日志**: `coolify app logs <app_id>`
2. **检查文档**: 参考相关文档链接
3. **社区支持**:
   - Coolify Discord: https://coolify.io/discord
   - Reflex Discord: https://discord.gg/reflex-dev
4. **提交 Issue**: 在项目 GitHub 仓库提交 issue

## 联系信息

- **Coolify 面板**: https://coolpanel.jackcwf.com
- **应用域名**: https://www.jackcwf.com
- **项目仓库**: [您的 Git 仓库 URL]

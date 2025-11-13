# 快速开始指南

> 5 分钟上手 Docker + Coolify 部署

## 目录

- [本地开发](#本地开发)
- [容器测试](#容器测试)
- [生产部署](#生产部署)
- [常见任务](#常见任务)

---

## 本地开发

### 方式 1: 使用开发脚本 (推荐)

```bash
# 一键启动开发环境
./scripts/dev.sh

# 或使用 Makefile
make dev
```

### 方式 2: 直接使用 uv

```bash
# 安装依赖
uv sync

# 启动开发服务器
uv run reflex run
```

### 访问应用

- 前端: http://localhost:3000
- 后端: http://localhost:8000
- 健康检查: http://localhost:3000/health

---

## 容器测试

### 测试生产容器

```bash
# 一键构建和测试
./scripts/test-docker.sh

# 或使用 Makefile
make test-docker
```

### 查看容器日志

```bash
# 实时日志
docker logs -f working-test

# 或使用 Makefile
make logs
```

### 进入容器调试

```bash
# 进入容器 shell
docker exec -it working-test /bin/bash

# 或使用 Makefile
make exec
```

### 停止容器

```bash
# 停止和清理
docker stop working-test
docker rm working-test

# 或使用 Makefile
make clean
```

---

## 生产部署

### 自动部署流程

```bash
# 1. 提交代码
git add .
git commit -m "Your changes"

# 2. 推送到远程 (触发 Coolify 自动部署)
git push origin main

# 或使用 Makefile (交互式)
make deploy
```

### 验证部署

```bash
# 访问生产环境
https://www.jackcwf.com

# 检查健康状态
curl https://www.jackcwf.com/health
```

### 查看部署日志

1. 登录 Coolify 面板: https://coolpanel.jackcwf.com
2. 选择应用: working
3. 点击 "Logs" 查看实时日志

---

## 常见任务

### 查看帮助

```bash
make help
```

输出：
```
Available commands:
  dev             Start local development server
  test-docker     Build and test Docker container locally
  build           Build Docker image
  deploy          Deploy to Coolify (via git push)
  clean           Clean up Docker resources
  logs            Show container logs (local)
  health          Check application health
  install         Install dependencies
  update          Update dependencies
  lint            Run linters
  format          Format code
  test            Run tests (if available)
  exec            Execute command in running container
  ps              Show running containers
  images          Show Docker images
```

### 安装/更新依赖

```bash
# 安装依赖
make install

# 更新依赖
make update
```

### 代码质量

```bash
# 运行 linter
make lint

# 格式化代码
make format
```

### 构建 Docker 镜像

```bash
# 本地构建
make build

# 构建并推送到 registry
make build-push
```

### 查看容器状态

```bash
# 查看运行中的容器
make ps

# 查看 Docker 镜像
make images
```

---

## 故障排除速查表

### 问题：本地开发服务器启动失败

```bash
# 检查依赖
uv sync

# 清理缓存
rm -rf .web

# 重新启动
./scripts/dev.sh
```

### 问题：容器启动失败

```bash
# 查看日志
docker logs working-test

# 检查健康状态
docker inspect working-test | grep -A 10 Health

# 进入容器调试
docker exec -it working-test /bin/bash
```

### 问题：数据库连接失败

```bash
# 测试数据库连接
docker exec -it working-test python -c "
from sqlalchemy import create_engine
import os
engine = create_engine(os.getenv('DATABASE_URL'))
with engine.connect() as conn:
    print('Connected successfully')
"
```

### 问题：WebSocket 连接失败

```bash
# 检查后端是否运行
curl http://localhost:8000/health

# 检查 WebSocket 端点
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
  http://localhost:8000/_event
```

---

## 开发工作流

### 日常开发

```bash
# 早上
make dev                    # 启动开发服务器

# 开发中...
# (文件修改会自动重载)

# 提交代码
git add .
git commit -m "Feature: ..."

# 推送到远程
git push origin main        # Coolify 自动部署
```

### 功能开发 + 容器测试

```bash
# 1. 本地开发
make dev

# 2. 本地测试
# ... test your changes ...

# 3. 容器测试
make test-docker

# 4. 验证容器
curl http://localhost:3000/health

# 5. 提交和部署
git add . && git commit -m "..." && git push
```

### 紧急修复

```bash
# 1. 快速修复代码
vim working/working.py

# 2. 本地验证
make dev

# 3. 立即部署
make deploy

# 4. 监控部署
# Coolify 面板 → Logs
```

---

## 环境配置

### 本地开发环境变量

创建 `.env` 文件：

```bash
# 应用配置
REFLEX_ENV=dev
FRONTEND_PORT=3000
BACKEND_PORT=8000
DEBUG=true

# 数据库 (可选)
DATABASE_URL=postgresql://user:pass@localhost:5432/working
```

### 生产环境变量 (Coolify)

在 Coolify 面板中配置：

```bash
REFLEX_ENV=production
FRONTEND_PORT=3000
BACKEND_PORT=8000
DEBUG=false
DATABASE_URL=postgresql://user:pass@pgvctor.jackcwf.com:5432/working
```

---

## 有用的别名

添加到 `.bashrc` 或 `.zshrc`：

```bash
# 快速命令
alias wd='cd /path/to/working'
alias wdev='make -C /path/to/working dev'
alias wtest='make -C /path/to/working test-docker'
alias wdeploy='make -C /path/to/working deploy'
alias wlogs='make -C /path/to/working logs'
```

---

## 资源链接

- **Coolify 面板**: https://coolpanel.jackcwf.com
- **生产应用**: https://www.jackcwf.com
- **健康检查**: https://www.jackcwf.com/health
- **Reflex 文档**: https://reflex.dev/docs
- **Docker 文档**: https://docs.docker.com

---

## 下一步

- 阅读完整文档: [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md)
- 配置数据库: 设置 `DATABASE_URL`
- 添加功能: 在 `working/` 目录开发
- 配置 CI/CD: 添加自动测试

---

**提示:** 所有脚本都需要执行权限，首次使用前运行：

```bash
chmod +x scripts/*.sh
chmod +x entrypoint.sh
```

**享受开发!** 如有问题，请查看 [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md) 的故障排除部分。

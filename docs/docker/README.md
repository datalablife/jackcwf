# Docker 部署配置文档

本文档说明项目的Docker相关配置和使用方法。

## 文件清单

### 主要文件（根目录）

| 文件 | 用途 | 说明 |
|-----|------|------|
| **Dockerfile** | 主生产Dockerfile | FastAPI+React多阶段构建配置，用于生产环境部署 |
| **.dockerignore** | Docker构建优化 | 排除不必要的文件，加快构建速度，减小镜像大小 |
| **docker-compose.yml** | 开发环境编排 | 本地开发环境的容器编排配置（默认）|
| **docker-compose.prod.yml** | 生产环境编排 | 生产环境的完整编排配置 |
| **Dockerfile.reflex.old** | 旧版存档 | 已废弃的Reflex框架Dockerfile，保留供参考 |

### 启动脚本（scripts目录）

| 文件 | 用途 | 说明 |
|-----|------|------|
| **scripts/container/entrypoint.sh** | 容器入口点 | 容器启动时执行的初始化脚本，处理PID 1进程、信号处理、数据库迁移等 |
| **scripts/dev/start.sh** | 本地开发启动 | 在开发机器上启动完整的本地开发环境 |

## 架构说明

### 技术栈

- **后端**: FastAPI + Uvicorn
- **前端**: React 19 + Vite
- **数据库**: PostgreSQL（外部托管）
- **容器运行时**: Docker

### 多阶段构建流程

Dockerfile使用三阶段构建：

```
Stage 1: Frontend Builder
├─ Node.js 20 Alpine镜像
├─ 安装npm依赖
├─ 构建React应用（Vite）
└─ 输出到 /build/frontend/dist

Stage 2: Backend Builder
├─ Python 3.12 Slim镜像
├─ 安装系统依赖
├─ 使用Poetry安装Python包
└─ 创建虚拟环境 (.venv)

Stage 3: Final Application
├─ Python 3.12 Slim镜像（最小化基础）
├─ 复制前端构建产物
├─ 复制后端虚拟环境
├─ 复制应用代码
├─ 复制启动脚本
└─ 最终镜像大小: ~600-800MB
```

### 镜像优化

**大小优化（多阶段构建）:**
- 删除不必要的构建工具
- 只包含生产运行时依赖
- 使用slim和alpine基础镜像
- 层缓存优化

**构建优化（.dockerignore）:**
```
✗ 开发文件        (.git, node_modules, .venv)
✗ 测试文件        (tests, coverage, .pytest_cache)
✗ IDE配置         (.vscode, .idea)
✗ 文档             (README.md, docs/)
✗ 临时文件         (logs/, tmp/)
✓ 必要文件         (src/, package.json, pyproject.toml)
✓ 脚本             (scripts/lib, scripts/container)
```

## 使用指南

### 本地开发

**使用一键启动脚本（推荐）:**
```bash
bash scripts/dev/start.sh
```

**使用Docker Compose开发环境:**
```bash
# 启动所有服务
docker-compose up

# 后台运行
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

**直接构建镜像（开发/测试）:**
```bash
# 构建镜像
docker build -t working:dev .

# 运行容器
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql+asyncpg://user:pass@db:5432/dev" \
  working:dev
```

### 生产部署

#### 方案A: Coolify（推荐）

1. 连接GitHub仓库到Coolify
2. 创建新应用
3. **Dockerfile位置**: `Dockerfile`（默认）
4. 设置环境变量: `DATABASE_URL`, `ENVIRONMENT`, etc.
5. 点击部署

Coolify会自动：
- 拉取代码
- 构建镜像
- 启动容器
- 配置域名和SSL
- 监控和日志

#### 方案B: Docker命令行

```bash
# 构建镜像
docker build -t working:latest .

# 推送到Registry
docker push your-registry/working:latest

# 运行容器
docker run -d \
  --name working \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql+asyncpg://..." \
  -e ENVIRONMENT=production \
  your-registry/working:latest
```

#### 方案C: Docker Compose

```bash
# 使用生产编排文件
docker-compose -f docker-compose.prod.yml up -d

# 监控日志
docker-compose -f docker-compose.prod.yml logs -f

# 停止服务
docker-compose -f docker-compose.prod.yml down
```

## 环境变量

### 开发环境 (docker-compose.yml)
```env
ENVIRONMENT=development
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/dev
BACKEND_PORT=8000
LOG_LEVEL=DEBUG
```

### 生产环境 (docker-compose.prod.yml)
```env
ENVIRONMENT=production
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/prod
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
BACKEND_WORKERS=auto  # (2-8基于CPU核心)
LOG_LEVEL=WARNING
```

见 `scripts/config/` 中的完整环境变量配置。

## 常见操作

### 构建镜像

```bash
# 标准构建
docker build -t myapp:latest .

# 使用构建缓存
docker build --cache-from myapp:latest -t myapp:latest .

# 指定平台（用于跨平台构建）
docker build --platform linux/amd64,linux/arm64 -t myapp:latest .

# 显示构建过程
docker build --progress=plain -t myapp:latest .
```

### 查看镜像信息

```bash
# 查看镜像大小
docker images working:latest

# 查看镜像历史（层）
docker history working:latest

# 查看镜像详细信息
docker inspect working:latest

# 查看镜像构建时间
docker image ls --format "table {{.ID}}\t{{.Tag}}\t{{.CreatedAt}}"
```

### 调试容器

```bash
# 进入运行中的容器
docker exec -it <container-id> /bin/bash

# 从容器启动交互式shell
docker run -it working:latest /bin/bash

# 查看容器日志
docker logs <container-id>

# 实时跟踪日志
docker logs -f <container-id>

# 查看容器资源使用
docker stats <container-id>
```

### 清理Docker资源

```bash
# 删除镜像
docker rmi working:latest

# 删除停止的容器
docker container prune

# 删除未使用的镜像
docker image prune

# 删除所有未使用的资源（镜像、容器、网络）
docker system prune -a
```

## 故障排除

### 镜像构建失败

**错误: "ExecutionFailure: npm ERR!"**
```
原因: npm依赖安装失败
解决:
1. 检查frontend/package.json依赖
2. 清理构建缓存: docker system prune -a
3. 重新构建: docker build --no-cache .
```

**错误: "Poetry lock file not found"**
```
原因: Poetry依赖文件缺失
解决:
1. 在backend目录运行: poetry lock
2. 提交poetry.lock到git
3. 重新构建镜像
```

### 容器启动失败

**错误: "Failed to connect to database"**
```
原因: DATABASE_URL配置错误或数据库不可达
解决:
1. 检查DATABASE_URL环境变量
2. 验证数据库是否运行
3. 检查防火墙和网络连接
4. 查看容器日志: docker logs <container-id>
```

**错误: "Health check failed"**
```
原因: 应用未正确启动或/health端点失败
解决:
1. 等待更长时间（初次启动60秒）
2. 检查应用日志
3. 验证端口是否正确
4. 检查依赖是否完整
```

### 性能问题

**镜像大小过大 (>1GB)**
```
检查:
1. docker history working:latest 查看各层大小
2. 是否包含了不必要的文件（检查.dockerignore）
3. 是否有重复的依赖安装
解决:
1. 优化.dockerignore
2. 使用多阶段构建（已实施）
3. 清理镜像层
```

**容器启动慢（>30秒）**
```
原因可能:
1. 数据库迁移耗时
2. 依赖加载缓慢
3. 镜像大小过大
解决:
1. 优化数据库迁移脚本
2. 使用构建缓存
3. 减小镜像大小
4. 增加初始化超时时间
```

## 配置参考

### Dockerfile参数

```dockerfile
ARG PYTHON_VERSION=3.12-slim  # Python版本
ARG NODE_VERSION=20-alpine    # Node.js版本
```

修改方式:
```bash
docker build \
  --build-arg PYTHON_VERSION=3.11-slim \
  --build-arg NODE_VERSION=18-alpine \
  .
```

### docker-compose参数

见 `docker-compose.yml` 和 `docker-compose.prod.yml` 中的完整配置。

常见配置:
- `IMAGE`: 镜像名称
- `CONTAINER_NAME`: 容器名称
- `PORTS`: 端口映射
- `VOLUMES`: 卷挂载
- `ENVIRONMENT`: 环境变量
- `NETWORKS`: 网络配置

## 最佳实践

### 安全性

✅ **推荐做法：**
- 使用slim/alpine基础镜像
- 不在镜像中存储秘密
- 使用环境变量传递敏感信息
- 定期扫描镜像安全漏洞

❌ **避免做法：**
- 将密码硬编码在Dockerfile中
- 使用最新的基础镜像（优先使用特定版本）
- 在镜像中安装不必要的包
- 以root用户运行应用

### 性能

✅ **优化建议：**
- 使用多阶段构建
- 充分利用构建缓存
- 将频繁变化的层放在后面
- 最小化镜像大小

❌ **性能陷阱：**
- 每个RUN命令创建新层
- 在构建中安装所有依赖
- 不使用.dockerignore
- 使用不稳定的基础镜像版本

### 可维护性

✅ **推荐做法：**
- 使用描述性的LABEL标签
- 记录Dockerfile的版本和更改
- 保持Dockerfile简洁易读
- 使用docker-compose简化本地开发

❌ **维护问题：**
- 过度复杂化的构建逻辑
- 硬编码版本号
- 缺乏注释和文档
- 混合多个应用在一个Dockerfile中

## 相关资源

- **Dockerfile语法**: [Docker官方文档](https://docs.docker.com/engine/reference/builder/)
- **最佳实践**: [Docker开发最佳实践](https://docs.docker.com/develop/dev-best-practices/)
- **Docker Compose**: [Docker Compose文档](https://docs.docker.com/compose/)
- **镜像构建**: [Docker构建优化](https://docs.docker.com/build/guide/)
- **多阶段构建**: [多阶段构建指南](https://docs.docker.com/build/building/multi-stage/)
- **Coolify部署**: 见项目根目录 `COOLIFY_DEPLOYMENT_GUIDE.md`

## 版本历史

| 日期 | 版本 | 说明 |
|-----|-----|------|
| 2025-11-13 | 1.0 | 初始版本，清理冗余Dockerfile，统一为FastAPI+React架构 |

---

**最后更新**: 2025-11-13
**维护人**: Cloud Dev Team

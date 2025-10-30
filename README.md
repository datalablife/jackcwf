# 云开发工作区 - Coolify PostgreSQL 项目

![Python Version](https://img.shields.io/badge/python-3.12-blue)
![uv](https://img.shields.io/badge/uv-0.9+-green)
![Reflex](https://img.shields.io/badge/reflex-0.8.16-blue)
![PostgreSQL](https://img.shields.io/badge/postgresql-15-green)

这是一个 Coolify 云开发平台上的全栈 Reflex 应用开发项目，集成了 PostgreSQL 数据库和 pgvector 扩展。

## 技术栈

- **前端框架**: Reflex (React + TypeScript)
- **后端框架**: FastAPI (Python)
- **数据库**: PostgreSQL 15 + pgvector (Lantern Suite)
- **包管理**: uv (快速 Python 包管理器)
- **部署平台**: Coolify
- **云服务**: 自托管 Docker 容器

## 快速开始

### 环境要求

- Python 3.12+
- uv 0.9+
- PostgreSQL 15+ (通过 Coolify 部署)
- Node.js 18+ (用于 Reflex)

### 环境设置

#### 1. 克隆项目

```bash
cd /mnt/d/工作区/云开发/working
```

#### 2. 使用 uv 安装依赖

```bash
# 同步虚拟环境和依赖
uv sync

# 激活虚拟环境
source .venv/bin/activate

# 或者直接运行命令而不激活虚拟环境
uv run python --version
```

#### 3. 配置数据库连接

```bash
# 加载 PostgreSQL 配置
source .postgres_config

# 测试数据库连接
psql -h host.docker.internal -p 5432 -U jackcwf888 -d postgres
```

#### 4. 启动开发服务器

```bash
# 使用 uv 启动（推荐 - 无需激活虚拟环境）
uv run reflex run

# 或激活虚拟环境后运行
source .venv/bin/activate
reflex run

# 应用将在 http://localhost:3000 启动
# 后端 API 在 http://localhost:8000
```

**更多 Reflex 命令**:
```bash
# 仅运行前端
uv run reflex run --frontend-only

# 仅运行后端
uv run reflex run --backend-only

# 指定自定义端口
uv run reflex run --frontend-port 3001 --backend-port 8001

# 数据库迁移
uv run reflex db makemigrations
uv run reflex db migrate
```

详细说明请参考 `REFLEX_WITH_UV.md`

## uv 使用指南

### 常用命令

```bash
# 同步虚拟环境（安装/更新所有依赖）
uv sync

# 运行 Python 脚本
uv run python script.py

# 运行命令（自动激活虚拟环境）
uv run pytest

# 添加新的依赖
uv add package_name

# 添加开发依赖
uv add --dev pytest

# 移除依赖
uv remove package_name

# 更新所有依赖
uv sync --upgrade

# 显示已安装的包
uv pip list

# 导出 requirements.txt
uv export --output-file requirements.txt
```

### 虚拟环境位置

```
.venv/                    # uv 管理的虚拟环境
.venv/bin/activate        # 激活脚本
.venv/bin/python          # Python 解释器
.venv/pyvenv.cfg          # 虚拟环境配置
```

## PostgreSQL 连接

### 数据库凭证

- **主机**: host.docker.internal
- **端口**: 5432
- **用户**: jackcwf888
- **密码**: Jack_00492300
- **数据库**: postgres

### 快速连接

```bash
# 使用 psql
psql -h host.docker.internal -p 5432 -U jackcwf888 -d postgres

# 使用 Python
import psycopg2
conn = psycopg2.connect(
    host="host.docker.internal",
    port=5432,
    user="jackcwf888",
    password="Jack_00492300",
    database="postgres"
)

# 使用 SQLAlchemy
from sqlalchemy import create_engine
engine = create_engine("postgresql://jackcwf888:Jack_00492300@host.docker.internal:5432/postgres")
```

### 管理脚本

```bash
# 查看应用信息
./coolify_postgres_manage.sh info

# 启动 psql 客户端
./coolify_postgres_manage.sh psql

# 查看应用状态
./coolify_postgres_manage.sh status

# 查看应用日志
./coolify_postgres_manage.sh logs
```

更多信息请参考 `POSTGRESQL_QUICK_START.md` 和 `POSTGRESQL_CONNECTION.md`。

## Coolify CLI 管理

### 应用管理

```bash
# 查看应用列表
coolify app list

# 获取应用详情
coolify app get ok0s0cgw8ck0w8kgs8kk4kk8

# 查看应用日志
coolify app logs ok0s0cgw8ck0w8kgs8kk4kk8

# 重启应用
coolify app restart ok0s0cgw8ck0w8kgs8kk4kk8

# 停止应用
coolify app stop ok0s0cgw8ck0w8kgs8kk4kk8

# 启动应用
coolify app start ok0s0cgw8ck0w8kgs8kk4kk8
```

更多信息请参考 `CLAUDE.md` 的 Coolify CLI 管理规则部分。

## 项目结构

```
working/
├── README.md                          # 本文件
├── CLAUDE.md                          # Claude Code 项目指南
├── pyproject.toml                     # uv 项目配置
├── .venv/                             # uv 虚拟环境
├── .postgres_config                   # PostgreSQL 配置文件
│
├── POSTGRESQL_QUICK_START.md          # PostgreSQL 快速开始
├── POSTGRESQL_CONNECTION.md           # PostgreSQL 详细连接指南
├── coolify_postgres_manage.sh         # PostgreSQL 管理脚本
├── test_postgres_connection.py        # 数据库连接测试
│
└── .venv.backup/                      # 旧虚拟环境备份（可删除）
```

## 开发工作流

### 代码审查

完成代码开发后，运行 CrewAI 代码审查系统：

```bash
cd code_review_crew
poetry run python src/code_review_crew/main.py /path/to/file.py
```

审查报告将生成在 `code_review_crew/output/code_review_report.md`

### 测试

```bash
# 运行所有测试
uv run pytest

# 运行特定测试文件
uv run pytest tests/test_app.py

# 生成覆盖率报告
uv run pytest --cov=src tests/
```

### 代码格式化

```bash
# 使用 Black 格式化代码
uv run black .

# 使用 isort 排序导入
uv run isort .

# 使用 flake8 检查代码风格
uv run flake8 src/
```

## 重要文件

- **`CLAUDE.md`** - Claude Code 项目规则和指南
- **`pyproject.toml`** - uv 项目配置和依赖声明
- **`POSTGRESQL_QUICK_START.md`** - PostgreSQL 快速开始指南
- **`POSTGRESQL_CONNECTION.md`** - PostgreSQL 详细连接指南
- **`.postgres_config`** - PostgreSQL 环境变量配置

## 注意事项

⚠️ **重要**:

1. `.venv` 由 uv 管理，不要手动修改
2. `.postgres_config` 包含敏感信息，不要提交到 Git
3. 使用 `uv add` 和 `uv remove` 管理依赖，不要直接编辑 `pyproject.toml`
4. `pyproject.toml` 中的依赖将自动同步到 `.venv`

## 故障排除

### uv 相关问题

```bash
# 重新同步虚拟环境
uv sync --refresh

# 清除缓存并重新安装
uv sync --clear-cache

# 更新 uv 本身
uv self update
```

### PostgreSQL 连接问题

参考 `POSTGRESQL_CONNECTION.md` 中的故障排除部分。

### Reflex 相关问题

```bash
# 清除 Reflex 缓存
rm -rf .web

# 重新安装 Reflex
uv remove reflex
uv add reflex==0.8.16

# 查看 Reflex 帮助
reflex --help
```

## Coolify 部署

### 快速部署

如果你需要将应用部署到 Coolify，请按照以下步骤：

#### 1. 阅读快速修复指南

```bash
cat QUICK_FIX_GUIDE.md
```

这个指南包含了部署到 Coolify 的所有必要步骤（5 分钟）。

#### 2. 提交代码

```bash
git add .
git commit -m "Deploy to Coolify"
git push origin main
```

#### 3. 在 Coolify 面板配置

访问 https://coolpanel.jackcwf.com，配置：

- **环境变量**: `PYTHONUNBUFFERED`, `REFLEX_ENV`, 等
- **健康检查**: Initial Delay = 60 秒（关键！）
- **资源限制**: Memory ≥ 1GB

#### 4. 部署和验证

点击 Deploy 按钮，等待 2-3 分钟，验证应用状态为 `running:healthy`。

### 部署文档索引

| 文档 | 用途 |
|------|------|
| **QUICK_FIX_GUIDE.md** | 5 分钟快速部署指南 |
| **DEPLOYMENT_DIAGNOSIS.md** | 完整的问题诊断和分析 |
| **COOLIFY_CONFIG.md** | 详细的 Coolify 配置步骤 |
| **nixpacks.toml** | Nixpacks 构建配置 |
| **start.sh** | 应用启动脚本 |
| **scripts/test/test-docker-build.sh** | 本地 Docker 测试 |
| **scripts/test/test-nixpacks-build.sh** | 本地 Nixpacks 测试 |

### 本地测试部署

在推送到 Coolify 之前，可以本地测试构建：

```bash
# 测试 Dockerfile 构建
./scripts/test/test-docker-build.sh

# 测试 Nixpacks 构建（需要先安装 Nixpacks）
./scripts/test/test-nixpacks-build.sh
```

### 部署故障排除

如果部署失败，请检查：

1. **容器日志为空** → 阅读 `DEPLOYMENT_DIAGNOSIS.md`
2. **健康检查失败** → 确认 Initial Delay = 60 秒
3. **前端 404** → 检查构建日志中的 `reflex export` 步骤
4. **容器立即退出** → 检查环境变量和依赖安装

详细的故障排除步骤请参考 `DEPLOYMENT_DIAGNOSIS.md`。

## 资源链接

- [uv 官方文档](https://docs.astral.sh/uv/)
- [Reflex 官方文档](https://reflex.dev/docs)
- [PostgreSQL 文档](https://www.postgresql.org/docs/)
- [Coolify 文档](https://coolify.io/docs)
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [Lantern 官方网站](https://lantern.dev/)
- [Nixpacks 文档](https://nixpacks.com/)

## 许可证

MIT License - 详见 LICENSE 文件

---

**维护者**: Jack
**最后更新**: 2025-10-27
**项目状态**: 开发中 (Alpha)

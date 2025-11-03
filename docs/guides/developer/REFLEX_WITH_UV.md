# 使用 uv 运行 Reflex 应用

本文档说明如何使用 **uv** 包管理器运行 Reflex 全栈应用。

## 快速开始

### 方式 1: 直接使用 uv run（推荐）

```bash
# 运行 Reflex 开发服务器
uv run reflex run

# 应用访问地址:
# - 前端: http://localhost:3000
# - 后端: http://localhost:8000
```

**优点**:
- 无需激活虚拟环境
- 自动使用 `.venv` 中的依赖
- 简洁清晰

### 方式 2: 激活虚拟环境后运行

```bash
# 激活虚拟环境
source .venv/bin/activate

# 运行 Reflex
reflex run

# 退出虚拟环境
deactivate
```

**优点**:
- 虚拟环境已激活，所有 Python 命令都可用
- 适合长时间开发会话

## Reflex 常用命令

### 使用 uv run 运行

```bash
# 运行开发服务器
uv run reflex run

# 仅运行前端
uv run reflex run --frontend-only

# 仅运行后端
uv run reflex run --backend-only

# 指定自定义端口
uv run reflex run --frontend-port 3001 --backend-port 8001

# 指定日志级别
uv run reflex run --loglevel debug

# 指定环境
uv run reflex run --env prod

# 运行前后端在同一端口
uv run reflex run --single-port
```

### 数据库命令

```bash
# 初始化数据库
uv run reflex db init

# 创建迁移
uv run reflex db makemigrations

# 应用迁移
uv run reflex db migrate

# 重置数据库
uv run reflex db reset
```

### 编译和部署

```bash
# 编译应用
uv run reflex compile

# 导出应用
uv run reflex export

# 部署到 Reflex 云
uv run reflex deploy
```

### 初始化和管理

```bash
# 初始化新 Reflex 项目
uv run reflex init

# 重命名项目
uv run reflex rename new_app_name

# 查看帮助
uv run reflex --help
uv run reflex run --help
```

## 项目配置

### rxconfig.py

```python
import reflex as rx

config = rx.Config(
    app_name="working",
    frontend_host="0.0.0.0",
    frontend_port=3000,
    backend_host="0.0.0.0",
    backend_port=8000,
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)
```

**说明**:
- `app_name`: 应用名称（对应 `working/` 目录）
- `frontend_host`: 前端绑定地址（0.0.0.0 接收所有连接）
- `frontend_port`: 前端端口（必须是 3000）
- `backend_host`: 后端绑定地址
- `backend_port`: 后端端口（必须是 8000）
- `plugins`: 启用的插件（Sitemap 和 TailwindV4）

### pyproject.toml

项目依赖声明在 `pyproject.toml` 中：

```toml
[project]
name = "working"
version = "0.1.0"
requires-python = ">=3.12"

dependencies = [
    "reflex==0.8.16",
    "reflex-hosting-cli==0.1.58",
    # ... 其他依赖
]
```

**修改依赖时**:
```bash
# 添加新的依赖包
uv add new_package

# 移除依赖包
uv remove old_package

# uv 会自动更新 pyproject.toml 和 uv.lock
```

## 项目结构

```
working/                          # 项目根目录
├── pyproject.toml                # uv 项目配置和依赖
├── uv.lock                       # 依赖版本锁定文件
├── rxconfig.py                   # Reflex 配置文件
├── .venv/                        # uv 虚拟环境
├── working/                      # 主应用目录
│   ├── __init__.py
│   └── working.py                # 主应用代码
├── .web/                         # 生成的前端代码
│   ├── app/                      # React 应用
│   ├── backend/                  # Python 后端路由
│   ├── node_modules/             # Node.js 依赖
│   ├── package.json              # 前端依赖配置
│   └── vite.config.js            # Vite 构建配置
├── assets/                       # 静态资源
└── __pycache__/                  # Python 缓存
```

## 开发工作流

### 1. 初始化项目（已完成）

```bash
# 项目已初始化，无需重复执行
uv run reflex init
```

### 2. 修改应用代码

编辑 `working/working.py`:

```python
import reflex as rx

class State(rx.State):
    """应用状态"""
    pass

def index() -> rx.Component:
    return rx.vstack(
        rx.heading("欢迎使用 Reflex + PostgreSQL"),
        rx.text("使用 uv 运行此应用"),
    )

app = rx.App()
app.add_page(index)
```

### 3. 运行开发服务器

```bash
# 使用 uv 直接运行（推荐）
uv run reflex run

# 或激活虚拟环境后运行
source .venv/bin/activate
reflex run
```

### 4. 访问应用

- **前端**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **后端文档**: http://localhost:8000/docs

### 5. 热重载

Reflex 会自动检测代码更改并重新加载应用。修改代码后，浏览器会自动刷新。

### 6. 数据库操作

```bash
# 如果使用 SQLModel 定义数据模型
uv run reflex db init      # 初始化数据库
uv run reflex db migrate   # 应用迁移
```

## 与 PostgreSQL 的集成

### 连接字符串配置

在 `rxconfig.py` 或应用代码中配置数据库连接：

```python
# 使用环境变量或直接指定
DATABASE_URL = "postgresql://jackcwf888:Jack_00492300@host.docker.internal:5432/postgres"

# 或加载自 .postgres_config
import os
os.environ.get("DATABASE_URL")
```

### SQLModel 示例

```python
from sqlmodel import SQLModel, Field, Session, create_engine, select
from sqlalchemy.pool import StaticPool

# 数据库模型
class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str

# 创建数据库连接
DATABASE_URL = "postgresql://jackcwf888:Jack_00492300@host.docker.internal:5432/postgres"
engine = create_engine(
    DATABASE_URL,
    echo=True,
    connect_args={"check_same_thread": False},
)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# 在应用启动时创建表
create_db_and_tables()
```

## 故障排除

### 端口已被占用

```bash
# 如果 3000 或 8000 端口被占用，使用自定义端口
uv run reflex run --frontend-port 3001 --backend-port 8001

# 查看占用的进程
lsof -i :3000
lsof -i :8000

# 杀死进程（如果需要）
kill -9 <PID>
```

### 依赖安装失败

```bash
# 重新同步虚拟环境
uv sync --refresh

# 清除缓存
uv sync --clear-cache

# 重新创建虚拟环境
rm -rf .venv
uv sync
```

### 数据库连接错误

```bash
# 1. 验证 PostgreSQL 是否运行
./coolify_postgres_manage.sh status

# 2. 测试数据库连接
./coolify_postgres_manage.sh test

# 3. 查看连接信息
./coolify_postgres_manage.sh info
```

### 前端构建错误

```bash
# 清除构建缓存
rm -rf .web

# 重新运行
uv run reflex run
```

### 虚拟环境问题

```bash
# 检查虚拟环境状态
uv pip list

# 验证关键包
uv run python -c "import reflex; print(reflex.__version__)"

# 重新创建虚拟环境
rm -rf .venv
uv sync
```

## 开发最佳实践

### 1. 使用虚拟环境

始终使用虚拟环境隔离项目依赖：

```bash
# 激活虚拟环境
source .venv/bin/activate

# 或使用 uv run
uv run reflex run
```

### 2. 管理依赖

使用 `uv add/remove` 管理依赖，不要手动编辑 `pyproject.toml`：

```bash
# ✓ 正确
uv add sqlalchemy

# ✗ 错误
# 手动编辑 pyproject.toml
```

### 3. 提交依赖文件

确保提交 `pyproject.toml` 和 `uv.lock`：

```bash
git add pyproject.toml uv.lock
git commit -m "Update dependencies"
```

### 4. 代码质量

定期运行代码检查：

```bash
# 格式化代码
uv run black working/

# 排序导入
uv run isort working/

# 代码检查
uv run flake8 working/

# 类型检查
uv run mypy working/
```

### 5. 测试

编写并运行测试：

```bash
# 运行所有测试
uv run pytest

# 带覆盖率的测试
uv run pytest --cov=working tests/
```

## 性能优化

### 1. 按需运行组件

```bash
# 仅运行前端（加快开发速度）
uv run reflex run --frontend-only

# 仅运行后端
uv run reflex run --backend-only
```

### 2. 自定义端口

```bash
# 在同一端口运行
uv run reflex run --single-port
```

### 3. 生产构建

```bash
# 编译生产版本
uv run reflex compile

# 导出为 zip
uv run reflex export
```

## 常见问题

### Q: 我可以使用 `pip` 代替 `uv` 吗？

**A**: 可以，但不推荐。uv 比 pip 快得多，且提供更好的依赖管理（uv.lock）。

### Q: `uv run` 和激活虚拟环境有什么区别？

**A**:
- `uv run` - 自动使用虚拟环境，不需手动激活
- 激活虚拟环境 - 需要手动运行 `source .venv/bin/activate`

两者效果相同，但 `uv run` 更方便。

### Q: 为什么要使用 pyproject.toml？

**A**:
- 现代 Python 项目标准
- 集中管理配置
- 支持依赖版本锁定（uv.lock）
- 便于团队协作

### Q: 如何在多个环境中同步依赖？

**A**:
1. 提交 `uv.lock` 到 Git
2. 新环境中运行 `uv sync`
3. 所有环境将使用完全相同的依赖版本

### Q: 可以使用特定的 Python 版本吗？

**A**: 可以，在 `pyproject.toml` 中指定：

```toml
[project]
requires-python = ">=3.12"
```

## 参考资源

- [Reflex 官方文档](https://reflex.dev/docs)
- [uv 官方文档](https://docs.astral.sh/uv/)
- [SQLModel 文档](https://sqlmodel.tiangolo.com/)
- [PostgreSQL 文档](https://www.postgresql.org/docs/)

## 总结

✅ **使用 uv 运行 Reflex 的最简单方式**:

```bash
# 一个命令启动完整的全栈应用
uv run reflex run

# 访问
# 前端: http://localhost:3000
# 后端: http://localhost:8000
```

现在你可以开始开发了！🚀

---

**更新时间**: 2025-10-27
**Reflex 版本**: 0.8.16
**uv 版本**: 0.9.2+
**Python**: 3.12.3

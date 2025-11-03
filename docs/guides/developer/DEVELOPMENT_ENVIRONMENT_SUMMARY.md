# 云开发工作区 - 开发环境完整设置总结

**日期**: 2025-10-27
**项目**: Coolify PostgreSQL + Reflex 全栈应用
**状态**: ✅ 环境配置完成

---

## 一、项目技术栈

| 组件 | 版本 | 用途 |
|------|------|------|
| **Python** | 3.12+ | 应用运行时 |
| **uv** | 0.9.2+ | Python 包管理器 |
| **Reflex** | 0.8.16 | 全栈 Web 框架 |
| **FastAPI** | 0.48.0 | 后端 API 框架 (自动生成) |
| **React** | 由 Reflex 生成 | 前端框架 |
| **PostgreSQL** | 15 + pgvector | 数据库 (Lantern Suite) |
| **Coolify** | 自托管 | 容器管理平台 |

---

## 二、完成的配置项

### ✅ 1. Coolify CLI 集成
- **配置文件**: CLAUDE.md (第 160-321 行)
- **功能**: 直接从 CLI 管理 Coolify 实例中的应用
- **配置上下文**:
  - `myapp`: 主应用上下文 (https://coolpanel.jackcwf.com)
  - `cloud`: 云端上下文
  - `localhost`: 本地测试上下文
- **验证**: ✅ `coolify context list` 显示正确连接
- **API Token**: 安全存储，支持特殊字符

```bash
# 使用示例
coolify app list                           # 列出所有应用
coolify app get ok0s0cgw8ck0w8kgs8kk4kk8  # 获取应用详情
coolify app logs ok0s0cgw8ck0w8kgs8kk4kk8 # 查看日志
```

### ✅ 2. PostgreSQL 数据库连接
- **配置文件**:
  - `.postgres_config` - 环境变量
  - `POSTGRESQL_CONNECTION.md` - 连接指南 (7.6 KB)
  - `test_postgres_connection.py` - 连接测试脚本
  - `coolify_postgres_manage.sh` - 管理脚本

- **数据库详情**:
  ```
  主机: host.docker.internal
  端口: 5432
  用户: jackcwf888
  密码: Jack_00492300
  数据库: postgres
  扩展: pgvector (Lantern Suite)
  ```

- **支持的连接方式** (6 种):
  1. psql CLI
  2. Python (psycopg2)
  3. SQLAlchemy ORM
  4. SQLModel (推荐用于 Reflex)
  5. pgAdmin 4 GUI
  6. DBeaver IDE

- **验证**: ✅ 连接测试脚本可成功连接

### ✅ 3. uv 虚拟环境管理
- **配置文件**:
  - `pyproject.toml` - 项目配置 (4.3 KB)
  - `uv.lock` - 依赖锁定文件 (231 KB)
  - `UV_GUIDE.md` - uv 使用指南 (7.6 KB)

- **已安装依赖**: 42 个生产依赖包
  ```
  核心: reflex, fastapi, starlette, granian
  数据库: sqlalchemy, sqlmodel, alembic, psycopg2
  数据验证: pydantic, python-multipart
  HTTP: httpx, httpcore, websocket 支持
  开发工具: pytest, black, isort, flake8, mypy, pylint
  ```

- **环境位置**: `.venv/` (uv 管理，不提交到 Git)
- **验证**: ✅ `uv sync` 成功，所有依赖已安装

### ✅ 4. Reflex 全栈应用框架
- **配置文件**:
  - `rxconfig.py` - Reflex 配置
  - `working/working.py` - 主应用代码 (212 行)
  - `REFLEX_WITH_UV.md` - 集成指南 (9.8 KB)
  - `REFLEX_TROUBLESHOOTING.md` - 故障排除 (新建)

- **应用功能**:
  - 完整的登录页面
  - 身份认证状态管理
  - 登录成功后显示仪表板
  - 使用 Reflex 组件库 (Card, VStack, Input 等)
  - Tailwind CSS 样式集成

- **端口规范** (固定，不可变更):
  - 前端: `http://localhost:3000`
  - 后端: `http://localhost:8000`
  - API 文档: `http://localhost:8000/docs`

- **编译状态**: ✅ `100% (21/21)` 文件编译成功

### ✅ 5. 项目文档完善
已创建的文档文件:
1. **README.md** (6.4 KB) - 项目概览和快速开始
2. **POSTGRESQL_QUICK_START.md** - PostgreSQL 快速参考
3. **POSTGRESQL_CONNECTION.md** - 详细连接指南
4. **REFLEX_WITH_UV.md** - Reflex + uv 集成指南
5. **REFLEX_TROUBLESHOOTING.md** - 故障排除指南 ✨ 新建
6. **UV_GUIDE.md** - uv 包管理器详细指南
7. **DEVELOPMENT_ENVIRONMENT_SUMMARY.md** - 此文件 ✨ 新建
8. **CLAUDE.md** (更新) - 项目规则和 Coolify CLI 配置

---

## 三、开发工作流程

### 快速开始 (5 分钟)

```bash
# 1. 进入项目目录
cd /mnt/d/工作区/云开发/working

# 2. 同步虚拟环境 (首次或依赖更新后)
uv sync

# 3. 测试数据库连接
source .postgres_config
python test_postgres_connection.py

# 4. 启动开发服务器
uv run reflex run

# 5. 打开浏览器
# 前端: http://localhost:3000
# 后端: http://localhost:8000/docs
```

### 完整开发流程

```bash
# 1. 清理旧进程和缓存
pkill -f "reflex run" -9 || true
rm -rf .web .reflex

# 2. 更新依赖 (如需要)
uv sync --upgrade

# 3. 运行测试
uv run pytest

# 4. 代码格式化
uv run black .
uv run isort .

# 5. 启动开发服务器
uv run reflex run

# 6. 代码审查 (完成功能后)
cd code_review_crew
poetry run python src/code_review_crew/main.py /path/to/file.py
```

### 添加新依赖

```bash
# 添加生产依赖
uv add package_name

# 添加开发依赖
uv add --dev pytest-cov

# 提交变更
git add pyproject.toml uv.lock
git commit -m "Add package_name dependency"
```

---

## 四、故障排除快速参考

### 问题 1: Worker 重启循环
```bash
rm -rf .web && uv run reflex run
```

### 问题 2: 端口占用
```bash
lsof -i :3000 :8000  # 查看占用进程
kill -9 <PID>        # 杀死进程
```

### 问题 3: 依赖冲突
```bash
uv sync --refresh
uv sync --clear-cache
```

### 问题 4: 编译失败
```bash
rm -rf .web .reflex __pycache__
uv run reflex build
```

### 问题 5: 数据库连接失败
```bash
source .postgres_config
python test_postgres_connection.py
```

详见: **REFLEX_TROUBLESHOOTING.md**

---

## 五、端口和网络配置

### 本地访问
- **前端**: http://localhost:3000
- **后端**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **API 交互**: http://localhost:8000/openapi.json

### WSL 环境访问
```bash
# 从 Windows 主机访问 WSL 应用
# 替换 localhost 为 WSL IP (如: 172.20.84.171)
http://172.20.84.171:3000
http://172.20.84.171:8000
```

### 获取 WSL IP
```bash
hostname -I  # 显示 WSL 虚拟 IP
```

---

## 六、Git 工作流程

### .gitignore 关键条目
```
.venv/                    # uv 虚拟环境
.web/                     # Reflex 编译产物
.reflex/                  # Reflex 元数据
__pycache__/             # Python 缓存
.postgres_config         # 敏感数据
.env                     # 环境变量
*.pyc                    # 编译文件
```

### 提交规范
```bash
# 仅提交这些文件到 Git
pyproject.toml           # 依赖声明 (必须)
uv.lock                  # 依赖锁定 (必须)
*.py                     # Python 源代码
*.md                     # 文档
rxconfig.py             # Reflex 配置
```

---

## 七、项目结构

```
working/
├── README.md                              # 项目概览
├── CLAUDE.md                              # Claude Code 项目规则
├── DEVELOPMENT_ENVIRONMENT_SUMMARY.md     # 此文件 (环境总结)
├── REFLEX_WITH_UV.md                     # Reflex + uv 指南
├── REFLEX_TROUBLESHOOTING.md             # 故障排除指南
├── UV_GUIDE.md                           # uv 包管理器指南
│
├── pyproject.toml                        # uv 项目配置 (依赖声明)
├── uv.lock                               # uv 依赖锁定文件
├── rxconfig.py                           # Reflex 应用配置
│
├── .postgres_config                      # PostgreSQL 环境变量
├── POSTGRESQL_CONNECTION.md              # PostgreSQL 连接指南
├── POSTGRESQL_QUICK_START.md             # PostgreSQL 快速参考
├── test_postgres_connection.py           # 数据库连接测试
├── coolify_postgres_manage.sh            # PostgreSQL 管理脚本
│
├── .venv/                               # uv 虚拟环境 (不提交)
├── .web/                                # Reflex 编译产物 (不提交)
├── .reflex/                             # Reflex 元数据 (不提交)
│
├── working/
│   ├── __init__.py                      # Python 包初始化
│   └── working.py                       # Reflex 应用主代码
│
└── code_review_crew/                    # CrewAI 代码审查系统
    ├── poetry.lock
    ├── pyproject.toml
    └── src/
        └── code_review_crew/
            └── main.py                  # 代码审查入口
```

---

## 八、常用命令速查表

### Reflex 命令
| 命令 | 作用 |
|------|------|
| `uv run reflex run` | 启动完整开发服务器 |
| `uv run reflex run --backend-only` | 仅启动后端 |
| `uv run reflex run --frontend-only` | 仅启动前端 |
| `uv run reflex build` | 构建生产版本 |
| `uv run reflex db makemigrations` | 创建数据库迁移 |
| `uv run reflex db migrate` | 执行数据库迁移 |

### uv 命令
| 命令 | 作用 |
|------|------|
| `uv sync` | 同步虚拟环境 |
| `uv add package` | 添加依赖 |
| `uv remove package` | 移除依赖 |
| `uv run python script.py` | 运行 Python 脚本 |
| `uv pip list` | 列出已安装包 |

### PostgreSQL 命令
| 命令 | 作用 |
|------|------|
| `source .postgres_config && psql` | 连接数据库 |
| `./coolify_postgres_manage.sh status` | 查看应用状态 |
| `python test_postgres_connection.py` | 测试连接 |

### 开发工具命令
| 命令 | 作用 |
|------|------|
| `uv run black .` | 代码格式化 |
| `uv run isort .` | 导入排序 |
| `uv run pytest` | 运行测试 |
| `uv run pytest --cov=src` | 生成覆盖率报告 |

---

## 九、性能优化建议

### 开发环境 (提速开发流程)
```bash
# 禁用遥测
uv run reflex run --no-telemetry

# 减少日志
uv run reflex run --loglevel info

# 禁用热重载 (调试时)
uv run reflex run --no-watch
```

### 生产环境 (部署优化)
```bash
# 构建优化版本
uv run reflex build --production

# 使用生产级服务器 (gunicorn/uvicorn)
# 而不是 reflex run
```

---

## 十、下一步建议

### 立即可做
1. ✅ 启动开发服务器: `uv run reflex run`
2. ✅ 测试登录页面: http://localhost:3000
3. ✅ 查看 API 文档: http://localhost:8000/docs
4. ✅ 验证数据库连接: `python test_postgres_connection.py`

### 短期任务 (1-2 周)
1. 集成 PostgreSQL 到 Reflex 应用 (使用 SQLModel)
2. 创建数据模型 (用户、认证等)
3. 编写 API 端点和数据库操作
4. 完成代码审查流程 (CrewAI)

### 中期任务 (2-4 周)
1. 添加单元测试和集成测试
2. 优化数据库查询性能
3. 部署到 Coolify 生产环境
4. 配置 CI/CD 流程

### 长期维护
1. 定期更新依赖 (uv sync --upgrade)
2. 监控应用性能和日志
3. 数据库备份和恢复策略
4. 安全审计和代码审查

---

## 十一、资源链接

| 资源 | 链接 |
|------|------|
| **Reflex 官方文档** | https://reflex.dev/docs |
| **Reflex UI 组件库** | https://reflex.dev/docs/library |
| **FastAPI 文档** | https://fastapi.tiangolo.com |
| **SQLAlchemy 文档** | https://docs.sqlalchemy.org |
| **PostgreSQL 文档** | https://www.postgresql.org/docs |
| **uv 官方文档** | https://docs.astral.sh/uv |
| **Coolify 文档** | https://coolify.io/docs |
| **pgvector GitHub** | https://github.com/pgvector/pgvector |

---

## 十二、技术支持

### 问题排查步骤
1. 检查相关文档 (README.md, REFLEX_TROUBLESHOOTING.md 等)
2. 查看详细日志 (`uv run reflex run --loglevel debug`)
3. 隔离问题 (前后端分离启动)
4. 清理缓存重试 (`rm -rf .web && uv run reflex run`)
5. 检查依赖版本 (`uv pip show package_name`)

### 常见问题
- **Worker 重启循环**: 见 REFLEX_TROUBLESHOOTING.md - 问题 1
- **端口占用**: 见 REFLEX_TROUBLESHOOTING.md - 问题 3
- **编译失败**: 见 REFLEX_TROUBLESHOOTING.md - 问题 4
- **数据库连接**: 见 POSTGRESQL_CONNECTION.md

---

## 总结

✅ **环境配置完成**:
- Coolify 云平台集成完成
- PostgreSQL 数据库连接配置完成
- uv 虚拟环境管理配置完成
- Reflex 全栈框架配置完成
- 完整文档体系建立完成

🚀 **已可开始开发**:
- 执行 `uv run reflex run` 启动开发服务器
- 访问 http://localhost:3000 查看前端应用
- 访问 http://localhost:8000/docs 查看 API 文档

📚 **参考文档完整**:
- 有 7+ 详细文档支持日常开发
- 有完整的故障排除指南
- 有快速参考命令表

---

**创建日期**: 2025-10-27
**最后更新**: 2025-10-27
**维护者**: Jack
**项目状态**: 开发环境 ✅ 就绪

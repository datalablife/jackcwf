# 🚀 最新启动前后端指南（2025年11月）

## 📌 快速开始（推荐）

### 一键启动所有服务

```bash
cd /mnt/d/工作区/云开发/working
bash scripts/dev.sh
```

**效果：**
- ✅ 自动检查依赖（Python 3.12, Node.js 18+）
- ✅ 自动安装虚拟环境和依赖
- ✅ 启动 PostgreSQL 数据库（如已配置）
- ✅ 启动后端 FastAPI（port 8000，热重载）
- ✅ 启动前端 React Vite（port 5173，热重载）

**访问地址：**
```
Frontend:     http://localhost:5173
Backend API:  http://localhost:8000
Swagger Docs: http://localhost:8000/docs
ReDoc Docs:   http://localhost:8000/redoc
```

---

## 📋 分步式启动（手动方式）

### 方式 A：使用 Makefile（最简洁）

```bash
cd /mnt/d/工作区/云开发/working

# 一行启动所有
make dev

# 或其他有用的命令
make install      # 安装依赖
make test         # 运行测试
make lint         # 代码检查
make format       # 格式化代码
make build        # 构建 Docker 镜像
```

### 方式 B：手动启动各服务

#### 第 1 步：安装依赖

```bash
cd /mnt/d/工作区/云开发/working

# 使用 uv（推荐，更快）
uv sync

# 或使用 pip
cd backend
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或 Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd ..

# 前端依赖
npm install --prefix frontend
```

#### 第 2 步：配置环境变量

**后端配置 (`backend/.env`)：**
```bash
cp backend/.env.example backend/.env

# 编辑 backend/.env 并设置：
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/your_db
ANTHROPIC_API_KEY=sk-xxxxxxxxxxxx  # Claude API key
ENVIRONMENT=development
DEBUG=true
```

**前端配置 (`frontend/.env`)：**
```bash
cp frontend/.env.example frontend/.env

# 或手动创建：
echo "VITE_API_URL=http://localhost:8000/api" > frontend/.env
```

#### 第 3 步：运行数据库迁移（可选）

```bash
cd backend
alembic upgrade head
cd ..
```

#### 第 4 步：启动服务（3 个终端窗口）

**终端 1 - 后端：**
```bash
cd /mnt/d/工作区/云开发/working

# 方式 A：使用 uv
uv run python -m uvicorn backend.src.main:app \
  --reload \
  --host 0.0.0.0 \
  --port 8000

# 方式 B：使用 venv
source backend/.venv/bin/activate
uvicorn backend.src.main:app --reload --host 0.0.0.0 --port 8000
```

**终端 2 - 前端：**
```bash
cd /mnt/d/工作区/云开发/working/frontend
npm run dev
```

**终端 3 - 可选监视：**
```bash
# 监视日志或运行测试
cd /mnt/d/工作区/云开发/working
npm run test:e2e --prefix frontend  # E2E 测试
make test                            # 后端单元测试
```

---

## 🛠️ npm 脚本列表（前端）

```bash
cd frontend

npm run dev              # 启动开发服务器（热重载）✅ 推荐
npm run build           # 构建生产版本
npm run preview         # 预览生产构建
npm run lint            # 运行 ESLint
npm run lint:fix        # 自动修复 linting 问题
npm run format          # 格式化代码（Prettier）
npm run test            # 运行 Vitest 单元测试
npm run test:ui         # 用 UI 运行单元测试
npm run test:e2e        # 运行 Playwright E2E 测试
npm run test:e2e:ui     # E2E 测试 UI 界面
npm run test:e2e:debug  # 调试 E2E 测试
npm run coverage        # 测试覆盖率报告
```

---

## 🐍 Python 脚本列表（后端）

```bash
cd backend

# 开发服务器
python -m uvicorn src.main:app --reload --port 8000

# 数据库迁移
alembic init migrations          # 初始化迁移
alembic revision -m "message"   # 创建新迁移
alembic upgrade head            # 应用迁移
alembic downgrade -1            # 回滚上一步

# 测试
python -m pytest tests/          # 运行所有测试
python -m pytest tests/ -v       # 详细输出
python -m pytest tests/ --cov    # 覆盖率报告

# 代码检查
ruff check .                     # 检查代码
ruff format .                    # 格式化代码

# Memori 内存系统
python examples/memori_integration_example.py
```

---

## 📦 项目结构快速参考

```
working/
├── frontend/                  # React 19 应用
│   ├── src/
│   │   ├── components/       # UI 组件（自定义 Tailwind）
│   │   ├── pages/            # 页面组件
│   │   ├── hooks/            # React hooks
│   │   ├── stores/           # Zustand 状态管理
│   │   └── main.tsx
│   ├── vite.config.ts        # Vite 配置
│   ├── tsconfig.app.json     # TypeScript 配置
│   ├── package.json          # 依赖列表
│   └── .env.example
│
├── backend/                   # FastAPI 应用
│   ├── src/
│   │   ├── main.py           # 应用入口 ⭐
│   │   ├── api/              # API 路由
│   │   ├── models/           # SQLAlchemy ORM 模型
│   │   ├── services/         # 业务逻辑
│   │   ├── memory/           # Memori 集成
│   │   └── schemas/          # Pydantic 验证模型
│   ├── pyproject.toml        # 依赖配置
│   ├── alembic/              # 数据库迁移
│   └── .env.example
│
├── scripts/
│   ├── dev.sh                # 开发启动脚本 ⭐
│   ├── build.sh              # Docker 构建
│   └── test-docker.sh
│
├── Makefile                  # 快捷命令
├── Dockerfile                # 生产镜像
├── docker-compose.yml        # Coolify 配置
├── README.md                 # 项目说明
└── ARCHITECTURE_ANALYSIS.md  # 架构分析 ⭐
```

---

## 🐳 Docker 方式启动

### 本地构建测试

```bash
cd /mnt/d/工作区/云开发/working

# 构建镜像
bash scripts/build.sh

# 或使用 Make
make build

# 运行容器
docker run -p 8000:8000 -p 3000:3000 \
  -e ENVIRONMENT=production \
  -e DATABASE_URL=postgresql://... \
  -e ANTHROPIC_API_KEY=sk-... \
  working:latest
```

### Docker Compose（Coolify 部署方式）

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

**docker-compose.yml 配置：**
- 前端：port 3000（Traefik 路由）
- 后端 API：port 8000（Traefik 路由）
- 健康检查：每 10 秒一次
- 启动宽限期：120 秒

---

## 🔧 环境变量完整参考

### 后端 (`backend/.env`)

```env
# ===== 数据库 =====
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/working_db

# ===== AI 服务 =====
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# ===== Memori 内存系统 =====
MEMORI_ENABLED=true
MEMORI_DB_TYPE=postgresql              # sqlite / postgresql
MEMORI_SQLITE_PATH=./memori.db
MEMORI_CONSCIOUS_INGEST=true           # 会话开始注入内存
MEMORI_AUTO_INGEST=true                # 调用时动态注入
MEMORI_ENABLE_SEMANTIC_SEARCH=true
MEMORI_MAX_MEMORY_ITEMS=1000
MEMORI_MEMORY_RETENTION_DAYS=90

# ===== 应用配置 =====
ENVIRONMENT=development                # development / production
DEBUG=true
LOG_LEVEL=INFO

# ===== CORS 设置 =====
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# ===== 服务端口 =====
HOST=0.0.0.0
PORT=8000
```

### 前端 (`frontend/.env`)

```env
VITE_API_URL=http://localhost:8000/api
VITE_APP_NAME=AI Data Analyzer
VITE_APP_VERSION=0.1.0
VITE_ENABLE_SCHEMA_EXPLORER=true
VITE_ENABLE_FILE_UPLOAD=true
VITE_DEBUG=false
```

---

## ✅ 启动检查清单

启动前确保以下条件都满足：

- [ ] Python 3.12+ 已安装
  ```bash
  python --version
  ```

- [ ] Node.js 18+ 已安装
  ```bash
  node --version
  npm --version
  ```

- [ ] 依赖已安装
  ```bash
  # 检查虚拟环境
  ls backend/.venv || echo "需要运行 uv sync"

  # 检查 npm 模块
  ls frontend/node_modules || echo "需要运行 npm install"
  ```

- [ ] `.env` 文件已创建
  ```bash
  ls backend/.env && echo "✅ 后端配置OK" || echo "❌ 需要创建 backend/.env"
  ls frontend/.env && echo "✅ 前端配置OK" || echo "❌ 需要创建 frontend/.env"
  ```

- [ ] 数据库已准备（如使用 PostgreSQL）
  ```bash
  # 验证数据库连接
  psql $DATABASE_URL -c "SELECT 1"
  ```

- [ ] 端口未被占用
  ```bash
  lsof -i :8000 || echo "✅ 8000 端口可用"
  lsof -i :5173 || echo "✅ 5173 端口可用"
  ```

---

## 🐛 常见问题排查

### ❌ "Port 8000 already in use"

```bash
# 查看占用进程
lsof -i :8000

# 杀死进程
kill -9 <PID>

# 或改用其他端口
uvicorn backend.src.main:app --port 8001
```

### ❌ "Cannot find module '@/components'"

```bash
# 这是 TypeScript 路径别名问题，应该自动工作
# 如果不行，重启 Vite 服务
npm run dev --prefix frontend
```

### ❌ "Database connection refused"

```bash
# 检查 DATABASE_URL
echo $DATABASE_URL

# 测试 PostgreSQL 连接
psql -h localhost -U postgres -d working_db -c "SELECT 1"

# 如果没有 PostgreSQL，Memori 会自动用 SQLite
```

### ❌ "Module not found" 错误

```bash
# 清除缓存并重新安装
uv sync --clear-cache

# 前端
rm -rf frontend/node_modules
npm install --prefix frontend
```

### ❌ "Hot reload not working"

```bash
# 检查文件观察者限制（Linux）
cat /proc/sys/fs/inotify/max_user_watches

# 增加限制
echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

---

## 📊 启动后的检查

启动完成后验证所有服务正常：

```bash
# 1. 检查前端
curl -s http://localhost:5173 | head -20

# 2. 检查后端
curl -s http://localhost:8000/health | jq .

# 3. 检查 API 文档
curl -s http://localhost:8000/docs | head -20

# 4. 测试 API 端点
curl -s http://localhost:8000/api/version | jq .
```

---

## 🔄 开发工作流

### 日常开发循环

1. **启动服务**
   ```bash
   bash scripts/dev.sh
   ```

2. **在你喜欢的编辑器中编辑代码**
   - 前端: `frontend/src/`
   - 后端: `backend/src/`

3. **代码自动重新加载**
   - 前端：Vite 热模块替换 (HMR)
   - 后端：Uvicorn 热重载

4. **运行测试**
   ```bash
   # 前端
   npm run test --prefix frontend

   # 后端
   make test

   # E2E
   npm run test:e2e --prefix frontend
   ```

5. **提交代码**
   ```bash
   git add .
   git commit -m "feat: description"
   git push origin main
   ```

---

## 🎯 下一步操作

启动后，你可以：

1. **浏览前端页面** → http://localhost:5173
2. **查看 API 文档** → http://localhost:8000/docs
3. **测试 Claude AI 集成** → POST `/api/memory/claude/message`
4. **上传数据文件** → `/api/files/upload`
5. **查看架构分析** → 根目录的 `ARCHITECTURE_ANALYSIS.md`

---

## 📚 相关文档

| 文档 | 位置 | 内容 |
|------|------|------|
| **架构分析** | `ARCHITECTURE_ANALYSIS.md` | 完整的前后端技术栈分析 |
| **快速入门** | `docs/guides/QUICK_START.md` | 项目快速开始指南 |
| **部署指南** | `docs/deployment/COOLIFY_DEPLOYMENT_GUIDE.md` | Coolify 云部署方式 |
| **API 文档** | `http://localhost:8000/docs` | Swagger 自动生成的 API 文档 |
| **内存系统** | `docs/tools/MEMORI/MEMORI_QUICKSTART.md` | Memori 记忆系统使用指南 |

---

**⏱️ 预计启动时间：**
- 首次启动：3-5 分钟（安装依赖）
- 后续启动：10-15 秒

**💡 建议：**
- 使用 `bash scripts/dev.sh` 最简单快速
- 使用 `make dev` 如果你熟悉 Makefile
- 分终端启动便于调试和观察日志


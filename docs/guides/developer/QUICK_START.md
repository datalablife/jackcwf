# 快速启动指南

本指南介绍如何快速启动完整的系统进行集成测试。

## 📋 前置要求

### 本地开发模式

- Node.js 16+
- Python 3.9+
- PostgreSQL 12+
- Git

### Docker 模式

- Docker 20.10+
- Docker Compose 1.29+

---

## 🚀 启动方式

### 方式 1: 本地开发（推荐用于开发）

#### 1.1 配置后端环境

```bash
cd backend

# 复制环境配置
cp .env.example .env

# 编辑 .env 文件（配置数据库等）
# 关键配置：
# DATABASE_URL=postgresql://user:password@localhost:5432/dbname
# API_PORT=8000

# 安装依赖
poetry install

# 运行数据库迁移
alembic upgrade head

# 启动后端服务
chmod +x start-backend.sh
./start-backend.sh dev
```

后端将在 `http://localhost:8000` 启动
- API 文档: `http://localhost:8000/docs`
- 健康检查: `http://localhost:8000/health`

#### 1.2 配置前端环境

```bash
cd frontend

# 安装依赖
npm install

# 创建环境配置
echo "VITE_API_URL=http://localhost:8000" > .env.local

# 启动前端开发服务器
chmod +x start-frontend.sh
./start-frontend.sh
```

前端将在 `http://localhost:5173` 启动

### 方式 2: Docker Compose（推荐用于测试和部署）

#### 2.1 快速启动

```bash
# 使用 docker-compose 启动所有服务
docker-compose -f docker-compose.prod.yml up -d

# 查看服务日志
docker-compose -f docker-compose.prod.yml logs -f

# 停止所有服务
docker-compose -f docker-compose.prod.yml down
```

#### 2.2 访问服务

| 服务 | URL | 备注 |
|------|-----|------|
| 前端 | http://localhost:5173 | 应用主界面 |
| 后端 API | http://localhost:8000 | API 服务 |
| API 文档 | http://localhost:8000/docs | Swagger UI |
| 数据库 | localhost:5432 | PostgreSQL |
| Redis | localhost:6379 | 缓存服务 |

---

## 🧪 运行集成测试

### 前置条件

确保前后端服务都已启动：
- 后端运行在 `http://localhost:8000`
- 前端运行在 `http://localhost:5173`

### 执行集成测试

```bash
# 方式 1: 使用测试脚本
chmod +x run-integration-tests.sh
./run-integration-tests.sh

# 方式 2: 详细模式
./run-integration-tests.sh -v

# 查看帮助
./run-integration-tests.sh --help
```

### 查看测试结果

```bash
# 测试结果存放目录
ls -la test-results/

# 查看测试报告
open test-results/integration_test_report_*.html  # macOS
xdg-open test-results/integration_test_report_*.html  # Linux
start test-results/integration_test_report_*.html  # Windows
```

---

## 📊 功能测试

### 1. 文件上传测试

```bash
# 使用 curl 测试上传
curl -X POST \
  -F "file=@test.csv" \
  -F "data_source_id=1" \
  http://localhost:8000/api/file-uploads

# 期望响应
# {
#   "id": 1,
#   "filename": "test.csv",
#   "file_format": "csv",
#   "file_size": 1024,
#   "parse_status": "pending",
#   "created_at": "2025-11-10T12:00:00Z"
# }
```

### 2. 文件列表测试

```bash
curl -X GET \
  "http://localhost:8000/api/file-uploads?skip=0&limit=20"
```

### 3. 文件预览测试

```bash
curl -X GET \
  "http://localhost:8000/api/file-uploads/1/preview?max_rows=100"
```

### 4. 前端页面测试

- 访问 http://localhost:5173
- 点击"开始上传"进入上传页面
- 选择文件并上传
- 查看上传进度和文件列表
- 点击文件预览按钮
- 验证数据显示和分页

---

## 🔧 环境配置

### 后端环境变量 (.env)

```env
# 数据库配置
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/data_management

# API 配置
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# CORS 配置
CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]

# 文件存储
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=536870912  # 500 MB

# 环境
ENVIRONMENT=development
DEBUG=true
```

### 前端环境变量 (.env.local)

```env
# API 配置
VITE_API_URL=http://localhost:8000

# 应用信息
VITE_APP_NAME=数据文件管理系统
VITE_APP_VERSION=1.0.0

# 开发配置
VITE_DEBUG=true
```

---

## 📝 常见问题

### Q1: 端口被占用

**问题**: `Error: listen EADDRINUSE :::8000`

**解决方案**:
```bash
# 查看占用端口的进程
lsof -i :8000

# 杀死进程
kill -9 <PID>

# 或更改端口
# 编辑 .env 或启动命令
```

### Q2: 数据库连接失败

**问题**: `Error: could not connect to server`

**解决方案**:
```bash
# 检查数据库是否运行
psql -U postgres -h localhost

# 如果使用 Docker
docker ps | grep postgres

# 查看 Docker 日志
docker logs data-management-db
```

### Q3: CORS 错误

**问题**: `Access to XMLHttpRequest blocked by CORS policy`

**解决方案**:
- 检查后端 CORS 配置
- 确保前端 URL 在后端允许列表中
- 检查 .env 文件中的 CORS_ORIGINS

### Q4: 前端连接不到后端

**问题**: API 请求 timeout

**解决方案**:
```bash
# 检查后端是否运行
curl http://localhost:8000/health

# 检查防火墙
# Linux: sudo ufw allow 8000
# macOS: 通常不需要配置

# 验证 VITE_API_URL 配置
cat frontend/.env.local
```

---

## 🚢 部署检查清单

启动前的检查：

- [ ] 后端依赖已安装
- [ ] 前端依赖已安装
- [ ] 数据库已配置
- [ ] 环境变量已设置
- [ ] 数据库迁移已执行
- [ ] 后端服务已启动
- [ ] 前端服务已启动
- [ ] 集成测试已通过
- [ ] API 文档可访问
- [ ] 前端界面可访问

---

## 📚 相关文档

- [部署指南](./DEPLOYMENT_GUIDE.md)
- [集成测试计划](./INTEGRATION_TEST_PLAN.md)
- [前端 README](./frontend/README.md)
- [后端项目文档](./backend/README.md)（待完成）

---

## 🆘 获取帮助

如遇到问题：

1. 查看相关日志
   ```bash
   # 后端日志
   tail -f logs/app.log

   # Docker 日志
   docker-compose logs -f backend
   ```

2. 运行诊断脚本
   ```bash
   # 检查服务状态
   ./run-integration-tests.sh
   ```

3. 查看常见问题 FAQ

---

**最后更新**: 2025-11-10
*下一步: 运行集成测试验证系统*
问题分析：这段代码存在...
方案评估：可以通过...或...来改进
方案选择：我建议用...因为...
实施步骤：
  1. 首先修改...
  2. 然后优化...
  3. 最后测试...
风险考虑：需要注意...
</thinking>

根据分析，以下是改进建议：
...
```

## 项目文件结构

```
working/
├── .claude/
│   ├── config.json                      ← 主配置（包含thinking设置）
│   ├── thinking-settings.json           ← thinking专用配置
│   ├── THINKING_CONFIG_GUIDE.md         ← 详细文档
│   └── hooks/
│       ├── user-prompt-submit-hook      ← 提示提交hook
│       ├── conversation-compacted-hook  ← 压缩hook
│       └── thinking-display-hook        ← thinking显示hook
├── claude-wrapper.sh                    ← 启动脚本
└── QUICK_START.md                       ← 本文件
```

## 核心配置说明

| 配置项 | 值 | 作用 |
|------|-----|------|
| `showThinking` | `true` | 启用thinking显示 |
| `expandThinkingByDefault` | `true` | 默认展开thinking内容 |
| `verbose` | `true` | 详细输出模式 |
| `thinkingLevel` | `comprehensive` | 完整的thinking过程 |
| `language` | `zh-CN` | 中文语言 |

## 常见问题

**Q: 为什么我还是看不到 thinking?**
- 重启 Claude Code
- 确认你在项目根目录运行 `claude`
- 运行 `claude --verbose` 获取更多信息

**Q: 如何禁用 thinking 显示?**
- 编辑 `.claude/config.json`
- 设置 `"showThinking": false`
- 重启会话

**Q: 对话压缩后会丢失 thinking 设置吗?**
- 不会，hooks 会自动保持 thinking 配置
- 你会看到提示：`📝 对话已压缩，中文模式继续有效`

**Q: 可以调整 thinking 的详细程度吗?**
- 可以，修改 `thinkingLevel` 值：
  - `brief` - 简要
  - `normal` - 正常
  - `comprehensive` - 完整（当前设置）

## 下一步

1. **启动 Claude Code**：`claude`
2. **进行一个复杂的编程任务**
3. **观察 thinking 过程的显示**
4. **调整配置**（如需要）

详细配置说明见：`.claude/THINKING_CONFIG_GUIDE.md`

---

💡 **提示**：thinking 过程对于学习如何解决问题非常有价值。建议保存包含 thinking 的对话以便后续参考。

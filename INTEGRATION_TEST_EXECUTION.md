# 系统集成测试执行指南

**文档版本**: 1.0
**创建日期**: 2025-11-10
**状态**: Phase 5 - T080 集成测试和 API 联调

---

## 📋 目录

1. [快速开始](#快速开始)
2. [前置条件检查](#前置条件检查)
3. [本地开发模式测试](#本地开发模式测试)
4. [Docker 模式测试](#docker-模式测试)
5. [手动 API 测试](#手动-api-测试)
6. [测试结果解释](#测试结果解释)
7. [故障排查](#故障排查)
8. [测试报告](#测试报告)

---

## 快速开始

### 选项 1：本地开发模式（推荐用于开发）

```bash
# 终端 1: 启动后端
cd backend
./start-backend.sh dev

# 终端 2: 启动前端
cd frontend
./start-frontend.sh

# 终端 3: 运行集成测试
./run-integration-tests.sh
```

### 选项 2：Docker Compose 模式（推荐用于完整测试）

```bash
# 启动所有服务
docker-compose -f docker-compose.prod.yml up -d

# 等待 30 秒让所有服务启动
sleep 30

# 运行集成测试
./run-integration-tests.sh

# 查看测试结果
ls -la test-results/
```

---

## 前置条件检查

### 系统要求

在运行测试前，请确保满足以下条件：

#### 本地开发模式

- ✅ Node.js 16+ 已安装
  ```bash
  node --version  # 应输出 v16.0.0 或更高
  ```

- ✅ Python 3.9+ 已安装
  ```bash
  python3 --version  # 应输出 Python 3.9.0 或更高
  ```

- ✅ PostgreSQL 12+ 已安装并运行
  ```bash
  psql --version  # 应输出 psql (PostgreSQL) 12.0 或更高
  ```

- ✅ Poetry 已安装（后端依赖管理）
  ```bash
  poetry --version  # 应输出 Poetry 1.0.0 或更高
  ```

#### Docker 模式

- ✅ Docker 20.10+ 已安装
  ```bash
  docker --version  # 应输出 Docker version 20.10 或更高
  ```

- ✅ Docker Compose 1.29+ 已安装
  ```bash
  docker-compose --version  # 应输出 docker-compose version 1.29 或更高
  ```

### 环境变量检查

```bash
# 后端环境变量 (.env)
ls backend/.env && echo "✅ 后端环境文件存在" || echo "❌ 后端环境文件不存在"

# 前端环境变量 (.env.local)
ls frontend/.env.local && echo "✅ 前端环境文件存在" || echo "❌ 前端环境文件不存在"
```

### 端口可用性检查

```bash
# 检查 8000 端口（后端 API）
lsof -i :8000 && echo "⚠️  端口 8000 已被占用" || echo "✅ 端口 8000 可用"

# 检查 5173 端口（前端开发服务器）
lsof -i :5173 && echo "⚠️  端口 5173 已被占用" || echo "✅ 端口 5173 可用"

# 检查 5432 端口（PostgreSQL）
lsof -i :5432 && echo "✅ PostgreSQL 可能在运行" || echo "⚠️  PostgreSQL 未运行"

# 检查 6379 端口（Redis，可选）
lsof -i :6379 && echo "✅ Redis 可能在运行" || echo "⚠️  Redis 未运行（可选）"
```

---

## 本地开发模式测试

### 步骤 1: 启动后端服务

```bash
cd backend

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "创建 .env 文件..."
    cp .env.example .env
    # 编辑 .env 配置数据库 URL
fi

# 启动后端
./start-backend.sh dev

# 预期输出:
# ✅ Python 版本: Python 3.9.0+
# ✅ 安装 Python 依赖...
# 🔄 运行数据库迁移...
# 🚀 后端服务已启动！
# API 地址: http://localhost:8000
# API 文档: http://localhost:8000/docs
```

### 步骤 2: 验证后端服务

在另一个终端：

```bash
# 检查健康状态
curl -s http://localhost:8000/health | jq .

# 预期响应:
# {"status":"ok","timestamp":"2025-11-10T12:00:00Z"}

# 访问 API 文档
open http://localhost:8000/docs  # macOS
# 或
xdg-open http://localhost:8000/docs  # Linux
```

### 步骤 3: 启动前端服务

```bash
cd frontend

# 启动前端
./start-frontend.sh

# 预期输出:
# 🚀 启动前端应用...
# ✅ Node.js 版本: v16.0.0+
# ✅ npm 版本: 8.0.0+
# 📦 安装 npm 依赖...
# 👀 开发模式: 启用热重载...
#
# ➜  Local:   http://localhost:5173/
```

### 步骤 4: 验证前端应用

在浏览器中：

```
http://localhost:5173
```

预期看到：
- ✅ 应用首页加载成功
- ✅ 导航栏显示正确
- ✅ 可以点击"开始上传"按钮
- ✅ 浏览器控制台没有错误

### 步骤 5: 运行集成测试

```bash
# 在第三个终端运行测试
./run-integration-tests.sh

# 或使用详细模式
./run-integration-tests.sh -v

# 预期输出:
# ╔════════════════════════════════════════╗
# ║  🚀 系统集成测试启动                    ║
# ╚════════════════════════════════════════╝
#
# ℹ️  检查 后端 服务...
# ✅ 后端 服务已就绪
#
# ℹ️  检查 前端 服务...
# ✅ 前端 服务已就绪
#
# ℹ️  开始执行测试...
# [各项测试结果...]
#
# ✅ 集成测试完成
```

---

## Docker 模式测试

### 步骤 1: 启动 Docker 容器

```bash
# 启动所有服务
docker-compose -f docker-compose.prod.yml up -d

# 查看容器状态
docker-compose -f docker-compose.prod.yml ps

# 预期输出:
# NAME                    STATUS
# data-management-db      Up 30s (healthy)
# data-management-backend Up 25s (healthy)
# data-management-frontend Up 20s (healthy)
# data-management-redis   Up 25s (healthy)
# data-management-nginx   Up 15s (healthy)
```

### 步骤 2: 验证服务启动

```bash
# 检查后端日志
docker-compose -f docker-compose.prod.yml logs backend

# 检查前端日志
docker-compose -f docker-compose.prod.yml logs frontend

# 检查数据库日志
docker-compose -f docker-compose.prod.yml logs postgres
```

### 步骤 3: 等待服务健康

```bash
# 脚本会自动等待，但可以手动检查：

# 后端健康检查
curl -s http://localhost:8000/health | jq .

# 前端页面加载
curl -s http://localhost:5173 | head -20

# 数据库连接
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U postgres -c "SELECT 1"
```

### 步骤 4: 运行集成测试

```bash
./run-integration-tests.sh
```

### 步骤 5: 查看测试结果

```bash
# 列出测试结果文件
ls -la test-results/

# 查看最新的 HTML 报告
open test-results/integration_test_report_*.html  # macOS
xdg-open test-results/integration_test_report_*.html  # Linux
start test-results/integration_test_report_*.html  # Windows
```

### 步骤 6: 清理容器

```bash
# 停止所有容器
docker-compose -f docker-compose.prod.yml down

# 删除容器和卷（包括数据库数据）
docker-compose -f docker-compose.prod.yml down -v

# 删除镜像（如需重新构建）
docker-compose -f docker-compose.prod.yml down --rmi all
```

---

## 手动 API 测试

### 1. 测试文件上传

```bash
# 创建测试文件
cat > test.csv << 'EOF'
id,name,email,age
1,Alice,alice@example.com,28
2,Bob,bob@example.com,34
3,Charlie,charlie@example.com,25
EOF

# 上传文件
curl -X POST \
  -F "file=@test.csv" \
  -F "data_source_id=1" \
  http://localhost:8000/api/file-uploads

# 预期响应:
# {
#   "id": 1,
#   "filename": "test.csv",
#   "file_format": "csv",
#   "file_size": 89,
#   "parse_status": "pending",
#   "created_at": "2025-11-10T12:00:00Z"
# }
```

### 2. 测试文件列表

```bash
curl -X GET \
  "http://localhost:8000/api/file-uploads?skip=0&limit=20"

# 预期响应:
# {
#   "items": [
#     {
#       "id": 1,
#       "filename": "test.csv",
#       "file_format": "csv",
#       "file_size": 89,
#       "parse_status": "success",
#       "created_at": "2025-11-10T12:00:00Z"
#     }
#   ],
#   "total": 1,
#   "skip": 0,
#   "limit": 20
# }
```

### 3. 测试文件预览

```bash
curl -X GET \
  "http://localhost:8000/api/file-uploads/1/preview?max_rows=100"

# 预期响应:
# {
#   "file_id": 1,
#   "filename": "test.csv",
#   "total_rows": 3,
#   "displayed_rows": 3,
#   "columns": ["id", "name", "email", "age"],
#   "data": [
#     {"id": "1", "name": "Alice", "email": "alice@example.com", "age": "28"},
#     ...
#   ]
# }
```

### 4. 测试文件删除

```bash
curl -X DELETE \
  http://localhost:8000/api/file-uploads/1

# 预期响应:
# {
#   "success": true,
#   "message": "File deleted successfully"
# }
```

---

## 测试结果解释

### API 健康检查 (✅ 通过)

- **含义**: 后端 API 正常运行，可以接收请求
- **失败**: API 无法连接或返回错误

### 文件上传 API (✅ 通过)

- **含义**: 可以成功上传文件并得到正确的响应
- **失败**: 上传失败、响应格式错误或文件存储出现问题
- **常见原因**:
  - 磁盘空间不足
  - 上传目录权限问题
  - 文件大小超过限制

### 文件列表 API (✅ 通过)

- **含义**: 可以成功查询已上传的文件列表
- **失败**: 数据库查询错误或响应格式错误
- **常见原因**:
  - 数据库连接问题
  - ORM 查询错误

### 前端页面加载 (✅ 通过)

- **含义**: 前端应用成功加载并渲染 HTML
- **失败**: 前端服务未运行或页面出现错误
- **常见原因**:
  - 前端进程已崩溃
  - 构建输出不完整

### 性能测试 (✅ 通过 / ⚠️ 警告)

- **通过**: API 平均响应时间 < 500ms
- **警告**: API 平均响应时间 > 500ms
- **含义**: 系统满足基本性能要求

---

## 故障排查

### 问题 1: 后端无法启动

**症状**: `./start-backend.sh dev` 运行后立即退出

**排查步骤**:

```bash
# 1. 检查 Python 安装
python3 --version

# 2. 检查虚拟环境
ls backend/.venv

# 3. 检查依赖
poetry show

# 4. 检查 .env 文件
cat backend/.env

# 5. 检查数据库连接
psql $DATABASE_URL -c "SELECT 1"

# 6. 查看详细错误
cd backend && poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 问题 2: 前端无法启动

**症状**: `./start-frontend.sh` 出现 npm 错误

**排查步骤**:

```bash
# 1. 检查 Node.js
node --version && npm --version

# 2. 清理依赖
rm -rf frontend/node_modules frontend/package-lock.json

# 3. 重新安装
cd frontend && npm install

# 4. 检查环境文件
cat frontend/.env.local

# 5. 查看详细错误
npm run dev
```

### 问题 3: 数据库连接失败

**症状**: 后端启动后立即显示数据库连接错误

**排查步骤**:

```bash
# 1. 检查 PostgreSQL 运行状态
psql -U postgres -h localhost -c "SELECT 1"

# 2. 检查数据库存在
psql -U postgres -l | grep data_management

# 3. 创建数据库
createdb -U postgres data_management

# 4. 检查连接字符串
echo $DATABASE_URL

# 5. 测试连接
psql $(echo $DATABASE_URL | sed 's/postgresql:\/\///')
```

### 问题 4: 端口已被占用

**症状**: `Address already in use` 错误

**排查步骤**:

```bash
# 1. 查看占用进程
lsof -i :8000  # 后端
lsof -i :5173  # 前端

# 2. 杀死进程
kill -9 <PID>

# 3. 或更改端口（在 .env 中）
API_PORT=8001
```

### 问题 5: CORS 错误

**症状**: 前端页面加载但 API 请求被 CORS 拦截

**排查步骤**:

```bash
# 1. 检查后端 CORS 配置
cat backend/.env | grep CORS

# 2. 确保前端 URL 在允许列表中
CORS_ORIGINS=["http://localhost:5173"]

# 3. 检查前端 API 配置
cat frontend/.env.local | grep VITE_API_URL

# 4. 重启后端
./start-backend.sh dev
```

---

## 测试报告

### 报告位置

所有测试报告保存在 `test-results/` 目录：

```
test-results/
├── integration_test_report_20251110_120000.html  # HTML 报告
├── upload_response_20251110_120000.json          # 上传 API 响应
├── upload_error_20251110_120000.json             # 上传错误（如有）
└── test_file_20251110_120000.csv                 # 测试文件
```

### 报告内容

HTML 报告包括：

- **测试概览**: 各项测试结果 (✅ 通过/❌ 失败)
- **测试统计**: 总测试数、通过数、失败数、成功率
- **执行时间**: 报告生成时间戳
- **性能指标**: API 响应时间、吞吐量

### 查看报告

```bash
# 打开最新报告
open test-results/integration_test_report_*.html

# 或使用浏览器
google-chrome test-results/integration_test_report_*.html

# 或简单查看文本
cat test-results/integration_test_report_*.html
```

---

## 持续集成建议

### GitHub Actions 工作流

```yaml
# .github/workflows/integration-tests.yml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Start Backend
        run: |
          cd backend
          ./start-backend.sh dev &
          sleep 30

      - name: Start Frontend
        run: |
          cd frontend
          npm install
          npm run build

      - name: Run Tests
        run: ./run-integration-tests.sh

      - name: Upload Report
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-results
          path: test-results/
```

---

## 总结

✅ **集成测试清单**:

- [ ] 前置条件已检查
- [ ] 后端服务已启动
- [ ] 前端服务已启动
- [ ] API 健康检查通过
- [ ] 文件上传测试通过
- [ ] 文件列表测试通过
- [ ] 前端页面加载成功
- [ ] 性能指标满足要求
- [ ] 测试报告已生成
- [ ] 所有故障已排查和解决

**下一步**: 继续进行 E2E 测试 (T081)、性能和安全审计 (T082)

---

**文档结束** | 最后更新: 2025-11-10

# 系统集成测试计划

**阶段**: Phase 5 - 集成测试和部署
**日期**: 2025-11-10
**目标**: 前后端完全联调，准备生产部署

---

## 📋 测试计划概述

### 测试类型

1. **API 集成测试** - 前端与后端 API 通信测试
2. **端到端测试 (E2E)** - 完整的用户场景测试
3. **性能测试** - 性能基准和优化
4. **安全测试** - 安全漏洞扫描

### 测试环境

| 环境 | 地址 | 用途 |
|------|------|------|
| 本地开发 | http://localhost:5173 | 开发调试 |
| 本地后端 | http://localhost:8000 | 后端 API |
| 测试环境 | staging.example.com | 集成测试 |
| 生产环境 | api.example.com | 最终部署 |

---

## 🧪 测试场景

### 1. 文件上传流程

**测试步骤:**
1. 访问首页
2. 点击"开始上传"
3. 选择 CSV/XLSX 文件
4. 监控上传进度
5. 验证文件列表更新
6. 检查解析状态

**预期结果:**
- 文件成功上传
- 进度条正确显示
- 列表实时更新
- 解析状态从 pending → success

### 2. 文件预览流程

**测试步骤:**
1. 从文件列表选择已上传的文件
2. 点击预览
3. 查看文件元数据
4. 浏览数据内容
5. 测试分页
6. 测试 Excel 多工作表

**预期结果:**
- 元数据正确显示
- 数据类型正确识别
- 分页功能正常
- 工作表切换正常

### 3. 错误处理

**测试步骤:**
1. 上传过大文件（超过限制）
2. 上传不支持的格式
3. 网络中断恢复
4. 后端错误响应

**预期结果:**
- 显示友好的错误提示
- 自动重试机制启动
- 错误日志记录完整

---

## 🔧 API 集成检查表

### 文件管理 API

- [ ] POST /api/file-uploads - 上传文件
- [ ] GET /api/file-uploads - 获取文件列表
- [ ] GET /api/file-uploads/{id} - 获取文件详情
- [ ] DELETE /api/file-uploads/{id} - 删除文件
- [ ] GET /api/file-uploads/{id}/preview - 获取预览
- [ ] GET /api/file-uploads/{id}/metadata - 获取元数据
- [ ] GET /api/file-uploads/{id}/sheets - 获取 Excel 工作表
- [ ] POST /api/file-uploads/{id}/parse - 解析文件

### 数据源 API

- [ ] GET /api/datasources - 获取数据源列表
- [ ] POST /api/datasources - 创建数据源
- [ ] GET /api/datasources/{id} - 获取数据源详情
- [ ] PUT /api/datasources/{id} - 更新数据源
- [ ] DELETE /api/datasources/{id} - 删除数据源
- [ ] POST /api/datasources/{id}/test - 测试连接

### Schema API

- [ ] GET /api/datasources/{id}/schema - 获取 Schema
- [ ] GET /api/datasources/{id}/tables - 获取表列表
- [ ] GET /api/datasources/{id}/tables/{name} - 获取表详情

---

## 📊 性能测试标准

| 指标 | 目标 | 单位 |
|------|------|------|
| 页面加载时间 | < 3 | 秒 |
| API 响应时间 | < 500 | 毫秒 |
| 文件上传速度 | > 5 | MB/s |
| 并发用户数 | > 100 | 用户 |
| 错误率 | < 0.1 | % |

---

## 🔐 安全测试项

- [ ] XSS 漏洞扫描
- [ ] SQL 注入测试
- [ ] CSRF 防护验证
- [ ] 认证和授权测试
- [ ] 敏感数据泄露检查
- [ ] 依赖库漏洞扫描

---

## 📈 部署前检查

### 前端检查

- [ ] npm run build 成功
- [ ] npm run lint 无错误
- [ ] npm test 全部通过
- [ ] 性能评分 > 80
- [ ] 无 console 错误

### 后端检查

- [ ] pytest 全部通过
- [ ] 代码覆盖率 > 80%
- [ ] 无安全漏洞
- [ ] 数据库迁移成功
- [ ] API 文档更新完整

---

## 🚀 部署步骤

### 本地测试

```bash
# 启动后端
cd backend
poetry install
poetry run uvicorn src.main:app --reload

# 启动前端
cd frontend
npm install
npm run dev
```

### Docker 部署

```bash
# 构建镜像
docker build -t system-frontend:latest ./frontend
docker build -t system-backend:latest ./backend

# 运行容器
docker-compose up -d
```

### 云部署

```bash
# Vercel 部署前端
vercel deploy

# 云服务器部署后端
ssh user@server
git clone repo
cd backend
poetry install
poetry run gunicorn -w 4 -b 0.0.0.0:8000 src.main:app
```

---

## 📝 测试报告

报告将在以下位置生成：
- 单元测试: `coverage/`
- 集成测试: `test-results/`
- E2E 测试: `e2e-results/`

---

## ✅ 完成标准

项目通过集成测试需要满足：

1. **功能完整** - 所有用户场景正常运行
2. **性能达标** - 所有性能指标达到目标
3. **安全审核** - 无重大安全漏洞
4. **文档完整** - API 文档和部署文档完整
5. **零 Bug** - 关键路径无 Bug，非关键 Bug < 5 个

---

**下一步**: 实施系统集成测试和端到端测试

*生成于 2025-11-10*

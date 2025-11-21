# 📅 Week 2 开发计划与进度跟踪

**开始日期**: 2025-11-21
**周期**: Week 2 (5 天工作日)
**目标**: 完成 Story 4.3 和 Story 4.4，准备生产发布
**系统状态**: ✅ 后端和前端都在正常运行

---

## 🎯 Week 2 任务概览

### Story 4.3: 功能定制与优化 (5 SP)
目标: 增强用户体验，添加实用功能

| # | 功能 | 优先级 | 状态 | 预计时间 |
|---|------|--------|------|---------|
| 1 | 输入指示器 (显示正在输入) | 🔴 高 | ⏳ 待开始 | 0.5 天 |
| 2 | 自动生成对话标题 | 🟠 中 | ⏳ 待开始 | 0.5 天 |
| 3 | 消息搜索功能 (全文搜索) | 🟠 中 | ⏳ 待开始 | 1 天 |
| 4 | 消息导出 (JSON/PDF) | 🟠 中 | ⏳ 待开始 | 1 天 |
| 5 | 暗模式切换 (主题系统) | 🟡 低 | ⏳ 待开始 | 1 天 |

### Story 4.4: 部署与发布 (5 SP)
目标: 准备生产环境，建立部署流程

| # | 任务 | 优先级 | 状态 | 预计时间 |
|---|------|--------|------|---------|
| 1 | 环境配置管理 | 🔴 高 | ⏳ 待开始 | 0.5 天 |
| 2 | Docker 容器化 | 🔴 高 | ⏳ 待开始 | 1 天 |
| 3 | CI/CD 流程设置 | 🔴 高 | ⏳ 待开始 | 1.5 天 |
| 4 | 监控告警配置 | 🟠 中 | ⏳ 待开始 | 0.5 天 |
| 5 | 上线检查清单 | 🟡 低 | ⏳ 待开始 | 0.5 天 |

---

## 📊 当前系统状态

### ✅ 已完成的工作 (Week 1)

#### Story 4.2: 前端核心组件开发
- ✅ 5个核心 React 组件 (1,300 LOC)
- ✅ Zustand 状态管理 (3 stores)
- ✅ 8个自定义 Hooks
- ✅ API 服务层集成
- ✅ TypeScript 严格模式 (0 错误)
- ✅ 生产 Bundle: 102.93 KB (gzipped)
- ✅ 测试框架: 24 个组件测试 + 10 个 API 集成测试

#### Milestone M2 验收签署
- ✅ 所有验收标准已满足
- ✅ 代码质量: A+ (95/100)
- ✅ 生产就绪: **APPROVED FOR PRODUCTION**

### ✅ 基础设施验证

| 组件 | 状态 | 细节 |
|------|------|------|
| **后端服务器** | ✅ 运行中 | PID 4376, 端口 8000, 健康检查通过 |
| **前端服务器** | ✅ 运行中 | PID 35578, 端口 5173, HMR 启用 |
| **数据库** | ✅ 就绪 | PostgreSQL 5432, 连接池初始化完成 |
| **网络连通性** | ✅ 验证 | 前后端通信正常, API 响应正常 |
| **开发环境** | ✅ 完整 | Node 18+, Python 3.12+, Git, Docker |

---

## 🚀 Week 2 详细计划

### 第1天 (Monday): Story 4.3 - 前半部分
**主要目标**: 完成功能 1-3

#### 上午 (2小时)
- 🎯 **任务 1**: 实现输入指示器
  - 前端: 在消息列表底部显示"用户正在输入..."
  - 后端: 通过 WebSocket 实时推送输入状态
  - 实现文件: `ChatInterface.tsx`, WebSocket 消息处理
  - 预期代码: ~50 LOC

#### 下午 (2小时)
- 🎯 **任务 2**: 自动生成对话标题
  - 前端: 获取首条消息内容
  - 后端: 使用 Claude 生成标题 (可选)
  - 实现文件: `Sidebar.tsx`, API 集成
  - 预期代码: ~40 LOC

#### 傍晚 (1小时)
- 📝 测试任务 1 和 2
- 📝 更新相关文档

---

### 第2天 (Tuesday): Story 4.3 - 中间部分
**主要目标**: 完成功能 3-4

#### 上午 (2.5小时)
- 🎯 **任务 3**: 消息搜索功能
  - 前端: 添加搜索输入框, 实时过滤消息
  - 搜索逻辑: 支持文本内容、发送者、日期范围
  - 实现文件: `ChatInterface.tsx`, 新建 `SearchBar.tsx`
  - 预期代码: ~100 LOC

#### 下午 (1.5小时)
- 🎯 **任务 4**: 消息导出功能
  - 前端: 添加导出按钮 (JSON/PDF)
  - JSON 导出: 直接使用 JSON.stringify
  - PDF 导出: 使用 jsPDF 或 html2pdf 库
  - 实现文件: `ChatInterface.tsx`, 新建 `ExportButton.tsx`
  - 预期代码: ~80 LOC

#### 傍晚 (1小时)
- 📝 测试任务 3 和 4
- 📝 集成测试

---

### 第3天 (Wednesday): Story 4.3 - 后期 + Story 4.4 启动
**主要目标**: 完成功能 5, 启动 Story 4.4

#### 上午 (2小时)
- 🎯 **任务 5**: 暗模式切换
  - 前端: Tailwind Dark Mode 配置
  - 状态管理: Zustand store (UI store)
  - UI: Theme Toggle Button in Header
  - 实现文件: `App.tsx`, 新增 `tailwind.config.js` 配置
  - 预期代码: ~60 LOC + CSS

#### 下午 (2小时)
- 🎯 **Story 4.4 启动**: 环境配置管理
  - 创建 `.env.development`, `.env.staging`, `.env.production`
  - 配置文件模板: API URL, 日志级别, 功能开关
  - 文档: 环境变量说明
  - 预期代码: 3 个配置文件

#### 傍晚 (1小时)
- 📝 Story 4.3 的最终测试和 QA
- 📝 性能基准测试 (Lighthouse)

---

### 第4天 (Thursday): Story 4.4 - 主要部分
**主要目标**: 完成 Docker 化和 CI/CD 基础

#### 上午 (2小时)
- 🎯 **Docker 容器化 (前端)**
  - 创建 `Dockerfile` (多阶段构建)
  - 创建 `docker-compose.yml` (前端 + 后端)
  - 构建和测试镜像
  - 预期代码: Dockerfile (30 LOC) + docker-compose.yml (40 LOC)

#### 下午 (2小时)
- 🎯 **CI/CD 流程设置 (GitHub Actions)**
  - 创建 `.github/workflows/`
  - 工作流: Test, Build, Deploy
  - 配置自动化测试和构建
  - 预期代码: YAML 配置 (100+ 行)

#### 傍晚 (1小时)
- 📝 Docker 和 CI/CD 测试
- 📝 修复遇到的问题

---

### 第5天 (Friday): Story 4.4 - 完成 + QA
**主要目标**: 完成监控、检查清单、最终 QA

#### 上午 (2小时)
- 🎯 **监控告警配置**
  - Sentry 错误追踪集成
  - 日志聚合配置 (可选)
  - 性能监控配置
  - 预期代码: Sentry 初始化 (20 LOC)

#### 下午 (2小时)
- 🎯 **上线检查清单**
  - 创建 `DEPLOYMENT_CHECKLIST.md`
  - 检查清单: 安全性、性能、功能、兼容性
  - 发布前验证步骤

#### 傍晚 (1小时)
- 📝 完整的端到端测试
- 📝 性能基准测试
- 📝 交叉浏览器兼容性测试
- 📝 生成 Week 2 总结报告

---

## 📋 关键实现细节

### Story 4.3 实现指南

#### 1️⃣ 输入指示器
```typescript
// 前端: 添加到 ChatInterface
- 监听 WebSocket "user_typing" 事件
- 显示 "用户正在输入..." 消息（带动画）
- 5秒超时后自动隐藏
```

#### 2️⃣ 自动标题生成
```typescript
// 前端: 在创建新对话时
- 获取首条用户消息
- 调用 API: POST /api/v1/conversations/{id}/generate-title
// 后端需要实现该 API
```

#### 3️⃣ 消息搜索
```typescript
// 前端: 客户端过滤 (不需要后端)
- 维护本地消息列表
- 实时搜索和过滤
- 高亮匹配结果
```

#### 4️⃣ 消息导出
```typescript
// 前端: 使用库
- JSON: JSON.stringify + 文件下载
- PDF: 使用 jsPDF 或 html2pdf
```

#### 5️⃣ 暗模式
```typescript
// 前端: Tailwind 原生支持
- tailwind.config.js: darkMode: 'class'
- App 组件根元素动态添加 dark class
- Zustand store 管理主题状态
```

### Story 4.4 实现指南

#### 1️⃣ 环境配置
```
.env.development    - 本地开发
.env.staging        - 测试环境
.env.production     - 生产环境
```

#### 2️⃣ Docker 化
```dockerfile
# 多阶段构建
FROM node:18 AS builder
WORKDIR /app
COPY . .
RUN npm install && npm run build

FROM node:18-alpine
COPY --from=builder /app/dist /app
EXPOSE 5173
```

#### 3️⃣ CI/CD
```yaml
# GitHub Actions
- 触发: push to main, PR
- 步骤:
  1. 安装依赖
  2. 运行测试
  3. 构建产物
  4. 构建 Docker 镜像
  5. 推送到仓库
  6. 部署到服务器 (可选)
```

---

## 📁 新增文件清单

### Story 4.3
```
frontend/src/components/
├── Chat/SearchBar.tsx          (新建)
├── Chat/ExportButton.tsx       (新建)
├── Chat/TypingIndicator.tsx    (新建)
├── Header.tsx                  (新增主题切换)

frontend/src/store/
├── uiStore.ts                  (新增主题管理)

frontend/styles/
├── dark-mode.css               (新建)
```

### Story 4.4
```
.env.development               (新建)
.env.staging                   (新建)
.env.production                (新建)

Dockerfile                     (新建)
docker-compose.yml             (新建)

.github/workflows/
├── test.yml                   (新建)
├── build.yml                  (新建)
├── deploy.yml                 (新建)

docs/
├── DEPLOYMENT_CHECKLIST.md     (新建)
├── ENVIRONMENT_GUIDE.md        (新建)
├── CI_CD_SETUP.md              (新建)
```

---

## ✅ 完成标准

### Story 4.3 完成标准
- [ ] 所有 5 个功能都实现并可用
- [ ] 单元测试覆盖率 > 80%
- [ ] 代码审查通过
- [ ] 性能无降低 (Bundle 大小 < 130 KB)
- [ ] 跨浏览器兼容性验证

### Story 4.4 完成标准
- [ ] 所有环境文件创建完成
- [ ] Docker 镜像构建成功
- [ ] CI/CD 工作流正常运行
- [ ] 至少一次完整部署验证
- [ ] 部署检查清单已创建

---

## 🎯 成功指标

| 指标 | 目标 | 预期值 |
|------|------|--------|
| **代码质量** | 零新错误 | ✅ |
| **测试覆盖** | > 80% | ✅ |
| **性能** | Bundle 无增长 | < 130 KB |
| **可部署性** | 一键部署 | Docker + GitHub Actions |
| **用户体验** | 5个新功能 | All working |

---

## 📞 技术支持

如遇到以下问题，请参考:
- 前端组件问题 → 检查 `src/components/`
- 状态管理问题 → 检查 `src/store/`
- API 集成问题 → 检查后端 API 路由
- Docker 问题 → 参考 `Dockerfile` 和 `docker-compose.yml`
- CI/CD 问题 → 检查 `.github/workflows/`

---

**最后更新**: 2025-11-21 04:54 UTC
**计划状态**: 准备开始执行
**下一步**: 开始 Story 4.3 任务 1 - 输入指示器实现

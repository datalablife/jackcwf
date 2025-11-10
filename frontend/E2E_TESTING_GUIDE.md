# E2E 测试实施指南

**文档版本**: 1.0
**创建日期**: 2025-11-10
**框架**: Playwright v1.46.1

---

## 📋 目录

1. [概述](#概述)
2. [安装和配置](#安装和配置)
3. [运行测试](#运行测试)
4. [测试文件说明](#测试文件说明)
5. [编写新测试](#编写新测试)
6. [调试和故障排查](#调试和故障排查)
7. [CI/CD 集成](#cicd-集成)

---

## 概述

### 测试覆盖范围

本项目包含 5 个 E2E 测试套件，共 40+ 个测试用例：

| 测试文件 | 覆盖范围 | 测试用例数 |
|---------|---------|----------|
| `navigation.spec.ts` | 首页、导航、路由 | 7 个 |
| `file-upload.spec.ts` | 文件上传工作流 | 8 个 |
| `file-preview.spec.ts` | 文件预览功能 | 9 个 |
| `datasource.spec.ts` | 数据源管理 | 9 个 |
| `error-handling.spec.ts` | 错误处理和异常 | 10 个 |

### 浏览器和设备

Playwright 配置支持以下环境：

**桌面浏览器**:
- Chromium (基于 Chrome)
- Firefox
- WebKit (Safari)

**移动设备模拟**:
- Pixel 5 (Android)
- iPhone 12 (iOS)

---

## 安装和配置

### 第 1 步：安装依赖

```bash
cd frontend

# 安装 Playwright 及其浏览器
npm install @playwright/test --save-dev

# 安装 Playwright 浏览器驱动
npx playwright install
```

### 第 2 步：验证安装

```bash
# 检查 Playwright 版本
npx playwright --version

# 生成 Playwright 示例项目（可选）
npx playwright codegen http://localhost:5173
```

### 第 3 步：配置验证

确保以下文件存在：

```bash
frontend/
├── playwright.config.ts          # 主配置文件
├── tests/
│   └── e2e/
│       ├── navigation.spec.ts
│       ├── file-upload.spec.ts
│       ├── file-preview.spec.ts
│       ├── datasource.spec.ts
│       └── error-handling.spec.ts
└── package.json                  # 包含 test:e2e 脚本
```

---

## 运行测试

### 基础命令

```bash
# 运行所有 E2E 测试
npm run test:e2e

# 运行特定测试文件
npm run test:e2e navigation.spec.ts

# 运行特定测试套件
npm run test:e2e -- --grep "首页和导航"

# 运行特定浏览器
npm run test:e2e -- --project=chromium
npm run test:e2e -- --project=firefox
npm run test:e2e -- --project=webkit

# 运行移动设备测试
npm run test:e2e -- --project="Mobile Chrome"
npm run test:e2e -- --project="Mobile Safari"
```

### 交互式测试（推荐用于开发）

```bash
# UI 模式（实时查看测试执行）
npm run test:e2e:ui

# 调试模式（逐步执行）
npm run test:e2e:debug

# 监视模式（文件变化时重新运行）
npm run test:e2e -- --watch
```

### 生成报告

```bash
# 生成 HTML 报告
npm run test:e2e
# 报告位置: playwright-report/index.html

# 打开报告
npx playwright show-report
```

### 运行前置条件

确保以下服务正在运行：

```bash
# 终端 1: 启动后端
cd backend
./start-backend.sh dev

# 终端 2: 启动前端
cd frontend
npm run dev

# 终端 3: 运行测试
npm run test:e2e
```

---

## 测试文件说明

### 1. navigation.spec.ts

**目的**: 验证首页加载和应用导航

**覆盖的场景**:
- 首页加载成功
- 导航栏显示所有链接
- 导航链接功能正常
- 移动端菜单切换
- 响应式布局

**关键测试**:
```typescript
test('首页加载成功', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: /数据文件管理系统/ })).toBeVisible()
})
```

### 2. file-upload.spec.ts

**目的**: 验证文件上传的完整工作流

**覆盖的场景**:
- 文件选择和上传
- 上传进度显示
- 文件列表管理
- 文件删除功能
- 大文件上传
- 错误文件类型处理

**关键测试**:
```typescript
test('可以选择并上传 CSV 文件', async ({ page }) => {
  const fileInput = page.locator('input[type="file"]')
  await fileInput.setInputFiles(testFilePath)
  await expect(page.getByText(/test.csv/)).toBeVisible()
})
```

### 3. file-preview.spec.ts

**目的**: 验证文件预览和数据展示

**覆盖的场景**:
- 预览页面加载
- 文件元数据显示
- 数据表格渲染
- 表格分页
- Excel 表单选择
- 响应式预览

**关键测试**:
```typescript
test('可以查看数据表格预览', async ({ page }) => {
  await page.goto('/preview/1')
  const table = page.locator('table')
  await expect(table).toBeVisible()
})
```

### 4. datasource.spec.ts

**目的**: 验证数据源管理功能

**覆盖的场景**:
- 数据源列表显示
- 添加新数据源
- 测试连接功能
- 编辑数据源
- 删除数据源
- 错误处理

**关键测试**:
```typescript
test('可以测试数据库连接', async ({ page }) => {
  const testButton = page.getByRole('button', { name: /测试/ })
  await testButton.click()
  const result = await page.getByText(/成功|失败/).isVisible()
  expect(result).toBeTruthy()
})
```

### 5. error-handling.spec.ts

**目的**: 验证错误处理和边界情况

**覆盖的场景**:
- API 连接失败
- 网络超时
- 服务器错误 (500)
- 未授权 (401) 错误
- CORS 错误处理
- 离线支持
- 表单验证

**关键测试**:
```typescript
test('后端 API 连接失败时显示错误', async ({ page }) => {
  await page.route('**/api/**', (route) => {
    route.abort('failed')
  })
  await page.goto('/upload')
  const error = page.locator('[class*="error"]')
  // 检查是否显示错误
})
```

---

## 编写新测试

### 基本结构

```typescript
import { test, expect } from '@playwright/test'

test.describe('功能名称', () => {
  test.beforeEach(async ({ page }) => {
    // 每个测试前的准备
    await page.goto('/')
  })

  test('应该做某事', async ({ page }) => {
    // 操作
    await page.getByRole('button', { name: /点击/ }).click()

    // 断言
    await expect(page.getByText(/结果/)).toBeVisible()
  })
})
```

### 常见测试模式

#### 1. 元素可见性测试

```typescript
test('按钮可见', async ({ page }) => {
  const button = page.getByRole('button', { name: /保存/ })
  await expect(button).toBeVisible()
})
```

#### 2. 导航测试

```typescript
test('点击导航链接', async ({ page }) => {
  await page.getByRole('link', { name: /上传/ }).click()
  await expect(page).toHaveURL(/\/upload/)
})
```

#### 3. 表单填充和提交

```typescript
test('提交表单', async ({ page }) => {
  await page.getByLabel(/用户名/).fill('testuser')
  await page.getByLabel(/密码/).fill('password123')
  await page.getByRole('button', { name: /登录/ }).click()
})
```

#### 4. 文件上传

```typescript
test('上传文件', async ({ page }) => {
  const fileInput = page.locator('input[type="file"]')
  await fileInput.setInputFiles('path/to/file.csv')
  await expect(page.getByText(/file.csv/)).toBeVisible()
})
```

#### 5. API 模拟

```typescript
test('模拟 API 响应', async ({ page }) => {
  await page.route('**/api/users/**', (route) => {
    route.fulfill({
      status: 200,
      body: JSON.stringify({ id: 1, name: 'Test' })
    })
  })
})
```

#### 6. 等待条件

```typescript
test('等待元素加载', async ({ page }) => {
  await page.waitForLoadState('networkidle')
  await expect(page.locator('[class*="data"]')).toBeVisible()
})
```

### 最佳实践

✅ **推荐**:
- 使用语义化的定位器 (`getByRole`, `getByLabel`)
- 使用明确的测试名称，说明预期行为
- 添加适当的等待条件
- 分离测试关注点
- 使用 Page Object 模式（对于复杂 UI）

❌ **避免**:
- 使用不稳定的定位器 (类名、ID 可能改变)
- 硬编码的等待时间
- 在单个测试中做过多操作
- 依赖全局状态
- 使用过于复杂的选择器

---

## 调试和故障排查

### 运行单个测试

```bash
# 运行特定文件中的特定测试
npm run test:e2e -- --grep "应该加载首页"

# 运行特定文件
npm run test:e2e navigation.spec.ts
```

### 查看失败详情

```bash
# 运行并保留失败的痕迹
npm run test:e2e

# 生成的报告包含：
# - 截图（失败时刻）
# - 视频录制
# - 执行日志
# - 网络请求
```

### 调试模式

```bash
# 逐步执行，可以在任何地方添加断点
npm run test:e2e:debug

# 或在测试中添加 pause()
test('example', async ({ page }) => {
  await page.goto('/')
  await page.pause()  // 执行会暂停在这里
})
```

### UI 模式调试

```bash
npm run test:e2e:ui

# 功能：
# - 实时看到测试执行
# - 暂停和逐步执行
# - 检查定位器
# - 记录执行步骤
```

### 常见问题

#### 问题 1: 测试超时

**错误**: `Timeout 30000ms exceeded`

**解决方案**:
```typescript
test('长操作', async ({ page }) => {
  // 增加超时时间
  await page.goto('/', { waitUntil: 'networkidle', timeout: 60000 })
})
```

#### 问题 2: 元素找不到

**错误**: `locator.click: Target page, context or browser has been closed`

**解决方案**:
- 确保等待正确的元素
- 检查元素定位器是否正确
- 添加适当的等待条件

```typescript
// 好的：等待元素可见后再操作
await expect(button).toBeVisible()
await button.click()

// 不好的：直接操作，可能元素还未加载
await button.click()
```

#### 问题 3: 测试依赖问题

**原因**: 测试执行顺序问题导致的不稳定

**解决方案**:
- 确保每个测试都是独立的
- 在 `beforeEach` 中设置初始状态
- 不要依赖其他测试的副作用

```typescript
test.beforeEach(async ({ page }) => {
  // 每个测试都从清晰的初始状态开始
  await page.goto('/')
  await page.waitForLoadState('networkidle')
})
```

---

## CI/CD 集成

### GitHub Actions 工作流

```yaml
# .github/workflows/e2e-tests.yml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm ci

      - name: Start backend
        run: |
          cd backend
          ./start-backend.sh dev &
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost/test_db

      - name: Run E2E tests
        run: npm run test:e2e

      - name: Upload test report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/
```

### 本地 CI 模拟

```bash
# 模拟 CI 环境运行
CI=true npm run test:e2e
```

### 持续测试

```bash
# 文件变化时自动运行测试
npm run test:e2e -- --watch
```

---

## 测试维护

### 定期审查

定期检查以下内容：

- [ ] 测试是否仍然与应用匹配
- [ ] 是否需要更新定位器
- [ ] 新功能是否需要新测试
- [ ] 过时的测试是否应该删除

### 更新测试

当 UI 或功能改变时：

```bash
# 使用 Codegen 生成新的定位器
npx playwright codegen http://localhost:5173
```

### 测试覆盖率

```bash
# 检查测试覆盖的用户流程
npm run test:e2e -- --reporter=html

# 分析哪些功能已测试，哪些未测试
```

---

## 性能优化

### 并行执行

```bash
# 使用 4 个 workers 并行运行测试
npm run test:e2e -- --workers=4
```

### 结果缓存

```bash
# Playwright 会自动缓存认证和会话
# 在配置中启用会话重用可加快测试
```

### 选择性测试

```bash
# 只运行关键路径测试
npm run test:e2e -- --grep "上传|预览"
```

---

## 后续任务

### T082: 性能和安全测试

- 使用 Artillery 进行负载测试
- OWASP ZAP 安全扫描
- Lighthouse 性能审计

### 文档和报告

- 生成测试报告
- 维护测试文档
- 发布测试覆盖率指标

---

## 参考资源

- **Playwright 文档**: https://playwright.dev
- **测试最佳实践**: https://playwright.dev/docs/best-practices
- **API 参考**: https://playwright.dev/docs/api/class-playwright
- **调试指南**: https://playwright.dev/docs/debug

---

**最后更新**: 2025-11-10
**维护者**: Claude Code
**状态**: ✅ 完成

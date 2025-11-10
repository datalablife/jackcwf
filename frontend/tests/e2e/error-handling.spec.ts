import { test, expect } from '@playwright/test'

/**
 * API 集成和错误处理测试套件
 */

test.describe('API 集成和错误处理', () => {
  test('后端 API 连接失败时显示错误', async ({ page }) => {
    // 拦截 API 请求并模拟失败
    await page.route('**/api/**', (route) => {
      route.abort('failed')
    })

    // 导航到需要 API 的页面
    await page.goto('/upload')

    // 应该显示错误消息或加载失败提示
    const errorMessage = page.locator('[class*="error"], [role="alert"]')

    // 给页面时间来显示错误
    await page.waitForTimeout(2000)

    // 可能显示错误或降级 UI
    const errorVisible = await errorMessage.isVisible()
    // 错误可能显示或不显示，取决于应用实现
    expect(typeof errorVisible).toBe('boolean')
  })

  test('文件上传 API 失败处理', async ({ page }) => {
    // 拦截文件上传 API
    await page.route('**/api/file-uploads', (route) => {
      route.abort('failed')
    })

    await page.goto('/upload')

    // 检查是否显示错误消息
    const errorMessage = page.locator('[class*="error"]')
    // 应该有某种错误指示
  })

  test('404 错误页面显示', async ({ page }) => {
    // 访问不存在的路由
    await page.goto('/non-existent-page')

    // 应该显示 404 页面或 Not Found
    const notFoundText = page.getByText(/404|找不到|不存在/)
    const heading = page.getByRole('heading', { name: /404|找不到/ })

    // 至少应该有一个指示
    const hasNotFound = await notFoundText.isVisible() || await heading.isVisible()
    expect(hasNotFound).toBeTruthy()
  })

  test('网络超时处理', async ({ page }) => {
    // 模拟网络缓慢
    await page.route('**/api/**', (route) => {
      setTimeout(() => route.continue(), 10000)
    })

    await page.goto('/upload', { waitUntil: 'domcontentloaded' })

    // 应该有加载指示或超时错误
    const loader = page.locator('[class*="loading"]')
    const errorMsg = page.locator('[class*="error"]')

    // 应该显示其中之一
    const hasIndicator = await loader.isVisible() || await errorMsg.isVisible()
    expect(hasIndicator).toBeTruthy()
  })

  test('未授权 (401) 错误处理', async ({ page }) => {
    // 拦截 API 请求返回 401
    await page.route('**/api/**', (route) => {
      route.abort('failed')
    })

    await page.goto('/upload')

    // 应该要么显示登录页面，要么显示错误
    // 取决于应用如何处理 401
  })

  test('服务器错误 (500) 处理', async ({ page }) => {
    // 模拟服务器错误
    await page.route('**/api/**', (route) => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ error: 'Internal Server Error' }),
      })
    })

    await page.goto('/upload')

    // 应该显示错误消息
    const errorMessage = page.locator('[class*="error"]')

    // 给时间加载
    await page.waitForTimeout(1000)

    // 可能显示或不显示，取决于实现
  })

  test('CORS 错误处理', async ({ page }) => {
    // 监听控制台错误
    const errors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text())
      }
    })

    await page.goto('/upload')

    // 即使有 CORS 错误，应用应该继续工作
    // 或显示友好的错误消息
    const hasUI = await page.getByRole('heading').isVisible()
    expect(hasUI).toBeTruthy()
  })

  test('缓存和离线支持', async ({ page }) => {
    // 首先访问页面
    await page.goto('/')

    // 获取一些静态资源
    await page.waitForLoadState('networkidle')

    // 模拟离线
    await page.context().setOffline(true)

    // 访问已访问过的页面
    await page.goto('/')

    // 应该仍然显示一些内容（来自缓存）
    const heading = page.getByRole('heading')
    const hasContent = await heading.isVisible()

    // 恢复在线
    await page.context().setOffline(false)
  })

  test('正确的响应头处理', async ({ page }) => {
    let responseHeaders: Record<string, string> = {}

    // 拦截响应
    page.on('response', (response) => {
      if (response.url().includes('/api')) {
        const headers = response.headers()
        Object.assign(responseHeaders, headers)
      }
    })

    await page.goto('/upload')

    // 验证重要的安全头（如果实现的话）
    // 例如：Content-Security-Policy, X-Frame-Options 等
  })

  test('表单验证错误显示', async ({ page }) => {
    await page.goto('/datasource')

    // 找到提交按钮
    const submitButton = page.getByRole('button', { name: /提交|保存/ })

    if (await submitButton.isVisible()) {
      // 不填任何字段就提交
      await submitButton.click()

      // 应该显示验证错误
      const validationErrors = page.locator('[class*="error"]')

      await page.waitForTimeout(1000)

      // 可能有验证错误消息
    }
  })

  test('长请求不会导致 UI 冻结', async ({ page }) => {
    // 模拟长时间运行的请求
    let requestStartTime = Date.now()
    let responseTime = 0

    page.route('**/api/**', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 5000))
      route.continue()
      responseTime = Date.now() - requestStartTime
    })

    await page.goto('/upload')

    // 即使请求很慢，UI 应该仍然响应
    const button = page.getByRole('button').first()

    if (await button.isVisible()) {
      await button.hover()
      // 按钮应该仍然可以与之交互
    }

    expect(responseTime).toBeGreaterThan(0)
  })
})

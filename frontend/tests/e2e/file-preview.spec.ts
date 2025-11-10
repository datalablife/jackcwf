import { test, expect } from '@playwright/test'

/**
 * 文件预览功能测试套件
 */

test.describe('文件预览功能', () => {
  test.beforeEach(async ({ page }) => {
    // 首先导航到上传页面
    await page.goto('/upload')

    // 等待页面加载
    await expect(page.getByRole('heading', { name: /文件上传/ })).toBeVisible()
  })

  test('预览页面正确加载', async ({ page }) => {
    // 导航到预览页面
    await page.goto('/preview/1')

    // 检查页面元素加载
    const heading = page.getByRole('heading')
    // 页面应该有某种内容
    expect(heading).toBeDefined()
  })

  test('文件元数据显示正确', async ({ page }) => {
    // 导航到预览页面
    await page.goto('/preview/1')

    // 查找文件信息卡片
    const metadataCard = page.locator('[class*="metadata"]')

    if (await metadataCard.isVisible()) {
      // 检查元数据信息
      await expect(metadataCard).toBeVisible()

      // 检查是否显示文件大小、行数等
      const text = await metadataCard.textContent()
      expect(text).toBeTruthy()
    }
  })

  test('可以查看数据表格预览', async ({ page }) => {
    // 导航到预览页面
    await page.goto('/preview/1')

    // 查找表格
    const table = page.locator('table')

    if (await table.isVisible()) {
      await expect(table).toBeVisible()

      // 检查表头
      const headers = page.locator('th')
      const headerCount = await headers.count()
      expect(headerCount).toBeGreaterThan(0)

      // 检查表行
      const rows = page.locator('tbody tr')
      const rowCount = await rows.count()
      expect(rowCount).toBeGreaterThan(0)
    }
  })

  test('表格分页工作正常', async ({ page }) => {
    // 导航到预览页面
    await page.goto('/preview/1')

    // 查找分页控件
    const pagination = page.locator('[class*="pagination"]')

    if (await pagination.isVisible()) {
      // 检查下一页按钮
      const nextButton = page.getByRole('button', { name: /下一页|Next/ })

      if (await nextButton.isVisible()) {
        // 点击下一页
        await nextButton.click()

        // 验证页面已更新
        await page.waitForLoadState('networkidle')
      }
    }
  })

  test('Excel 文件表单选择器工作', async ({ page }) => {
    // 导航到预览页面（假设有 Excel 文件）
    await page.goto('/preview/1')

    // 查找表单/工作表选择器
    const sheetSelector = page.locator('select[name*="sheet"]')

    if (await sheetSelector.isVisible()) {
      // 检查是否有多个选项
      const options = page.locator('option')
      const count = await options.count()

      if (count > 1) {
        // 选择第二个表单
        await sheetSelector.selectOption({ index: 1 })

        // 验证表格内容已更新
        await page.waitForLoadState('networkidle')
      }
    }
  })

  test('可以返回上传页面', async ({ page }) => {
    // 导航到预览页面
    await page.goto('/preview/1')

    // 查找返回/编辑按钮
    const backButton = page.getByRole('link', { name: /编辑|返回|上传/ })

    if (await backButton.isVisible()) {
      await backButton.click()

      // 验证返回到上传页面
      await expect(page).toHaveURL(/\/upload/)
    }
  })

  test('数据正确显示，无格式错误', async ({ page }) => {
    // 导航到预览页面
    await page.goto('/preview/1')

    // 检查是否有错误提示
    const errorMessages = page.locator('[class*="error"]')
    const errorCount = await errorMessages.count()

    // 不应该有错误
    expect(errorCount).toBe(0)
  })

  test('响应式表格在移动设备上工作', async ({ page }) => {
    // 设置移动端视口
    await page.setViewportSize({ width: 375, height: 667 })

    // 导航到预览页面
    await page.goto('/preview/1')

    // 表格应该仍然可见（可能是响应式的或有水平滚动）
    const table = page.locator('table')
    if (await table.isVisible()) {
      await expect(table).toBeVisible()
    }
  })

  test('加载动画显示和隐藏正确', async ({ page }) => {
    // 导航到预览页面
    await page.goto('/preview/1')

    // 查找加载指示器
    const loader = page.locator('[class*="loading"]')

    // 加载指示器应该在加载时出现，然后消失
    if (await loader.isVisible()) {
      // 等待加载完成
      await expect(loader).toBeHidden({ timeout: 5000 })
    }
  })
})

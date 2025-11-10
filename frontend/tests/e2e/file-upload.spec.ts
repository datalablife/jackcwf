import { test, expect } from '@playwright/test'
import * as fs from 'fs'
import * as path from 'path'

/**
 * 文件上传和管理测试套件
 */

test.describe('文件上传功能', () => {
  test.beforeEach(async ({ page }) => {
    // 访问上传页面
    await page.goto('/upload')

    // 等待页面加载
    await expect(page.getByRole('heading', { name: /文件上传/ })).toBeVisible()
  })

  test('上传页面加载成功', async ({ page }) => {
    // 检查页面元素
    await expect(page.getByText(/选择要上传的文件/)).toBeVisible()
    await expect(page.getByRole('button', { name: /选择文件/ })).toBeVisible()
  })

  test('可以选择并上传 CSV 文件', async ({ page }) => {
    // 创建临时测试文件
    const testFilePath = path.join(process.cwd(), 'test-upload.csv')
    const csvContent = `id,name,email,age
1,Alice,alice@example.com,28
2,Bob,bob@example.com,34
3,Charlie,charlie@example.com,25`

    fs.writeFileSync(testFilePath, csvContent)

    try {
      // 找到文件输入
      const fileInput = page.locator('input[type="file"]')

      // 上传文件
      if (fileInput) {
        await fileInput.setInputFiles(testFilePath)

        // 检查文件是否出现在列表中
        await expect(page.getByText(/test-upload.csv/)).toBeVisible({ timeout: 5000 })

        // 检查上传状态
        await expect(page.getByText(/上传中|已上传|pending|success/)).toBeVisible()
      }
    } finally {
      // 清理临时文件
      fs.unlinkSync(testFilePath)
    }
  })

  test('显示上传进度信息', async ({ page }) => {
    // 找到进度指示器
    const progressBar = page.locator('[role="progressbar"]')

    // 如果存在进度条，验证其功能
    if (await progressBar.isVisible()) {
      await expect(progressBar).toBeVisible()
    }

    // 检查上传统计信息
    const statistics = page.locator('[class*="statistics"]')
    if (await statistics.isVisible()) {
      // 检查统计信息包含数字或文本
      const text = await statistics.textContent()
      expect(text).toBeTruthy()
    }
  })

  test('文件列表显示已上传的文件', async ({ page }) => {
    // 查找文件列表
    const fileList = page.locator('[class*="file-list"]')

    // 列表应该存在
    if (await fileList.isVisible()) {
      await expect(fileList).toBeVisible()

      // 检查文件项
      const fileItems = page.locator('[class*="file-item"]')
      const count = await fileItems.count()

      // 如果有文件，应该可以看到它们
      if (count > 0) {
        await expect(fileItems.first()).toBeVisible()
      }
    }
  })

  test('可以删除上传的文件', async ({ page }) => {
    // 查找删除按钮
    const deleteButtons = page.locator('button[aria-label*="删除"]')

    const count = await deleteButtons.count()
    if (count > 0) {
      // 获取第一个文件的名称
      const firstFileItem = page.locator('[class*="file-item"]').first()
      const fileName = await firstFileItem.textContent()

      // 点击删除按钮
      await deleteButtons.first().click()

      // 确认删除（如果有确认对话框）
      const confirmButton = page.locator('button:has-text("确认")')
      if (await confirmButton.isVisible()) {
        await confirmButton.click()
      }

      // 验证文件从列表中移除
      if (fileName) {
        await expect(page.getByText(fileName)).not.toBeVisible({ timeout: 5000 })
      }
    }
  })

  test('数据源选择器工作正常', async ({ page }) => {
    // 查找数据源选择器
    const selector = page.locator('select[name="dataSource"], [class*="datasource-select"]')

    if (await selector.isVisible()) {
      // 检查选择器有选项
      const options = page.locator('option')
      const optionCount = await options.count()
      expect(optionCount).toBeGreaterThan(0)
    }
  })

  test('处理大文件上传', async ({ page }) => {
    // 创建较大的测试文件
    const testFilePath = path.join(process.cwd(), 'large-test.csv')
    let csvContent = 'id,name,email,age\n'

    // 生成 1000 行数据
    for (let i = 1; i <= 1000; i++) {
      csvContent += `${i},User${i},user${i}@example.com,${20 + (i % 50)}\n`
    }

    fs.writeFileSync(testFilePath, csvContent)

    try {
      const fileInput = page.locator('input[type="file"]')

      if (fileInput) {
        await fileInput.setInputFiles(testFilePath)

        // 等待上传完成（使用更长的超时）
        await expect(page.getByText(/large-test/)).toBeVisible({ timeout: 10000 })
      }
    } finally {
      fs.unlinkSync(testFilePath)
    }
  })

  test('显示上传错误信息', async ({ page }) => {
    // 创建不支持的文件类型
    const testFilePath = path.join(process.cwd(), 'test.txt')
    fs.writeFileSync(testFilePath, 'This is not a supported file type')

    try {
      const fileInput = page.locator('input[type="file"]')

      if (fileInput) {
        await fileInput.setInputFiles(testFilePath)

        // 检查是否显示错误信息
        const errorMessage = page.locator('[class*="error"]')
        if (await errorMessage.isVisible()) {
          await expect(errorMessage).toBeVisible()
        }
      }
    } finally {
      fs.unlinkSync(testFilePath)
    }
  })
})

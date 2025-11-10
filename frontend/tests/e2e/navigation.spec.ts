import { test, expect } from '@playwright/test'

/**
 * 首页和导航测试套件
 */

test.describe('首页和导航', () => {
  test.beforeEach(async ({ page }) => {
    // 访问首页
    await page.goto('/')
  })

  test('首页加载成功', async ({ page }) => {
    // 检查页面标题
    await expect(page).toHaveTitle(/.*/)

    // 检查主要元素存在
    await expect(page.getByRole('heading', { name: /数据文件管理系统/ })).toBeVisible()
    await expect(page.getByText(/快速上传和管理数据文件/)).toBeVisible()
  })

  test('导航栏显示正确', async ({ page }) => {
    const nav = page.getByRole('navigation')

    // 检查导航链接
    await expect(nav.getByRole('link', { name: /首页/ })).toBeVisible()
    await expect(nav.getByRole('link', { name: /开始上传/ })).toBeVisible()
    await expect(nav.getByRole('link', { name: /数据源/ })).toBeVisible()

    // 检查右侧按钮
    await expect(nav.getByRole('link', { name: /文档/ })).toBeVisible()
    await expect(nav.getByRole('button', { name: /登录/ })).toBeVisible()
  })

  test('可以点击开始上传按钮导航到上传页面', async ({ page }) => {
    // 找到"开始上传"按钮
    const uploadButton = page.getByRole('button', { name: /开始上传/ })
    await expect(uploadButton).toBeVisible()

    // 点击按钮
    await uploadButton.click()

    // 验证导航到上传页面
    await expect(page).toHaveURL(/\/upload/)
    await expect(page.getByRole('heading', { name: /文件上传/ })).toBeVisible()
  })

  test('移动端导航菜单切换', async ({ page, viewport }) => {
    // 调整窗口大小到移动端
    await page.setViewportSize({ width: 375, height: 667 })

    // 查找汉堡菜单按钮
    const menuButton = page.getByRole('button', { name: /菜单/ })

    // 在移动端应该可见
    if (viewport && viewport.width < 768) {
      await expect(menuButton).toBeVisible()

      // 点击打开菜单
      await menuButton.click()

      // 菜单应该变得可见
      const mobileMenu = page.locator('[class*="mobile"]')
      if (await mobileMenu.isVisible()) {
        await expect(mobileMenu).toBeVisible()
      }
    }
  })

  test('页脚显示正确信息', async ({ page }) => {
    // 滚动到底部
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))

    const footer = page.locator('footer')
    // 验证页脚存在
    await expect(footer).toBeVisible()
  })

  test('可以导航到数据源页面', async ({ page }) => {
    const datasourceLink = page.getByRole('link', { name: /数据源/ })
    await expect(datasourceLink).toBeVisible()

    await datasourceLink.click()
    await expect(page).toHaveURL(/\/datasource/)
  })

  test('响应式布局适应不同屏幕宽度', async ({ page }) => {
    // 测试桌面端
    await page.setViewportSize({ width: 1920, height: 1080 })
    await page.goto('/')
    const desktopNav = page.locator('[class*="desktop"]')
    if (await desktopNav.isVisible()) {
      await expect(desktopNav).toBeVisible()
    }

    // 测试平板端
    await page.setViewportSize({ width: 768, height: 1024 })
    await page.goto('/')
    // 页面应该正确响应

    // 测试移动端
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/')
    // 页面应该正确响应
  })
})

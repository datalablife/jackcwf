/**
 * 应用布局组件。
 *
 * 包含导航栏和页面内容的整体布局。
 */

import { Outlet } from 'react-router-dom'
import { Navigation } from '@/components/navigation/Navigation'
import { Footer } from '@/components/layout/Footer'

export function Layout() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* 导航栏 */}
      <Navigation />

      {/* 主要内容 */}
      <main className="flex-1">
        <Outlet />
      </main>

      {/* 页脚 */}
      <Footer />
    </div>
  )
}

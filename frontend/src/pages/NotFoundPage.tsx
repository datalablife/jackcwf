/**
 * 404 页面。
 *
 * 处理所有未找到的路由。
 */

import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-md text-center">
        <h1 className="text-6xl font-bold text-gray-900 mb-4">404</h1>
        <h2 className="text-2xl font-semibold text-gray-700 mb-4">
          页面未找到
        </h2>
        <p className="text-gray-600 mb-8">
          抱歉，您访问的页面不存在或已被删除。
        </p>
        <Link
          to="/"
          className="inline-block px-8 py-3 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 transition-colors"
        >
          返回首页
        </Link>
      </div>
    </div>
  )
}

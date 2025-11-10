/**
 * 应用首页。
 *
 * 展示应用的主要功能和快速导航。
 */

import { Link } from 'react-router-dom'

export function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50">
      {/* 主横幅 */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center mb-16">
          <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
            🚀 数据文件管理系统
          </h1>
          <p className="text-xl md:text-2xl text-gray-600 mb-8">
            强大的文件上传、预览和管理工具
          </p>
          <div className="flex justify-center gap-4">
            <Link
              to="/upload"
              className="px-8 py-3 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 transition-colors shadow-lg"
            >
              开始上传
            </Link>
            <Link
              to="/datasource"
              className="px-8 py-3 rounded-lg bg-gray-200 text-gray-900 font-semibold hover:bg-gray-300 transition-colors"
            >
              数据源配置
            </Link>
          </div>
        </div>

        {/* 功能卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
          {/* 文件上传 */}
          <div className="bg-white rounded-lg shadow-lg p-8 hover:shadow-xl transition-shadow">
            <div className="text-4xl mb-4">📤</div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">智能上传</h3>
            <p className="text-gray-600 mb-6">
              支持多种文件格式，拖拽上传，实时进度跟踪。
            </p>
            <ul className="text-sm text-gray-700 space-y-2">
              <li>✓ CSV, XLSX, XLS, JSON</li>
              <li>✓ 支持大文件上传</li>
              <li>✓ 拖拽上传支持</li>
              <li>✓ 进度实时显示</li>
            </ul>
          </div>

          {/* 数据预览 */}
          <div className="bg-white rounded-lg shadow-lg p-8 hover:shadow-xl transition-shadow">
            <div className="text-4xl mb-4">👁️</div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">数据预览</h3>
            <p className="text-gray-600 mb-6">
              快速浏览文件数据，支持分页和多工作表。
            </p>
            <ul className="text-sm text-gray-700 space-y-2">
              <li>✓ 实时数据预览</li>
              <li>✓ 数据类型识别</li>
              <li>✓ Excel 多工作表</li>
              <li>✓ 分页浏览</li>
            </ul>
          </div>

          {/* 文件管理 */}
          <div className="bg-white rounded-lg shadow-lg p-8 hover:shadow-xl transition-shadow">
            <div className="text-4xl mb-4">📁</div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">文件管理</h3>
            <p className="text-gray-600 mb-6">
              完整的文件管理功能，支持查询和删除。
            </p>
            <ul className="text-sm text-gray-700 space-y-2">
              <li>✓ 文件列表管理</li>
              <li>✓ 文件详情查看</li>
              <li>✓ 支持文件删除</li>
              <li>✓ 解析状态跟踪</li>
            </ul>
          </div>
        </div>

        {/* 快速开始 */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">⚡ 快速开始</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-blue-600 mb-2">1</div>
              <h4 className="font-semibold text-gray-900 mb-2">配置数据源</h4>
              <p className="text-sm text-gray-600">
                在数据源设置中配置您的数据源信息
              </p>
            </div>
            <div className="bg-green-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-green-600 mb-2">2</div>
              <h4 className="font-semibold text-gray-900 mb-2">上传文件</h4>
              <p className="text-sm text-gray-600">
                使用拖拽或点击上传您的数据文件
              </p>
            </div>
            <div className="bg-purple-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-purple-600 mb-2">3</div>
              <h4 className="font-semibold text-gray-900 mb-2">预览数据</h4>
              <p className="text-sm text-gray-600">
                点击文件预览您上传的数据内容
              </p>
            </div>
            <div className="bg-orange-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-orange-600 mb-2">4</div>
              <h4 className="font-semibold text-gray-900 mb-2">管理文件</h4>
              <p className="text-sm text-gray-600">
                查看、编辑或删除您的文件
              </p>
            </div>
          </div>
        </div>

        {/* 技术栈 */}
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">🛠️ 技术栈</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-3xl mb-2">⚛️</div>
              <p className="text-sm font-semibold">React 19</p>
              <p className="text-xs text-gray-600">UI 框架</p>
            </div>
            <div className="text-center">
              <div className="text-3xl mb-2">🎨</div>
              <p className="text-sm font-semibold">Tailwind CSS</p>
              <p className="text-xs text-gray-600">样式系统</p>
            </div>
            <div className="text-center">
              <div className="text-3xl mb-2">🔄</div>
              <p className="text-sm font-semibold">Zustand</p>
              <p className="text-xs text-gray-600">状态管理</p>
            </div>
            <div className="text-center">
              <div className="text-3xl mb-2">🌐</div>
              <p className="text-sm font-semibold">Axios</p>
              <p className="text-xs text-gray-600">HTTP 客户端</p>
            </div>
            <div className="text-center">
              <div className="text-3xl mb-2">🚀</div>
              <p className="text-sm font-semibold">Vite</p>
              <p className="text-xs text-gray-600">构建工具</p>
            </div>
            <div className="text-center">
              <div className="text-3xl mb-2">📊</div>
              <p className="text-sm font-semibold">Tremor</p>
              <p className="text-xs text-gray-600">数据可视化</p>
            </div>
            <div className="text-center">
              <div className="text-3xl mb-2">✅</div>
              <p className="text-sm font-semibold">TypeScript</p>
              <p className="text-xs text-gray-600">类型安全</p>
            </div>
            <div className="text-center">
              <div className="text-3xl mb-2">🧪</div>
              <p className="text-sm font-semibold">Vitest</p>
              <p className="text-xs text-gray-600">单元测试</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

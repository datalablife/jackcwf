/**
 * 数据源设置页面。
 *
 * 完整的数据源管理界面，包括列表和创建表单。
 */

import { useState } from 'react'
import { ConnectPostgres } from '@/components/datasources/ConnectPostgres'
import { DataSourceList } from '@/components/datasources/DataSourceList'

type TabType = 'list' | 'connect'

export function DataSourceSetup() {
  const [activeTab, setActiveTab] = useState<TabType>('list')

  return (
    <div className="min-h-screen bg-gray-100">
      {/* 页头 */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-6 py-8">
          <h1 className="text-3xl font-bold text-gray-900">数据源管理</h1>
          <p className="text-gray-600 mt-2">
            连接和管理您的数据源（PostgreSQL 数据库和上传的文件）
          </p>
        </div>
      </div>

      {/* 选项卡 */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex gap-8">
            <button
              onClick={() => setActiveTab('list')}
              className={`py-4 px-2 border-b-2 font-medium transition ${
                activeTab === 'list'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              📋 数据源列表
            </button>
            <button
              onClick={() => setActiveTab('connect')}
              className={`py-4 px-2 border-b-2 font-medium transition ${
                activeTab === 'connect'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              ➕ 连接新数据源
            </button>
          </div>
        </div>
      </div>

      {/* 内容区域 */}
      <div className="max-w-6xl mx-auto px-6 py-12">
        {activeTab === 'list' && (
          <div>
            <DataSourceList />
          </div>
        )}

        {activeTab === 'connect' && (
          <div>
            <ConnectPostgres />
          </div>
        )}
      </div>

      {/* 页脚提示 */}
      <div className="bg-blue-50 border-t border-blue-200 mt-12">
        <div className="max-w-6xl mx-auto px-6 py-6">
          <p className="text-blue-900 text-sm">
            💡 <strong>提示:</strong> 所有数据库密码都使用 AES-256 加密存储。
            创建数据源后，您可以立即使用 Text2SQL 功能查询数据库。
          </p>
        </div>
      </div>
    </div>
  )
}

/**
 * 数据源列表组件。
 *
 * 显示所有已连接的数据源，支持选择、删除等操作。
 */

import { useEffect } from 'react'
import { useDataSourceStore } from '@/stores/useDataSourceStore'
import { StatusBadge } from '@/components/common/StatusBadge'
// type DataSource is not used directly in JSX, only through store destructuring

export function DataSourceList() {
  const {
    dataSources,
    selectedId,
    isLoading,
    error,
    fetchDataSources,
    selectDataSource,
    removeDataSource,
    testConnection,
  } = useDataSourceStore()

  useEffect(() => {
    fetchDataSources()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleSelectDataSource = (id: number) => {
    selectDataSource(id)
  }

  const handleDeleteDataSource = async (id: number) => {
    if (window.confirm('确认删除此数据源？此操作无法撤销。')) {
      try {
        await removeDataSource(id)
      } catch (err) {
        console.error('删除数据源失败:', err)
      }
    }
  }

  const handleTestConnection = async (id: number) => {
    try {
      const success = await testConnection(id)
      if (success) {
        alert('连接测试成功！')
      }
    } catch (err) {
      console.error('连接测试失败:', err)
    }
  }

  if (isLoading && dataSources.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="inline-block">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
        <p className="text-gray-600 mt-4">加载数据源中...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <p className="text-red-800">❌ {error}</p>
      </div>
    )
  }

  if (dataSources.length === 0) {
    return (
      <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
        <p className="text-gray-600 text-lg">暂无数据源</p>
        <p className="text-gray-500 mt-2">点击"连接新数据源"按钮添加数据源</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">
          数据源列表 ({dataSources.length})
        </h3>
      </div>

      <div className="grid gap-4">
        {dataSources.map((datasource) => (
          <div
            key={datasource.id}
            onClick={() => handleSelectDataSource(datasource.id)}
            className={`border rounded-lg p-6 cursor-pointer transition ${
              selectedId === datasource.id
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300 bg-white'
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3">
                  <h4 className="text-lg font-semibold text-gray-900">
                    {datasource.name}
                  </h4>
                  <StatusBadge status={datasource.status} />
                </div>

                {datasource.description && (
                  <p className="text-gray-600 text-sm mt-1">{datasource.description}</p>
                )}

                {datasource.error_message && (
                  <p className="text-red-600 text-sm mt-1">错误: {datasource.error_message}</p>
                )}

                <div className="flex items-center gap-4 mt-3 text-sm text-gray-500">
                  <span>📊 类型: {datasource.type === 'postgresql' ? 'PostgreSQL' : datasource.type}</span>
                  <span>📅 创建: {new Date(datasource.created_at).toLocaleDateString()}</span>
                </div>
              </div>

              <div className="flex flex-col gap-2 ml-4">
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    handleTestConnection(datasource.id)
                  }}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm font-medium transition whitespace-nowrap"
                >
                  测试连接
                </button>

                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    handleDeleteDataSource(datasource.id)
                  }}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm font-medium transition whitespace-nowrap"
                >
                  删除
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

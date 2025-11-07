/**
 * 架构查看器组件。
 *
 * 显示 PostgreSQL 数据库的表和列信息。
 */

import { useState, useEffect } from 'react'
import { useDataSourceStore } from '@/stores/useDataSourceStore'

interface Table {
  name: string
  schema: string
  columns: Column[]
  row_count: number
}

interface Column {
  name: string
  type: string
  nullable: boolean
}

interface SchemaViewerProps {
  datasourceId: number
}

export function SchemaViewer({ datasourceId }: SchemaViewerProps) {
  const [schema, setSchema] = useState<Table[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [expandedTable, setExpandedTable] = useState<string | null>(null)

  useEffect(() => {
    loadSchema()
  }, [datasourceId])

  const loadSchema = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`/api/datasources/${datasourceId}/schema`)
      if (!response.ok) {
        throw new Error('无法加载架构信息')
      }
      const data = await response.json()
      setSchema(data.tables || [])
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '加载架构失败'
      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="text-center py-12">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p className="text-gray-600 mt-4">加载架构信息中...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <p className="text-red-800">❌ {error}</p>
        <button
          onClick={loadSchema}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm font-medium"
        >
          重试
        </button>
      </div>
    )
  }

  if (schema.length === 0) {
    return (
      <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
        <p className="text-gray-600">暂无表</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">
          数据库架构 ({schema.length} 个表)
        </h3>
        <button
          onClick={loadSchema}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
        >
          刷新
        </button>
      </div>

      <div className="space-y-2">
        {schema.map((table) => (
          <div key={`${table.schema}.${table.name}`} className="border border-gray-200 rounded-lg">
            <button
              onClick={() =>
                setExpandedTable(
                  expandedTable === `${table.schema}.${table.name}`
                    ? null
                    : `${table.schema}.${table.name}`
                )
              }
              className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition"
            >
              <div className="flex items-center gap-3 flex-1">
                <span className="text-xl">
                  {expandedTable === `${table.schema}.${table.name}` ? '▼' : '▶'}
                </span>
                <div className="text-left">
                  <p className="font-semibold text-gray-900">{table.name}</p>
                  <p className="text-sm text-gray-600">
                    Schema: {table.schema} • Columns: {table.columns.length} • Rows:{' '}
                    {table.row_count.toLocaleString()}
                  </p>
                </div>
              </div>
            </button>

            {expandedTable === `${table.schema}.${table.name}` && (
              <div className="bg-gray-50 border-t border-gray-200 px-6 py-4">
                <div className="space-y-2">
                  <div className="text-sm font-semibold text-gray-700 mb-3">列信息:</div>
                  {table.columns.map((column) => (
                    <div
                      key={column.name}
                      className="flex items-center justify-between p-3 bg-white rounded border border-gray-100"
                    >
                      <div>
                        <p className="font-mono text-sm font-semibold text-gray-900">
                          {column.name}
                        </p>
                        <p className="text-xs text-gray-600 mt-1">{column.type}</p>
                      </div>
                      <span className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded">
                        {column.nullable ? '可空' : '非空'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

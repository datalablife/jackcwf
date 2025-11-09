/**
 * 预览表格组件。
 *
 * 功能：
 * - 表格布局
 * - 数据展示
 * - 滚动支持
 * - 分页（可选）
 */

import { useState, useMemo } from 'react'

interface PreviewTableProps {
  columns: string[]
  data: (string | number | boolean | null)[][]
  dataTypes?: string[]
  maxRows?: number
  pageSize?: number
  showPagination?: boolean
}

export function PreviewTable({
  columns,
  data,
  dataTypes = [],
  maxRows = 100,
  pageSize = 10,
  showPagination = true,
}: PreviewTableProps) {
  const [currentPage, setCurrentPage] = useState(1)

  // 限制最大显示行数
  const limitedData = useMemo(() => {
    return data.slice(0, maxRows)
  }, [data, maxRows])

  // 分页处理
  const paginatedData = useMemo(() => {
    if (!showPagination) return limitedData
    const start = (currentPage - 1) * pageSize
    const end = start + pageSize
    return limitedData.slice(start, end)
  }, [limitedData, currentPage, pageSize, showPagination])

  const totalPages = Math.ceil(limitedData.length / pageSize)

  const formatCellValue = (value: unknown): string => {
    if (value === null || value === undefined) {
      return '(null)'
    }
    if (typeof value === 'boolean') {
      return value ? '✓ 真' : '✗ 假'
    }
    if (typeof value === 'number') {
      return value.toString()
    }
    return String(value).substring(0, 100) // 限制长度
  }

  const getDataTypeColor = (dataType: string): string => {
    const type = dataType.toLowerCase()
    if (type.includes('int') || type.includes('integer'))
      return 'bg-blue-50 text-blue-700'
    if (type.includes('float') || type.includes('double'))
      return 'bg-purple-50 text-purple-700'
    if (type.includes('bool'))
      return 'bg-green-50 text-green-700'
    if (type.includes('text') || type.includes('string'))
      return 'bg-gray-50 text-gray-700'
    return 'bg-gray-50 text-gray-700'
  }

  const getCellAlignment = (dataType: string): string => {
    const type = dataType.toLowerCase()
    if (
      type.includes('int') ||
      type.includes('float') ||
      type.includes('double')
    ) {
      return 'text-right'
    }
    return 'text-left'
  }

  if (columns.length === 0) {
    return (
      <div className="flex items-center justify-center p-8 text-gray-500">
        <p>无法显示表格：没有列信息</p>
      </div>
    )
  }

  if (limitedData.length === 0) {
    return (
      <div className="flex items-center justify-center p-8 text-gray-500">
        <p>无数据显示</p>
      </div>
    )
  }

  return (
    <div className="w-full space-y-4">
      {/* 表格容器 */}
      <div className="overflow-x-auto border border-gray-200 rounded-lg">
        <table className="w-full text-sm">
          {/* 表头 */}
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              {/* 行号列 */}
              <th className="w-12 px-4 py-3 text-center text-gray-700 font-semibold bg-gray-100 border-r border-gray-200">
                #
              </th>

              {/* 数据列 */}
              {columns.map((column, index) => (
                <th
                  key={index}
                  className="px-4 py-3 text-left text-gray-700 font-semibold min-w-max border-r border-gray-200 last:border-r-0 whitespace-nowrap"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate">{column}</span>

                    {/* 数据类型标签 */}
                    {dataTypes[index] && (
                      <span
                        className={`text-xs font-medium px-2 py-1 rounded whitespace-nowrap ${getDataTypeColor(
                          dataTypes[index]
                        )}`}
                      >
                        {dataTypes[index]}
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>

          {/* 表体 */}
          <tbody>
            {paginatedData.map((row, rowIndex) => (
              <tr
                key={rowIndex}
                className="border-b border-gray-200 hover:bg-gray-50 transition-colors"
              >
                {/* 行号 */}
                <td className="w-12 px-4 py-3 text-center text-gray-500 text-xs font-medium bg-gray-50 border-r border-gray-200">
                  {(currentPage - 1) * pageSize + rowIndex + 1}
                </td>

                {/* 数据列 */}
                {row.map((cell, cellIndex) => (
                  <td
                    key={cellIndex}
                    className={`px-4 py-3 text-gray-900 border-r border-gray-200 last:border-r-0 font-mono text-xs whitespace-nowrap ${getCellAlignment(
                      dataTypes[cellIndex] || 'string'
                    )}`}
                  >
                    {cell === null ? (
                      <span className="text-gray-400 italic">(null)</span>
                    ) : cell === '' ? (
                      <span className="text-gray-400 italic">(empty)</span>
                    ) : (
                      formatCellValue(cell)
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 底部信息和分页 */}
      {showPagination && limitedData.length > pageSize && (
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          {/* 信息 */}
          <div className="text-sm text-gray-600">
            <p>
              显示
              <span className="font-semibold mx-1">
                {(currentPage - 1) * pageSize + 1}
              </span>
              至
              <span className="font-semibold mx-1">
                {Math.min(currentPage * pageSize, limitedData.length)}
              </span>
              条，共
              <span className="font-semibold mx-1">{limitedData.length}</span>
              条数据
            </p>
          </div>

          {/* 分页按钮 */}
          <div className="flex items-center gap-2">
            {/* 上一页 */}
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-3 py-2 rounded border border-gray-300 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              ← 上一页
            </button>

            {/* 页码信息 */}
            <div className="flex items-center gap-1 px-3 py-2">
              <span className="text-sm font-medium text-gray-700">
                {currentPage}
              </span>
              <span className="text-sm text-gray-500">/</span>
              <span className="text-sm text-gray-500">{totalPages}</span>
            </div>

            {/* 下一页 */}
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-2 rounded border border-gray-300 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              下一页 →
            </button>

            {/* 每页行数选择 */}
            <select
              value={pageSize}
              className="ml-2 px-3 py-2 rounded border border-gray-300 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
              disabled
            >
              <option value={10}>10/页</option>
              <option value={20}>20/页</option>
              <option value={50}>50/页</option>
            </select>
          </div>
        </div>
      )}

      {/* 无分页时的信息 */}
      {!showPagination && (
        <div className="text-sm text-gray-600 text-center">
          <p>
            显示全部
            <span className="font-semibold mx-1">{limitedData.length}</span>
            条数据
            {limitedData.length < data.length && (
              <span>
                （总共
                <span className="font-semibold mx-1">{data.length}</span>
                条，已限制显示前 {maxRows} 条）
              </span>
            )}
          </p>
        </div>
      )}
    </div>
  )
}

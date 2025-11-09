/**
 * 文件预览信息组件。
 *
 * 功能：
 * - 文件信息展示（名称、大小、格式、上传时间）
 * - 列名显示
 * - 数据类型显示
 * - 行数统计
 * - 关联 PreviewTable 组件
 */

import { useState } from 'react'

export interface FileMetadata {
  id: number
  filename: string
  file_format: string
  file_size: number
  row_count?: number
  column_count?: number
  created_at?: string
  parse_status?: string
  metadata?: {
    rows_count?: number
    columns_count?: number
    column_names?: string[]
    data_types?: string[]
  }
}

interface FilePreviewProps {
  file: FileMetadata
  onRefresh?: () => void
  isLoading?: boolean
  children?: React.ReactNode // 用于显示 PreviewTable 组件
}

export function FilePreview({
  file,
  onRefresh,
  isLoading = false,
  children,
}: FilePreviewProps) {
  const [expandedSections, setExpandedSections] = useState<
    Record<string, boolean>
  >({
    info: true,
    columns: true,
  })

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }))
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i]
  }

  const formatDate = (dateStr?: string): string => {
    if (!dateStr) return '未知'
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN')
  }

  const getFormatIcon = (format: string): string => {
    switch (format.toLowerCase()) {
      case 'csv':
        return '📄'
      case 'xlsx':
      case 'xls':
        return '📊'
      case 'json':
      case 'jsonl':
        return '{ }'
      default:
        return '📑'
    }
  }

  const getDataTypeColor = (dataType: string): string => {
    const type = dataType.toLowerCase()
    if (type.includes('int') || type.includes('integer')) return 'bg-blue-100 text-blue-800'
    if (type.includes('float') || type.includes('double')) return 'bg-purple-100 text-purple-800'
    if (type.includes('bool')) return 'bg-green-100 text-green-800'
    return 'bg-gray-100 text-gray-800'
  }

  const metadata = file.metadata
  const columnNames = metadata?.column_names || []
  const dataTypes = metadata?.data_types || []
  const rowCount = metadata?.rows_count || file.row_count || 0
  const columnCount = metadata?.columns_count || file.column_count || 0

  return (
    <div className="w-full space-y-4">
      {/* 文件基本信息 */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        {/* 标题栏 */}
        <button
          onClick={() => toggleSection('info')}
          className="w-full px-6 py-4 flex items-center justify-between bg-gray-50 hover:bg-gray-100 transition-colors"
        >
          <div className="flex items-center gap-3">
            <span className="text-2xl">{getFormatIcon(file.file_format)}</span>
            <div className="text-left">
              <p className="text-sm font-medium text-gray-900">{file.filename}</p>
              <p className="text-xs text-gray-500">{file.file_format.toUpperCase()}</p>
            </div>
          </div>

          <svg
            className={`h-5 w-5 text-gray-400 transition-transform ${
              expandedSections.info ? 'transform rotate-180' : ''
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 14l-7 7m0 0l-7-7m7 7V3"
            />
          </svg>
        </button>

        {/* 内容 */}
        {expandedSections.info && (
          <div className="px-6 py-4 border-t border-gray-200 space-y-4">
            {/* 基本信息网格 */}
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              {/* 文件大小 */}
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-600 mb-1">文件大小</p>
                <p className="text-sm font-semibold text-gray-900">
                  {formatFileSize(file.file_size)}
                </p>
              </div>

              {/* 行数 */}
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-600 mb-1">总行数</p>
                <p className="text-sm font-semibold text-gray-900">
                  {rowCount > 0 ? rowCount.toLocaleString() : '未解析'}
                </p>
              </div>

              {/* 列数 */}
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-600 mb-1">总列数</p>
                <p className="text-sm font-semibold text-gray-900">
                  {columnCount > 0 ? columnCount : '未解析'}
                </p>
              </div>

              {/* 上传时间 */}
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-600 mb-1">上传时间</p>
                <p className="text-sm font-semibold text-gray-900">
                  {formatDate(file.created_at)}
                </p>
              </div>
            </div>

            {/* 解析状态 */}
            {file.parse_status && (
              <div className="pt-2 border-t border-gray-200">
                <p className="text-xs text-gray-600 mb-2">解析状态</p>
                <span
                  className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${
                    file.parse_status === 'success'
                      ? 'bg-green-100 text-green-800'
                      : file.parse_status === 'pending'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                  }`}
                >
                  <span>
                    {file.parse_status === 'success'
                      ? '✓'
                      : file.parse_status === 'pending'
                        ? '⏳'
                        : '✗'}
                  </span>
                  <span>
                    {file.parse_status === 'success'
                      ? '已解析'
                      : file.parse_status === 'pending'
                        ? '解析中'
                        : '解析失败'}
                  </span>
                </span>
              </div>
            )}

            {/* 刷新按钮 */}
            {onRefresh && (
              <div className="pt-2 border-t border-gray-200">
                <button
                  onClick={onRefresh}
                  disabled={isLoading}
                  className="w-full px-4 py-2 rounded-lg text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isLoading ? '⏳ 刷新中...' : '🔄 刷新信息'}
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 列信息 */}
      {columnNames.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          {/* 标题栏 */}
          <button
            onClick={() => toggleSection('columns')}
            className="w-full px-6 py-4 flex items-center justify-between bg-gray-50 hover:bg-gray-100 transition-colors"
          >
            <div>
              <p className="text-sm font-medium text-gray-900">
                列信息 ({columnNames.length} 列)
              </p>
            </div>

            <svg
              className={`h-5 w-5 text-gray-400 transition-transform ${
                expandedSections.columns ? 'transform rotate-180' : ''
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 14l-7 7m0 0l-7-7m7 7V3"
              />
            </svg>
          </button>

          {/* 列表内容 */}
          {expandedSections.columns && (
            <div className="px-6 py-4 border-t border-gray-200">
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {columnNames.map((name, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between bg-gray-50 rounded p-3"
                  >
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      {/* 列索引 */}
                      <span className="flex-shrink-0 w-6 h-6 rounded-full bg-gray-200 text-gray-700 text-xs font-semibold flex items-center justify-center">
                        {index + 1}
                      </span>

                      {/* 列名 */}
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {name}
                      </p>
                    </div>

                    {/* 数据类型标签 */}
                    {dataTypes[index] && (
                      <span
                        className={`ml-2 text-xs font-medium px-2 py-1 rounded ${getDataTypeColor(
                          dataTypes[index]
                        )}`}
                      >
                        {dataTypes[index]}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 数据预览表格 */}
      {children && (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
            <p className="text-sm font-medium text-gray-900">数据预览</p>
          </div>
          <div className="overflow-auto">{children}</div>
        </div>
      )}
    </div>
  )
}

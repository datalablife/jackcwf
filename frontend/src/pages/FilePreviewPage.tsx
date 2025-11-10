/**
 * 文件预览页面。
 *
 * 完整的文件预览功能页面。
 */

import { useState, useEffect } from 'react'
import { FilePreview, PreviewTable } from '@/components/file-preview'
import { useFilePreviewStore } from '@/stores/useFilePreviewStore'
import { useFileUploadStore } from '@/stores/useFileUploadStore'
import {
  fetchFileMetadata,
  fetchFilePreview,
  fetchExcelSheets,
  parseFileData,
} from '@/services/preview.api'

export function FilePreviewPage() {
  const [fileId, setFileId] = useState<number | null>(null)

  const {
    currentFile,
    previewData,
    selectedSheet,
    setCurrentFile,
    setPreviewData,
    setSelectedSheet,
    setSheets,
    setLoading,
    isLoading,
    error,
    setError,
  } = useFilePreviewStore()

  const { files: uploadedFiles } = useFileUploadStore()

  // 获取预览数据
  const loadPreviewData = async (id: number, sheet?: string) => {
    setLoading(true)
    setError(null)

    try {
      const [metadata, preview] = await Promise.all([
        fetchFileMetadata(id),
        fetchFilePreview(id, { sheetName: sheet }),
      ])

      setCurrentFile({
        id: id,
        filename: currentFile?.filename || 'Unknown',
        file_format: currentFile?.file_format || 'unknown',
        file_size: currentFile?.file_size || 0,
        metadata: {
          rows_count: metadata.rows_count,
          columns_count: metadata.columns_count,
          column_names: metadata.column_names,
          data_types: metadata.data_types,
          storage_path: metadata.storage_path,
        },
      })

      setPreviewData({
        columns: preview.columns || [],
        data: preview.data || [],
        dataTypes: preview.dataTypes,
        totalRows: preview.data?.length || 0,
      })

      // 如果是 Excel，加载工作表列表
      if (
        currentFile?.file_format?.toLowerCase() === 'xlsx' ||
        currentFile?.file_format?.toLowerCase() === 'xls'
      ) {
        try {
          const sheetsResponse = await fetchExcelSheets(id)
          setSheets(sheetsResponse.sheets || [])
        } catch (err) {
          console.error('获取工作表列表失败:', err)
        }
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : '加载预览数据失败'
      setError(errorMessage)
      console.error('加载预览数据失败:', err)
    } finally {
      setLoading(false)
    }
  }

  // 处理解析文件
  const handleParseFile = async () => {
    if (!fileId) return

    setLoading(true)
    setError(null)

    try {
      const result = await parseFileData(fileId, {
        sheetName: selectedSheet?.name,
      })

      if (result.success) {
        // 重新加载预览数据
        await loadPreviewData(fileId, selectedSheet?.name)
      } else {
        setError(result.message || '解析失败')
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : '文件解析失败'
      setError(errorMessage)
      console.error('文件解析失败:', err)
    } finally {
      setLoading(false)
    }
  }

  // 初始化加载
  useEffect(() => {
    // 这里可以从路由参数或其他来源获取 fileId
    // 暂时设置为 null，可在实际应用中更新
    if (fileId !== null) {
      const file = uploadedFiles.find((f) => f.id === fileId)
      if (file) {
        setCurrentFile({
          ...file,
          metadata: {
            rows_count: file.row_count,
            columns_count: file.column_count,
          },
        })
        loadPreviewData(fileId)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fileId, uploadedFiles.length])

  if (!fileId) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-yellow-900">
              ⚠️ 文件未找到
            </h2>
            <p className="mt-2 text-yellow-800">
              请从文件列表中选择要预览的文件。
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* 页面标题 */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900">文件预览</h1>
          <p className="mt-2 text-lg text-gray-600">
            {currentFile?.filename || '加载中...'}
          </p>
        </div>

        {/* 主要内容 */}
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-4">
          {/* 左侧：文件操作 */}
          <div className="lg:col-span-1">
            {/* Excel 工作表选择 */}
            {currentFile?.file_format?.toLowerCase() === 'xlsx' ||
            currentFile?.file_format?.toLowerCase() === 'xls' ? (
              <div className="bg-white rounded-lg shadow p-6 mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  工作表
                </h3>
                <select
                  value={selectedSheet?.name || ''}
                  onChange={(e) => {
                    const sheet = useFilePreviewStore
                      .getState()
                      .sheets.find((s) => s.name === e.target.value)
                    if (sheet) {
                      setSelectedSheet(sheet)
                      if (fileId) {
                        loadPreviewData(fileId, sheet.name)
                      }
                    }
                  }}
                  className="w-full px-4 py-2 rounded-lg border border-gray-300 text-gray-900 focus:border-blue-500 focus:outline-none"
                >
                  <option value="">默认工作表</option>
                  {useFilePreviewStore
                    .getState()
                    .sheets.map((sheet) => (
                      <option key={sheet.index} value={sheet.name}>
                        {sheet.name}
                      </option>
                    ))}
                </select>
              </div>
            ) : null}

            {/* 操作按钮 */}
            <div className="bg-white rounded-lg shadow p-6 space-y-3">
              <button
                onClick={() => fileId && loadPreviewData(fileId)}
                disabled={isLoading}
                className="w-full px-4 py-2 rounded-lg font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isLoading ? '刷新中...' : '🔄 刷新'}
              </button>

              <button
                onClick={handleParseFile}
                disabled={isLoading}
                className="w-full px-4 py-2 rounded-lg font-medium text-white bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isLoading ? '解析中...' : '📊 解析文件'}
              </button>

              <button
                onClick={() => window.history.back()}
                className="w-full px-4 py-2 rounded-lg font-medium text-gray-700 bg-gray-200 hover:bg-gray-300 transition-colors"
              >
                ← 返回
              </button>
            </div>

            {/* 错误提示 */}
            {error && (
              <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-sm text-red-800 font-semibold">
                  ❌ {error}
                </p>
              </div>
            )}
          </div>

          {/* 右侧：文件预览 */}
          <div className="lg:col-span-3">
            {currentFile ? (
              <FilePreview
                file={currentFile}
                onRefresh={() => fileId && loadPreviewData(fileId)}
                isLoading={isLoading}
              >
                {previewData && (
                  <PreviewTable
                    columns={previewData.columns}
                    data={previewData.data}
                    dataTypes={previewData.dataTypes}
                    pageSize={10}
                    showPagination={true}
                    maxRows={100}
                  />
                )}
              </FilePreview>
            ) : (
              <div className="bg-white rounded-lg shadow p-8 text-center">
                <div className="animate-spin h-12 w-12 text-blue-600 mx-auto mb-4">
                  ⏳
                </div>
                <p className="text-gray-600">加载文件信息中...</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

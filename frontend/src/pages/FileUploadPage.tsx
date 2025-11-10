/**
 * 文件上传页面。
 *
 * 完整的文件上传功能页面，集成所有上传相关组件。
 */

import { useState, useEffect } from 'react'
import { FileUploadForm, FileDropZone, UploadProgress } from '@/components/file-upload'
import { useFileUploadStore } from '@/stores/useFileUploadStore'
import { uploadFile, getFileList } from '@/services/file.api'

export function FileUploadPage() {
  const [dataSourceId, setDataSourceId] = useState<number>(1)
  const [isLoadingList, setIsLoadingList] = useState(false)

  const {
    files,
    setFiles,
    addFile,
    isLoading,
    setLoading,
    error,
    setError,
    uploadProgress,
    setUploadProgress,
  } = useFileUploadStore()

  // 加载文件列表
  const loadFiles = async () => {
    setIsLoadingList(true)
    setError(null)
    try {
      const response = await getFileList(dataSourceId)
      setFiles(response.items)
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : '加载文件列表失败'
      setError(errorMessage)
      console.error('加载文件列表失败:', err)
    } finally {
      setIsLoadingList(false)
    }
  }

  // 处理文件上传
  const handleFileUpload = async (file: File, sourceId: number) => {
    setLoading(true)
    setError(null)

    const startTime = Date.now()
    let lastUpdateTime = startTime
    let lastUploadedSize = 0

    try {
      const result = await uploadFile(file, sourceId, (progress) => {
        const currentTime = Date.now()
        const timeElapsed = (currentTime - startTime) / 1000 // 秒
        const speed =
          timeElapsed > 0 ? progress.loaded / timeElapsed : 0 // bytes/s
        const remainingBytes = progress.total - progress.loaded
        const remainingTime =
          speed > 0 ? remainingBytes / speed : 0 // 秒

        // 更新进度（避免过于频繁）
        if (currentTime - lastUpdateTime > 100 || progress.percentage >= 100) {
          const currentSpeed =
            currentTime > lastUpdateTime
              ? ((progress.loaded - lastUploadedSize) /
                  ((currentTime - lastUpdateTime) / 1000)) *
                1000
              : speed

          setUploadProgress({
            fileName: file.name,
            fileSize: file.size,
            uploadedSize: progress.loaded,
            progress: progress.percentage,
            speed: currentSpeed,
            remainingTime: remainingTime,
            status: progress.percentage >= 100 ? 'completed' : 'uploading',
          })

          lastUpdateTime = currentTime
          lastUploadedSize = progress.loaded
        }
      })

      // 上传成功
      addFile(result)
      setUploadProgress(null)

      // 重新加载文件列表
      await loadFiles()
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : '文件上传失败'
      setError(errorMessage)
      setUploadProgress({
        fileName: file.name,
        fileSize: file.size,
        uploadedSize: 0,
        progress: 0,
        speed: 0,
        remainingTime: 0,
        status: 'error',
        error: errorMessage,
      })
      console.error('文件上传失败:', err)
    } finally {
      setLoading(false)
    }
  }

  // 处理拖拽上传的文件
  const handleFilesSelected = async (selectedFiles: File[]) => {
    if (selectedFiles.length > 0) {
      const file = selectedFiles[0]
      await handleFileUpload(file, dataSourceId)
    }
  }

  // 初始化加载
  useEffect(() => {
    loadFiles()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dataSourceId])

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        {/* 页面标题 */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900">文件上传管理</h1>
          <p className="mt-2 text-lg text-gray-600">
            上传和管理您的数据文件，支持多种格式
          </p>
        </div>

        {/* 主要内容 */}
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          {/* 左侧：上传区域 */}
          <div className="lg:col-span-1 space-y-6">
            {/* 数据源选择 */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                选择数据源
              </h3>
              <select
                value={dataSourceId}
                onChange={(e) => setDataSourceId(parseInt(e.target.value))}
                className="w-full px-4 py-2 rounded-lg border border-gray-300 text-gray-900 focus:border-blue-500 focus:outline-none"
              >
                <option value={1}>数据源 1</option>
                <option value={2}>数据源 2</option>
                <option value={3}>数据源 3</option>
              </select>
            </div>

            {/* 上传表单 */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                📝 上传文件
              </h3>
              <FileUploadForm
                onUpload={handleFileUpload}
                isLoading={isLoading}
                error={error}
                dataSourceId={dataSourceId}
              />
            </div>

            {/* 拖拽上传 */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                ✨ 或拖拽上传
              </h3>
              <FileDropZone
                onFilesSelected={handleFilesSelected}
                isLoading={isLoading}
              />
            </div>
          </div>

          {/* 右侧：上传进度和文件列表 */}
          <div className="lg:col-span-2 space-y-6">
            {/* 上传进度 */}
            {uploadProgress && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  ⬆️ 上传进度
                </h3>
                <UploadProgress
                  progress={uploadProgress.progress}
                  fileName={uploadProgress.fileName}
                  fileSize={uploadProgress.fileSize}
                  uploadedSize={uploadProgress.uploadedSize}
                  speed={uploadProgress.speed}
                  remainingTime={uploadProgress.remainingTime}
                  status={uploadProgress.status}
                  errorMessage={uploadProgress.error}
                  onCancel={() => setUploadProgress(null)}
                />
              </div>
            )}

            {/* 文件列表 */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  📁 已上传文件 ({files.length})
                </h3>
                <button
                  onClick={loadFiles}
                  disabled={isLoadingList}
                  className="px-4 py-2 rounded-lg text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isLoadingList ? '刷新中...' : '🔄 刷新'}
                </button>
              </div>

              {files.length === 0 ? (
                <div className="text-center py-8">
                  <svg
                    className="mx-auto h-12 w-12 text-gray-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                  <p className="mt-4 text-gray-500">暂无文件</p>
                  <p className="text-sm text-gray-400">
                    上传文件后将显示在这里
                  </p>
                </div>
              ) : (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {files.map((file) => (
                    <div
                      key={file.id}
                      className="flex items-center justify-between bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors"
                    >
                      <div className="flex items-center gap-3 flex-1 min-w-0">
                        {/* 文件图标 */}
                        <div className="flex-shrink-0">
                          <svg
                            className="h-8 w-8 text-gray-400"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                            />
                          </svg>
                        </div>

                        {/* 文件信息 */}
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {file.filename}
                          </p>
                          <p className="text-xs text-gray-500">
                            {(file.file_size / 1024).toFixed(2)} KB •{' '}
                            {new Date(file.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>

                      {/* 状态标签 */}
                      <div className="ml-4 flex-shrink-0">
                        {file.parse_status === 'success' ? (
                          <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            <span>✓</span> 已解析
                          </span>
                        ) : file.parse_status === 'pending' ? (
                          <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                            <span>⏳</span> 解析中
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                            <span>✗</span> 失败
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* 统计信息 */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-semibold text-blue-900 mb-2">统计信息</h4>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-sm text-blue-600">总文件数</p>
                  <p className="text-2xl font-bold text-blue-900">{files.length}</p>
                </div>
                <div>
                  <p className="text-sm text-blue-600">已解析</p>
                  <p className="text-2xl font-bold text-blue-900">
                    {files.filter((f) => f.parse_status === 'success').length}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-blue-600">总大小</p>
                  <p className="text-2xl font-bold text-blue-900">
                    {(files.reduce((sum, f) => sum + f.file_size, 0) / 1024 / 1024).toFixed(2)}
                    MB
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

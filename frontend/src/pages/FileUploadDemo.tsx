/**
 * 文件上传演示页面。
 *
 * 展示所有文件上传相关组件的使用方式。
 */

import { useState } from 'react'
import {
  FileUploadForm,
  FileDropZone,
  UploadProgress,
} from '../components/file-upload'
import { FilePreview, PreviewTable } from '../components/file-preview'
import type { FileMetadata } from '../components/file-preview/FilePreview'
import { uploadFile } from '../services/file.api'

export function FileUploadDemo() {
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState<
    'uploading' | 'completed' | 'error' | 'paused' | 'none'
  >('none')
  const [currentFile, setCurrentFile] = useState<FileMetadata | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  // 真实文件上传 - 调用后端 API
  const handleFileUpload = async (file: File, dataSourceId: number) => {
    console.log('上传文件:', file.name, '数据源:', dataSourceId)

    setIsUploading(true)
    setUploadStatus('uploading')
    setErrorMessage(null)
    setUploadProgress(0)

    try {
      // 调用真实的后端 API
      const result = await uploadFile(file, dataSourceId, (progress) => {
        console.log('上传进度:', progress.percentage + '%')
        setUploadProgress(progress.percentage)
      })

      // 上传成功 - 设置文件元数据
      setUploadProgress(100)
      setUploadStatus('completed')
      setCurrentFile({
        id: result.id,
        filename: result.filename,
        file_format: result.file_format,
        file_size: result.file_size,
        row_count: result.row_count,
        column_count: result.column_count,
        parse_status: result.parse_status,
        created_at: result.created_at,
        metadata: {
          rows_count: result.row_count || 0,
          columns_count: result.column_count || 0,
          column_names: [],
          data_types: [],
        },
      })

      console.log('文件上传成功:', result)
    } catch (error) {
      // 上传失败 - 显示错误信息
      setUploadStatus('error')
      const errorMsg = error instanceof Error ? error.message : '上传失败: 网络错误或服务器问题'
      setErrorMessage(errorMsg)
      console.error('文件上传错误:', error)
    } finally {
      setIsUploading(false)
    }
  }

  // 模拟文件下拉上传
  const handleFilesSelected = (files: File[]) => {
    if (files.length > 0) {
      console.log('选择的文件:', files.map((f) => f.name))
    }
  }

  // 模拟预览数据
  const previewColumns = ['id', 'name', 'email', 'age', 'status']
  const previewDataTypes = ['integer', 'string', 'string', 'integer', 'string']
  const previewData = [
    [1, 'Alice', 'alice@example.com', 25, 'active'],
    [2, 'Bob', 'bob@example.com', 30, 'active'],
    [3, 'Charlie', 'charlie@example.com', 35, 'inactive'],
    [4, 'David', 'david@example.com', 28, 'active'],
    [5, 'Eve', 'eve@example.com', 32, 'active'],
    [6, 'Frank', 'frank@example.com', 29, 'inactive'],
    [7, 'Grace', 'grace@example.com', 27, 'active'],
    [8, 'Henry', 'henry@example.com', 31, 'active'],
    [9, 'Ivy', 'ivy@example.com', 26, 'inactive'],
    [10, 'Jack', 'jack@example.com', 33, 'active'],
    [11, 'Kate', 'kate@example.com', 24, 'active'],
    [12, 'Leo', 'leo@example.com', 29, 'inactive'],
  ]

  return (
    <div className="min-h-screen bg-gray-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        {/* 页面标题 */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">文件上传演示</h1>
          <p className="mt-2 text-gray-600">
            展示所有文件上传和预览相关组件的使用方式
          </p>
        </div>

        {/* 内容区 */}
        <div className="grid grid-cols-1 gap-8">
          {/* 左侧：上传相关组件 */}
          <div className="space-y-8">
            {/* FileUploadForm 组件 */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                📝 文件上传表单 (FileUploadForm)
              </h2>
              <FileUploadForm
                onUpload={handleFileUpload}
                isLoading={isUploading}
                error={errorMessage}
              />
            </div>

            {/* FileDropZone 组件 */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                ✨ 拖拽上传 (FileDropZone)
              </h2>
              <FileDropZone onFilesSelected={handleFilesSelected} />
            </div>

            {/* UploadProgress 组件 */}
            {uploadStatus !== 'none' && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  ⬆️ 上传进度 (UploadProgress)
                </h2>
                <UploadProgress
                  progress={uploadProgress}
                  fileName={currentFile?.filename || 'test.csv'}
                  fileSize={currentFile?.file_size || 1024}
                  uploadedSize={
                    (currentFile?.file_size || 1024) *
                    (uploadProgress / 100)
                  }
                  speed={50 * 1024} // 50 KB/s
                  remainingTime={Math.max(0, 60 - uploadProgress)}
                  status={uploadStatus}
                  onCancel={() => setUploadStatus('none')}
                />
              </div>
            )}
          </div>

          {/* 右侧：预览相关组件 */}
          {currentFile && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                👁️ 文件预览 (FilePreview + PreviewTable)
              </h2>
              <FilePreview file={currentFile}>
                <PreviewTable
                  columns={previewColumns}
                  data={previewData}
                  dataTypes={previewDataTypes}
                  pageSize={5}
                  showPagination={true}
                />
              </FilePreview>
            </div>
          )}
        </div>

        {/* 信息框 */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="font-semibold text-blue-900 mb-2">💡 使用提示</h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>
              • 尝试上传 CSV、XLSX 或 JSON 文件（最大 500MB）
            </li>
            <li>• 或者将文件拖拽到"拖拽上传"区域</li>
            <li>• 文件上传后会显示预览和进度信息</li>
            <li>• 所有组件都支持响应式设计</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

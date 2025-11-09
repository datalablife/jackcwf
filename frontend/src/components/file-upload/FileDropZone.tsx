/**
 * 拖拽上传组件。
 *
 * 功能：
 * - 拖拽上传区域
 * - 文件预览
 * - 拖拽反馈
 * - 样式处理
 * - 支持单个或多个文件
 */

import { useState } from 'react'

interface FileDropZoneProps {
  onFilesSelected: (files: File[]) => void
  acceptedFileTypes?: string[]
  maxFileSize?: number
  multiple?: boolean
  isLoading?: boolean
}

const DEFAULT_ACCEPTED_TYPES = ['csv', 'xlsx', 'xls', 'json', 'jsonl']
const DEFAULT_MAX_SIZE = 500 * 1024 * 1024 // 500MB

export function FileDropZone({
  onFilesSelected,
  acceptedFileTypes = DEFAULT_ACCEPTED_TYPES,
  maxFileSize = DEFAULT_MAX_SIZE,
  multiple = false,
  isLoading = false,
}: FileDropZoneProps) {
  const [isDragActive, setIsDragActive] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [errors, setErrors] = useState<string[]>([])

  const getFileExtension = (filename: string): string => {
    return filename.split('.').pop()?.toLowerCase() || ''
  }

  const validateFiles = (files: File[]): File[] => {
    const validFiles: File[] = []
    const newErrors: string[] = []

    files.forEach((file) => {
      // 检查文件类型
      const extension = getFileExtension(file.name)
      if (!acceptedFileTypes.includes(extension)) {
        newErrors.push(
          `❌ ${file.name}: 不支持的文件类型。支持：${acceptedFileTypes.join(', ')}`
        )
        return
      }

      // 检查文件大小
      if (file.size > maxFileSize) {
        newErrors.push(
          `❌ ${file.name}: 文件过大（${formatFileSize(file.size)} > ${formatFileSize(maxFileSize)}）`
        )
        return
      }

      validFiles.push(file)
    })

    setErrors(newErrors)
    return validFiles
  }

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragActive(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragActive(false)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragActive(false)

    const files = Array.from(e.dataTransfer.files)
    const validFiles = validateFiles(files)

    if (validFiles.length > 0) {
      if (multiple) {
        setSelectedFiles([...selectedFiles, ...validFiles])
        onFilesSelected([...selectedFiles, ...validFiles])
      } else {
        setSelectedFiles([validFiles[0]])
        onFilesSelected([validFiles[0]])
      }
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    const validFiles = validateFiles(files)

    if (validFiles.length > 0) {
      if (multiple) {
        setSelectedFiles([...selectedFiles, ...validFiles])
        onFilesSelected([...selectedFiles, ...validFiles])
      } else {
        setSelectedFiles([validFiles[0]])
        onFilesSelected([validFiles[0]])
      }
    }
  }

  const removeFile = (index: number) => {
    const newFiles = selectedFiles.filter((_, i) => i !== index)
    setSelectedFiles(newFiles)
    onFilesSelected(newFiles)
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i]
  }

  return (
    <div className="w-full space-y-4">
      {/* 拖拽区域 */}
      <label
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`block border-2 border-dashed rounded-lg p-8 text-center transition-all cursor-pointer ${
          isDragActive
            ? 'border-blue-500 bg-blue-50 shadow-md'
            : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
        } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <input
          type="file"
          multiple={multiple}
          onChange={handleInputChange}
          disabled={isLoading}
          accept={acceptedFileTypes.map((t) => `.${t}`).join(',')}
          className="hidden"
        />

        <div className="space-y-2">
          {/* 图标 */}
          <div className="flex justify-center">
            <svg
              className={`h-16 w-16 transition-colors ${
                isDragActive ? 'text-blue-500' : 'text-gray-400'
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5a4.5 4.5 0 01-1.41-8.775 5.25 5.25 0 0110.233-2.33A3 3 0 0116.5 19.5H6.75z"
              />
            </svg>
          </div>

          {/* 文字 */}
          <div>
            <p className="text-lg font-semibold text-gray-700">
              {isDragActive ? '释放文件即可上传' : '拖拽文件到此处'}
            </p>
            <p className="text-sm text-gray-500">或点击浏览选择文件</p>
          </div>

          {/* 支持的格式 */}
          <div className="pt-2">
            <p className="text-xs text-gray-600">
              支持格式：{acceptedFileTypes.join(', ').toUpperCase()}
            </p>
            <p className="text-xs text-gray-600">
              最大文件大小：{formatFileSize(maxFileSize)}
            </p>
          </div>
        </div>
      </label>

      {/* 错误信息 */}
      {errors.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 space-y-1">
          <p className="font-medium text-red-900">验证失败：</p>
          {errors.map((error, index) => (
            <p key={index} className="text-sm text-red-800">
              {error}
            </p>
          ))}
        </div>
      )}

      {/* 已选文件列表 */}
      {selectedFiles.length > 0 && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 mb-3">
            已选文件 ({selectedFiles.length})
          </h4>
          <div className="space-y-2">
            {selectedFiles.map((file, index) => (
              <div
                key={index}
                className="flex items-center justify-between bg-white border border-gray-200 rounded p-3"
              >
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  {/* 文件图标 */}
                  <div className="flex-shrink-0">
                    <svg
                      className="h-6 w-6 text-gray-400"
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
                      {file.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {formatFileSize(file.size)}
                    </p>
                  </div>
                </div>

                {/* 移除按钮 */}
                {!isLoading && (
                  <button
                    type="button"
                    onClick={() => removeFile(index)}
                    className="flex-shrink-0 ml-2 p-1 rounded hover:bg-red-50 text-gray-400 hover:text-red-600 transition-colors"
                    title="移除文件"
                  >
                    <svg
                      className="h-5 w-5"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

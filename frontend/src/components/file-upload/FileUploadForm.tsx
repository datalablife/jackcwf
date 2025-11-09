/**
 * 文件上传表单组件。
 *
 * 功能：
 * - 文件输入表单
 * - 表单验证
 * - 上传按钮
 * - 错误提示
 * - 显示文件类型和大小限制信息
 */

import { useState, useRef } from 'react'

interface FileUploadFormProps {
  onUpload: (file: File, dataSourceId: number) => Promise<void>
  isLoading?: boolean
  error?: string | null
  dataSourceId?: number
}

const ALLOWED_FILE_TYPES = ['csv', 'xlsx', 'xls', 'json', 'jsonl']
const ALLOWED_MIME_TYPES = [
  'text/csv',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/vnd.ms-excel',
  'application/json',
]
const MAX_FILE_SIZE = 500 * 1024 * 1024 // 500MB

export function FileUploadForm({
  onUpload,
  isLoading = false,
  error = null,
  dataSourceId = 1,
}: FileUploadFormProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [formError, setFormError] = useState<string | null>(null)

  const getFileExtension = (filename: string): string => {
    return filename.split('.').pop()?.toLowerCase() || ''
  }

  const validateFile = (file: File): boolean => {
    setFormError(null)

    // 检查文件类型
    const extension = getFileExtension(file.name)
    if (!ALLOWED_FILE_TYPES.includes(extension)) {
      setFormError(
        `不支持的文件类型。支持的类型：${ALLOWED_FILE_TYPES.join(', ')}`
      )
      return false
    }

    // 检查 MIME 类型
    if (!ALLOWED_MIME_TYPES.includes(file.type) && extension !== 'jsonl') {
      setFormError(`文件 MIME 类型不匹配：${file.type}`)
      return false
    }

    // 检查文件大小
    if (file.size > MAX_FILE_SIZE) {
      setFormError(
        `文件过大。最大允许 500MB，当前文件大小：${(file.size / 1024 / 1024).toFixed(2)}MB`
      )
      return false
    }

    return true
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    const file = files[0]
    if (validateFile(file)) {
      setSelectedFile(file)
    } else {
      setSelectedFile(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!selectedFile) {
      setFormError('请选择要上传的文件')
      return
    }

    if (!validateFile(selectedFile)) {
      return
    }

    try {
      await onUpload(selectedFile, dataSourceId)
      // 上传成功后清除表单
      setSelectedFile(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch {
      // 错误由父组件通过 error prop 处理
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()

    const files = e.dataTransfer.files
    if (!files || files.length === 0) return

    const file = files[0]
    if (validateFile(file)) {
      setSelectedFile(file)
      // 更新文件输入
      const dataTransfer = new DataTransfer()
      dataTransfer.items.add(file)
      if (fileInputRef.current) {
        fileInputRef.current.files = dataTransfer.files
      }
    }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
  }

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl">
      <div className="space-y-6">
        {/* 文件输入区域 */}
        <div
          className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 hover:bg-blue-50 transition-colors cursor-pointer"
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileSelect}
            accept={ALLOWED_FILE_TYPES.map((t) => `.${t}`).join(',')}
            disabled={isLoading}
            className="hidden"
          />

          <div className="space-y-2">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              stroke="currentColor"
              fill="none"
              viewBox="0 0 48 48"
            >
              <path
                d="M28 8H12a4 4 0 00-4 4v20a4 4 0 004 4h24a4 4 0 004-4V20m-14-8v16m-8-8h16"
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>

            <div className="text-gray-600">
              <p className="text-lg font-medium">
                {selectedFile ? selectedFile.name : '拖拽文件到此处或点击选择'}
              </p>
              {selectedFile && (
                <p className="text-sm text-gray-500">
                  文件大小：{formatFileSize(selectedFile.size)}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* 支持的文件类型信息 */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-medium text-blue-900 mb-2">支持的文件格式</h4>
          <div className="grid grid-cols-2 gap-2 text-sm text-blue-800">
            {ALLOWED_FILE_TYPES.map((type) => (
              <div key={type} className="flex items-center gap-2">
                <span className="text-blue-500">✓</span>
                <span className="uppercase">{type}</span>
              </div>
            ))}
          </div>
        </div>

        {/* 大小限制信息 */}
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 mb-2">文件限制</h4>
          <div className="space-y-1 text-sm text-gray-700">
            <p>• 最大文件大小：500 MB</p>
            <p>• 支持单个文件上传</p>
            <p>• 上传后文件将被保存到服务器</p>
          </div>
        </div>

        {/* 错误提示 */}
        {(formError || error) && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-sm text-red-800 font-medium">
              ❌ {formError || error}
            </p>
          </div>
        )}

        {/* 上传按钮 */}
        <div className="flex gap-4">
          <button
            type="submit"
            disabled={!selectedFile || isLoading}
            className={`flex-1 py-2 px-4 rounded-lg font-medium text-white transition-colors ${
              !selectedFile || isLoading
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 active:bg-blue-800'
            }`}
          >
            {isLoading ? (
              <span className="flex items-center justify-center gap-2">
                <svg
                  className="animate-spin h-4 w-4"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                >
                  <circle cx="12" cy="12" r="10" />
                  <path d="M12 2a10 10 0 0110 10" strokeWidth={2} />
                </svg>
                上传中...
              </span>
            ) : (
              '开始上传'
            )}
          </button>

          <button
            type="button"
            onClick={() => {
              setSelectedFile(null)
              setFormError(null)
              if (fileInputRef.current) {
                fileInputRef.current.value = ''
              }
            }}
            disabled={!selectedFile || isLoading}
            className="px-6 py-2 rounded-lg font-medium text-gray-700 bg-gray-200 hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            取消
          </button>
        </div>
      </div>
    </form>
  )
}

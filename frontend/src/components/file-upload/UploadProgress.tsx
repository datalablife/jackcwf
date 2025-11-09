/**
 * 上传进度条组件。
 *
 * 功能：
 * - 进度显示
 * - 上传速度
 * - 剩余时间
 * - 暂停/恢复功能（可选）
 */

import { useEffect, useState } from 'react'

interface UploadProgressProps {
  progress: number // 0-100
  fileName: string
  fileSize: number // bytes
  uploadedSize: number // bytes
  speed?: number // bytes/s
  remainingTime?: number // seconds
  onPause?: () => void
  onResume?: () => void
  onCancel?: () => void
  status?: 'uploading' | 'completed' | 'error' | 'paused'
  errorMessage?: string | null
}

export function UploadProgress({
  progress,
  fileName,
  fileSize,
  uploadedSize,
  speed = 0,
  remainingTime = 0,
  onPause,
  onResume,
  onCancel,
  status = 'uploading',
  errorMessage = null,
}: UploadProgressProps) {
  const [displaySpeed, setDisplaySpeed] = useState<string>('0 MB/s')
  const [displayRemainingTime, setDisplayRemainingTime] =
    useState<string>('计算中...')

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i]
  }

  const formatSpeed = (bytesPerSecond: number): string => {
    if (bytesPerSecond === 0) return '0 B/s'
    const k = 1024
    const sizes = ['B/s', 'KB/s', 'MB/s', 'GB/s']
    const i = Math.floor(Math.log(bytesPerSecond) / Math.log(k))
    return (bytesPerSecond / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i]
  }

  const formatRemainingTime = (seconds: number): string => {
    if (seconds === 0 || !isFinite(seconds)) return '计算中...'
    if (seconds < 60) return `${Math.ceil(seconds)} 秒`
    const minutes = Math.floor(seconds / 60)
    const secs = Math.ceil(seconds % 60)
    return `${minutes} 分 ${secs} 秒`
  }

  useEffect(() => {
    setDisplaySpeed(formatSpeed(speed))
  }, [speed])

  useEffect(() => {
    setDisplayRemainingTime(formatRemainingTime(remainingTime))
  }, [remainingTime])

  const getStatusColor = (): string => {
    switch (status) {
      case 'completed':
        return 'bg-green-500'
      case 'error':
        return 'bg-red-500'
      case 'paused':
        return 'bg-yellow-500'
      default:
        return 'bg-blue-500'
    }
  }

  const getStatusLabel = (): string => {
    switch (status) {
      case 'completed':
        return '已完成'
      case 'error':
        return '上传失败'
      case 'paused':
        return '已暂停'
      default:
        return `上传中 ${progress}%`
    }
  }

  const getStatusIcon = (): string => {
    switch (status) {
      case 'completed':
        return '✓'
      case 'error':
        return '✗'
      case 'paused':
        return '⏸'
      default:
        return '⬆'
    }
  }

  return (
    <div className="w-full space-y-4">
      {/* 文件名和状态 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          {/* 状态图标 */}
          <div
            className={`flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-full ${getStatusColor()} text-white text-sm font-semibold`}
          >
            {getStatusIcon()}
          </div>

          {/* 文件信息 */}
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">
              {fileName}
            </p>
            <p className="text-xs text-gray-500">
              {formatFileSize(uploadedSize)} / {formatFileSize(fileSize)}
            </p>
          </div>
        </div>

        {/* 状态标签 */}
        <span
          className={`ml-4 text-sm font-semibold ${
            status === 'completed'
              ? 'text-green-600'
              : status === 'error'
                ? 'text-red-600'
                : status === 'paused'
                  ? 'text-yellow-600'
                  : 'text-blue-600'
          }`}
        >
          {getStatusLabel()}
        </span>
      </div>

      {/* 进度条 */}
      <div className="space-y-2">
        <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-300 ${getStatusColor()}`}
            style={{ width: `${Math.min(progress, 100)}%` }}
          />
        </div>

        {/* 进度百分比数字 */}
        <div className="flex justify-between items-center">
          <div className="text-xs text-gray-500">进度</div>
          <div className="text-sm font-semibold text-gray-700">
            {progress.toFixed(1)}%
          </div>
        </div>
      </div>

      {/* 上传统计信息 */}
      {status === 'uploading' && (
        <div className="grid grid-cols-3 gap-4">
          {/* 上传速度 */}
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-600 mb-1">上传速度</p>
            <p className="text-sm font-semibold text-gray-900">
              {displaySpeed}
            </p>
          </div>

          {/* 剩余时间 */}
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-600 mb-1">剩余时间</p>
            <p className="text-sm font-semibold text-gray-900">
              {displayRemainingTime}
            </p>
          </div>

          {/* 已上传百分比 */}
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-600 mb-1">已上传</p>
            <p className="text-sm font-semibold text-gray-900">
              {((uploadedSize / fileSize) * 100).toFixed(1)}%
            </p>
          </div>
        </div>
      )}

      {/* 错误信息 */}
      {status === 'error' && errorMessage && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-800">
            <span className="font-semibold">❌ 错误：</span>
            {errorMessage}
          </p>
        </div>
      )}

      {/* 完成信息 */}
      {status === 'completed' && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <p className="text-sm text-green-800 font-semibold">
            ✓ 文件上传成功！
          </p>
        </div>
      )}

      {/* 操作按钮 */}
      {(status === 'uploading' || status === 'paused') && (
        <div className="flex gap-3 pt-2">
          {status === 'uploading' && onPause && (
            <button
              onClick={onPause}
              className="flex-1 px-4 py-2 rounded-lg font-medium text-gray-700 bg-gray-200 hover:bg-gray-300 transition-colors"
            >
              ⏸ 暂停
            </button>
          )}

          {status === 'paused' && onResume && (
            <button
              onClick={onResume}
              className="flex-1 px-4 py-2 rounded-lg font-medium text-white bg-blue-600 hover:bg-blue-700 transition-colors"
            >
              ▶ 继续
            </button>
          )}

          {onCancel && (
            <button
              onClick={onCancel}
              className="flex-1 px-4 py-2 rounded-lg font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 transition-colors"
            >
              ✕ 取消
            </button>
          )}
        </div>
      )}

      {/* 完成后的按钮 */}
      {status === 'completed' && onCancel && (
        <div className="flex gap-3 pt-2">
          <button
            onClick={onCancel}
            className="flex-1 px-4 py-2 rounded-lg font-medium text-gray-700 bg-gray-200 hover:bg-gray-300 transition-colors"
          >
            ✕ 关闭
          </button>
        </div>
      )}
    </div>
  )
}

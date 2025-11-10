/**
 * useFileUploadStore 单元测试。
 *
 * 测试文件上传状态存储的所有操作。
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { useFileUploadStore } from '@/stores/useFileUploadStore'

describe('useFileUploadStore', () => {
  beforeEach(() => {
    // 重置状态
    useFileUploadStore.setState({
      files: [],
      isLoading: false,
      error: null,
      uploadProgress: null,
      selectedFile: null,
    })
  })

  it('应该初始化空状态', () => {
    const store = useFileUploadStore.getState()
    expect(store.files).toEqual([])
    expect(store.isLoading).toBe(false)
    expect(store.error).toBeNull()
    expect(store.uploadProgress).toBeNull()
    expect(store.selectedFile).toBeNull()
  })

  it('应该能够添加文件', () => {
    const store = useFileUploadStore.getState()
    const newFile = {
      id: 1,
      filename: 'test.csv',
      file_format: 'csv',
      file_size: 1024,
      created_at: '2025-11-10T00:00:00Z',
      parse_status: 'success' as const,
    }

    store.addFile(newFile)

    const updated = useFileUploadStore.getState()
    expect(updated.files).toHaveLength(1)
    expect(updated.files[0]).toEqual(newFile)
  })

  it('应该能够设置加载状态', () => {
    const store = useFileUploadStore.getState()
    store.setLoading(true)

    const updated = useFileUploadStore.getState()
    expect(updated.isLoading).toBe(true)

    store.setLoading(false)
    const updated2 = useFileUploadStore.getState()
    expect(updated2.isLoading).toBe(false)
  })

  it('应该能够设置错误信息', () => {
    const store = useFileUploadStore.getState()
    const errorMsg = '上传失败'
    store.setError(errorMsg)

    const updated = useFileUploadStore.getState()
    expect(updated.error).toBe(errorMsg)
  })

  it('应该能够设置上传进度', () => {
    const store = useFileUploadStore.getState()
    const progress = {
      fileName: 'test.csv',
      fileSize: 1024,
      uploadedSize: 512,
      progress: 50,
      speed: 1024,
      remainingTime: 1,
      status: 'uploading' as const,
    }

    store.setUploadProgress(progress)

    const updated = useFileUploadStore.getState()
    expect(updated.uploadProgress).toEqual(progress)
  })

  it('应该能够清空所有状态', () => {
    const store = useFileUploadStore.getState()

    // 先设置一些数据
    store.addFile({
      id: 1,
      filename: 'test.csv',
      file_format: 'csv',
      file_size: 1024,
      created_at: '2025-11-10T00:00:00Z',
      parse_status: 'success' as const,
    })
    store.setError('测试错误')

    // 清空
    store.clearAll()

    const updated = useFileUploadStore.getState()
    expect(updated.files).toEqual([])
    expect(updated.error).toBeNull()
    expect(updated.isLoading).toBe(false)
  })
})

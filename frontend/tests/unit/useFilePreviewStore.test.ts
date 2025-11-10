/**
 * useFilePreviewStore 单元测试。
 *
 * 测试文件预览状态存储的所有操作。
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { useFilePreviewStore } from '@/stores/useFilePreviewStore'

describe('useFilePreviewStore', () => {
  beforeEach(() => {
    // 重置状态
    useFilePreviewStore.setState({
      currentFile: null,
      previewData: null,
      sheets: [],
      selectedSheet: null,
      isLoading: false,
      error: null,
    })
  })

  it('应该初始化空状态', () => {
    const store = useFilePreviewStore.getState()
    expect(store.currentFile).toBeNull()
    expect(store.previewData).toBeNull()
    expect(store.sheets).toEqual([])
    expect(store.selectedSheet).toBeNull()
    expect(store.isLoading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('应该能够设置当前文件', () => {
    const store = useFilePreviewStore.getState()
    const file = {
      id: 1,
      filename: 'test.csv',
      file_format: 'csv',
      file_size: 1024,
      metadata: {
        rows_count: 100,
        columns_count: 5,
        column_names: ['id', 'name', 'email', 'age', 'city'],
        data_types: ['integer', 'string', 'string', 'integer', 'string'],
        storage_path: '/uploads/test.csv',
      },
    }

    store.setCurrentFile(file)

    const updated = useFilePreviewStore.getState()
    expect(updated.currentFile).toEqual(file)
  })

  it('应该能够设置预览数据', () => {
    const store = useFilePreviewStore.getState()
    const data = {
      columns: ['id', 'name'],
      data: [
        [1, 'Alice'],
        [2, 'Bob'],
      ],
      dataTypes: ['integer', 'string'],
      totalRows: 2,
    }

    store.setPreviewData(data)

    const updated = useFilePreviewStore.getState()
    expect(updated.previewData).toEqual(data)
  })

  it('应该能够设置工作表', () => {
    const store = useFilePreviewStore.getState()
    const sheets = [
      { name: 'Sheet1', index: 0 },
      { name: 'Sheet2', index: 1 },
    ]

    store.setSheets(sheets)

    const updated = useFilePreviewStore.getState()
    expect(updated.sheets).toEqual(sheets)
  })

  it('应该能够选择工作表', () => {
    const store = useFilePreviewStore.getState()
    const sheet = { name: 'Sheet1', index: 0 }

    store.setSelectedSheet(sheet)

    const updated = useFilePreviewStore.getState()
    expect(updated.selectedSheet).toEqual(sheet)
  })

  it('应该能够设置加载状态', () => {
    const store = useFilePreviewStore.getState()
    store.setLoading(true)

    const updated = useFilePreviewStore.getState()
    expect(updated.isLoading).toBe(true)
  })

  it('应该能够设置错误信息', () => {
    const store = useFilePreviewStore.getState()
    store.setError('加载失败')

    const updated = useFilePreviewStore.getState()
    expect(updated.error).toBe('加载失败')
  })

  it('应该能够加载文件元数据', () => {
    const store = useFilePreviewStore.getState()
    const file = {
      id: 1,
      filename: 'test.csv',
      file_format: 'csv',
      file_size: 1024,
    }

    store.loadFileMetadata(file)

    const updated = useFilePreviewStore.getState()
    expect(updated.currentFile).toEqual(file)
    expect(updated.previewData).toBeNull()
    expect(updated.sheets).toEqual([])
  })

  it('应该能够清除预览数据', () => {
    const store = useFilePreviewStore.getState()

    // 先设置数据
    store.setPreviewData({
      columns: ['id'],
      data: [[1]],
      totalRows: 1,
    })
    store.setSheets([{ name: 'Sheet1', index: 0 }])

    // 清除
    store.clearPreview()

    const updated = useFilePreviewStore.getState()
    expect(updated.previewData).toBeNull()
    expect(updated.sheets).toEqual([])
  })

  it('应该能够清空所有状态', () => {
    const store = useFilePreviewStore.getState()

    // 先设置数据
    store.setCurrentFile({
      id: 1,
      filename: 'test.csv',
      file_format: 'csv',
      file_size: 1024,
    })
    store.setError('测试错误')

    // 清空
    store.clearAll()

    const updated = useFilePreviewStore.getState()
    expect(updated.currentFile).toBeNull()
    expect(updated.previewData).toBeNull()
    expect(updated.error).toBeNull()
    expect(updated.isLoading).toBe(false)
  })
})

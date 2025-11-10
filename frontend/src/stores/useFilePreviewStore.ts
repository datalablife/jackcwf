/**
 * 文件预览状态存储。
 *
 * 使用 Zustand 管理文件预览的全局状态。
 */

import { create } from 'zustand'

export interface FileMetadata {
  id: number
  filename: string
  file_format: string
  file_size: number
  row_count?: number
  column_count?: number
  created_at?: string
  parse_status?: 'pending' | 'success' | 'error'
  parse_error?: string
  metadata?: {
    rows_count?: number
    columns_count?: number
    column_names?: string[]
    data_types?: string[]
    storage_path?: string
  }
}

export interface PreviewData {
  columns: string[]
  data: (string | number | boolean | null)[][]
  dataTypes?: string[]
  totalRows?: number
  currentPage?: number
  pageSize?: number
}

export interface ExcelSheet {
  name: string
  index: number
}

export interface FilePreviewStore {
  // 状态
  currentFile: FileMetadata | null
  previewData: PreviewData | null
  sheets: ExcelSheet[]
  selectedSheet: ExcelSheet | null
  isLoading: boolean
  error: string | null

  // 操作
  setCurrentFile: (file: FileMetadata | null) => void
  setPreviewData: (data: PreviewData | null) => void
  setSheets: (sheets: ExcelSheet[]) => void
  setSelectedSheet: (sheet: ExcelSheet | null) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  loadFileMetadata: (file: FileMetadata) => void
  clearPreview: () => void
  clearAll: () => void
}

export const useFilePreviewStore = create<FilePreviewStore>((set) => ({
  // 初始状态
  currentFile: null,
  previewData: null,
  sheets: [],
  selectedSheet: null,
  isLoading: false,
  error: null,

  // 设置当前文件
  setCurrentFile: (file) => set({ currentFile: file }),

  // 设置预览数据
  setPreviewData: (data) => set({ previewData: data }),

  // 设置工作表列表
  setSheets: (sheets) => set({ sheets }),

  // 选择工作表
  setSelectedSheet: (sheet) => set({ selectedSheet: sheet }),

  // 设置加载状态
  setLoading: (loading) => set({ isLoading: loading }),

  // 设置错误信息
  setError: (error) => set({ error }),

  // 加载文件元数据
  loadFileMetadata: (file) =>
    set({
      currentFile: file,
      previewData: null,
      sheets: [],
      selectedSheet: null,
      error: null,
    }),

  // 清除预览数据
  clearPreview: () =>
    set({
      previewData: null,
      sheets: [],
      selectedSheet: null,
    }),

  // 清空所有状态
  clearAll: () =>
    set({
      currentFile: null,
      previewData: null,
      sheets: [],
      selectedSheet: null,
      isLoading: false,
      error: null,
    }),
}))

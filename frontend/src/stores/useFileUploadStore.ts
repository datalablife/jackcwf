/**
 * 文件上传状态存储。
 *
 * 使用 Zustand 管理文件上传的全局状态。
 */

import { create } from 'zustand'

export interface UploadedFile {
  id: number
  filename: string
  file_format: string
  file_size: number
  row_count?: number
  column_count?: number
  created_at: string
  parse_status: 'pending' | 'success' | 'error'
  parse_error?: string
}

export interface UploadProgress {
  fileName: string
  fileSize: number
  uploadedSize: number
  progress: number
  speed: number
  remainingTime: number
  status: 'uploading' | 'completed' | 'error' | 'paused'
  error?: string
}

export interface FileUploadStore {
  // 状态
  files: UploadedFile[]
  isLoading: boolean
  error: string | null
  uploadProgress: UploadProgress | null
  selectedFile: UploadedFile | null

  // 操作
  setFiles: (files: UploadedFile[]) => void
  addFile: (file: UploadedFile) => void
  removeFile: (id: number) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  setUploadProgress: (progress: UploadProgress | null) => void
  setSelectedFile: (file: UploadedFile | null) => void
  clearAll: () => void
}

export const useFileUploadStore = create<FileUploadStore>((set) => ({
  // 初始状态
  files: [],
  isLoading: false,
  error: null,
  uploadProgress: null,
  selectedFile: null,

  // 设置文件列表
  setFiles: (files) => set({ files }),

  // 添加新文件
  addFile: (file) =>
    set((state) => ({
      files: [file, ...state.files],
    })),

  // 删除文件
  removeFile: (id) =>
    set((state) => ({
      files: state.files.filter((f) => f.id !== id),
      selectedFile:
        state.selectedFile?.id === id ? null : state.selectedFile,
    })),

  // 设置加载状态
  setLoading: (loading) => set({ isLoading: loading }),

  // 设置错误信息
  setError: (error) => set({ error }),

  // 设置上传进度
  setUploadProgress: (progress) => set({ uploadProgress: progress }),

  // 选择文件
  setSelectedFile: (file) => set({ selectedFile: file }),

  // 清空所有状态
  clearAll: () =>
    set({
      files: [],
      isLoading: false,
      error: null,
      uploadProgress: null,
      selectedFile: null,
    }),
}))

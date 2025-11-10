/**
 * 文件上传 API 客户端。
 *
 * 使用 Axios 与后端 API 通信。
 */

import axios, { AxiosInstance, AxiosProgressEvent } from 'axios'

// API 基础 URL
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// 创建 Axios 实例
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 秒超时
  headers: {
    'Content-Type': 'multipart/form-data',
  },
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // 401 未授权，清除 token 并重定向
      localStorage.removeItem('auth_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export interface UploadResponse {
  id: number
  filename: string
  file_format: string
  file_size: number
  row_count?: number
  column_count?: number
  parse_status: string
  created_at: string
}

export interface FileListResponse {
  total: number
  skip: number
  limit: number
  items: UploadResponse[]
}

export interface DeleteResponse {
  success: boolean
  message?: string
}

export interface UploadProgressCallback {
  (progress: {
    loaded: number
    total: number
    percentage: number
  }): void
}

/**
 * 上传文件
 */
export async function uploadFile(
  file: File,
  dataSourceId: number,
  onProgress?: UploadProgressCallback
): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('data_source_id', String(dataSourceId))

  const response = await apiClient.post<UploadResponse>(
    '/api/file-uploads',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent: AxiosProgressEvent) => {
        if (onProgress && progressEvent.total) {
          onProgress({
            loaded: progressEvent.loaded,
            total: progressEvent.total,
            percentage: (progressEvent.loaded / progressEvent.total) * 100,
          })
        }
      },
    }
  )
  return response.data
}

/**
 * 获取文件列表
 */
export async function getFileList(
  dataSourceId?: number,
  skip: number = 0,
  limit: number = 20
): Promise<FileListResponse> {
  const params = new URLSearchParams()
  params.append('skip', String(skip))
  params.append('limit', String(limit))
  if (dataSourceId) {
    params.append('data_source_id', String(dataSourceId))
  }

  const response = await apiClient.get<FileListResponse>(
    '/api/file-uploads',
    { params }
  )
  return response.data
}

/**
 * 获取文件详情
 */
export async function getFileDetail(fileId: number): Promise<UploadResponse> {
  const response = await apiClient.get<UploadResponse>(
    `/api/file-uploads/${fileId}`
  )
  return response.data
}

/**
 * 删除文件
 */
export async function deleteFile(fileId: number): Promise<DeleteResponse> {
  const response = await apiClient.delete<DeleteResponse>(
    `/api/file-uploads/${fileId}`
  )
  return response.data
}

/**
 * 获取文件预览数据
 */
export async function getFilePreview(
  fileId: number,
  maxRows: number = 100,
  sheetName?: string
): Promise<{
  columns: string[]
  data: (string | number | boolean | null)[][]
  dataTypes: string[]
  rowCount: number
  columnCount: number
}> {
  const params = new URLSearchParams()
  params.append('max_rows', String(maxRows))
  if (sheetName) {
    params.append('sheet_name', sheetName)
  }

  const response = await apiClient.get(
    `/api/file-uploads/${fileId}/preview`,
    { params }
  )
  return response.data
}

/**
 * 获取文件元数据
 */
export async function getFileMetadata(fileId: number): Promise<{
  rows_count: number
  columns_count: number
  column_names: string[]
  data_types: string[]
  storage_path: string
}> {
  const response = await apiClient.get(
    `/api/file-uploads/${fileId}/metadata`
  )
  return response.data
}

/**
 * 获取 Excel 工作表列表
 */
export async function getExcelSheets(
  fileId: number
): Promise<{ name: string; index: number }[]> {
  const response = await apiClient.get(
    `/api/file-uploads/${fileId}/sheets`
  )
  return response.data?.sheets || []
}

/**
 * 解析文件
 */
export async function parseFile(
  fileId: number,
  sheetName?: string
): Promise<{
  success: boolean
  rows_count: number
  columns_count: number
  column_names: string[]
  data_types: string[]
  message?: string
}> {
  const response = await apiClient.post(
    `/api/file-uploads/${fileId}/parse`,
    sheetName ? { sheet_name: sheetName } : {}
  )
  return response.data
}

export default apiClient

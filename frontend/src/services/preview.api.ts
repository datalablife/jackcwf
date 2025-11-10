/**
 * 文件预览 API 客户端。
 *
 * 为文件预览功能提供 API 接口。
 */

import apiClient from './file.api'

export interface PreviewResponse {
  columns: string[]
  data: (string | number | boolean | null)[][]
  dataTypes?: string[]
  totalRows?: number
  fileName?: string
}

export interface MetadataResponse {
  rows_count: number
  columns_count: number
  column_names: string[]
  data_types: string[]
  storage_path: string
  additional_metadata?: Record<string, unknown>
}

export interface SheetsResponse {
  sheets: {
    name: string
    index: number
  }[]
  fileName?: string
}

export interface ParseResponse {
  success: boolean
  rows_count?: number
  columns_count?: number
  column_names?: string[]
  data_types?: string[]
  message?: string
}

/**
 * 获取文件预览数据
 */
export async function fetchFilePreview(
  fileId: number,
  options?: {
    maxRows?: number
    sheetName?: string
  }
): Promise<PreviewResponse> {
  const params = new URLSearchParams()
  if (options?.maxRows) {
    params.append('max_rows', String(options.maxRows))
  }
  if (options?.sheetName) {
    params.append('sheet_name', options.sheetName)
  }

  const response = await apiClient.get<PreviewResponse>(
    `/api/file-uploads/${fileId}/preview`,
    { params: Object.fromEntries(params) }
  )
  return response.data
}

/**
 * 获取文件元数据
 */
export async function fetchFileMetadata(
  fileId: number
): Promise<MetadataResponse> {
  const response = await apiClient.get<MetadataResponse>(
    `/api/file-uploads/${fileId}/metadata`
  )
  return response.data
}

/**
 * 获取 Excel 工作表列表
 */
export async function fetchExcelSheets(fileId: number): Promise<SheetsResponse> {
  const response = await apiClient.get<SheetsResponse>(
    `/api/file-uploads/${fileId}/sheets`
  )
  return response.data
}

/**
 * 解析文件
 */
export async function parseFileData(
  fileId: number,
  options?: {
    sheetName?: string
  }
): Promise<ParseResponse> {
  const response = await apiClient.post<ParseResponse>(
    `/api/file-uploads/${fileId}/parse`,
    options || {}
  )
  return response.data
}

/**
 * 获取完整的预览数据（包括元数据）
 */
export async function fetchCompletePreviewData(
  fileId: number,
  sheetName?: string
): Promise<{
  preview: PreviewResponse
  metadata: MetadataResponse
}> {
  const [preview, metadata] = await Promise.all([
    fetchFilePreview(fileId, { sheetName }),
    fetchFileMetadata(fileId),
  ])
  return { preview, metadata }
}

export default {
  fetchFilePreview,
  fetchFileMetadata,
  fetchExcelSheets,
  parseFileData,
  fetchCompletePreviewData,
}

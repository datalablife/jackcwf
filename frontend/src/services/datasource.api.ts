/**
 * 数据源 API 客户端服务。
 *
 * 提供与后端数据源 API 端点的通信。
 */

import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface PostgresConnectionConfig {
  name: string
  description?: string
  host: string
  port: number
  database: string
  username: string
  password: string
}

export interface DataSourceResponse {
  id: number
  name: string
  description?: string
  type: string
  status: string
  error_message?: string
  created_at: string
  updated_at: string
}

export interface DataSourceListResponse {
  total: number
  datasources: DataSourceResponse[]
}

/**
 * 数据源 API 操作对象。
 */
export const dataSourceAPI = {
  /**
   * 列出所有数据源。
   *
   * @returns 数据源列表响应
   * @throws 如果请求失败
   */
  listDataSources: async (): Promise<DataSourceListResponse> => {
    const response = await apiClient.get('/api/datasources')
    return response.data
  },

  /**
   * 创建新的 PostgreSQL 数据源。
   *
   * @param config PostgreSQL 连接配置
   * @returns 创建的数据源
   * @throws 如果创建失败
   */
  createPostgresDataSource: async (
    config: PostgresConnectionConfig
  ): Promise<DataSourceResponse> => {
    const response = await apiClient.post('/api/datasources/postgres', config)
    return response.data
  },

  /**
   * 测试数据源连接。
   *
   * @param dataSourceId 数据源 ID
   * @returns 测试结果
   * @throws 如果测试失败
   */
  testConnection: async (
    dataSourceId: number
  ): Promise<{ success: boolean; message: string }> => {
    const response = await apiClient.post(`/api/datasources/${dataSourceId}/test`)
    return response.data
  },

  /**
   * 获取特定数据源。
   *
   * @param id 数据源 ID
   * @returns 数据源详情
   * @throws 如果数据源未找到
   */
  getDataSource: async (id: number): Promise<DataSourceResponse> => {
    const response = await apiClient.get(`/api/datasources/${id}`)
    return response.data
  },

  /**
   * 删除数据源。
   *
   * @param id 数据源 ID
   * @throws 如果删除失败
   */
  deleteDataSource: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/datasources/${id}`)
  },
}


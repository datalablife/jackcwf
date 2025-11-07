import { create } from 'zustand'

export interface DataSource {
  id: number
  name: string
  description?: string
  type: 'postgresql' | 'csv' | 'excel' | 'json'
  status: 'connected' | 'disconnected' | 'error' | 'testing'
  error_message?: string
  created_at: string
  updated_at: string
}

interface DataSourceStore {
  // 状态
  dataSources: DataSource[]
  selectedId: number | null
  isLoading: boolean
  error: string | null

  // 操作
  fetchDataSources: () => Promise<void>
  selectDataSource: (id: number) => void
  addDataSource: (
    name: string,
    description: string | undefined,
    host: string,
    port: number,
    database: string,
    username: string,
    password: string
  ) => Promise<DataSource>
  removeDataSource: (id: number) => Promise<void>
  testConnection: (id: number) => Promise<boolean>
  setError: (error: string | null) => void
  setLoading: (loading: boolean) => void
  clearError: () => void
}

export const useDataSourceStore = create<DataSourceStore>((set) => ({
  // 初始状态
  dataSources: [],
  selectedId: null,
  isLoading: false,
  error: null,

  // 操作实现
  fetchDataSources: async () => {
    set({ isLoading: true, error: null })
    try {
      const response = await fetch('/api/datasources')
      if (!response.ok) {
        throw new Error(`获取数据源失败: ${response.statusText}`)
      }
      const data = await response.json()
      set({ dataSources: data.datasources || [] })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '未知错误'
      set({ error: errorMessage })
    } finally {
      set({ isLoading: false })
    }
  },

  selectDataSource: (id: number) => {
    set({ selectedId: id })
  },

  addDataSource: async (
    name: string,
    description: string | undefined,
    host: string,
    port: number,
    database: string,
    username: string,
    password: string
  ) => {
    set({ isLoading: true, error: null })
    try {
      const response = await fetch('/api/datasources/postgres', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name,
          description,
          host,
          port,
          database,
          username,
          password,
        }),
      })
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `创建数据源失败: ${response.statusText}`)
      }
      const datasource = await response.json()
      set((state) => ({
        dataSources: [datasource, ...state.dataSources],
      }))
      return datasource
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '未知错误'
      set({ error: errorMessage })
      throw error
    } finally {
      set({ isLoading: false })
    }
  },

  removeDataSource: async (id: number) => {
    set({ isLoading: true, error: null })
    try {
      const response = await fetch(`/api/datasources/${id}`, {
        method: 'DELETE',
      })
      if (!response.ok) {
        throw new Error(`删除数据源失败: ${response.statusText}`)
      }
      set((state) => ({
        dataSources: state.dataSources.filter((ds) => ds.id !== id),
        selectedId: state.selectedId === id ? null : state.selectedId,
      }))
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '未知错误'
      set({ error: errorMessage })
      throw error
    } finally {
      set({ isLoading: false })
    }
  },

  testConnection: async (id: number) => {
    set({ isLoading: true, error: null })
    try {
      const response = await fetch(`/api/datasources/${id}/test`, {
        method: 'POST',
      })
      if (!response.ok) {
        throw new Error(`连接测试失败: ${response.statusText}`)
      }
      const result = await response.json()
      if (!result.success) {
        set({ error: result.message })
        return false
      }
      return true
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '未知错误'
      set({ error: errorMessage })
      return false
    } finally {
      set({ isLoading: false })
    }
  },

  setError: (error: string | null) => {
    set({ error })
  },

  setLoading: (loading: boolean) => {
    set({ isLoading: loading })
  },

  clearError: () => {
    set({ error: null })
  },
}))


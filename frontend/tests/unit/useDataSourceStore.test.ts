"""
数据源 Zustand 存储单元测试

测试所有存储操作：
- fetchDataSources
- selectDataSource
- addDataSource
- removeDataSource
- testConnection
- 错误处理和加载状态
"""

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useDataSourceStore } from '@/stores/useDataSourceStore'
import * as api from '@/services/datasource.api'

// 模拟 API 服务
vi.mock('@/services/datasource.api')

describe('useDataSourceStore', () => {
  beforeEach(() => {
    // 重置 mock 和存储状态
    vi.clearAllMocks()
    useDataSourceStore.setState({
      dataSources: [],
      selectedId: null,
      isLoading: false,
      error: null,
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('初始状态', () => {
    it('应该有正确的初始状态', () => {
      const { result } = renderHook(() => useDataSourceStore())

      expect(result.current.dataSources).toEqual([])
      expect(result.current.selectedId).toBeNull()
      expect(result.current.isLoading).toBe(false)
      expect(result.current.error).toBeNull()
    })
  })

  describe('fetchDataSources', () => {
    it('应该成功获取数据源列表', async () => {
      const mockDataSources = [
        {
          id: 1,
          name: 'test_postgres_1',
          type: 'postgresql',
          status: 'connected',
          description: '测试数据库 1',
          created_at: '2025-11-08T10:00:00',
          updated_at: '2025-11-08T10:00:00',
          error_message: null,
        },
        {
          id: 2,
          name: 'test_postgres_2',
          type: 'postgresql',
          status: 'error',
          description: '测试数据库 2',
          created_at: '2025-11-08T11:00:00',
          updated_at: '2025-11-08T11:00:00',
          error_message: '连接失败',
        },
      ]

      vi.mocked(api.dataSourceAPI.listDataSources).mockResolvedValue({
        datasources: mockDataSources,
      })

      const { result } = renderHook(() => useDataSourceStore())

      // 开始获取
      expect(result.current.isLoading).toBe(false)

      await act(async () => {
        await result.current.fetchDataSources()
      })

      // 验证结果
      expect(result.current.dataSources).toHaveLength(2)
      expect(result.current.dataSources[0].name).toBe('test_postgres_1')
      expect(result.current.dataSources[1].status).toBe('error')
      expect(result.current.error).toBeNull()
    })

    it('应该处理获取失败的情况', async () => {
      const errorMessage = '获取数据源失败'
      vi.mocked(api.dataSourceAPI.listDataSources).mockRejectedValue(
        new Error(errorMessage)
      )

      const { result } = renderHook(() => useDataSourceStore())

      await act(async () => {
        await result.current.fetchDataSources()
      })

      expect(result.current.error).toBe(errorMessage)
      expect(result.current.dataSources).toEqual([])
    })

    it('应该在获取过程中设置加载状态', async () => {
      vi.mocked(api.dataSourceAPI.listDataSources).mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  datasources: [],
                }),
              100
            )
          )
      )

      const { result } = renderHook(() => useDataSourceStore())

      const fetchPromise = act(async () => {
        await result.current.fetchDataSources()
      })

      // 在获取过程中，isLoading 应该为 true
      // 等待完成
      await fetchPromise

      expect(result.current.isLoading).toBe(false)
    })
  })

  describe('selectDataSource', () => {
    it('应该成功选择数据源', () => {
      const { result } = renderHook(() => useDataSourceStore())

      act(() => {
        result.current.selectDataSource(1)
      })

      expect(result.current.selectedId).toBe(1)
    })

    it('应该能够改变选择', () => {
      const { result } = renderHook(() => useDataSourceStore())

      act(() => {
        result.current.selectDataSource(1)
      })
      expect(result.current.selectedId).toBe(1)

      act(() => {
        result.current.selectDataSource(2)
      })
      expect(result.current.selectedId).toBe(2)
    })

    it('应该能够取消选择（选择 null）', () => {
      const { result } = renderHook(() => useDataSourceStore())

      act(() => {
        result.current.selectDataSource(1)
      })
      expect(result.current.selectedId).toBe(1)

      act(() => {
        result.current.selectDataSource(null)
      })
      expect(result.current.selectedId).toBeNull()
    })
  })

  describe('addDataSource', () => {
    it('应该成功添加新的数据源', async () => {
      const newDataSource = {
        id: 1,
        name: 'new_postgres',
        type: 'postgresql',
        status: 'connected',
        description: '新数据源',
        created_at: '2025-11-08T12:00:00',
        updated_at: '2025-11-08T12:00:00',
        error_message: null,
      }

      vi.mocked(api.dataSourceAPI.createPostgresDataSource).mockResolvedValue(
        newDataSource
      )

      const { result } = renderHook(() => useDataSourceStore())

      const config = {
        name: 'new_postgres',
        host: 'localhost',
        port: 5432,
        database: 'test',
        username: 'user',
        password: 'pass',
      }

      await act(async () => {
        await result.current.addDataSource(config)
      })

      expect(result.current.dataSources).toHaveLength(1)
      expect(result.current.dataSources[0].name).toBe('new_postgres')
      expect(result.current.error).toBeNull()
    })

    it('应该处理添加失败的情况', async () => {
      const errorMessage = '创建数据源失败'
      vi.mocked(api.dataSourceAPI.createPostgresDataSource).mockRejectedValue(
        new Error(errorMessage)
      )

      const { result } = renderHook(() => useDataSourceStore())

      const config = {
        name: 'new_postgres',
        host: 'localhost',
        port: 5432,
        database: 'test',
        username: 'user',
        password: 'pass',
      }

      await act(async () => {
        await result.current.addDataSource(config)
      })

      expect(result.current.error).toBe(errorMessage)
      expect(result.current.dataSources).toHaveLength(0)
    })
  })

  describe('removeDataSource', () => {
    it('应该成功删除数据源', async () => {
      // 首先添加数据源
      useDataSourceStore.setState({
        dataSources: [
          {
            id: 1,
            name: 'test',
            type: 'postgresql',
            status: 'connected',
            created_at: '2025-11-08T10:00:00',
            updated_at: '2025-11-08T10:00:00',
            error_message: null,
          },
        ],
      })

      vi.mocked(api.dataSourceAPI.deleteDataSource).mockResolvedValue(true)

      const { result } = renderHook(() => useDataSourceStore())

      expect(result.current.dataSources).toHaveLength(1)

      await act(async () => {
        await result.current.removeDataSource(1)
      })

      expect(result.current.dataSources).toHaveLength(0)
      expect(result.current.error).toBeNull()
    })

    it('应该处理删除失败的情况', async () => {
      useDataSourceStore.setState({
        dataSources: [
          {
            id: 1,
            name: 'test',
            type: 'postgresql',
            status: 'connected',
            created_at: '2025-11-08T10:00:00',
            updated_at: '2025-11-08T10:00:00',
            error_message: null,
          },
        ],
      })

      const errorMessage = '删除数据源失败'
      vi.mocked(api.dataSourceAPI.deleteDataSource).mockRejectedValue(
        new Error(errorMessage)
      )

      const { result } = renderHook(() => useDataSourceStore())

      await act(async () => {
        await result.current.removeDataSource(1)
      })

      expect(result.current.error).toBe(errorMessage)
      expect(result.current.dataSources).toHaveLength(1)
    })
  })

  describe('testConnection', () => {
    it('应该成功测试连接', async () => {
      vi.mocked(api.dataSourceAPI.testConnection).mockResolvedValue({
        connected: true,
        message: '连接成功',
      })

      const { result } = renderHook(() => useDataSourceStore())

      const connected = await act(async () => {
        return await result.current.testConnection(1)
      })

      expect(connected).toBe(true)
      expect(result.current.error).toBeNull()
    })

    it('应该处理连接失败的情况', async () => {
      vi.mocked(api.dataSourceAPI.testConnection).mockResolvedValue({
        connected: false,
        message: '连接失败',
      })

      const { result } = renderHook(() => useDataSourceStore())

      const connected = await act(async () => {
        return await result.current.testConnection(1)
      })

      expect(connected).toBe(false)
    })

    it('应该处理异常错误', async () => {
      const errorMessage = '测试连接异常'
      vi.mocked(api.dataSourceAPI.testConnection).mockRejectedValue(
        new Error(errorMessage)
      )

      const { result } = renderHook(() => useDataSourceStore())

      await act(async () => {
        await result.current.testConnection(1)
      })

      expect(result.current.error).toBe(errorMessage)
    })
  })

  describe('错误处理', () => {
    it('应该能够清除错误', () => {
      const { result } = renderHook(() => useDataSourceStore())

      // 设置错误
      act(() => {
        result.current.setError('测试错误')
      })
      expect(result.current.error).toBe('测试错误')

      // 清除错误
      act(() => {
        result.current.clearError()
      })
      expect(result.current.error).toBeNull()
    })

    it('应该能够设置加载状态', () => {
      const { result } = renderHook(() => useDataSourceStore())

      act(() => {
        result.current.setLoading(true)
      })
      expect(result.current.isLoading).toBe(true)

      act(() => {
        result.current.setLoading(false)
      })
      expect(result.current.isLoading).toBe(false)
    })
  })

  describe('复杂场景', () => {
    it('应该处理多个数据源的选择和删除', async () => {
      const mockDataSources = [
        {
          id: 1,
          name: 'postgres_1',
          type: 'postgresql',
          status: 'connected',
          created_at: '2025-11-08T10:00:00',
          updated_at: '2025-11-08T10:00:00',
          error_message: null,
        },
        {
          id: 2,
          name: 'postgres_2',
          type: 'postgresql',
          status: 'connected',
          created_at: '2025-11-08T10:00:00',
          updated_at: '2025-11-08T10:00:00',
          error_message: null,
        },
      ]

      useDataSourceStore.setState({
        dataSources: mockDataSources,
      })

      vi.mocked(api.dataSourceAPI.deleteDataSource).mockResolvedValue(true)

      const { result } = renderHook(() => useDataSourceStore())

      // 选择第一个
      act(() => {
        result.current.selectDataSource(1)
      })
      expect(result.current.selectedId).toBe(1)

      // 删除第一个
      await act(async () => {
        await result.current.removeDataSource(1)
      })

      expect(result.current.dataSources).toHaveLength(1)
      expect(result.current.selectedId).toBe(1) // 仍然选中已删除的 ID

      // 选择第二个
      act(() => {
        result.current.selectDataSource(2)
      })
      expect(result.current.selectedId).toBe(2)
    })

    it('应该在并发操作中保持一致性', async () => {
      const mockDataSources = [
        {
          id: 1,
          name: 'postgres_1',
          type: 'postgresql',
          status: 'connected',
          created_at: '2025-11-08T10:00:00',
          updated_at: '2025-11-08T10:00:00',
          error_message: null,
        },
      ]

      vi.mocked(api.dataSourceAPI.listDataSources).mockResolvedValue({
        datasources: mockDataSources,
      })

      vi.mocked(api.dataSourceAPI.testConnection).mockResolvedValue({
        connected: true,
        message: '成功',
      })

      const { result } = renderHook(() => useDataSourceStore())

      // 并发执行多个操作
      await act(async () => {
        await Promise.all([
          result.current.fetchDataSources(),
          result.current.testConnection(1),
        ])
      })

      expect(result.current.dataSources).toHaveLength(1)
    })
  })
})

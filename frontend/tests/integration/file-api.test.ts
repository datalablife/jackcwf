/**
 * file.api.ts 集成测试。
 *
 * 测试文件 API 客户端的所有函数。
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'
import * as fileApi from '@/services/file.api'

// Mock axios
vi.mock('axios')

const mockedAxios = axios as unknown as {
  create: ReturnType<typeof vi.fn>
}

describe('file.api', () => {
  let mockInstance: ReturnType<typeof vi.fn>

  beforeEach(() => {
    // 创建模拟的 axios 实例
    mockInstance = vi.fn()
    mockInstance.get = vi.fn()
    mockInstance.post = vi.fn()
    mockInstance.delete = vi.fn()
    mockInstance.interceptors = {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    }

    ;(mockedAxios.create as ReturnType<typeof vi.fn>).mockReturnValue(mockInstance)
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('getFileList', () => {
    it('应该返回文件列表', async () => {
      const mockResponse = {
        data: {
          total: 10,
          skip: 0,
          limit: 20,
          items: [
            {
              id: 1,
              filename: 'test.csv',
              file_format: 'csv',
              file_size: 1024,
              parse_status: 'success',
              created_at: '2025-11-10T00:00:00Z',
            },
          ],
        },
      }

      mockInstance.get.mockResolvedValue(mockResponse)

      const result = await fileApi.getFileList()

      expect(result).toEqual(mockResponse.data)
      expect(mockInstance.get).toHaveBeenCalledWith('/api/file-uploads', {
        params: { skip: 0, limit: 20 },
      })
    })

    it('应该支持数据源 ID 过滤', async () => {
      const mockResponse = { data: { total: 0, skip: 0, limit: 20, items: [] } }
      mockInstance.get.mockResolvedValue(mockResponse)

      await fileApi.getFileList(1)

      expect(mockInstance.get).toHaveBeenCalledWith('/api/file-uploads', {
        params: { skip: 0, limit: 20, data_source_id: '1' },
      })
    })

    it('应该支持分页参数', async () => {
      const mockResponse = { data: { total: 0, skip: 10, limit: 10, items: [] } }
      mockInstance.get.mockResolvedValue(mockResponse)

      await fileApi.getFileList(undefined, 10, 10)

      expect(mockInstance.get).toHaveBeenCalledWith('/api/file-uploads', {
        params: { skip: 10, limit: 10 },
      })
    })
  })

  describe('getFileDetail', () => {
    it('应该返回文件详情', async () => {
      const mockResponse = {
        data: {
          id: 1,
          filename: 'test.csv',
          file_format: 'csv',
          file_size: 1024,
          parse_status: 'success',
          created_at: '2025-11-10T00:00:00Z',
        },
      }

      mockInstance.get.mockResolvedValue(mockResponse)

      const result = await fileApi.getFileDetail(1)

      expect(result).toEqual(mockResponse.data)
      expect(mockInstance.get).toHaveBeenCalledWith('/api/file-uploads/1')
    })
  })

  describe('deleteFile', () => {
    it('应该删除文件', async () => {
      const mockResponse = { data: { success: true, message: '文件已删除' } }
      mockInstance.delete.mockResolvedValue(mockResponse)

      const result = await fileApi.deleteFile(1)

      expect(result).toEqual(mockResponse.data)
      expect(mockInstance.delete).toHaveBeenCalledWith('/api/file-uploads/1')
    })
  })

  describe('getFileMetadata', () => {
    it('应该返回文件元数据', async () => {
      const mockResponse = {
        data: {
          rows_count: 100,
          columns_count: 5,
          column_names: ['id', 'name', 'email', 'age', 'city'],
          data_types: ['integer', 'string', 'string', 'integer', 'string'],
          storage_path: '/uploads/test.csv',
        },
      }

      mockInstance.get.mockResolvedValue(mockResponse)

      const result = await fileApi.getFileMetadata(1)

      expect(result).toEqual(mockResponse.data)
      expect(mockInstance.get).toHaveBeenCalledWith('/api/file-uploads/1/metadata')
    })
  })

  describe('getExcelSheets', () => {
    it('应该返回 Excel 工作表列表', async () => {
      const mockResponse = {
        data: {
          sheets: [
            { name: 'Sheet1', index: 0 },
            { name: 'Sheet2', index: 1 },
          ],
        },
      }

      mockInstance.get.mockResolvedValue(mockResponse)

      const result = await fileApi.getExcelSheets(1)

      expect(result).toEqual([
        { name: 'Sheet1', index: 0 },
        { name: 'Sheet2', index: 1 },
      ])
      expect(mockInstance.get).toHaveBeenCalledWith('/api/file-uploads/1/sheets')
    })

    it('当没有工作表时应该返回空数组', async () => {
      mockInstance.get.mockResolvedValue({ data: {} })

      const result = await fileApi.getExcelSheets(1)

      expect(result).toEqual([])
    })
  })
})

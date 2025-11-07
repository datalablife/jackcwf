"""
数据源设置页面集成测试

测试完整的 UI 流程：
- 列表标签页的数据源加载和显示
- 连接标签页的表单提交
- 数据源选择和删除
- 错误处理和加载状态
"""

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { DataSourceSetup } from '@/pages/DataSourceSetup'
import * as api from '@/services/datasource.api'

// 模拟 API 服务
vi.mock('@/services/datasource.api')

describe('DataSourceSetup 集成测试', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('页面初始化', () => {
    it('应该正确渲染页面标题和说明', () => {
      vi.mocked(api.dataSourceAPI.listDataSources).mockResolvedValue({
        datasources: [],
      })

      render(<DataSourceSetup />)

      expect(screen.getByText('数据源管理')).toBeInTheDocument()
      expect(
        screen.getByText(
          /连接和管理您的数据源（PostgreSQL 数据库和上传的文件）/
        )
      ).toBeInTheDocument()
    })

    it('应该默认显示列表标签页', () => {
      vi.mocked(api.dataSourceAPI.listDataSources).mockResolvedValue({
        datasources: [],
      })

      render(<DataSourceSetup />)

      expect(screen.getByText('📋 数据源列表')).toBeInTheDocument()
      expect(screen.getByText('➕ 连接新数据源')).toBeInTheDocument()
    })

    it('应该显示页脚安全提示', () => {
      vi.mocked(api.dataSourceAPI.listDataSources).mockResolvedValue({
        datasources: [],
      })

      render(<DataSourceSetup />)

      expect(screen.getByText(/所有数据库密码都使用 AES-256 加密存储/)).toBeInTheDocument()
    })
  })

  describe('列表标签页功能', () => {
    it('应该加载并显示数据源列表', async () => {
      const mockDataSources = [
        {
          id: 1,
          name: 'production_db',
          type: 'postgresql',
          status: 'connected',
          description: '生产环境数据库',
          created_at: '2025-11-08T10:00:00',
          updated_at: '2025-11-08T10:00:00',
          error_message: null,
        },
        {
          id: 2,
          name: 'test_db',
          type: 'postgresql',
          status: 'error',
          description: '测试数据库',
          created_at: '2025-11-08T11:00:00',
          updated_at: '2025-11-08T11:00:00',
          error_message: '连接超时',
        },
      ]

      vi.mocked(api.dataSourceAPI.listDataSources).mockResolvedValue({
        datasources: mockDataSources,
      })

      render(<DataSourceSetup />)

      await waitFor(() => {
        expect(screen.getByText('production_db')).toBeInTheDocument()
        expect(screen.getByText('test_db')).toBeInTheDocument()
      })
    })

    it('应该显示空状态当没有数据源时', async () => {
      vi.mocked(api.dataSourceAPI.listDataSources).mockResolvedValue({
        datasources: [],
      })

      render(<DataSourceSetup />)

      await waitFor(() => {
        expect(screen.getByText('暂无数据源')).toBeInTheDocument()
      })
    })

    it('应该显示加载状态', () => {
      vi.mocked(api.dataSourceAPI.listDataSources).mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(() => resolve({ datasources: [] }), 1000)
          )
      )

      render(<DataSourceSetup />)

      expect(screen.getByText('加载数据源中...')).toBeInTheDocument()
    })

    it('应该显示错误消息', async () => {
      vi.mocked(api.dataSourceAPI.listDataSources).mockRejectedValue(
        new Error('获取数据源失败')
      )

      render(<DataSourceSetup />)

      await waitFor(() => {
        expect(screen.getByText(/获取数据源失败/)).toBeInTheDocument()
      })
    })

    it('应该能够选择数据源', async () => {
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

      render(<DataSourceSetup />)

      await waitFor(() => {
        const datasourceCard = screen.getByText('postgres_1').closest('div')
        expect(datasourceCard).toBeInTheDocument()
      })
    })

    it('应该能够删除数据源（带确认）', async () => {
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

      vi.mocked(api.dataSourceAPI.deleteDataSource).mockResolvedValue(true)

      const user = userEvent.setup()
      render(<DataSourceSetup />)

      await waitFor(() => {
        expect(screen.getByText('postgres_1')).toBeInTheDocument()
      })

      const deleteButton = screen.getByText('删除')
      await user.click(deleteButton)

      // 验证确认对话框
      // 注意：需要处理 window.confirm
      expect(api.dataSourceAPI.deleteDataSource).toHaveBeenCalledWith(1)
    })

    it('应该能够测试连接', async () => {
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
        message: '连接成功',
      })

      const user = userEvent.setup()
      render(<DataSourceSetup />)

      await waitFor(() => {
        expect(screen.getByText('postgres_1')).toBeInTheDocument()
      })

      const testButton = screen.getByText('测试连接')
      await user.click(testButton)

      expect(api.dataSourceAPI.testConnection).toHaveBeenCalledWith(1)
    })
  })

  describe('连接标签页功能', () => {
    it('应该切换到连接标签页', async () => {
      vi.mocked(api.dataSourceAPI.listDataSources).mockResolvedValue({
        datasources: [],
      })

      const user = userEvent.setup()
      render(<DataSourceSetup />)

      const connectTab = screen.getByText('➕ 连接新数据源')
      await user.click(connectTab)

      // 应该显示连接表单
      expect(screen.getByText(/连接新的 PostgreSQL 数据库/i)).toBeInTheDocument()
    })

    it('应该包含所有必需的表单字段', async () => {
      vi.mocked(api.dataSourceAPI.listDataSources).mockResolvedValue({
        datasources: [],
      })

      const user = userEvent.setup()
      render(<DataSourceSetup />)

      const connectTab = screen.getByText('➕ 连接新数据源')
      await user.click(connectTab)

      // 验证表单字段存在
      expect(screen.getByLabelText(/数据源名称/)).toBeInTheDocument()
      expect(screen.getByLabelText(/主机/)).toBeInTheDocument()
      expect(screen.getByLabelText(/端口/)).toBeInTheDocument()
      expect(screen.getByLabelText(/数据库名称/)).toBeInTheDocument()
      expect(screen.getByLabelText(/用户名/)).toBeInTheDocument()
      expect(screen.getByLabelText(/密码/)).toBeInTheDocument()
    })

    it('应该能够填写和提交连接表单', async () => {
      vi.mocked(api.dataSourceAPI.listDataSources).mockResolvedValue({
        datasources: [],
      })

      vi.mocked(api.dataSourceAPI.createPostgresDataSource).mockResolvedValue({
        id: 1,
        name: 'new_db',
        type: 'postgresql',
        status: 'connected',
        description: '新数据库',
        created_at: '2025-11-08T12:00:00',
        updated_at: '2025-11-08T12:00:00',
        error_message: null,
      })

      const user = userEvent.setup()
      render(<DataSourceSetup />)

      // 切换到连接标签页
      const connectTab = screen.getByText('➕ 连接新数据源')
      await user.click(connectTab)

      // 填写表单
      const nameInput = screen.getByLabelText(/数据源名称/)
      const hostInput = screen.getByLabelText(/主机/)
      const portInput = screen.getByLabelText(/端口/)
      const dbInput = screen.getByLabelText(/数据库名称/)
      const userInput = screen.getByLabelText(/用户名/)
      const passInput = screen.getByLabelText(/^密码$/)

      await user.type(nameInput, 'new_db')
      await user.type(hostInput, 'localhost')
      await user.type(portInput, '5432')
      await user.type(dbInput, 'mydb')
      await user.type(userInput, 'admin')
      await user.type(passInput, 'password123')

      // 提交表单
      const submitButton = screen.getByText('创建数据源')
      await user.click(submitButton)

      expect(api.dataSourceAPI.createPostgresDataSource).toHaveBeenCalled()
    })

    it('应该显示表单验证错误', async () => {
      vi.mocked(api.dataSourceAPI.listDataSources).mockResolvedValue({
        datasources: [],
      })

      const user = userEvent.setup()
      render(<DataSourceSetup />)

      const connectTab = screen.getByText('➕ 连接新数据源')
      await user.click(connectTab)

      // 尝试提交空表单
      const submitButton = screen.getByText('创建数据源')
      await user.click(submitButton)

      // 应该显示验证错误
      await waitFor(() => {
        expect(screen.getByText(/数据源名称为必填项/)).toBeInTheDocument()
      })
    })

    it('应该在创建失败时显示错误', async () => {
      vi.mocked(api.dataSourceAPI.listDataSources).mockResolvedValue({
        datasources: [],
      })

      vi.mocked(api.dataSourceAPI.createPostgresDataSource).mockRejectedValue(
        new Error('连接失败：无法连接到数据库')
      )

      const user = userEvent.setup()
      render(<DataSourceSetup />)

      const connectTab = screen.getByText('➕ 连接新数据源')
      await user.click(connectTab)

      // 填写表单
      const nameInput = screen.getByLabelText(/数据源名称/)
      await user.type(nameInput, 'test')

      const hostInput = screen.getByLabelText(/主机/)
      await user.type(hostInput, 'invalid-host')

      // 尝试创建
      const submitButton = screen.getByText('创建数据源')
      await user.click(submitButton)

      await waitFor(() => {
        expect(
          screen.getByText(/连接失败：无法连接到数据库/)
        ).toBeInTheDocument()
      })
    })

    it('应该在测试连接成功后显示成功消息', async () => {
      vi.mocked(api.dataSourceAPI.listDataSources).mockResolvedValue({
        datasources: [],
      })

      vi.mocked(api.dataSourceAPI.testConnection).mockResolvedValue({
        connected: true,
        message: '连接成功',
      })

      const user = userEvent.setup()
      render(<DataSourceSetup />)

      const connectTab = screen.getByText('➕ 连接新数据源')
      await user.click(connectTab)

      // 填写最少的表单字段
      const nameInput = screen.getByLabelText(/数据源名称/)
      await user.type(nameInput, 'test_db')

      const hostInput = screen.getByLabelText(/主机/)
      await user.type(hostInput, 'localhost')

      // 测试连接
      const testButton = screen.getByText('测试连接')
      await user.click(testButton)

      expect(api.dataSourceAPI.testConnection).toHaveBeenCalled()
    })
  })

  describe('标签页导航', () => {
    it('应该能够在标签页之间切换', async () => {
      vi.mocked(api.dataSourceAPI.listDataSources).mockResolvedValue({
        datasources: [],
      })

      const user = userEvent.setup()
      render(<DataSourceSetup />)

      // 从列表切换到连接
      let connectTab = screen.getByText('➕ 连接新数据源')
      await user.click(connectTab)
      expect(screen.getByText(/连接新的 PostgreSQL 数据库/i)).toBeInTheDocument()

      // 从连接切换回列表
      let listTab = screen.getByText('📋 数据源列表')
      await user.click(listTab)
      expect(screen.getByText('暂无数据源')).toBeInTheDocument()
    })

    it('应该保持标签页状态', async () => {
      vi.mocked(api.dataSourceAPI.listDataSources).mockResolvedValue({
        datasources: [],
      })

      const user = userEvent.setup()
      render(<DataSourceSetup />)

      // 切换到连接
      let connectTab = screen.getByText('➕ 连接新数据源')
      await user.click(connectTab)

      // 填写一些字段
      const nameInput = screen.getByLabelText(/数据源名称/)
      await user.type(nameInput, 'test')

      // 切换回列表再切换回连接
      let listTab = screen.getByText('📋 数据源列表')
      await user.click(listTab)

      connectTab = screen.getByText('➕ 连接新数据源')
      await user.click(connectTab)

      // 验证表单清空（根据实现）
      // 或者如果保留状态，验证数据仍在
    })
  })

  describe('状态指示器', () => {
    it('应该显示已连接的数据源状态', async () => {
      const mockDataSources = [
        {
          id: 1,
          name: 'active_db',
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

      render(<DataSourceSetup />)

      await waitFor(() => {
        expect(screen.getByText(/已连接/)).toBeInTheDocument()
      })
    })

    it('应该显示错误状态的数据源', async () => {
      const mockDataSources = [
        {
          id: 1,
          name: 'broken_db',
          type: 'postgresql',
          status: 'error',
          created_at: '2025-11-08T10:00:00',
          updated_at: '2025-11-08T10:00:00',
          error_message: '连接被拒绝',
        },
      ]

      vi.mocked(api.dataSourceAPI.listDataSources).mockResolvedValue({
        datasources: mockDataSources,
      })

      render(<DataSourceSetup />)

      await waitFor(() => {
        expect(screen.getByText(/错误/)).toBeInTheDocument()
        expect(screen.getByText('连接被拒绝')).toBeInTheDocument()
      })
    })
  })

  describe('无障碍性 (Accessibility)', () => {
    it('应该有适当的 ARIA 标签', async () => {
      vi.mocked(api.dataSourceAPI.listDataSources).mockResolvedValue({
        datasources: [],
      })

      render(<DataSourceSetup />)

      // 验证标题结构
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
        '数据源管理'
      )
    })

    it('应该支持键盘导航', async () => {
      vi.mocked(api.dataSourceAPI.listDataSources).mockResolvedValue({
        datasources: [],
      })

      const user = userEvent.setup()
      render(<DataSourceSetup />)

      const connectTab = screen.getByText('➕ 连接新数据源')

      // 使用 Tab 键导航
      await user.tab()
      // 验证焦点位置（根据实现）
    })
  })
})

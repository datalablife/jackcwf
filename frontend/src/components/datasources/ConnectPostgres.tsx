/**
 * PostgreSQL 连接表单组件。
 *
 * 允许用户输入 PostgreSQL 连接参数并创建数据源。
 */

import { useState } from 'react'
import { useDataSourceStore } from '@/stores/useDataSourceStore'
import { useQueryClient } from '@tanstack/react-query'

interface ConnectPostgresFormData {
  name: string
  description: string
  host: string
  port: number
  database: string
  username: string
  password: string
  confirmPassword: string
}

export function ConnectPostgres() {
  const [formData, setFormData] = useState<ConnectPostgresFormData>({
    name: '',
    description: '',
    host: 'localhost',
    port: 5432,
    database: '',
    username: '',
    password: '',
    confirmPassword: '',
  })

  const [errors, setErrors] = useState<Record<string, string>>({})
  const [isTesting, setIsTesting] = useState(false)
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null)

  const { addDataSource, isLoading, error, clearError } = useDataSourceStore()
  const queryClient = useQueryClient()

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!formData.name.trim()) {
      newErrors.name = '数据源名称为必填项'
    }

    if (!formData.host.trim()) {
      newErrors.host = '主机名为必填项'
    }

    if (formData.port < 1 || formData.port > 65535) {
      newErrors.port = '端口号必须在 1-65535 之间'
    }

    if (!formData.database.trim()) {
      newErrors.database = '数据库名称为必填项'
    }

    if (!formData.username.trim()) {
      newErrors.username = '用户名为必填项'
    }

    if (!formData.password.trim()) {
      newErrors.password = '密码为必填项'
    }

    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = '密码不匹配'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target

    setFormData((prev) => ({
      ...prev,
      [name]: name === 'port' ? parseInt(value) || 0 : value,
    }))

    // 清除该字段的错误
    if (errors[name]) {
      setErrors((prev) => {
        const newErrors = { ...prev }
        delete newErrors[name]
        return newErrors
      })
    }
  }

  const handleTestConnection = async () => {
    if (!validateForm()) {
      return
    }

    setIsTesting(true)
    setTestResult(null)

    try {
      // 先创建临时数据源以便测试
      const datasource = await addDataSource(
        formData.name,
        formData.description,
        formData.host,
        formData.port,
        formData.database,
        formData.username,
        formData.password
      )

      // 测试连接
      const response = await fetch(`/api/datasources/${datasource.id}/test`, {
        method: 'POST',
      })
      const result = await response.json()
      setTestResult(result)
    } catch (err) {
      setTestResult({
        success: false,
        message: err instanceof Error ? err.message : '测试失败',
      })
    } finally {
      setIsTesting(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) {
      return
    }

    try {
      clearError()
      await addDataSource(
        formData.name,
        formData.description,
        formData.host,
        formData.port,
        formData.database,
        formData.username,
        formData.password
      )

      // 清空表单
      setFormData({
        name: '',
        description: '',
        host: 'localhost',
        port: 5432,
        database: '',
        username: '',
        password: '',
        confirmPassword: '',
      })
      setTestResult(null)

      // 刷新数据源列表
      queryClient.invalidateQueries({ queryKey: ['datasources'] })
    } catch (err) {
      // 错误已由 store 处理
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900">连接 PostgreSQL 数据库</h2>
        <p className="text-gray-600 mt-2">输入数据库连接信息以添加新的数据源</p>
      </div>

      {/* 通用错误显示 */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">❌ {error}</p>
        </div>
      )}

      {/* 连接测试结果 */}
      {testResult && (
        <div
          className={`border rounded-lg p-4 ${
            testResult.success
              ? 'bg-green-50 border-green-200'
              : 'bg-red-50 border-red-200'
          }`}
        >
          <p className={testResult.success ? 'text-green-800' : 'text-red-800'}>
            {testResult.success ? '✅' : '❌'} {testResult.message}
          </p>
        </div>
      )}

      {/* 基本信息 */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">基本信息</h3>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            数据源名称 *
          </label>
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleInputChange}
            placeholder="例如: 生产数据库"
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.name ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.name && <p className="text-red-600 text-sm mt-1">{errors.name}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            描述
          </label>
          <textarea
            name="description"
            value={formData.description}
            onChange={handleInputChange}
            placeholder="可选的数据源描述"
            rows={2}
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.description ? 'border-red-500' : 'border-gray-300'
            }`}
          />
        </div>
      </div>

      {/* 连接信息 */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">连接信息</h3>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              主机名 *
            </label>
            <input
              type="text"
              name="host"
              value={formData.host}
              onChange={handleInputChange}
              placeholder="localhost"
              className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.host ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {errors.host && <p className="text-red-600 text-sm mt-1">{errors.host}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              端口 *
            </label>
            <input
              type="number"
              name="port"
              value={formData.port}
              onChange={handleInputChange}
              placeholder="5432"
              className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.port ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {errors.port && <p className="text-red-600 text-sm mt-1">{errors.port}</p>}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            数据库名称 *
          </label>
          <input
            type="text"
            name="database"
            value={formData.database}
            onChange={handleInputChange}
            placeholder="mydb"
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.database ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.database && <p className="text-red-600 text-sm mt-1">{errors.database}</p>}
        </div>
      </div>

      {/* 认证信息 */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">认证信息</h3>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            用户名 *
          </label>
          <input
            type="text"
            name="username"
            value={formData.username}
            onChange={handleInputChange}
            placeholder="postgres"
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.username ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.username && <p className="text-red-600 text-sm mt-1">{errors.username}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            密码 *
          </label>
          <input
            type="password"
            name="password"
            value={formData.password}
            onChange={handleInputChange}
            placeholder="输入密码"
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.password ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.password && <p className="text-red-600 text-sm mt-1">{errors.password}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            确认密码 *
          </label>
          <input
            type="password"
            name="confirmPassword"
            value={formData.confirmPassword}
            onChange={handleInputChange}
            placeholder="确认密码"
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.confirmPassword ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.confirmPassword && (
            <p className="text-red-600 text-sm mt-1">{errors.confirmPassword}</p>
          )}
        </div>
      </div>

      {/* 按钮 */}
      <div className="flex gap-4">
        <button
          type="button"
          onClick={handleTestConnection}
          disabled={isLoading || isTesting}
          className="flex-1 px-6 py-3 border border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition"
        >
          {isTesting ? '测试中...' : '测试连接'}
        </button>

        <button
          type="submit"
          disabled={isLoading}
          className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition"
        >
          {isLoading ? '创建中...' : '创建数据源'}
        </button>
      </div>

      <p className="text-gray-600 text-sm text-center">
        密码将使用 AES-256 加密存储。密码不会以纯文本形式保存。
      </p>
    </form>
  )
}

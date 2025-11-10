/**
 * 应用全局类型定义。
 *
 * 包含所有通用类型和接口定义。
 */

/**
 * 用户信息
 */
export interface User {
  id: number
  username: string
  email: string
  role: 'admin' | 'user'
  createdAt: string
}

/**
 * 应用配置
 */
export interface AppConfig {
  apiUrl: string
  appName: string
  appVersion: string
  environment: 'development' | 'production' | 'staging'
}

/**
 * 路由配置
 */
export interface RouteConfig {
  path: string
  label: string
  icon?: string
  component: React.ComponentType<Record<string, unknown>>
  children?: RouteConfig[]
  requiresAuth?: boolean
}
// Removed 'any' type - replaced with Record<string, unknown> for strict type safety

/**
 * API 响应结构
 */
export interface ApiResponse<T> {
  code: number
  message: string
  data?: T
  timestamp?: string
}

/**
 * 分页信息
 */
export interface Pagination {
  page: number
  pageSize: number
  total: number
  totalPages: number
}

/**
 * 分页响应
 */
export interface PaginatedResponse<T> {
  items: T[]
  pagination: Pagination
}

/**
 * 错误信息
 */
export interface ErrorInfo {
  code: string
  message: string
  details?: Record<string, unknown>
  timestamp: string
}

/**
 * 通知信息
 */
export interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  message: string
  duration?: number
  timestamp: string
}

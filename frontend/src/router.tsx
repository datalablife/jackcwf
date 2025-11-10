/**
 * React Router 路由配置。
 *
 * 定义应用的所有路由和页面。
 */

import { createBrowserRouter, RouteObject } from 'react-router-dom'
import { Layout } from '@/components/layout/Layout'
import { HomePage } from '@/pages/HomePage'
import { FileUploadPage } from '@/pages/FileUploadPage'
import { FilePreviewPage } from '@/pages/FilePreviewPage'
import { DataSourceSetup } from '@/pages/DataSourceSetup'
import { NotFoundPage } from '@/pages/NotFoundPage'

/**
 * 路由配置数组
 */
export const routes: RouteObject[] = [
  {
    path: '/',
    element: <Layout />,
    errorElement: <NotFoundPage />,
    children: [
      {
        index: true,
        element: <HomePage />,
      },
      {
        path: 'upload',
        element: <FileUploadPage />,
      },
      {
        path: 'preview/:fileId',
        element: <FilePreviewPage />,
      },
      {
        path: 'datasource',
        element: <DataSourceSetup />,
      },
      {
        path: '*',
        element: <NotFoundPage />,
      },
    ],
  },
]

/**
 * 创建 Router 实例
 */
export const router = createBrowserRouter(routes)

/**
 * 导航菜单配置
 */
export const navigationConfig = [
  {
    label: '首页',
    path: '/',
    icon: '🏠',
  },
  {
    label: '文件上传',
    path: '/upload',
    icon: '📤',
  },
  {
    label: '数据源配置',
    path: '/datasource',
    icon: '⚙️',
  },
]

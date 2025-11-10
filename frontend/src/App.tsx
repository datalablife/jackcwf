/**
 * 应用主入口。
 *
 * 使用 React Router 进行路由管理。
 */

import { RouterProvider } from 'react-router-dom'
import { router } from '@/router'

function App() {
  return <RouterProvider router={router} />
}

export default App

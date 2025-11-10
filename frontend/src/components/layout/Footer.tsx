/**
 * 页脚组件。
 *
 * 应用的底部页脚。
 */

export function Footer() {
  return (
    <footer className="bg-gray-800 text-gray-200 mt-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* 关于 */}
          <div>
            <h3 className="text-lg font-bold text-white mb-4">关于我们</h3>
            <p className="text-sm text-gray-400">
              数据文件管理系统是一个功能强大的文件管理和预览工具。
            </p>
          </div>

          {/* 快速链接 */}
          <div>
            <h3 className="text-lg font-bold text-white mb-4">快速链接</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <a
                  href="/"
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  首页
                </a>
              </li>
              <li>
                <a
                  href="/upload"
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  文件上传
                </a>
              </li>
              <li>
                <a
                  href="/datasource"
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  数据源配置
                </a>
              </li>
            </ul>
          </div>

          {/* 资源 */}
          <div>
            <h3 className="text-lg font-bold text-white mb-4">资源</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <a
                  href="#"
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  文档
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  API 文档
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  示例
                </a>
              </li>
            </ul>
          </div>

          {/* 联系 */}
          <div>
            <h3 className="text-lg font-bold text-white mb-4">联系我们</h3>
            <ul className="space-y-2 text-sm">
              <li className="text-gray-400">
                📧 Email: support@example.com
              </li>
              <li className="text-gray-400">📱 Phone: +86 123 4567</li>
              <li>
                <a
                  href="#"
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  💬 在线支持
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* 分隔线 */}
        <div className="border-t border-gray-700 pt-8">
          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-400">
              &copy; 2025 数据文件管理系统. 保留所有权利。
            </p>
            <div className="flex gap-4">
              <a
                href="#"
                className="text-sm text-gray-400 hover:text-white transition-colors"
              >
                隐私政策
              </a>
              <a
                href="#"
                className="text-sm text-gray-400 hover:text-white transition-colors"
              >
                服务条款
              </a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  )
}

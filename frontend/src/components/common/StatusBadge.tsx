/**
 * 连接状态徽章组件。
 *
 * 显示数据源的连接状态（已连接、已断开、错误、测试中）。
 */

interface StatusBadgeProps {
  status: 'connected' | 'disconnected' | 'error' | 'testing'
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const statusConfig = {
    connected: {
      label: '已连接',
      icon: '✅',
      bgColor: 'bg-green-100',
      textColor: 'text-green-800',
    },
    disconnected: {
      label: '已断开',
      icon: '⏸️',
      bgColor: 'bg-gray-100',
      textColor: 'text-gray-800',
    },
    error: {
      label: '错误',
      icon: '❌',
      bgColor: 'bg-red-100',
      textColor: 'text-red-800',
    },
    testing: {
      label: '测试中',
      icon: '⏳',
      bgColor: 'bg-yellow-100',
      textColor: 'text-yellow-800',
    },
  }

  const config = statusConfig[status]

  return (
    <span
      className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium ${config.bgColor} ${config.textColor}`}
    >
      <span>{config.icon}</span>
      <span>{config.label}</span>
    </span>
  )
}

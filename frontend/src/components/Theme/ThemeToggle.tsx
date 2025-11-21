/**
 * ThemeToggle 组件
 *
 * 主题切换开关按钮，支持亮色和暗色主题
 * 使用 Zustand store 管理主题状态，自动应用到 HTML 根元素
 *
 * 使用方式：
 * ```tsx
 * <ThemeToggle />
 * ```
 */

import React, { useEffect } from 'react';
import { useUIStore } from '../../store';

/**
 * ThemeToggle - 主题切换开关
 *
 * 特性：
 * - 点击切换亮色/暗色主题
 * - 主题状态持久化到 localStorage
 * - 自动应用到 HTML class
 * - 平滑过渡动画
 * - 显示当前主题图标
 */
export const ThemeToggle: React.FC = () => {
  const theme = useUIStore((state) => state.theme);
  const toggleTheme = useUIStore((state) => state.toggleTheme);

  // 在主题改变时更新 HTML class
  useEffect(() => {
    const htmlElement = document.documentElement;

    if (theme === 'dark') {
      htmlElement.classList.add('dark');
    } else {
      htmlElement.classList.remove('dark');
    }
  }, [theme]);

  return (
    <button
      onClick={toggleTheme}
      className="p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 dark:text-slate-400 dark:hover:text-slate-200 dark:hover:bg-slate-800 rounded-lg transition-colors"
      title={theme === 'light' ? '切换到暗模式' : '切换到亮模式'}
      aria-label="切换主题"
    >
      {theme === 'light' ? (
        // 太阳图标 - 亮色模式中显示
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l-2.12-2.12a1 1 0 00-1.414 0l-2.12 2.12a1 1 0 001.414 1.414L9 13.414l1.586 1.586a1 1 0 001.414-1.414zm2.12-10.607a1 1 0 010 1.414l-2.12 2.12a1 1 0 11-1.414-1.414l2.12-2.12a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.464 5.05l-1.414 1.414zm5.657 9.193l-1.414 1.414A1 1 0 104.95 15.05l1.414-1.414z" clipRule="evenodd" />
        </svg>
      ) : (
        // 月亮图标 - 暗色模式中显示
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
        </svg>
      )}
    </button>
  );
};

export default ThemeToggle;

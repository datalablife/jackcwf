/**
 * SearchBar 组件
 *
 * 消息搜索输入框，支持实时搜索和过滤
 * 功能：
 * - 文本内容搜索
 * - 实时搜索和过滤
 * - 清除搜索结果
 * - 显示匹配数量
 *
 * 使用方式：
 * ```tsx
 * <SearchBar
 *   value={searchQuery}
 *   onChange={handleSearchChange}
 *   onClear={handleClearSearch}
 *   resultCount={filteredCount}
 * />
 * ```
 */

import React from 'react';

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onClear: () => void;
  resultCount?: number;
  placeholder?: string;
}

/**
 * SearchBar - 消息搜索输入框
 *
 * 特性：
 * - 实时搜索响应
 * - 清除按钮
 * - 搜索结果计数显示
 * - 键盘事件支持
 *
 * @param value - 搜索输入值
 * @param onChange - 输入改变回调
 * @param onClear - 清除搜索回调
 * @param resultCount - 匹配结果数
 * @param placeholder - 占位符文本
 */
export const SearchBar: React.FC<SearchBarProps> = ({
  value,
  onChange,
  onClear,
  resultCount,
  placeholder = '搜索消息... (输入内容实时过滤)'
}) => {
  return (
    <div className="border-b border-slate-200 bg-white px-4 py-3">
      <div className="max-w-4xl mx-auto flex items-center gap-2">
        <div className="flex-1 relative">
          <div className="relative">
            <input
              type="text"
              value={value}
              onChange={(e) => onChange(e.target.value)}
              placeholder={placeholder}
              className="w-full px-4 py-2 pl-10 pr-4 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <svg
              className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
        </div>

        {/* 搜索结果计数 */}
        {value && resultCount !== undefined && (
          <div className="text-sm text-slate-600 whitespace-nowrap">
            {resultCount} 条结果
          </div>
        )}

        {/* 清除按钮 */}
        {value && (
          <button
            onClick={onClear}
            className="px-3 py-2 text-sm text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
            title="清除搜索"
          >
            ✕
          </button>
        )}
      </div>
    </div>
  );
};

export default SearchBar;

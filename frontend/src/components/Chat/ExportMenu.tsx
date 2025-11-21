/**
 * ExportMenu 组件
 *
 * 消息导出菜单，支持 JSON 和 PDF 两种格式
 * - JSON 导出：原始数据格式，易于处理
 * - PDF 导出：格式化文档，易于阅读
 *
 * 使用方式：
 * ```tsx
 * <ExportMenu
 *   messages={filteredMessages}
 *   threadId={threadId}
 *   threadTitle="Conversation Title"
 *   isOpen={isExportMenuOpen}
 *   onClose={() => setIsExportMenuOpen(false)}
 * />
 * ```
 */

import React, { useState } from 'react';
import { exportAsJSON, exportAsPDF } from '../../services/exportService';
import type { ChatMessage } from '../../types';

interface ExportMenuProps {
  messages: ChatMessage[];
  threadId: string;
  threadTitle?: string;
  isOpen: boolean;
  onClose: () => void;
}

/**
 * ExportMenu - 消息导出菜单组件
 *
 * 特性：
 * - JSON 导出 - 快速导出
 * - PDF 导出 - 美观的文档格式
 * - 加载状态反馈
 * - 错误处理
 * - 菜单自动关闭
 *
 * @param messages - 要导出的消息列表
 * @param threadId - 对话线程 ID
 * @param threadTitle - 对话标题（可选）
 * @param isOpen - 菜单是否显示
 * @param onClose - 关闭菜单回调
 */
export const ExportMenu: React.FC<ExportMenuProps> = ({
  messages,
  threadId,
  threadTitle,
  isOpen,
  onClose,
}) => {
  const [isExporting, setIsExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  // 处理 JSON 导出
  const handleExportJSON = async (): Promise<void> => {
    try {
      setIsExporting(true);
      setExportError(null);

      exportAsJSON(messages, {
        threadId,
        threadTitle,
        includeMetadata: true,
      });

      onClose();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '导出 JSON 失败';
      setExportError(errorMessage);
      console.error('JSON 导出失败:', error);
    } finally {
      setIsExporting(false);
    }
  };

  // 处理 PDF 导出
  const handleExportPDF = async (): Promise<void> => {
    try {
      setIsExporting(true);
      setExportError(null);

      await exportAsPDF(messages, {
        threadId,
        threadTitle,
      });

      onClose();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '导出 PDF 失败';
      setExportError(errorMessage);
      console.error('PDF 导出失败:', error);
    } finally {
      setIsExporting(false);
    }
  };

  if (!isOpen) {
    return null;
  }

  return (
    <>
      {/* 背景遮罩 - 点击关闭菜单 */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40 transition-opacity"
        onClick={onClose}
        role="presentation"
        aria-hidden="true"
      />

      {/* 导出菜单 */}
      <div className="fixed bottom-20 right-4 bg-white rounded-lg shadow-lg border border-slate-200 z-50 min-w-max">
        {/* 菜单头 */}
        <div className="px-4 py-3 border-b border-slate-200">
          <h3 className="text-sm font-semibold text-slate-900">导出对话</h3>
          <p className="text-xs text-slate-500 mt-1">{messages.length} 条消息</p>
        </div>

        {/* 菜单项 */}
        <div className="py-2">
          {/* JSON 导出 */}
          <button
            onClick={handleExportJSON}
            disabled={isExporting || messages.length === 0}
            className="w-full px-4 py-2 text-left text-sm text-slate-700 hover:bg-slate-100 disabled:text-slate-400 disabled:hover:bg-white transition-colors flex items-center gap-2"
            title="导出为 JSON 格式"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2m0 0v-8m0 8a9 9 0 110-18 9 9 0 010 18z" />
            </svg>
            <span>导出为 JSON</span>
          </button>

          {/* PDF 导出 */}
          <button
            onClick={handleExportPDF}
            disabled={isExporting || messages.length === 0}
            className="w-full px-4 py-2 text-left text-sm text-slate-700 hover:bg-slate-100 disabled:text-slate-400 disabled:hover:bg-white transition-colors flex items-center gap-2"
            title="导出为 PDF 格式"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
            <span>导出为 PDF</span>
          </button>
        </div>

        {/* 加载状态 */}
        {isExporting && (
          <div className="px-4 py-3 border-t border-slate-200 bg-blue-50">
            <div className="flex items-center gap-2 text-sm text-blue-700">
              <div className="w-4 h-4 border-2 border-blue-700 border-t-transparent rounded-full animate-spin" />
              <span>正在导出...</span>
            </div>
          </div>
        )}

        {/* 错误提示 */}
        {exportError && (
          <div className="px-4 py-3 border-t border-slate-200 bg-red-50">
            <p className="text-sm text-red-700">{exportError}</p>
          </div>
        )}

        {/* 无消息提示 */}
        {messages.length === 0 && (
          <div className="px-4 py-3 border-t border-slate-200 bg-slate-50">
            <p className="text-sm text-slate-600">暂无消息可导出</p>
          </div>
        )}
      </div>
    </>
  );
};

export default ExportMenu;

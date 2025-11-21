/**
 * ChatInterface 组件
 *
 * 主要的聊天视口组件，显示消息并与聊天系统集成。
 * - 显示来自 useChatStore 的消息列表
 * - 处理自动滚动到最新消息
 * - 显示加载和错误状态
 * - 管理流式消息渲染
 * - 显示输入指示器（其他用户正在输入）
 * - 实时消息搜索和过滤
 * - 消息导出（JSON 和 PDF 格式）
 *
 * 使用方式：
 * ```tsx
 * <ChatInterface threadId="thread_abc123" />
 * ```
 */

import React, { useEffect, useRef, useState } from 'react';
import { useChatStore, useThreadsStore } from '../../store';
import { ChatMessage } from './ChatMessage';
import { TypingIndicator } from './TypingIndicator';
import { ExportMenu } from './ExportMenu';
import type { ChatMessage as ChatMessageType } from '../../types';

interface ChatInterfaceProps {
  threadId: string;
  isLoading?: boolean;
  error?: string | null;
}

/**
 * ChatInterface - Main chat message viewport
 *
 * Features:
 * - Auto-scroll to bottom when new messages arrive
 * - Loading spinner during message submission
 * - Error toast display
 * - Message streaming animation support
 * - Thread-isolated message rendering
 * - Typing indicators for active users
 *
 * @param threadId - Current thread ID (format: thread_<uuid>)
 * @param isLoading - Whether chat is loading (from useChat hook)
 * @param error - Error message to display (from useChat hook)
 */
export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  threadId,
  isLoading = false,
  error = null
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const [isAutoScrollEnabled, setIsAutoScrollEnabled] = useState(true);
  const [isExportMenuOpen, setIsExportMenuOpen] = useState(false);

  // 从存储获取消息和输入用户
  const messages = useChatStore((state) => state.messages[threadId] || []);
  const searchQuery = useChatStore((state) => state.searchQuery);
  const { setSearchQuery } = useChatStore();
  const typingUsers = useChatStore((state) => Array.from(state.typingUsers[threadId] || []));

  // 获取对话标题
  const threads = useThreadsStore((state) => state.threads);
  const currentThread = threads.find((t) => t.threadId === threadId);
  const threadTitle = currentThread?.title || 'Untitled Conversation';

  // 搜索过滤逻辑
  const filteredMessages = messages.filter((message) => {
    if (!searchQuery.trim()) return true;

    const query = searchQuery.toLowerCase();
    const contentMatch = message.content.toLowerCase().includes(query);
    const roleMatch = message.role.toLowerCase().includes(query);

    return contentMatch || roleMatch;
  });

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    if (isAutoScrollEnabled && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isAutoScrollEnabled]);

  // Handle user scroll - disable auto-scroll if scrolled up
  const handleScroll = () => {
    if (messagesContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.current;
      // If user has scrolled up (more than 100px from bottom), disable auto-scroll
      const isScrolledToBottom = scrollHeight - scrollTop - clientHeight < 100;
      setIsAutoScrollEnabled(isScrolledToBottom);
    }
  };

  // Empty state
  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-full bg-gradient-to-b from-slate-50 to-slate-100">
        <div className="text-center">
          <div className="mb-4 text-5xl">💬</div>
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Start a Conversation</h2>
          <p className="text-slate-600 max-w-sm">
            Create a new thread or select an existing conversation to begin chatting with the AI assistant.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-white">
      {/* 搜索栏和导出按钮 */}
      <div className="border-b border-slate-200 bg-white px-4 py-3">
        <div className="max-w-4xl mx-auto flex items-center gap-2">
          {/* 搜索栏 - 全宽 */}
          <div className="flex-1">
            <div className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="搜索消息..."
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
          {searchQuery && (
            <div className="text-sm text-slate-600 whitespace-nowrap">
              {messages.filter((message) => {
                const query = searchQuery.toLowerCase();
                const contentMatch = message.content.toLowerCase().includes(query);
                const roleMatch = message.role.toLowerCase().includes(query);
                return contentMatch || roleMatch;
              }).length} 条结果
            </div>
          )}

          {/* 清除搜索按钮 */}
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="px-3 py-2 text-sm text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
              title="清除搜索"
            >
              ✕
            </button>
          )}

          {/* 导出按钮 */}
          <button
            onClick={() => setIsExportMenuOpen(!isExportMenuOpen)}
            className="px-3 py-2 text-sm text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors flex items-center gap-1"
            title="导出对话"
            disabled={messages.length === 0}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            导出
          </button>
        </div>
      </div>

      {/* 消息容器 */}
      <div
        ref={messagesContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto scroll-smooth px-4 py-6 space-y-4"
      >
        {/* 消息列表 */}
        {filteredMessages.length > 0 && (
          <div className="max-w-4xl mx-auto space-y-4">
            {filteredMessages.map((message: ChatMessageType, index: number) => (
              <ChatMessage
                key={message.id || index}
                message={message}
                isStreaming={message.isStreaming || false}
              />
            ))}
          </div>
        )}

        {/* 无搜索结果提示 */}
        {searchQuery && filteredMessages.length === 0 && (
          <div className="max-w-4xl mx-auto flex items-center justify-center py-8">
            <div className="text-center text-slate-500">
              <div className="text-3xl mb-2">🔍</div>
              <p>未找到匹配 "{searchQuery}" 的消息</p>
            </div>
          </div>
        )}

        {/* Loading Indicator */}
        {isLoading && (
          <div className="max-w-4xl mx-auto flex items-center gap-3 py-4">
            <div className="flex gap-1">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0s' }}></div>
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
            </div>
            <span className="text-sm text-slate-600">AI is thinking...</span>
          </div>
        )}

        {/* Typing Indicator */}
        <TypingIndicator typingUsers={typingUsers} />

        {/* Scroll Anchor */}
        <div ref={messagesEndRef} />
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="border-t border-slate-200 bg-red-50 px-4 py-3 flex items-start gap-3">
          <div className="text-red-600 text-xl">⚠️</div>
          <div className="flex-1">
            <h3 className="font-semibold text-red-900 text-sm">错误</h3>
            <p className="text-red-700 text-sm mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* 导出菜单 */}
      <ExportMenu
        messages={messages}
        threadId={threadId}
        threadTitle={threadTitle}
        isOpen={isExportMenuOpen}
        onClose={() => setIsExportMenuOpen(false)}
      />
    </div>
  );
};

export default ChatInterface;

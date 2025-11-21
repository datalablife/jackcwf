/**
 * Sidebar Component
 *
 * Left sidebar showing:
 * - List of conversations/threads
 * - Create new thread button
 * - Thread selection and switching
 * - Delete thread functionality
 * - Thread search/filter
 *
 * Usage:
 * ```tsx
 * <Sidebar
 *   threads={threads}
 *   selectedThreadId={selectedId}
 *   onSelectThread={handleSelect}
 *   onCreateThread={handleCreate}
 *   onDeleteThread={handleDelete}
 * />
 * ```
 */

import React, { useState, useMemo } from 'react';
import type { Thread } from '../../types';

interface SidebarProps {
  threads: Thread[];
  selectedThreadId: string | null;
  onSelectThread: (threadId: string) => void;
  onCreateThread: () => Promise<void>;
  onDeleteThread: (threadId: string) => Promise<void>;
  isLoading?: boolean;
}

/**
 * Format thread title for display (truncate if too long)
 */
const formatThreadTitle = (title: string, maxLength: number = 30): string => {
  return title.length > maxLength ? `${title.substring(0, maxLength)}...` : title;
};

/**
 * Format date for display
 */
const formatDate = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffDays === 0) {
      return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    }
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  } catch {
    return '';
  }
};

/**
 * Sidebar - Thread list and navigation component
 *
 * Features:
 * - Thread list with selection
 * - Create new thread button
 * - Delete thread with confirmation
 * - Search/filter threads
 * - Thread metadata display
 * - Loading states
 *
 * @param threads - Array of Thread objects
 * @param selectedThreadId - Currently selected thread ID
 * @param onSelectThread - Callback when thread is selected
 * @param onCreateThread - Callback to create new thread
 * @param onDeleteThread - Callback to delete thread
 * @param isLoading - Whether sidebar is loading
 */
export const Sidebar: React.FC<SidebarProps> = ({
  threads,
  selectedThreadId,
  onSelectThread,
  onCreateThread,
  onDeleteThread,
  isLoading = false
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [deletingThreadId, setDeletingThreadId] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  // Filter threads based on search query
  const filteredThreads = useMemo(() => {
    return threads.filter(
      (thread) =>
        thread.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        thread.conversationId.toString().includes(searchQuery)
    );
  }, [threads, searchQuery]);

  // Handle create thread
  const handleCreateClick = async () => {
    try {
      setIsCreating(true);
      await onCreateThread();
    } catch (error) {
      console.error('Error creating thread:', error);
    } finally {
      setIsCreating(false);
    }
  };

  // Handle delete thread
  const handleDeleteClick = async (threadId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this conversation?')) {
      return;
    }
    try {
      setDeletingThreadId(threadId);
      await onDeleteThread(threadId);
    } catch (error) {
      console.error('Error deleting thread:', error);
    } finally {
      setDeletingThreadId(null);
    }
  };

  return (
    <div className="flex flex-col h-full w-64 bg-slate-900 text-slate-100">
      {/* Header */}
      <div className="p-4 border-b border-slate-700">
        <h1 className="text-lg font-bold mb-4">💬 Chat</h1>

        {/* Create New Thread Button */}
        <button
          onClick={handleCreateClick}
          disabled={isCreating || isLoading}
          className={`w-full py-2 px-3 rounded-lg font-medium transition-all flex items-center justify-center gap-2 ${
            isCreating || isLoading
              ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700 text-white'
          }`}
        >
          {isCreating ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>Creating...</span>
            </>
          ) : (
            <>
              <span>➕</span>
              <span>New Chat</span>
            </>
          )}
        </button>
      </div>

      {/* Search Box */}
      <div className="p-3 border-b border-slate-700">
        <input
          type="text"
          placeholder="Search conversations..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full px-3 py-2 rounded-lg bg-slate-800 text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Threads List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="p-4 text-center text-slate-400">
            <div className="inline-block w-5 h-5 border-2 border-slate-600 border-t-blue-500 rounded-full animate-spin mb-2" />
            <p className="text-sm">Loading conversations...</p>
          </div>
        ) : filteredThreads.length === 0 ? (
          <div className="p-4 text-center text-slate-400">
            <p className="text-sm">
              {threads.length === 0
                ? 'No conversations yet. Create one to get started!'
                : 'No matching conversations found.'}
            </p>
          </div>
        ) : (
          <div className="space-y-2 p-3">
            {filteredThreads.map((thread) => (
              <div
                key={thread.threadId}
                onClick={() => onSelectThread(thread.threadId)}
                className={`group p-3 rounded-lg cursor-pointer transition-all ${
                  selectedThreadId === thread.threadId
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-800 text-slate-100 hover:bg-slate-700'
                }`}
              >
                {/* Thread Title */}
                <h3 className="font-semibold text-sm truncate">{formatThreadTitle(thread.title)}</h3>

                {/* Thread Metadata */}
                <div className={`text-xs mt-1 flex items-center justify-between ${
                  selectedThreadId === thread.threadId ? 'text-blue-100' : 'text-slate-400'
                }`}>
                  <span>{thread.messageCount} messages</span>
                  <span>{formatDate(thread.updatedAt.toString())}</span>
                </div>

                {/* Delete Button */}
                <button
                  onClick={(e) => handleDeleteClick(thread.threadId, e)}
                  disabled={deletingThreadId === thread.threadId}
                  className={`mt-2 w-full px-2 py-1 rounded text-xs font-medium transition-all opacity-0 group-hover:opacity-100 ${
                    deletingThreadId === thread.threadId
                      ? 'bg-red-900 text-red-200 cursor-not-allowed'
                      : 'bg-red-900/50 hover:bg-red-900 text-red-100'
                  }`}
                >
                  {deletingThreadId === thread.threadId ? '⏳ Deleting...' : '🗑️ Delete'}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-slate-700 p-3 text-xs text-slate-400 space-y-1">
        <div className="flex items-center justify-between">
          <span>Total: {threads.length} chats</span>
          <span>✓ Connected</span>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;

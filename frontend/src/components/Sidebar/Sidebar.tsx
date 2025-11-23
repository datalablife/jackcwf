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

import React, { useState } from 'react';
import type { Thread } from '../../types';

interface SidebarProps {
  threads: Thread[];
  selectedThreadId: string | null;
  onSelectThread: (threadId: string) => void;
  onCreateThread: () => Promise<void>;
  onDeleteThread: (threadId: string) => Promise<void>;
  isLoading?: boolean;
  onClose: () => void;
}

/**
 * Format thread title for display (truncate if too long)
 */
/**
 * Format thread title for display (truncate if too long)
 */
const formatThreadTitle = (title: string, maxLength: number = 30): string => {
  return title.length > maxLength ? `${title.substring(0, maxLength)}...` : title;
};

/**
 * Sidebar - Thread list and navigation component
 */
export const Sidebar: React.FC<SidebarProps> = ({
  threads,
  selectedThreadId,
  onSelectThread,
  onCreateThread,
  onDeleteThread,
  isLoading = false,
  onClose
}) => {
  const [deletingThreadId, setDeletingThreadId] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);

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

  // Logo Component
  const Logo = () => (
    <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" className="text-foreground">
      <path d="M16 2L4 9V23L16 30L28 23V9L16 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M16 12V20" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M12 16H20" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="16" cy="16" r="6" stroke="currentColor" strokeWidth="2" />
      <circle cx="16" cy="6" r="1" fill="currentColor" />
      <circle cx="6" cy="11" r="1" fill="currentColor" />
      <circle cx="6" cy="21" r="1" fill="currentColor" />
      <circle cx="16" cy="26" r="1" fill="currentColor" />
      <circle cx="26" cy="21" r="1" fill="currentColor" />
      <circle cx="26" cy="11" r="1" fill="currentColor" />
    </svg>
  );

  return (
    <aside className="flex flex-col h-full w-full bg-[#f9f9f9] dark:bg-[#171717] text-foreground">
      {/* Header */}
      <div className="flex-shrink-0 p-3 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-2 px-2">
          <Logo />
          <span className="font-bold text-lg tracking-tight">Nexus AI</span>
        </div>

        {/* Close Sidebar Button */}
        <button
          onClick={onClose}
          className="p-2 rounded-lg hover:bg-black/5 dark:hover:bg-white/5 text-muted-foreground hover:text-foreground transition-colors"
          title="Close sidebar"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M9 3V21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
      </div>

      {/* New Chat Button (ChatGPT Style) */}
      <div className="px-3 pb-2">
        <button
          onClick={handleCreateClick}
          disabled={isCreating || isLoading}
          className="w-full flex items-center gap-3 px-3 py-3 rounded-lg hover:bg-black/5 dark:hover:bg-white/5 transition-colors text-sm font-medium text-foreground text-left group"
        >
          <div className="w-7 h-7 rounded-full bg-black dark:bg-white flex items-center justify-center text-white dark:text-black">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 5v14M5 12h14" />
            </svg>
          </div>
          <span>New chat</span>
        </button>
      </div>

      {/* Threads List */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1">
        <div className="text-xs font-medium text-muted-foreground px-3 py-2">Today</div>
        {isLoading ? (
          <div className="px-3 py-2 text-sm text-muted-foreground animate-pulse">Loading...</div>
        ) : threads.length === 0 ? (
          <div className="px-3 py-2 text-sm text-muted-foreground">No chats yet</div>
        ) : (
          threads.map((thread) => (
            <div
              key={thread.threadId}
              onClick={() => onSelectThread(thread.threadId)}
              className={`group relative flex items-center gap-3 px-3 py-3 rounded-lg cursor-pointer transition-colors text-sm ${selectedThreadId === thread.threadId
                ? 'bg-black/10 dark:bg-white/10'
                : 'hover:bg-black/5 dark:hover:bg-white/5'
                }`}
            >
              <div className="flex-1 truncate text-foreground/90 group-hover:text-foreground">
                {formatThreadTitle(thread.title)}
              </div>

              {/* Delete Button - Only visible on hover or if deleting */}
              <button
                onClick={(e) => handleDeleteClick(thread.threadId, e)}
                disabled={deletingThreadId === thread.threadId}
                className={`absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-md transition-opacity ${deletingThreadId === thread.threadId
                  ? 'opacity-100 text-destructive'
                  : 'opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive'
                  }`}
                title="Delete conversation"
              >
                {deletingThreadId === thread.threadId ? (
                  <div className="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" />
                ) : (
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                  </svg>
                )}
              </button>
            </div>
          ))
        )}
      </div>

      {/* User Profile / Settings */}
      <div className="p-3 border-t border-black/5 dark:border-white/5">
        <button className="w-full flex items-center gap-3 px-3 py-3 rounded-lg hover:bg-black/5 dark:hover:bg-white/5 transition-colors text-sm font-medium text-foreground text-left">
          <div className="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center text-white font-medium text-sm">
            U
          </div>
          <div className="flex-1">
            <div className="font-medium">User</div>
            <div className="text-xs text-muted-foreground">Free Plan</div>
          </div>
        </button>
      </div>
    </aside>
  );
};

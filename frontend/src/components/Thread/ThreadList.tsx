/**
 * ThreadList Component
 *
 * Displays a list of all threads in the current conversation
 * Features:
 * - Thread display with title, last message, and timestamp
 * - Search and filter functionality
 * - Pagination and virtual scrolling support
 * - Thread actions: select, delete, rename
 * - Empty state handling
 * - Loading states
 */

import React, { useMemo, useState, useCallback } from 'react';
import { Thread } from '../../types';
import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';

interface ThreadListProps {
  threads: Thread[];
  selectedThreadId: string | null;
  onSelectThread: (threadId: string) => void;
  onCreateThread: () => void;
  onDeleteThread: (threadId: string) => void;
  isLoading?: boolean;
}

/**
 * ThreadList - Main thread list component
 *
 * Manages display of all threads with search, filter, and actions
 *
 * @param threads - Array of threads to display
 * @param selectedThreadId - Currently selected thread ID
 * @param onSelectThread - Callback when thread is selected
 * @param onCreateThread - Callback to create new thread
 * @param onDeleteThread - Callback to delete a thread
 * @param isLoading - Whether threads are loading
 */
export const ThreadList: React.FC<ThreadListProps> = ({
  threads,
  selectedThreadId,
  onSelectThread,
  onCreateThread,
  onDeleteThread,
  isLoading = false
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedDeleteId, setExpandedDeleteId] = useState<string | null>(null);

  // Filter threads based on search query
  const filteredThreads = useMemo(() => {
    if (!searchQuery.trim()) return threads;

    const query = searchQuery.toLowerCase();
    return threads.filter((thread) =>
      thread.title.toLowerCase().includes(query) ||
      thread.conversationId.toString().includes(query)
    );
  }, [threads, searchQuery]);

  // Sort threads by most recent first
  const sortedThreads = useMemo(() => {
    return [...filteredThreads].sort((a, b) =>
      new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
    );
  }, [filteredThreads]);

  const handleDeleteClick = useCallback((e: React.MouseEvent, threadId: string) => {
    e.stopPropagation();
    if (expandedDeleteId === threadId) {
      onDeleteThread(threadId);
      setExpandedDeleteId(null);
    } else {
      setExpandedDeleteId(threadId);
    }
  }, [expandedDeleteId, onDeleteThread]);

  const handleCancelDelete = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    setExpandedDeleteId(null);
  }, []);

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <button
          onClick={onCreateThread}
          disabled={isLoading}
          className="w-full px-4 py-2.5 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90
            font-medium transition-colors duration-200
            disabled:opacity-50 disabled:cursor-not-allowed
            flex items-center justify-center gap-2"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          New Chat
        </button>
      </div>

      {/* Search Bar */}
      <div className="px-3 py-2">
        <div className="relative">
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.35-4.35" />
          </svg>
          <input
            type="text"
            placeholder="Search chats..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 rounded-lg bg-input text-foreground
              border border-border placeholder:text-muted-foreground
              focus:outline-none focus:ring-2 focus:ring-primary/50
              transition-all duration-200"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground
                hover:text-foreground transition-colors"
              aria-label="Clear search"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Thread List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          // Loading state
          <div className="flex items-center justify-center h-full">
            <div className="flex flex-col items-center gap-2">
              <div className="relative w-8 h-8">
                <div className="absolute inset-0 border-2 border-primary/20 rounded-full" />
                <div className="absolute inset-0 border-2 border-transparent border-t-primary rounded-full animate-spin" />
              </div>
              <p className="text-sm text-muted-foreground">Loading chats...</p>
            </div>
          </div>
        ) : sortedThreads.length === 0 ? (
          // Empty state
          <div className="flex items-center justify-center h-full p-4">
            <div className="text-center">
              <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center mx-auto mb-3">
                <svg
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="text-muted-foreground"
                >
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
              </div>
              <h3 className="font-medium text-foreground mb-1">No chats yet</h3>
              <p className="text-sm text-muted-foreground">
                {searchQuery ? 'No chats match your search' : 'Start a new chat to begin'}
              </p>
            </div>
          </div>
        ) : (
          // Thread items
          <div className="space-y-1 p-2">
            {sortedThreads.map((thread) => (
              <ThreadItem
                key={thread.threadId}
                thread={thread}
                isSelected={selectedThreadId === thread.threadId}
                isDeleteExpanded={expandedDeleteId === thread.threadId}
                onSelect={onSelectThread}
                onDeleteClick={handleDeleteClick}
                onCancelDelete={handleCancelDelete}
              />
            ))}
          </div>
        )}
      </div>

      {/* Thread count footer */}
      {sortedThreads.length > 0 && (
        <div className="px-4 py-2 text-xs text-muted-foreground border-t border-border">
          {sortedThreads.length} {sortedThreads.length === 1 ? 'chat' : 'chats'}
        </div>
      )}
    </div>
  );
};

interface ThreadItemProps {
  thread: Thread;
  isSelected: boolean;
  isDeleteExpanded: boolean;
  onSelect: (threadId: string) => void;
  onDeleteClick: (e: React.MouseEvent, threadId: string) => void;
  onCancelDelete: (e: React.MouseEvent) => void;
}

/**
 * ThreadItem - Individual thread item component
 */
const ThreadItem: React.FC<ThreadItemProps> = ({
  thread,
  isSelected,
  isDeleteExpanded,
  onSelect,
  onDeleteClick,
  onCancelDelete
}) => {
  const timeAgo = formatDistanceToNow(new Date(thread.updatedAt), {
    addSuffix: true,
    locale: zhCN
  });

  return (
    <div
      onClick={() => onSelect(thread.threadId)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          onSelect(thread.threadId);
        }
      }}
      className={`w-full text-left px-3 py-2.5 rounded-lg transition-all duration-200 group cursor-pointer
        ${
          isSelected
            ? 'bg-primary/10 border border-primary/30'
            : 'hover:bg-black/5 dark:hover:bg-white/5 border border-transparent'
        }
        ${isDeleteExpanded ? 'bg-destructive/5' : ''}`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          {/* Thread title */}
          <h3 className="font-medium text-sm text-foreground truncate group-hover:text-primary
            transition-colors">
            {thread.title}
          </h3>

          {/* Thread meta */}
          <div className="flex items-center gap-2 mt-1">
            <span className="text-xs text-muted-foreground">{timeAgo}</span>
            {thread.messageCount > 0 && (
              <>
                <span className="text-xs text-muted-foreground">•</span>
                <span className="text-xs text-muted-foreground">
                  {thread.messageCount} {thread.messageCount === 1 ? 'message' : 'messages'}
                </span>
              </>
            )}
          </div>
        </div>

        {/* Delete button */}
        <div className="flex-shrink-0">
          {isDeleteExpanded ? (
            <div className="flex items-center gap-1.5">
              <button
                onClick={(e) => onDeleteClick(e, thread.threadId)}
                className="p-1.5 rounded bg-destructive text-destructive-foreground
                  hover:bg-destructive/90 transition-colors text-xs font-medium"
                title="Confirm delete"
              >
                Delete
              </button>
              <button
                onClick={onCancelDelete}
                className="p-1.5 rounded bg-muted text-muted-foreground
                  hover:bg-muted/80 transition-colors"
                title="Cancel"
              >
                ✕
              </button>
            </div>
          ) : (
            <button
              onClick={(e) => onDeleteClick(e, thread.threadId)}
              className="p-1.5 rounded opacity-0 group-hover:opacity-100 transition-opacity
                hover:bg-destructive/10 text-muted-foreground hover:text-destructive"
              title="Delete chat"
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <polyline points="3 6 5 6 21 6" />
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                <line x1="10" y1="11" x2="10" y2="17" />
                <line x1="14" y1="11" x2="14" y2="17" />
              </svg>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ThreadList;

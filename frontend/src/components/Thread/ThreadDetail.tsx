/**
 * ThreadDetail Component
 *
 * Displays detailed information about a selected thread
 * Features:
 * - Thread title editing
 * - Message count display
 * - Creation and update timestamps
 * - Thread metadata
 * - Thread statistics
 * - Copy thread ID button
 */

import React, { useState, useCallback } from 'react';
import { Thread } from '../../types';
import { useThreadsStore } from '../../store';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';

interface ThreadDetailProps {
  thread: Thread | null;
  isLoading?: boolean;
}

/**
 * ThreadDetail - Thread metadata and information display component
 *
 * Shows detailed information about the currently selected thread
 * Allows inline editing of thread title
 *
 * @param thread - The thread to display details for
 * @param isLoading - Whether details are loading
 */
export const ThreadDetail: React.FC<ThreadDetailProps> = ({
  thread,
  isLoading = false
}) => {
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [editedTitle, setEditedTitle] = useState(thread?.title || '');
  const { updateThread } = useThreadsStore();
  const [isCopied, setIsCopied] = useState(false);

  // Update edited title when thread changes
  React.useEffect(() => {
    if (thread) {
      setEditedTitle(thread.title);
    }
  }, [thread]);

  const handleSaveTitle = useCallback(async () => {
    if (!thread || !editedTitle.trim()) {
      setEditedTitle(thread?.title || '');
      setIsEditingTitle(false);
      return;
    }

    if (editedTitle === thread.title) {
      setIsEditingTitle(false);
      return;
    }

    try {
      // Update in store
      updateThread(thread.threadId, { title: editedTitle });
      setIsEditingTitle(false);

      // TODO: Call API to persist title change
      // await threadApi.updateThread(thread.threadId, { title: editedTitle });
    } catch (error) {
      console.error('Failed to update thread title:', error);
      setEditedTitle(thread.title);
    }
  }, [thread, editedTitle, updateThread]);

  const handleCopyThreadId = useCallback(async () => {
    if (!thread) return;

    try {
      // Copy conversation ID to clipboard
      const conversationIdStr = thread.conversationId.toString();
      await navigator.clipboard.writeText(conversationIdStr);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy thread ID:', error);
    }
  }, [thread]);

  if (!thread) {
    return (
      <div className="flex items-center justify-center h-full p-4">
        <div className="text-center">
          {isLoading ? (
            <>
              <div className="relative w-8 h-8 mx-auto mb-2">
                <div className="absolute inset-0 border-2 border-primary/20 rounded-full" />
                <div className="absolute inset-0 border-2 border-transparent border-t-primary rounded-full animate-spin" />
              </div>
              <p className="text-sm text-muted-foreground">Loading thread...</p>
            </>
          ) : (
            <p className="text-sm text-muted-foreground">No thread selected</p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4 p-4">
      {/* Title Section */}
      <div className="space-y-2">
        <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
          Thread Title
        </label>
        {isEditingTitle ? (
          <div className="flex gap-2">
            <input
              type="text"
              value={editedTitle}
              onChange={(e) => setEditedTitle(e.target.value)}
              placeholder="Enter thread title..."
              autoFocus
              className="flex-1 px-3 py-2 rounded-lg bg-input text-foreground
                border border-primary/30 placeholder:text-muted-foreground
                focus:outline-none focus:ring-2 focus:ring-primary/50
                transition-all duration-200"
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleSaveTitle();
                if (e.key === 'Escape') {
                  setEditedTitle(thread.title);
                  setIsEditingTitle(false);
                }
              }}
            />
            <button
              onClick={handleSaveTitle}
              className="px-3 py-2 rounded-lg bg-primary text-primary-foreground
                hover:bg-primary/90 font-medium transition-colors text-sm"
            >
              Save
            </button>
            <button
              onClick={() => {
                setEditedTitle(thread.title);
                setIsEditingTitle(false);
              }}
              className="px-3 py-2 rounded-lg bg-muted text-muted-foreground
                hover:bg-muted/80 font-medium transition-colors text-sm"
            >
              Cancel
            </button>
          </div>
        ) : (
          <div
            onClick={() => setIsEditingTitle(true)}
            className="px-3 py-2 rounded-lg bg-card border border-border
              hover:border-primary/30 hover:bg-primary/5 cursor-pointer
              transition-colors group flex items-center justify-between"
          >
            <h2 className="font-semibold text-foreground text-lg">{thread.title}</h2>
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z" />
            </svg>
          </div>
        )}
      </div>

      {/* Divider */}
      <div className="h-px bg-border" />

      {/* Statistics */}
      <div className="grid grid-cols-2 gap-3">
        {/* Message Count */}
        <div className="p-3 rounded-lg bg-card border border-border">
          <p className="text-xs text-muted-foreground font-medium mb-1">Messages</p>
          <p className="text-2xl font-bold text-foreground">{thread.messageCount}</p>
        </div>

        {/* Conversation ID */}
        <div className="p-3 rounded-lg bg-card border border-border">
          <p className="text-xs text-muted-foreground font-medium mb-1">Conv. ID</p>
          <p className="text-lg font-mono text-foreground truncate">
            {thread.conversationId}
          </p>
        </div>
      </div>

      {/* Timestamps */}
      <div className="space-y-2">
        <div>
          <p className="text-xs text-muted-foreground font-medium mb-1">Created</p>
          <p className="text-sm text-foreground">
            {format(new Date(thread.createdAt), 'PPP p', { locale: zhCN })}
          </p>
        </div>

        <div>
          <p className="text-xs text-muted-foreground font-medium mb-1">Last Updated</p>
          <p className="text-sm text-foreground">
            {format(new Date(thread.updatedAt), 'PPP p', { locale: zhCN })}
          </p>
        </div>
      </div>

      {/* Copy Thread ID Button */}
      <button
        onClick={handleCopyThreadId}
        className="w-full px-3 py-2 rounded-lg bg-secondary text-secondary-foreground
          hover:bg-secondary/80 font-medium transition-all duration-200
          flex items-center justify-center gap-2 text-sm"
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
          <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
          <rect x="8" y="2" width="8" height="4" rx="1" ry="1" />
        </svg>
        {isCopied ? 'Copied!' : 'Copy Thread ID'}
      </button>

      {/* Metadata Section */}
      {thread.metadata && Object.keys(thread.metadata).length > 0 && (
        <div className="space-y-2">
          <p className="text-xs text-muted-foreground font-semibold uppercase tracking-wide">
            Metadata
          </p>
          <div className="p-3 rounded-lg bg-muted/30 border border-border overflow-hidden">
            <pre className="text-xs text-muted-foreground overflow-x-auto">
              {JSON.stringify(thread.metadata, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};

export default ThreadDetail;

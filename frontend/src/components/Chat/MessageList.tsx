/**
 * MessageList Component with Virtual Scrolling
 *
 * Optimized message display for large conversation histories
 * Features:
 * - Virtual scrolling for 1000+ messages
 * - Auto-scroll to bottom on new messages
 * - Message loading and error states
 * - Message search highlighting
 * - Timestamp grouping
 */

import React, { useRef, useEffect, useCallback, useMemo } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { ChatMessage as ChatMessageType } from '../../types';
import { ChatMessage } from './ChatMessage';
import { TypingIndicator } from './TypingIndicator';

interface MessageListProps {
  messages: ChatMessageType[];
  threadId: string;
  isLoading?: boolean;
  error?: string | null;
  typingUsers?: string[];
  searchQuery?: string;
  hasMoreMessages?: boolean;
  onLoadMoreMessages?: () => void;
}

/**
 * MessageList - Virtualized message list component
 *
 * Handles rendering large numbers of messages efficiently using
 * React Virtual for windowing
 *
 * @param messages - Array of messages to display
 * @param threadId - Current thread ID
 * @param isLoading - Whether messages are loading
 * @param error - Error message if any
 * @param typingUsers - List of users currently typing
 * @param searchQuery - Current search query to highlight
 * @param hasMoreMessages - Whether there are more messages to load
 * @param onLoadMoreMessages - Callback to load more messages
 */
export const MessageList: React.FC<MessageListProps> = ({
  messages,
  isLoading = false,
  error = null,
  typingUsers = [],
  searchQuery: _searchQuery = '', // For future search result highlighting
  hasMoreMessages = false,
  onLoadMoreMessages
}) => {
  const parentRef = useRef<HTMLDivElement>(null);
  const scrollingRef = useRef<boolean>(false);
  const shouldAutoScrollRef = useRef<boolean>(true);

  // Group messages by date
  const groupedMessages = useMemo(() => {
    const groups: Map<string, ChatMessageType[]> = new Map();

    messages.forEach((msg) => {
      const date = new Date(msg.timestamp);
      const dateKey = date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });

      if (!groups.has(dateKey)) {
        groups.set(dateKey, []);
      }
      groups.get(dateKey)!.push(msg);
    });

    return groups;
  }, [messages]);

  // Flatten grouped messages for virtualization
  const flatMessages = useMemo(() => {
    const flat: Array<{ type: 'date' | 'message'; data: ChatMessageType | string }> = [];

    groupedMessages.forEach((msgs, date) => {
      flat.push({ type: 'date', data: date });
      msgs.forEach((msg) => {
        flat.push({ type: 'message', data: msg });
      });
    });

    return flat;
  }, [groupedMessages]);

  // Virtual scrolling setup
  const virtualizer = useVirtualizer({
    count: flatMessages.length + (typingUsers.length > 0 ? 1 : 0),
    getScrollElement: () => parentRef.current,
    estimateSize: useCallback(() => 80, []),
    overscan: 10,
  });

  const virtualItems = virtualizer.getVirtualItems();
  const totalSize = virtualizer.getTotalSize();

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (shouldAutoScrollRef.current && parentRef.current) {
      scrollingRef.current = true;
      parentRef.current.scrollTop = parentRef.current.scrollHeight;

      setTimeout(() => {
        scrollingRef.current = false;
      }, 100);
    }
  }, [messages.length]);

  // Track when user scrolls to disable auto-scroll
  const handleScroll = useCallback(() => {
    if (!parentRef.current || scrollingRef.current) return;

    const { scrollHeight, scrollTop, clientHeight } = parentRef.current;
    const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;

    shouldAutoScrollRef.current = isNearBottom;

    // Load more messages when scrolled to top
    if (scrollTop < 100 && hasMoreMessages && onLoadMoreMessages) {
      onLoadMoreMessages();
    }
  }, [hasMoreMessages, onLoadMoreMessages]);

  return (
    <div
      ref={parentRef}
      onScroll={handleScroll}
      className="h-full overflow-y-auto scroll-smooth"
    >
      {/* Virtualizer wrapper */}
      <div
        style={{
          height: `${totalSize}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {/* Load more indicator */}
        {hasMoreMessages && (
          <div className="sticky top-0 z-20 text-center py-2">
            <button
              onClick={onLoadMoreMessages}
              disabled={isLoading}
              className="text-xs text-primary hover:text-primary/80 font-medium
                disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? 'Loading...' : 'Load earlier messages'}
            </button>
          </div>
        )}

        {/* Render virtual items */}
        {virtualItems.map((virtualItem) => {
          const actualIndex = virtualItem.index;
          const item = flatMessages[actualIndex];

          if (!item) return null;

          return (
            <div
              key={`${item.type}-${actualIndex}`}
              data-index={actualIndex}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                transform: `translateY(${virtualItem.start}px)`,
              }}
            >
              {item.type === 'date' ? (
                <DateDivider date={item.data as string} />
              ) : (
                <ChatMessage
                  message={item.data as ChatMessageType}
                  isStreaming={false}
                />
              )}
            </div>
          );
        })}

        {/* Typing indicator */}
        {typingUsers.length > 0 && (
          <div
            style={{
              position: 'absolute',
              top: totalSize - 40,
              left: 0,
              width: '100%',
              padding: '8px 16px',
            }}
          >
            <TypingIndicator typingUsers={typingUsers} />
          </div>
        )}
      </div>

      {/* Error state */}
      {error && (
        <div className="sticky bottom-0 w-full p-3 bg-destructive/10 border-t border-destructive/30">
          <p className="text-sm text-destructive">{error}</p>
        </div>
      )}

      {/* Empty state */}
      {messages.length === 0 && !isLoading && (
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
            <h3 className="font-medium text-foreground mb-1">No messages yet</h3>
            <p className="text-sm text-muted-foreground">
              Send a message to start the conversation
            </p>
          </div>
        </div>
      )}

      {/* Loading state */}
      {isLoading && messages.length === 0 && (
        <div className="flex items-center justify-center h-full">
          <div className="flex flex-col items-center gap-2">
            <div className="relative w-8 h-8">
              <div className="absolute inset-0 border-2 border-primary/20 rounded-full" />
              <div className="absolute inset-0 border-2 border-transparent border-t-primary rounded-full animate-spin" />
            </div>
            <p className="text-sm text-muted-foreground">Loading messages...</p>
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * DateDivider - Displays a date separator between message groups
 */
const DateDivider: React.FC<{ date: string }> = ({ date }) => {
  return (
    <div className="flex items-center gap-3 my-4 px-4">
      <div className="flex-1 h-px bg-border" />
      <span className="text-xs text-muted-foreground font-medium whitespace-nowrap">
        {date}
      </span>
      <div className="flex-1 h-px bg-border" />
    </div>
  );
};

export default MessageList;

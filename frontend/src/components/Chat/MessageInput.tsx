/**
 * MessageInput Component
 *
 * Handles user input with typing indicators and real-time updates
 * Features:
 * - Auto-growing textarea
 * - Typing indicator broadcast
 * - Message submission
 * - Loading states
 * - Error handling
 * - Keyboard shortcuts (Ctrl+Enter to submit)
 *
 * Usage:
 * ```tsx
 * <MessageInput
 *   onSendMessage={handleSendMessage}
 *   disabled={isLoading}
 *   placeholder="Type your message..."
 * />
 * ```
 */

import React, { useRef, useEffect, useCallback, useState } from 'react';

interface MessageInputProps {
  onSendMessage: (content: string) => void;
  onTypingStart?: () => void;
  onTypingStop?: () => void;
  disabled?: boolean;
  isLoading?: boolean;
  placeholder?: string;
  maxLength?: number;
}

/**
 * MessageInput - Textarea for sending messages with typing indicators
 *
 * Automatically grows textarea, broadcasts typing status, and handles submission
 *
 * @param props - Component props
 */
export const MessageInput: React.FC<MessageInputProps> = ({
  onSendMessage,
  onTypingStart,
  onTypingStop,
  disabled = false,
  isLoading = false,
  placeholder = 'Type your message...',
  maxLength = 5000,
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [content, setContent] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * Auto-grow textarea as user types
   */
  const autoGrowTextarea = useCallback(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    textarea.style.height = 'auto';
    const newHeight = Math.min(textarea.scrollHeight, 200); // Max 200px
    textarea.style.height = `${newHeight}px`;
  }, []);

  /**
   * Handle text input with typing indicator
   */
  const handleInput = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const value = e.target.value.slice(0, maxLength);
      setContent(value);

      autoGrowTextarea();

      // Notify typing start if not already typing
      if (!isTyping && value.length > 0) {
        setIsTyping(true);
        onTypingStart?.();
      }

      // Reset typing timeout
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }

      // Notify typing stop after 1 second of inactivity
      typingTimeoutRef.current = setTimeout(() => {
        if (value.length === 0) {
          setIsTyping(false);
          onTypingStop?.();
        }
      }, 1000);
    },
    [autoGrowTextarea, isTyping, maxLength, onTypingStart, onTypingStop],
  );

  /**
   * Handle message submission
   */
  const handleSubmit = useCallback(
    (e?: React.FormEvent<HTMLFormElement> | React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e) {
        e.preventDefault();
      }

      const trimmedContent = content.trim();
      if (!trimmedContent || disabled || isLoading) {
        return;
      }

      // Send message
      onSendMessage(trimmedContent);

      // Reset state
      setContent('');
      setIsTyping(false);
      onTypingStop?.();

      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }

      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    },
    [content, disabled, isLoading, onSendMessage, onTypingStop],
  );

  /**
   * Handle keyboard shortcuts
   */
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      // Ctrl+Enter or Cmd+Enter to submit
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        handleSubmit(e);
      }
    },
    [handleSubmit],
  );

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
      if (isTyping) {
        onTypingStop?.();
      }
    };
  }, [isTyping, onTypingStop]);

  const charCount = content.length;
  const isNearLimit = charCount > maxLength * 0.9;

  return (
    <form onSubmit={handleSubmit} className="space-y-2 border-t border-border p-4">
      {/* Textarea container */}
      <div className="relative">
        <textarea
          ref={textareaRef}
          value={content}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          disabled={disabled || isLoading}
          placeholder={placeholder}
          className="w-full px-4 py-3 rounded-lg bg-input text-foreground
            border border-input placeholder:text-muted-foreground
            focus:outline-none focus:ring-2 focus:ring-primary/50
            transition-all duration-200 resize-none
            disabled:opacity-50 disabled:cursor-not-allowed
            max-h-[200px]"
          rows={1}
        />

        {/* Send button */}
        <button
          type="submit"
          disabled={!content.trim() || disabled || isLoading}
          className="absolute bottom-3 right-3 p-2 rounded-lg bg-primary text-primary-foreground
            hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed
            transition-colors duration-200"
          title="Send message (Ctrl+Enter)"
          aria-label="Send message"
        >
          {isLoading ? (
            <div className="w-5 h-5 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
          ) : (
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          )}
        </button>
      </div>

      {/* Character count and info */}
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <div className="space-x-2">
          {isTyping && (
            <span className="inline-flex items-center gap-1">
              <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse" />
              Typing...
            </span>
          )}
        </div>

        <div className={`transition-colors ${isNearLimit ? 'text-warning' : ''}`}>
          {charCount} / {maxLength}
        </div>
      </div>

      {/* Keyboard shortcut hint */}
      <div className="text-xs text-muted-foreground text-center">
        Press <kbd className="px-1.5 py-0.5 bg-muted rounded text-foreground text-xs font-mono">Ctrl+Enter</kbd> to send
      </div>
    </form>
  );
};

export default MessageInput;

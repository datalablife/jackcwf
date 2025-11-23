/**
 * ChatMessage Component
 *
 * Renders individual chat messages with support for:
 * - User vs Assistant message styling
 * - Markdown content rendering
 * - Streaming text animation
 * - Tool call display
 * - Timestamp and metadata
 *
 * Usage:
 * ```tsx
 * <ChatMessage
 *   message={message}
 *   isStreaming={false}
 * />
 * ```
 */

import React, { useEffect, useState } from 'react';
import { ToolRenderer } from './ToolRenderer';
import type { ChatMessage as ChatMessageType, ToolCall } from '../../types';

interface ChatMessageProps {
  message: ChatMessageType;
  isStreaming?: boolean;
}

/**
 * Format timestamp to readable format
 * @param timestamp - ISO string timestamp
 * @returns Formatted time string
 */
const formatTime = (timestamp: string): string => {
  try {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return '';
  }
};

/**
 * Convert markdown-like content to HTML (simplified)
 * Supports: **bold**, *italic*, `code`, links
 * @param content - Content with markdown
 * @returns React nodes with formatted content
 */
const renderMarkdown = (content: string): React.ReactNode => {
  // Split by markdown patterns while preserving delimiters
  const parts = content.split(/(\*\*.*?\*\*|\*.*?\*|`.*?`|\[.*?\]\(.*?\))/g);

  return parts.map((part, index) => {
    if (!part) return null;

    // Bold: **text**
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={index} className="font-semibold">
          {part.slice(2, -2)}
        </strong>
      );
    }

    // Italic: *text*
    if (part.startsWith('*') && part.endsWith('*') && !part.startsWith('**')) {
      return (
        <em key={index} className="italic">
          {part.slice(1, -1)}
        </em>
      );
    }

    // Inline code: `text`
    if (part.startsWith('`') && part.endsWith('`')) {
      return (
        <code key={index} className="bg-slate-100 px-2 py-0.5 rounded text-sm font-mono text-slate-700">
          {part.slice(1, -1)}
        </code>
      );
    }

    // Links: [text](url)
    const linkMatch = part.match(/\[(.*?)\]\((.*?)\)/);
    if (linkMatch) {
      const [, text, url] = linkMatch;
      return (
        <a
          key={index}
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:underline"
        >
          {text}
        </a>
      );
    }

    // Plain text with line breaks
    return (
      <span key={index}>
        {part.split('\n').map((line, lineIndex) => (
          <React.Fragment key={lineIndex}>
            {line}
            {lineIndex < part.split('\n').length - 1 && <br />}
          </React.Fragment>
        ))}
      </span>
    );
  });
};

/**
 * ChatMessage - Individual message component
 *
 * Features:
 * - Role-based styling (user vs assistant)
 * - Markdown content rendering
 * - Streaming cursor animation
 * - Tool call display via ToolRenderer
 * - Timestamp display
 * - Loading state indicators
 *
 * @param message - ChatMessage object with content, role, etc.
 * @param isStreaming - Whether message is currently streaming
 */
export const ChatMessage: React.FC<ChatMessageProps> = ({ message, isStreaming = false }) => {
  const [displayedContent, setDisplayedContent] = useState('');
  const [displayIndex, setDisplayIndex] = useState(0);

  // Streaming animation effect
  useEffect(() => {
    if (!isStreaming || !message.content) {
      setDisplayedContent(message.content || '');
      return;
    }

    // Animate text reveal
    if (displayIndex < message.content.length) {
      const timer = setTimeout(() => {
        setDisplayedContent(message.content.slice(0, displayIndex + 1));
        setDisplayIndex(displayIndex + 1);
      }, 10); // 10ms per character for smooth animation

      return () => clearTimeout(timer);
    }
  }, [isStreaming, message.content, displayIndex]);

  const isUser = message.role === 'user';

  return (
    <div className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'} animate-enter group`}>
      <div
        className={`relative max-w-3xl w-full flex gap-4 p-2 rounded-xl transition-colors ${isUser
            ? ''
            : 'hover:bg-muted/30'
          }`}
      >
        {/* Avatar */}
        <div className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center shadow-sm ${isUser
            ? 'bg-primary text-primary-foreground order-2'
            : 'bg-white dark:bg-slate-800 border border-border/50 text-foreground order-1'
          }`}>
          {isUser ? 'U' : 'AI'}
        </div>

        {/* Content */}
        <div className={`flex-1 min-w-0 ${isUser ? 'order-1 text-right' : 'order-2'}`}>
          {/* Name & Time */}
          <div className={`flex items-center gap-2 mb-1 text-xs text-muted-foreground ${isUser ? 'justify-end' : 'justify-start'}`}>
            <span className="font-medium text-foreground">{isUser ? 'You' : 'Assistant'}</span>
            <span>•</span>
            <span>{formatTime(message.timestamp.toString())}</span>
          </div>

          {/* Message Bubble */}
          <div className={`text-sm leading-7 prose prose-sm dark:prose-invert max-w-none ${isUser
              ? 'bg-primary text-primary-foreground px-4 py-2.5 rounded-2xl rounded-tr-sm inline-block text-left shadow-md shadow-primary/10'
              : 'text-foreground'
            }`}>
            {renderMarkdown(displayedContent || message.content)}
            {isStreaming && displayIndex < message.content.length && (
              <span className="streaming-cursor"></span>
            )}
          </div>

          {/* Tool Calls */}
          {message.toolCalls && message.toolCalls.length > 0 && (
            <div className="mt-3 pl-2 border-l-2 border-border/60">
              <p className="text-xs font-semibold text-muted-foreground mb-2 flex items-center gap-1">
                <span>🔧</span> Using tools...
              </p>
              <div className="space-y-2">
                {message.toolCalls.map((toolCall: ToolCall, index: number) => (
                  <ToolRenderer key={`${message.id}-tool-${index}`} toolCall={toolCall} />
                ))}
              </div>
            </div>
          )}

          {/* Tool Results */}
          {message.toolResults && message.toolResults.length > 0 && (
            <div className="mt-2 pl-2 border-l-2 border-green-500/30">
              <div className="space-y-1">
                {message.toolResults.map((result: any, index: number) => (
                  <div key={`${message.id}-result-${index}`} className="text-xs text-muted-foreground bg-muted/30 p-2 rounded border border-border/30 font-mono">
                    <span className="font-semibold text-foreground">{result.toolName}</span>: {JSON.stringify(result).substring(0, 100)}...
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;

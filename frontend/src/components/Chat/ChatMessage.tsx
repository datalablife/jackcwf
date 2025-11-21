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
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-fadeIn`}>
      <div
        className={`max-w-2xl ${
          isUser
            ? 'bg-blue-600 text-white rounded-lg rounded-tr-none'
            : 'bg-slate-100 text-slate-900 rounded-lg rounded-tl-none'
        } px-4 py-3 shadow-sm`}
      >
        {/* Message Content */}
        <div className={`text-sm leading-relaxed ${isUser ? 'text-blue-50' : ''}`}>
          {renderMarkdown(displayedContent || message.content)}
          {isStreaming && displayIndex < message.content.length && (
            <span className="inline-block w-2 h-5 ml-1 bg-current opacity-70 animate-pulse">▌</span>
          )}
        </div>

        {/* Tool Calls */}
        {message.toolCalls && message.toolCalls.length > 0 && (
          <div className="mt-3 pt-3 border-t border-slate-200">
            <p className={`text-xs font-semibold mb-2 ${isUser ? 'text-blue-200' : 'text-slate-600'}`}>
              🔧 Tool Calls
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
          <div className="mt-3 pt-3 border-t border-slate-200">
            <p className={`text-xs font-semibold mb-2 ${isUser ? 'text-blue-200' : 'text-slate-600'}`}>
              ✓ Tool Results
            </p>
            <div className="space-y-1">
              {message.toolResults.map((result: any, index: number) => (
                <div key={`${message.id}-result-${index}`} className={`text-xs ${isUser ? 'text-blue-100' : 'text-slate-600'}`}>
                  <span className="font-mono">{result.toolName}</span>: {JSON.stringify(result).substring(0, 100)}...
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Metadata */}
        <div className={`text-xs mt-2 flex items-center gap-2 ${isUser ? 'text-blue-200' : 'text-slate-500'}`}>
          {formatTime(message.timestamp.toString())}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;

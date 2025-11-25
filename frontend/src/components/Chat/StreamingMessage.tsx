/**
 * StreamingMessage Component
 *
 * Displays messages that are being streamed in real-time
 * Features:
 * - Animated text rendering as it arrives
 * - Tool call visualization
 * - Streaming status indicator
 * - Error handling for failed streams
 * - Token count display
 *
 * Usage:
 * ```tsx
 * <StreamingMessage
 *   content="This is being typed..."
 *   isStreaming={true}
 *   toolCalls={toolCalls}
 * />
 * ```
 */

import React, { useMemo, useEffect } from 'react';
import { ToolCall, StreamEventWithState } from '../../types';
import { Markdown } from '../Markdown';

interface StreamingMessageProps {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  isStreaming: boolean;
  toolCalls?: ToolCall[];
  streamingState?: StreamEventWithState;
  error?: string;
  onComplete?: () => void;
}

/**
 * ToolCallVisualization - Shows tool calls in progress
 */
const ToolCallVisualization: React.FC<{ toolCall: ToolCall }> = ({ toolCall }) => {
  const getStatusColor = (status: string): string => {
    const colorMap: Record<string, string> = {
      pending: 'text-yellow-600 dark:text-yellow-400',
      executing: 'text-blue-600 dark:text-blue-400 animate-pulse',
      completed: 'text-green-600 dark:text-green-400',
      failed: 'text-red-600 dark:text-red-400',
    };
    return colorMap[status] || '';
  };

  const getStatusIcon = (status: string): string => {
    const iconMap: Record<string, string> = {
      pending: '⏳',
      executing: '⚙️',
      completed: '✓',
      failed: '✗',
    };
    return iconMap[status] || '';
  };

  const hasInput = Object.keys(toolCall.toolInput as Record<string, unknown>).length > 0;
  const inputContent = hasInput ? JSON.stringify(toolCall.toolInput, null, 2) : '';
  const resultContent = toolCall.result
    ? typeof toolCall.result === 'string'
      ? toolCall.result
      : JSON.stringify(toolCall.result, null, 2)
    : '';

  return (
    <div className={`p-3 rounded-lg bg-muted/50 border border-border ${getStatusColor(toolCall.status)}`}>
      <div className="flex items-start gap-2">
        <span className="text-lg flex-shrink-0">{getStatusIcon(toolCall.status)}</span>
        <div className="flex-1 min-w-0">
          <div className="font-medium text-sm">{toolCall.toolName}</div>

          {/* Input */}
          {hasInput ? (
            <details className="mt-1">
              <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground">
                Input
              </summary>
              <pre className="mt-1 p-2 bg-background rounded text-xs overflow-x-auto">
                {inputContent}
              </pre>
            </details>
          ) : null}

          {/* Result */}
          {toolCall.result ? (
            <details className="mt-1">
              <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground">
                Result {toolCall.executionTimeMs ? `(${toolCall.executionTimeMs}ms)` : ''}
              </summary>
              <pre className="mt-1 p-2 bg-background rounded text-xs overflow-x-auto">
                {resultContent}
              </pre>
            </details>
          ) : null}
        </div>
      </div>
    </div>
  );
};

/**
 * StreamingMessage - Displays message content with streaming animation
 *
 * Renders message content with visual feedback for streaming state
 * Includes tool call visualization and error handling
 *
 * @param props - Component props
 */
export const StreamingMessage: React.FC<StreamingMessageProps> = ({
  content,
  role,
  isStreaming,
  toolCalls = [],
  streamingState,
  error,
  onComplete,
}) => {
  // Parse markdown content
  const displayContent = useMemo(() => {
    if (!content) return '';
    return content;
  }, [content]);

  // Calculate token count if available
  const tokenCount = useMemo(() => {
    if (streamingState?.metadata?.tokenUsage) {
      return streamingState.metadata.tokenUsage;
    }
    // Rough estimation: ~4 characters per token
    return Math.ceil(content.length / 4);
  }, [content, streamingState]);

  // Call onComplete when message finishes streaming
  useEffect(() => {
    if (!isStreaming && onComplete) {
      onComplete();
    }
  }, [isStreaming, onComplete]);

  return (
    <div className="space-y-3">
      {/* Main message content */}
      <div className="prose dark:prose-invert max-w-none">
        {displayContent ? (
          <Markdown content={displayContent} />
        ) : isStreaming ? (
          <div className="text-muted-foreground italic">Waiting for response...</div>
        ) : null}

        {/* Streaming cursor */}
        {isStreaming && displayContent && (
          <span className="inline-block w-2 h-5 ml-1 bg-foreground animate-pulse" />
        )}
      </div>

      {/* Tool calls visualization */}
      {toolCalls.length > 0 && (
        <div className="space-y-2 mt-4 pt-4 border-t border-border">
          <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
            Tool Calls ({toolCalls.filter((t) => t.status === 'completed').length}/{toolCalls.length})
          </div>
          <div className="space-y-2">
            {toolCalls.map((toolCall) => (
              <ToolCallVisualization key={toolCall.toolId} toolCall={toolCall} />
            ))}
          </div>
        </div>
      )}

      {/* Streaming state information */}
      {streamingState && (
        <div className="text-xs text-muted-foreground space-y-1 pt-2 border-t border-border">
          {streamingState.metadata?.latencyMs && (
            <div>Latency: {streamingState.metadata.latencyMs}ms</div>
          )}
          {streamingState.metadata?.tokenUsage && (
            <div>Tokens: {streamingState.metadata.tokenUsage}</div>
          )}
        </div>
      )}

      {/* Token count */}
      {!isStreaming && role === 'assistant' && (
        <div className="text-xs text-muted-foreground">
          ~{tokenCount} tokens
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/30">
          <p className="text-sm text-destructive">{error}</p>
        </div>
      )}
    </div>
  );
};

export default StreamingMessage;

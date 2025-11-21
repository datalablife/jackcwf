import { useCallback, useState, useRef, useEffect } from 'react';
import { conversationApi } from '../services/api';
import { useChatStore, useThreadsStore, useUIStore } from '../store';
import { ChatMessage, ThreadState } from '../types';

// useAutoTitle Hook - Auto-generate conversation title from first message
export const useAutoTitle = () => {
  const { updateThread } = useThreadsStore();

  const generateTitleFromContent = useCallback(async (
    threadId: string,
    conversationId: string,
    messageContent: string
  ) => {
    try {
      // Call API to generate title from message content
      const response = await conversationApi.generateTitle(conversationId, messageContent);

      if (response.data && typeof response.data === 'object' && 'title' in response.data) {
        const newTitle = (response.data as any).title;
        // Update the thread in store with new title
        updateThread(threadId, { title: newTitle });
      }
    } catch (error) {
      console.error('Failed to generate title:', error);
      // Silently fail - keep the default title
    }
  }, [updateThread]);

  return { generateTitleFromContent };
};
export const useTypingIndicator = (threadId: string, wsUrl: string = 'ws://localhost:8000/ws') => {
  const { addTypingUser, removeTypingUser, clearTypingUsers } = useChatStore();
  const wsRef = useRef<WebSocket | null>(null);
  const typingTimeoutRef = useRef<Record<string, NodeJS.Timeout>>({});
  const TYPING_TIMEOUT_MS = 5000; // Auto-clear typing indicator after 5 seconds

  useEffect(() => {
    try {
      const token = localStorage.getItem('auth_token');
      const url = `${wsUrl}${wsUrl.includes('?') ? '&' : '?'}token=${token}`;
      wsRef.current = new WebSocket(url);

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          // Handle typing events
          if (data.type === 'user_typing' && data.threadId === threadId) {
            const userName = data.userName || 'User';

            // Add typing user
            addTypingUser(threadId, userName);

            // Clear existing timeout for this user
            if (typingTimeoutRef.current[userName]) {
              clearTimeout(typingTimeoutRef.current[userName]);
            }

            // Set new timeout to remove typing indicator after 5 seconds
            typingTimeoutRef.current[userName] = setTimeout(() => {
              removeTypingUser(threadId, userName);
              delete typingTimeoutRef.current[userName];
            }, TYPING_TIMEOUT_MS);
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      return () => {
        if (wsRef.current) {
          wsRef.current.close();
        }
        // Clear all timeouts
        Object.values(typingTimeoutRef.current).forEach(timeout => clearTimeout(timeout));
      };
    } catch (error) {
      console.error('Failed to setup typing indicator:', error);
    }
  }, [threadId, wsUrl, addTypingUser, removeTypingUser]);

  return { clearTypingUsers };
};

// useChat Hook - Manages chat operations
export const useChat = (threadId: string) => {
  const { addMessage, updateStreamingMessage, finalizeStreamingMessage, setError } = useChatStore();
  const { setLoading } = useUIStore();
  const [retryCount, setRetryCount] = useState(0);
  const maxRetries = 3;

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim()) return;

      // Add user message to local state
      const userMessage: ChatMessage = {
        id: `msg-${Date.now()}`,
        threadId,
        role: 'user',
        content,
        timestamp: new Date(),
      };
      addMessage(threadId, userMessage);
      setLoading(true);

      try {
        // Call streaming API
        const response = await fetch(`/api/v1/conversations/${threadId}/stream`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${localStorage.getItem('auth_token') || ''}`,
          },
          body: JSON.stringify({ content }),
        });

        if (!response.ok) {
          if (response.status === 502 || response.status === 503) {
            if (retryCount < maxRetries) {
              const delay = Math.min(1000 * Math.pow(1.5, retryCount), 10000);
              setTimeout(() => {
                setRetryCount(retryCount + 1);
                sendMessage(content);
              }, delay);
              return;
            }
          }
          throw new Error(`HTTP ${response.status}`);
        }

        // Create assistant message for streaming
        const assistantMessage: ChatMessage = {
          id: `msg-${Date.now()}-ai`,
          threadId,
          role: 'assistant',
          content: '',
          timestamp: new Date(),
          isStreaming: true,
        };
        addMessage(threadId, assistantMessage);

        // Parse SSE events
        const reader = response.body?.getReader();
        if (!reader) throw new Error('No response body');

        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = JSON.parse(line.slice(6));
              if (data.type === 'chunk' && data.data.chunk) {
                updateStreamingMessage(threadId, data.data.chunk);
              }
            }
          }
        }

        finalizeStreamingMessage(threadId);
        setRetryCount(0);
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        setError(errorMessage);
        console.error('Failed to send message:', error);
      } finally {
        setLoading(false);
      }
    },
    [threadId, addMessage, updateStreamingMessage, finalizeStreamingMessage, setLoading, setError, retryCount]
  );

  return { sendMessage };
};

// useThread Hook - Manages thread operations
export const useThread = () => {
  const [thread, setThread] = useState<ThreadState | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const createThread = useCallback(async (title?: string) => {
    setIsLoading(true);
    try {
      // Call API to create conversation/thread
      const response = await conversationApi.createConversation({ title: title || 'New Conversation' });
      if (response.error) throw new Error(response.error.message);
      return response.data;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getThreadState = useCallback(async (threadId: string) => {
    setIsLoading(true);
    try {
      const response = await fetch(`/api/v1/threads/${threadId}/state?include_messages=true`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('auth_token') || ''}`,
        },
      });
      const data = await response.json();
      setThread(data);
      return data;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { thread, isLoading, createThread, getThreadState };
};

// useWebSocket Hook - Manages WebSocket connection with exponential backoff
export const useWebSocket = (url: string, onMessage?: (data: unknown) => void) => {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [reconnectAttempt, setReconnectAttempt] = useState(0);
  const maxReconnectAttempts = 10;
  const baseDelay = 1000; // 1 second

  const connect = useCallback(() => {
    try {
      const token = localStorage.getItem('auth_token');
      const wsUrl = `${url}${url.includes('?') ? '&' : '?'}token=${token}`;
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setReconnectAttempt(0);
      };

      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        onMessage?.(data);
      };

      wsRef.current.onclose = () => {
        setIsConnected(false);
        if (reconnectAttempt < maxReconnectAttempts) {
          const delay = Math.min(baseDelay * Math.pow(1.5, reconnectAttempt), 30000);
          console.log(`Reconnecting in ${delay}ms...`);
          setTimeout(() => {
            setReconnectAttempt((prev) => prev + 1);
            connect();
          }, delay);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  }, [url, onMessage, reconnectAttempt]);

  useEffect(() => {
    connect();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  return { isConnected, ws: wsRef.current };
};

// useDebounce Hook - Debounce values
export const useDebounce = <T,>(value: T, delay: number): T => {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => clearTimeout(handler);
  }, [value, delay]);

  return debouncedValue;
};

// useLocalStorage Hook - Persist values in localStorage
export const useLocalStorage = <T,>(key: string, initialValue: T): [T, (value: T) => void] => {
  const [storedValue, setStoredValue] = useState<T>(() => {
    const item = window.localStorage.getItem(key);
    return item ? JSON.parse(item) : initialValue;
  });

  const setValue = useCallback(
    (value: T) => {
      setStoredValue(value);
      window.localStorage.setItem(key, JSON.stringify(value));
    },
    [key]
  );

  return [storedValue, setValue];
};

// useStreaming Hook - Parse SSE events
export const useStreaming = () => {
  const streamMessage = useCallback(async (
    threadId: string,
    message: string,
    onChunk: (chunk: string) => void,
    onComplete?: () => void,
    onError?: (error: Error) => void
  ) => {
    try {
      const response = await fetch(`/api/v1/conversations/${threadId}/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('auth_token') || ''}`,
        },
        body: JSON.stringify({ content: message }),
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response body');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === 'chunk' && data.data.chunk) {
                onChunk(data.data.chunk);
              }
            } catch (parseError) {
              console.warn('Failed to parse SSE event:', parseError);
            }
          }
        }
      }

      onComplete?.();
    } catch (error) {
      onError?.(error instanceof Error ? error : new Error(String(error)));
    }
  }, []);

  return { streamMessage };
};

// useCache Hook - Track cache hit/miss metrics
export const useCache = () => {
  const [cacheStats, setCacheStats] = useState({
    hits: 0,
    misses: 0,
    totalRequests: 0,
  });

  const recordHit = useCallback(() => {
    setCacheStats((prev) => ({
      hits: prev.hits + 1,
      misses: prev.misses,
      totalRequests: prev.totalRequests + 1,
    }));
  }, []);

  const recordMiss = useCallback(() => {
    setCacheStats((prev) => ({
      hits: prev.hits,
      misses: prev.misses + 1,
      totalRequests: prev.totalRequests + 1,
    }));
  }, []);

  const hitRate = cacheStats.totalRequests > 0
    ? ((cacheStats.hits / cacheStats.totalRequests) * 100).toFixed(2)
    : '0';

  return { cacheStats, recordHit, recordMiss, hitRate };
};

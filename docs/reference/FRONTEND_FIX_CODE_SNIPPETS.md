# Frontend API Integration Fixes - Code Snippets

Copy these snippets directly into your files.

---

## Issue 1: Missing system_prompt in createConversation

**File: `/mnt/d/工作区/云开发/working/frontend/src/services/api.ts`**

Replace lines 108-109 with:

```typescript
createConversation: (data: {
  title: string;
  system_prompt?: string;
  model?: string;
  metadata?: unknown;
}) =>
  request('POST', '/conversations', data),
```

**File: `/mnt/d/工作区/云开发/working/frontend/src/hooks/index.ts`**

Replace the `createThread` function (lines 194-204) with:

```typescript
const createThread = useCallback(async (title?: string) => {
  setIsLoading(true);
  try {
    const response = await conversationApi.createConversation({
      title: title || 'New Conversation',
      system_prompt: 'You are a helpful AI assistant. Provide clear, concise, and accurate responses.',
      model: 'claude-3-5-sonnet-20241022'
    });
    if (response.error) throw new Error(response.error.message);
    return response.data;
  } finally {
    setIsLoading(false);
  }
}, []);
```

---

## Issue 2: Response Parsing Error in getConversations

**File: `/mnt/d/工作区/云开发/working/frontend/src/services/api.ts`**

Add these interfaces at the top (after imports):

```typescript
interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

interface ConversationData {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
  message_count?: number;
  meta?: Record<string, unknown>;
}
```

Replace the `getConversations` method with:

```typescript
getConversations: () =>
  request<PaginatedResponse<ConversationData>>('GET', '/conversations'),
```

**File: `/mnt/d/工作区/云开发/working/frontend/src/App.tsx`**

Replace the `loadConversations` function (lines 50-82) with:

```typescript
const loadConversations = async () => {
  try {
    setIsInitializing(true);
    const response = await conversationApi.getConversations();

    // Backend returns { items: [...], total, skip, limit }
    const conversations = response.data?.items || [];

    if (Array.isArray(conversations)) {
      const mappedThreads: typeof threads = conversations.map((conv: any) => ({
        threadId: `thread_${conv.id}`,
        conversationId: conv.id,
        title: conv.title || 'Untitled Conversation',
        createdAt: new Date(conv.created_at),
        updatedAt: new Date(conv.updated_at),
        messageCount: conv.message_count || 0,
        metadata: conv.meta || {}
      }));

      setThreads(mappedThreads);

      // Auto-select first thread if available
      if (mappedThreads.length > 0 && mappedThreads[0]) {
        setSelectedThread(mappedThreads[0].threadId);
      }
    }
  } catch (error) {
    console.error('Failed to load conversations:', error);
    setChatError('Failed to load conversations. Please try again.');
  } finally {
    setIsInitializing(false);
  }
};
```

---

## Issue 4: Thread ID Format Inconsistency

**File: `/mnt/d/工作区/云开发/working/frontend/src/App.tsx`**

Add this import at the top:

```typescript
import { getConversationId, getConversationIdAsNumber } from './utils/threadUtils';
```

Replace `handleDeleteThread` function (lines 110-130) with:

```typescript
const handleDeleteThread = async (threadId: string) => {
  try {
    const conversationId = getConversationIdAsNumber(threadId);
    await conversationApi.deleteConversation(conversationId);

    const updatedThreads = threads.filter((t) => t.threadId !== threadId);
    setThreads(updatedThreads);

    // Select another thread if the deleted one was selected
    if (selectedThreadId === threadId && updatedThreads.length > 0 && updatedThreads[0]) {
      setSelectedThread(updatedThreads[0].threadId);
    } else if (updatedThreads.length === 0) {
      setSelectedThread(null);
    }

    setChatError(null);
  } catch (error) {
    console.error('Failed to delete thread:', error);
    setChatError('Failed to delete conversation');
  }
};
```

**File: `/mnt/d/工作区/云开发/working/frontend/src/hooks/index.ts`**

Add these imports at the top:

```typescript
import { getConversationId, getConversationIdAsNumber } from '../utils/threadUtils';
import { generateTitleFromContent } from '../utils/titleGenerator';
```

Replace the `sendMessage` function in `useChat` hook (lines 97-184) with:

```typescript
const sendMessage = useCallback(
  async (content: string) => {
    if (!content.trim()) return;

    // Extract conversation ID properly for API calls
    const conversationId = getConversationIdAsNumber(threadId);

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
      // Use conversationId (not threadId) in API call
      const response = await fetch(`/api/v1/conversations/${conversationId}/stream`, {
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
```

Replace the `useStreaming` hook (lines 316-371) with:

```typescript
export const useStreaming = () => {
  const streamMessage = useCallback(async (
    threadId: string,
    message: string,
    onChunk: (chunk: string) => void,
    onComplete?: () => void,
    onError?: (error: Error) => void
  ) => {
    try {
      // Use conversationId in API call
      const conversationId = getConversationIdAsNumber(threadId);
      const response = await fetch(`/api/v1/conversations/${conversationId}/stream`, {
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
```

---

## Issue 5: Remove Non-existent Title Generation Endpoint

**File: `/mnt/d/工作区/云开发/working/frontend/src/services/api.ts`**

Delete these lines (around 120-121):

```typescript
generateTitle: (conversationId: string, content: string) =>
  request('POST', `/conversations/${conversationId}/generate-title`, { content }),
```

**File: `/mnt/d/工作区/云开发/working/frontend/src/hooks/index.ts`**

Replace the `useAutoTitle` hook (lines 6-31) with:

```typescript
export const useAutoTitle = () => {
  const { updateThread } = useThreadsStore();

  const generateTitleFromFirstMessage = useCallback(async (
    threadId: string,
    messageContent: string
  ) => {
    try {
      // Generate title locally instead of calling non-existent backend endpoint
      const newTitle = generateTitleFromContent(messageContent);

      // Update the thread in store with new title
      updateThread(threadId, { title: newTitle });

      // Also update via API to persist the title
      const conversationId = getConversationIdAsNumber(threadId);
      await conversationApi.updateConversation(conversationId, { title: newTitle });
    } catch (error) {
      console.error('Failed to generate/update title:', error);
      // Silently fail - keep the default title
    }
  }, [updateThread]);

  return { generateTitleFromFirstMessage };
};
```

**File: `/mnt/d/工作区/云开发/working/frontend/src/App.tsx`**

Add this import at the top:

```typescript
import { generateTitleFromContent } from './utils/titleGenerator';
```

And also add:

```typescript
import { getConversationId, getConversationIdAsNumber } from './utils/threadUtils';
```

Update the hook usage at line 33:

```typescript
// BEFORE:
const { generateTitleFromContent } = useAutoTitle();

// AFTER:
const { generateTitleFromFirstMessage } = useAutoTitle();
```

Replace the title generation section in `handleSendMessage` (around line 160):

```typescript
// Auto-generate title for first message in this thread
if (!firstMessageSent.has(selectedThreadId)) {
  setFirstMessageSent(prev => new Set([...prev, selectedThreadId]));
  const threadMessages = messages[selectedThreadId] || [];
  if (threadMessages.length === 1) { // Only user message so far
    // Generate title asynchronously (don't block message sending)
    generateTitleFromFirstMessage(selectedThreadId, message);
  }
}
```

---

## Issue 3: WebSocket Connection (Optional - Advanced)

**File: `/mnt/d/工作区/云开发/working/frontend/src/hooks/index.ts`**

Replace the entire `useTypingIndicator` function (lines 32-88) with:

```typescript
import { BackendWebSocketAdapter, type BackendConnectOptions } from '../services/backendWebSocketAdapter';

export const useTypingIndicator = (threadId: string) => {
  const { addTypingUser, removeTypingUser, clearTypingUsers } = useChatStore();
  const adapterRef = useRef<BackendWebSocketAdapter | null>(null);
  const typingTimeoutRef = useRef<Record<string, NodeJS.Timeout>>({});
  const TYPING_TIMEOUT_MS = 5000;

  useEffect(() => {
    if (!threadId) return;

    try {
      const conversationId = getConversationId(threadId);
      const userId = localStorage.getItem('user_id') || 'anonymous';
      const username = localStorage.getItem('username') || 'User';

      const options: BackendConnectOptions = {
        conversationId,
        userId,
        username,
        onResponse: (content: string, done: boolean) => {
          if (!done) {
            addTypingUser(threadId, 'Assistant');

            if (typingTimeoutRef.current['Assistant']) {
              clearTimeout(typingTimeoutRef.current['Assistant']);
            }

            typingTimeoutRef.current['Assistant'] = setTimeout(() => {
              removeTypingUser(threadId, 'Assistant');
              delete typingTimeoutRef.current['Assistant'];
            }, TYPING_TIMEOUT_MS);
          }
        },
        onError: (error: string) => {
          console.error('WebSocket error:', error);
          removeTypingUser(threadId, 'Assistant');
        },
      };

      adapterRef.current = new BackendWebSocketAdapter(options);

      adapterRef.current.connect().catch((error) => {
        console.error('Failed to connect WebSocket:', error);
      });

      return () => {
        if (adapterRef.current) {
          adapterRef.current.disconnect();
        }
        Object.values(typingTimeoutRef.current).forEach(timeout => clearTimeout(timeout));
      };
    } catch (error) {
      console.error('Failed to setup typing indicator:', error);
    }
  }, [threadId, addTypingUser, removeTypingUser, clearTypingUsers]);

  return { clearTypingUsers };
};
```

Add this import:

```typescript
import { BackendWebSocketAdapter, type BackendConnectOptions } from '../services/backendWebSocketAdapter';
```

---

## Summary: Lines Changed

| File | Lines | Change |
|------|-------|--------|
| `api.ts` | 104-122 | Add interfaces, update methods |
| `hooks/index.ts` | 1-5 | Add imports |
| `hooks/index.ts` | 6-31 | Replace useAutoTitle |
| `hooks/index.ts` | 32-88 | Replace useTypingIndicator |
| `hooks/index.ts` | 97-184 | Update useChat.sendMessage |
| `hooks/index.ts` | 316-371 | Update useStreaming |
| `App.tsx` | 1-8 | Add imports |
| `App.tsx` | 33 | Update hook usage |
| `App.tsx` | 50-82 | Replace loadConversations |
| `App.tsx` | 110-130 | Replace handleDeleteThread |
| `App.tsx` | 160 | Replace title generation |

---

## Files to Create

1. **`/mnt/d/工作区/云开发/working/frontend/src/utils/threadUtils.ts`**
   - Already created and ready to copy

2. **`/mnt/d/工作区/云开发/working/frontend/src/utils/titleGenerator.ts`**
   - Already created and ready to copy

---

## Verification Commands

```bash
# Navigate to frontend directory
cd /mnt/d/工作区/云开发/working/frontend

# Install dependencies (if needed)
npm install

# Run dev server
npm run dev

# Run type checking
npm run type-check

# Run linter
npm run lint
```

---

## Expected Results After Fixes

### Before Fixes
- Conversations fail to create (422 Validation Error)
- Empty sidebar (conversations don't load)
- Title stays "New Conversation" forever
- API returns 404 for title generation
- WebSocket connection fails
- API calls use wrong URLs (thread_123 instead of 123)

### After Fixes
- Conversations create successfully
- Sidebar loads all existing conversations
- Conversation titles auto-generate from first message
- No 404 errors in console
- (Optional) WebSocket connects and shows typing indicator
- All API calls use correct URLs

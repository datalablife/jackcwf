# Frontend API Integration Fixes - Diagnostic Report & Solutions

## Executive Summary

Five critical issues have been identified in the frontend API integration layer that prevent proper communication with the backend. These issues span API request construction, response parsing, WebSocket configuration, and endpoint availability.

---

## Issue 1: Incomplete createConversation Request Body

### Problem
**Location:** `/mnt/d/工作区/云开发/working/frontend/src/services/api.ts:108-109`

```typescript
createConversation: (data: { title: string }) =>
  request('POST', '/conversations', data),
```

**Why it fails:**
- The backend endpoint (line 85-100 in `conversation_routes.py`) expects `CreateConversationRequest` with required fields
- Inspection of the backend shows it requires `system_prompt` as a required field
- Frontend only sends `{title}`, missing the `system_prompt` parameter

**Impact:**
- API returns 422 Unprocessable Entity validation error
- Conversation creation fails silently
- Cannot create new chat threads

### Solution

**Step 1: Update the API method signature**

```typescript
// File: /mnt/d/工作区/云开发/working/frontend/src/services/api.ts (line 108-109)

// BEFORE:
createConversation: (data: { title: string }) =>
  request('POST', '/conversations', data),

// AFTER:
createConversation: (data: { title: string; system_prompt?: string; model?: string; metadata?: unknown }) =>
  request('POST', '/conversations', data),
```

**Step 2: Update the hook to provide system_prompt**

```typescript
// File: /mnt/d/工作区/云开发/working/frontend/src/hooks/index.ts (line 194-204)

// BEFORE:
const createThread = useCallback(async (title?: string) => {
  setIsLoading(true);
  try {
    const response = await conversationApi.createConversation({ title: title || 'New Conversation' });
    if (response.error) throw new Error(response.error.message);
    return response.data;
  } finally {
    setIsLoading(false);
  }
}, []);

// AFTER:
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

## Issue 2: Response Data Parsing Error in getConversations

### Problem
**Location:** `/mnt/d/工作区/云开发/working/frontend/src/App.tsx:49-82`

```typescript
const response = await conversationApi.getConversations();

if (response.data && Array.isArray(response.data)) {
  const mappedThreads: typeof threads = (response.data as any[]).map((conv: any) => ({
    threadId: `thread_${conv.id}`,
    // ...
  }));
```

**Why it fails:**
- The backend returns a paginated response: `{ items: [], total, skip, limit }`
- Frontend expects `response.data` to be an array
- The actual array is at `response.data.items` not `response.data`

**Backend Response Structure:**
```json
{
  "items": [
    { "id": 1, "title": "...", "created_at": "...", ... }
  ],
  "total": 5,
  "skip": 0,
  "limit": 50
}
```

**Impact:**
- Conversations fail to load
- Empty sidebar with no thread list
- App shows "No conversations" even when they exist

### Solution

**Step 1: Update the getConversations parsing in App.tsx**

```typescript
// File: /mnt/d/工作区/云开发/working/frontend/src/App.tsx (line 49-82)

// BEFORE:
const loadConversations = async () => {
  try {
    setIsInitializing(true);
    const response = await conversationApi.getConversations();

    if (response.data && Array.isArray(response.data)) {
      const mappedThreads: typeof threads = (response.data as any[]).map((conv: any) => ({
        threadId: `thread_${conv.id}`,
        conversationId: conv.id,
        title: conv.title || 'Untitled Conversation',
        createdAt: new Date(conv.created_at),
        updatedAt: new Date(conv.updated_at),
        messageCount: conv.message_count || 0,
        metadata: conv.meta || {}
      }));

// AFTER:
const loadConversations = async () => {
  try {
    setIsInitializing(true);
    const response = await conversationApi.getConversations();

    // Backend returns paginated response: { items: [...], total, skip, limit }
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
```

**Step 2: Add type safety by updating the API response type**

```typescript
// File: /mnt/d/工作区/云开发/working/frontend/src/services/api.ts (line 104-109)

// Add interface for paginated response
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

// BEFORE:
getConversations: () =>
  request('GET', '/conversations'),

// AFTER:
getConversations: () =>
  request<PaginatedResponse<ConversationData>>('GET', '/conversations'),
```

---

## Issue 3: WebSocket URL Construction Error

### Problem
**Location:** `/mnt/d/工作区/云开发/working/frontend/src/hooks/index.ts:32-88`

```typescript
export const useTypingIndicator = (threadId: string, wsUrl: string = 'ws://localhost:8000/ws') => {
  // ...
  const url = `${wsUrl}${wsUrl.includes('?') ? '&' : '?'}token=${token}`;
  wsRef.current = new WebSocket(url);
```

**Why it fails:**
1. **Hardcoded localhost URL:** Uses `ws://localhost:8000/ws` - won't work in production
2. **Missing conversation ID:** Should be `ws://host/ws/conversations/{conversationId}`
3. **Token in URL:** Tokens in URLs are logged in server logs (security issue)
4. **No handshake protocol:** Doesn't follow backend's initial message requirement

**Backend WebSocket Requirements:**
- Connect to: `ws://host/ws/conversations/{conversationId}`
- First message must contain: `{ type: 'initial', user_id, username, conversation_id }`
- Then handle events: `agent_thinking`, `tool_call`, `tool_result`, `response`, `complete`, `error`

**Impact:**
- Typing indicators never display
- No real-time communication
- WebSocket connection fails immediately

### Solution

**Step 1: Create a proper WebSocket URL builder utility**

```typescript
// File: /mnt/d/工作区/云开发/working/frontend/src/services/websocketService.ts (NEW)

/**
 * Build WebSocket URL from current environment
 */
export const buildWebSocketUrl = (path: string): string => {
  if (typeof window === 'undefined') {
    return `ws://localhost:8000${path}`;
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host;

  return `${protocol}//${host}/api/v1${path}`;
};

/**
 * Build conversation-specific WebSocket URL
 */
export const buildConversationWebSocketUrl = (conversationId: string): string => {
  return buildWebSocketUrl(`/conversations/${conversationId}/ws`);
};
```

**Step 2: Update useTypingIndicator to use BackendWebSocketAdapter**

```typescript
// File: /mnt/d/工作区/云开发/working/frontend/src/hooks/index.ts (line 32-88)

// BEFORE:
export const useTypingIndicator = (threadId: string, wsUrl: string = 'ws://localhost:8000/ws') => {
  const { addTypingUser, removeTypingUser, clearTypingUsers } = useChatStore();
  const wsRef = useRef<WebSocket | null>(null);
  const typingTimeoutRef = useRef<Record<string, NodeJS.Timeout>>({});
  const TYPING_TIMEOUT_MS = 5000;

  useEffect(() => {
    try {
      const token = localStorage.getItem('auth_token');
      const url = `${wsUrl}${wsUrl.includes('?') ? '&' : '?'}token=${token}`;
      wsRef.current = new WebSocket(url);
      // ... token handling in URL
    }
  }, ...);
};

// AFTER:
export const useTypingIndicator = (threadId: string) => {
  const { addTypingUser, removeTypingUser, clearTypingUsers } = useChatStore();
  const adapterRef = useRef<BackendWebSocketAdapter | null>(null);
  const typingTimeoutRef = useRef<Record<string, NodeJS.Timeout>>({});
  const TYPING_TIMEOUT_MS = 5000;

  useEffect(() => {
    if (!threadId) return;

    try {
      // Extract conversation ID from threadId (format: thread_<id>)
      const conversationId = threadId.replace('thread_', '');
      const userId = localStorage.getItem('user_id') || 'anonymous';
      const username = localStorage.getItem('username') || 'User';

      adapterRef.current = new BackendWebSocketAdapter({
        conversationId,
        userId,
        username,
        onResponse: (content: string, done: boolean) => {
          if (!done) {
            // Update typing indicator
            addTypingUser(threadId, username);

            // Reset timeout
            if (typingTimeoutRef.current[username]) {
              clearTimeout(typingTimeoutRef.current[username]);
            }

            typingTimeoutRef.current[username] = setTimeout(() => {
              removeTypingUser(threadId, username);
              delete typingTimeoutRef.current[username];
            }, TYPING_TIMEOUT_MS);
          }
        },
        onError: (error: string) => {
          console.error('WebSocket error:', error);
        },
      });

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
  }, [threadId, addTypingUser, removeTypingUser]);

  return { clearTypingUsers };
};
```

---

## Issue 4: Thread ID Format Inconsistency

### Problem
**Location:** Multiple files - thread ID prefixing inconsistency

Files affected:
- `/mnt/d/工作区/云开发/working/frontend/src/App.tsx:57` - Creates `thread_${conv.id}`
- `/mnt/d/工作区/云开发/working/frontend/src/hooks/index.ts:114` - Uses `threadId` in fetch URL directly
- `/mnt/d/工作区/云开发/working/frontend/src/hooks/index.ts:160` - Removes prefix in generateTitleFromContent

```typescript
// App.tsx - Creates threadId with prefix
threadId: `thread_${conv.id}`,

// hooks/index.ts line 114 - Uses threadId directly in URL
const response = await fetch(`/api/v1/conversations/${threadId}/stream`, {

// hooks/index.ts line 158 - Tries to remove prefix
const conversationId = selectedThreadId.replace('thread_', '');
```

**Why it fails:**
- When you use `threadId` directly in API calls: `/api/v1/conversations/thread_123/stream`
- Backend expects: `/api/v1/conversations/123/stream`
- The prefix-stripping logic is inconsistent and error-prone

**Impact:**
- 404 Not Found errors when sending messages
- API calls construct malformed URLs
- Thread operations fail silently

### Solution

**Create a utility function for consistent ID handling**

```typescript
// File: /mnt/d/工作区/云开发/working/frontend/src/utils/threadUtils.ts (NEW)

/**
 * Utility functions for thread ID handling
 */

export const THREAD_ID_PREFIX = 'thread_';

/**
 * Create a thread ID with prefix
 */
export const createThreadId = (conversationId: number | string): string => {
  return `${THREAD_ID_PREFIX}${conversationId}`;
};

/**
 * Extract conversation ID from thread ID
 */
export const getConversationId = (threadId: string): string => {
  if (threadId.startsWith(THREAD_ID_PREFIX)) {
    return threadId.substring(THREAD_ID_PREFIX.length);
  }
  return threadId;
};

/**
 * Ensure thread ID has the correct format
 */
export const ensureThreadId = (id: string | number): string => {
  const idStr = String(id);
  return idStr.startsWith(THREAD_ID_PREFIX) ? idStr : createThreadId(idStr);
};
```

**Update App.tsx to use the utility**

```typescript
// File: /mnt/d/工作区/云开发/working/frontend/src/App.tsx (line 49-82)

import { getConversationId } from './utils/threadUtils';

// ... in loadConversations:
const mappedThreads: typeof threads = conversations.map((conv: any) => ({
  threadId: `thread_${conv.id}`,
  conversationId: conv.id,
  // ...
}));

// In handleSendMessage - extract conversation ID properly:
const handleSendMessage = async (message: string) => {
  if (!selectedThreadId) {
    setChatError('Please select a conversation first');
    return;
  }

  try {
    setChatError(null);

    // Extract conversation ID properly
    const conversationId = getConversationId(selectedThreadId);

    // ... rest of code

    // When generating title, use conversationId not selectedThreadId
    generateTitleFromContent(selectedThreadId, conversationId, message);
  }
};
```

**Update hooks to use the utility**

```typescript
// File: /mnt/d/工作区/云开发/working/frontend/src/hooks/index.ts (line 114)

import { getConversationId } from '../utils/threadUtils';

// In useChat hook:
const sendMessage = useCallback(
  async (content: string) => {
    if (!content.trim()) return;

    const conversationId = getConversationId(threadId);

    // Use conversationId in API calls, NOT threadId
    const response = await fetch(`/api/v1/conversations/${conversationId}/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${localStorage.getItem('auth_token') || ''}`,
      },
      body: JSON.stringify({ content }),
    });
    // ...
  },
  [threadId, ...]
);
```

---

## Issue 5: Non-existent Title Generation Endpoint

### Problem
**Location:** `/mnt/d/工作区/云开发/working/frontend/src/hooks/index.ts:120-121`

```typescript
generateTitle: (conversationId: string, content: string) =>
  request('POST', `/conversations/${conversationId}/generate-title`, { content }),
```

**Why it fails:**
- Backend does NOT have a `/conversations/{id}/generate-title` endpoint
- The endpoint doesn't exist in `conversation_routes.py`
- API returns 404 Not Found

**Backend Available Endpoints:**
- `POST /conversations` - Create conversation
- `GET /conversations` - List conversations
- `GET /conversations/{id}` - Get conversation
- `PATCH /conversations/{id}` - Update conversation
- `DELETE /conversations/{id}` - Delete conversation
- `POST /conversations/{id}/messages` - Add message
- `POST /conversations/{id}/stream` - Stream chat response

**Impact:**
- Auto-title generation fails silently
- Conversations stay with default "New Conversation" title
- Error logs show 404 for non-existent endpoint

### Solution

**Option A: Use LLM in Frontend (Recommended for offline fallback)**

```typescript
// File: /mnt/d/工作区/云开发/working/frontend/src/services/api.ts (line 120-121)

// REPLACE the generateTitle method - it's not on backend
// Instead, generate title from the first message content locally

// Remove this:
// generateTitle: (conversationId: string, content: string) =>
//   request('POST', `/conversations/${conversationId}/generate-title`, { content }),
```

**Option B: Add Backend Endpoint (If available)**

If the backend team adds `/conversations/{id}/auto-title` endpoint:

```typescript
// File: /mnt/d/工作区/云开发/working/frontend/src/services/api.ts

generateTitle: (conversationId: string, content: string) =>
  request('POST', `/conversations/${conversationId}/auto-title`, { content }),
```

**Implement Client-Side Title Generation**

```typescript
// File: /mnt/d/工作区/云开发/working/frontend/src/utils/titleGenerator.ts (NEW)

/**
 * Generate a concise title from message content
 * Uses simple heuristics: first 50 chars or first sentence
 */
export const generateTitleFromContent = (content: string): string => {
  // Remove leading/trailing whitespace
  const trimmed = content.trim();

  // Find first sentence or 50 characters, whichever is shorter
  const sentenceEnd = Math.min(
    trimmed.length,
    trimmed.search(/[.!?]/),
  );

  if (sentenceEnd === -1) {
    // No sentence terminator found
    return trimmed.length > 50
      ? trimmed.substring(0, 50) + '...'
      : trimmed;
  }

  return trimmed.substring(0, sentenceEnd + 1);
};
```

**Update App.tsx to use local title generation**

```typescript
// File: /mnt/d/工作区/云开发/working/frontend/src/App.tsx (line 160)

import { generateTitleFromContent as generateLocalTitle } from './utils/titleGenerator';

// In handleSendMessage:
// Auto-generate title for first message in this thread
if (!firstMessageSent.has(selectedThreadId)) {
  setFirstMessageSent(prev => new Set([...prev, selectedThreadId]));
  const threadMessages = messages[selectedThreadId] || [];
  if (threadMessages.length === 1) { // Only user message so far
    // Generate title locally from message content
    const generatedTitle = generateLocalTitle(message);

    // Update conversation title via API
    const conversationId = getConversationId(selectedThreadId);
    conversationApi.updateConversation(parseInt(conversationId), {
      title: generatedTitle
    }).catch(error => {
      console.warn('Failed to update conversation title:', error);
    });
  }
}
```

---

## Implementation Checklist

### Phase 1: Critical Fixes (Do First)

- [ ] **Fix Issue 1:** Update `createConversation` to include `system_prompt`
  - File: `/mnt/d/工作区/云开发/working/frontend/src/services/api.ts`
  - File: `/mnt/d/工作区/云开发/working/frontend/src/hooks/index.ts`

- [ ] **Fix Issue 2:** Update `getConversations` response parsing
  - File: `/mnt/d/工作区/云开发/working/frontend/src/App.tsx`
  - Add proper type definitions

- [ ] **Fix Issue 4:** Create thread ID utility and apply everywhere
  - Create: `/mnt/d/工作区/云开发/working/frontend/src/utils/threadUtils.ts`
  - Update: `/mnt/d/工作区/云开发/working/frontend/src/App.tsx`
  - Update: `/mnt/d/工作区/云开发/working/frontend/src/hooks/index.ts`

### Phase 2: WebSocket & Real-time (Do Second)

- [ ] **Fix Issue 3:** Replace raw WebSocket with BackendWebSocketAdapter
  - File: `/mnt/d/工作区/云开发/working/frontend/src/hooks/index.ts` (useTypingIndicator)
  - Create WebSocket URL utilities

### Phase 3: Title Generation (Do Last)

- [ ] **Fix Issue 5:** Implement client-side title generation
  - Create: `/mnt/d/工作区/云开发/working/frontend/src/utils/titleGenerator.ts`
  - Update: `/mnt/d/工作区/云开发/working/frontend/src/App.tsx`
  - Remove backend endpoint call

---

## Testing Plan

### Unit Tests

```typescript
// Test thread ID utilities
describe('threadUtils', () => {
  it('creates thread ID with prefix', () => {
    expect(createThreadId(123)).toBe('thread_123');
  });

  it('extracts conversation ID from thread ID', () => {
    expect(getConversationId('thread_123')).toBe('123');
  });

  it('handles already-prefixed IDs', () => {
    expect(getConversationId('thread_123')).toBe('123');
    expect(getConversationId('123')).toBe('123');
  });
});

// Test title generation
describe('titleGenerator', () => {
  it('generates title from short content', () => {
    const title = generateTitleFromContent('What is AI?');
    expect(title).toBe('What is AI?');
  });

  it('truncates long content', () => {
    const longText = 'a'.repeat(100);
    const title = generateTitleFromContent(longText);
    expect(title.length).toBeLessThanOrEqual(53); // 50 + '...'
  });
});
```

### Integration Tests

```typescript
// Test API request/response flow
describe('Conversation API', () => {
  it('creates conversation with required system_prompt', async () => {
    const response = await conversationApi.createConversation({
      title: 'Test',
      system_prompt: 'Test prompt'
    });
    expect(response.data).toBeDefined();
    expect(response.data?.id).toBeDefined();
  });

  it('parses paginated conversations response', async () => {
    const response = await conversationApi.getConversations();
    expect(Array.isArray(response.data?.items)).toBe(true);
    expect(response.data?.total).toBeDefined();
  });
});
```

### Manual Testing

1. **Create Conversation Test**
   - Click "New Conversation"
   - Check Network tab: POST `/conversations` should include `system_prompt`
   - Verify new conversation appears in sidebar

2. **Load Conversations Test**
   - Refresh page
   - Check Network tab: GET `/conversations` response structure
   - Verify all conversations load in sidebar

3. **Send Message Test**
   - Click a conversation
   - Send a message
   - Check Network tab: POST `/conversations/{id}/stream` URL
   - Verify message appears and gets response

4. **WebSocket Test** (Optional)
   - Open DevTools > Network > WS filter
   - Should see WebSocket connection to `/ws/conversations/{id}`
   - First message should contain `user_id` and `conversation_id`

---

## Summary of Changes

| Issue | File | Change | Impact |
|-------|------|--------|--------|
| 1 | `api.ts` | Add `system_prompt` parameter | Conversations can be created |
| 2 | `App.tsx` | Parse `response.data.items` | Thread list loads correctly |
| 4 | `threadUtils.ts` (NEW) | ID prefix utility functions | Consistent API calls |
| 4 | `App.tsx`, `hooks/index.ts` | Use conversion ID in API calls | Correct API URLs |
| 3 | `hooks/index.ts` | Use BackendWebSocketAdapter | WebSocket connects properly |
| 5 | `App.tsx` | Client-side title generation | Conversations get auto-titled |

---

## Files to Create
1. `/mnt/d/工作区/云开发/working/frontend/src/utils/threadUtils.ts`
2. `/mnt/d/工作区/云开发/working/frontend/src/utils/titleGenerator.ts`

## Files to Modify
1. `/mnt/d/工作区/云开发/working/frontend/src/services/api.ts`
2. `/mnt/d/工作区/云开发/working/frontend/src/App.tsx`
3. `/mnt/d/工作区/云开发/working/frontend/src/hooks/index.ts`

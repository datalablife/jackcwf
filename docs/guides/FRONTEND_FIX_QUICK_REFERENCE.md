# Frontend API Integration Fixes - Quick Reference Guide

## Quick Navigation

Five critical issues need to be fixed. Use this guide to apply patches in order.

---

## Fix 1: API Request Body - Missing system_prompt

**Problem:** Conversations can't be created because `system_prompt` is required but not sent

**Files to modify:**
- `/mnt/d/工作区/云开发/working/frontend/src/services/api.ts` (line 108-109)
- `/mnt/d/工作区/云开发/working/frontend/src/hooks/index.ts` (line 194-204)

**Changes:**

File: `api.ts`
```diff
- createConversation: (data: { title: string }) =>
-   request('POST', '/conversations', data),
+ createConversation: (data: { title: string; system_prompt?: string; model?: string; metadata?: unknown }) =>
+   request('POST', '/conversations', data),
```

File: `hooks/index.ts`
```diff
const createThread = useCallback(async (title?: string) => {
  setIsLoading(true);
  try {
-   const response = await conversationApi.createConversation({ title: title || 'New Conversation' });
+   const response = await conversationApi.createConversation({
+     title: title || 'New Conversation',
+     system_prompt: 'You are a helpful AI assistant. Provide clear, concise, and accurate responses.',
+     model: 'claude-3-5-sonnet-20241022'
+   });
    if (response.error) throw new Error(response.error.message);
    return response.data;
  } finally {
    setIsLoading(false);
  }
}, []);
```

---

## Fix 2: Response Parsing - Conversations List

**Problem:** API returns `{ items: [...], total, skip, limit }` but code expects array directly

**File to modify:**
- `/mnt/d/工作区/云开发/working/frontend/src/App.tsx` (line 49-82)

**Change:**

```diff
const loadConversations = async () => {
  try {
    setIsInitializing(true);
    const response = await conversationApi.getConversations();

-   if (response.data && Array.isArray(response.data)) {
-     const mappedThreads: typeof threads = (response.data as any[]).map((conv: any) => ({
+   // Backend returns { items: [...], total, skip, limit }
+   const conversations = response.data?.items || [];
+
+   if (Array.isArray(conversations)) {
+     const mappedThreads: typeof threads = conversations.map((conv: any) => ({
        threadId: `thread_${conv.id}`,
```

Also add type safety to `api.ts`:
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

// Update the method:
getConversations: () =>
  request<PaginatedResponse<ConversationData>>('GET', '/conversations'),
```

---

## Fix 3: WebSocket Connection - Raw Socket Issues

**Problem:** WebSocket uses hardcoded localhost, doesn't follow handshake protocol, tokens in URL

**Files to create:**
- `/mnt/d/工作区/云开发/working/frontend/src/utils/threadUtils.ts` (NEW)

**Files to modify:**
- `/mnt/d/工作区/云开发/working/frontend/src/hooks/index.ts` (line 32-88)

**Create threadUtils first:**
```typescript
// See full content in provided threadUtils.ts file
```

**Update useTypingIndicator:**
```typescript
// REPLACE the entire useTypingIndicator function with version from hooks/index.ts.fixed
// Key changes:
// - Use BackendWebSocketAdapter instead of raw WebSocket
// - Extract conversationId from threadId
// - No tokens in URL
// - Proper WebSocket protocol handshake
```

---

## Fix 4: Thread ID Format Consistency

**Problem:** Thread IDs use prefix but API calls don't strip it, causing malformed URLs

**Files to create:**
- `/mnt/d/工作区/云开发/working/frontend/src/utils/threadUtils.ts` (NEW - already created in Fix 3)

**Files to modify:**
- `/mnt/d/工作区/云开发/working/frontend/src/App.tsx` (multiple locations)
- `/mnt/d/工作区/云开发/working/frontend/src/hooks/index.ts` (multiple locations)

**In App.tsx:**
```typescript
// Add import
import { getConversationId, getConversationIdAsNumber } from './utils/threadUtils';

// In handleDeleteThread:
const handleDeleteThread = async (threadId: string) => {
  try {
    const conversationId = getConversationIdAsNumber(threadId);
    await conversationApi.deleteConversation(conversationId);
    // ...
  }
};
```

**In hooks/index.ts:**
```typescript
// Add imports
import { getConversationId, getConversationIdAsNumber } from '../utils/threadUtils';

// In useChat hook:
const sendMessage = useCallback(
  async (content: string) => {
    const conversationId = getConversationIdAsNumber(threadId);
    // Use conversationId in fetch URL, NOT threadId
    const response = await fetch(`/api/v1/conversations/${conversationId}/stream`, {
      // ...
    });
  },
  [threadId, ...]
);

// In useStreaming hook:
const streamMessage = useCallback(async (
  threadId: string,
  message: string,
  onChunk: (chunk: string) => void,
  onComplete?: () => void,
  onError?: (error: Error) => void
) => {
  const conversationId = getConversationIdAsNumber(threadId);
  const response = await fetch(`/api/v1/conversations/${conversationId}/stream`, {
    // ...
  });
}, []);
```

---

## Fix 5: Title Generation Endpoint (Non-existent)

**Problem:** Backend doesn't have `/conversations/{id}/generate-title` endpoint

**Files to create:**
- `/mnt/d/工作区/云开发/working/frontend/src/utils/titleGenerator.ts` (NEW)

**Files to modify:**
- `/mnt/d/工作区/云开发/working/frontend/src/services/api.ts` (remove generateTitle method)
- `/mnt/d/工作区/云开发/working/frontend/src/hooks/index.ts` (update useAutoTitle)
- `/mnt/d/工作区/云开发/working/frontend/src/App.tsx` (import and use titleGenerator)

**Step 1: Create titleGenerator.ts**
```typescript
// See full content in provided titleGenerator.ts file
```

**Step 2: Remove from api.ts**
```diff
// DELETE this entire method:
- generateTitle: (conversationId: string, content: string) =>
-   request('POST', `/conversations/${conversationId}/generate-title`, { content }),
```

**Step 3: Update hooks/index.ts**
```diff
+ import { generateTitleFromContent } from '../utils/titleGenerator';

export const useAutoTitle = () => {
  const { updateThread } = useThreadsStore();

  const generateTitleFromFirstMessage = useCallback(async (
    threadId: string,
    messageContent: string
  ) => {
    try {
      // FIX 5: Generate title locally instead of calling non-existent endpoint
+     const newTitle = generateTitleFromContent(messageContent);

      updateThread(threadId, { title: newTitle });

+     // Also persist to backend
+     const conversationId = getConversationIdAsNumber(threadId);
+     await conversationApi.updateConversation(conversationId, { title: newTitle });
    } catch (error) {
      console.error('Failed to generate/update title:', error);
    }
  }, [updateThread]);

- return { generateTitleFromContent };
+ return { generateTitleFromFirstMessage };
};
```

**Step 4: Update App.tsx**
```diff
+ import { generateTitleFromContent } from './utils/titleGenerator';

// In handleSendMessage:
if (!firstMessageSent.has(selectedThreadId)) {
  setFirstMessageSent(prev => new Set([...prev, selectedThreadId]));
  const threadMessages = messages[selectedThreadId] || [];
  if (threadMessages.length === 1) {
-   generateTitleFromContent(selectedThreadId, conversationId, message);
+   generateTitleFromFirstMessage(selectedThreadId, message);
  }
}
```

---

## Implementation Order

1. **First (Critical):** Fix 1 + Fix 2 (API request/response)
2. **Second:** Fix 4 (Create threadUtils, update all ID handling)
3. **Third:** Fix 5 (Create titleGenerator, remove backend endpoint)
4. **Fourth (Optional):** Fix 3 (WebSocket - for real-time features)

---

## Testing Checklist

After each fix, verify:

### Fix 1 & 2: Conversation Creation & Loading
- [ ] Click "New Conversation" - should create without error
- [ ] Check Network tab: POST `/conversations` includes `system_prompt`
- [ ] Page refresh - sidebar loads existing conversations
- [ ] Check Network tab: GET `/conversations` response structure is `{ items, total, ... }`

### Fix 4: Thread ID Handling
- [ ] Send message - Check Network tab: URL is `/conversations/123/stream` (NOT `thread_123`)
- [ ] Thread operations work correctly with various thread IDs
- [ ] No 404 errors in console

### Fix 5: Title Generation
- [ ] Create conversation and send first message
- [ ] Thread title should update to message content (not stay "New Conversation")
- [ ] No 404 errors for missing `/generate-title` endpoint

### Fix 3: WebSocket (Optional)
- [ ] Open DevTools > Network > WS filter
- [ ] Should see WebSocket connection
- [ ] First message should have proper handshake (no errors)

---

## Files Reference

**Already Provided (Copy-Paste Ready):**
1. `/mnt/d/工作区/云开发/working/frontend/src/utils/threadUtils.ts` - FULLY IMPLEMENTED
2. `/mnt/d/工作区/云开发/working/frontend/src/utils/titleGenerator.ts` - FULLY IMPLEMENTED
3. `/mnt/d/工作区/云开发/working/frontend/src/services/api.ts.fixed` - REFERENCE ONLY
4. `/mnt/d/工作区/云开发/working/frontend/src/hooks/index.ts.fixed` - REFERENCE ONLY
5. `/mnt/d/工作区/云开发/working/frontend/src/App.tsx.fixed` - REFERENCE ONLY

**To Modify:**
1. `/mnt/d/工作区/云开发/working/frontend/src/services/api.ts`
2. `/mnt/d/工作区/云开发/working/frontend/src/hooks/index.ts`
3. `/mnt/d/工作区/云开发/working/frontend/src/App.tsx`

---

## Troubleshooting

**502/503 errors on message send?**
- Fix 4: Ensure using conversationId (numeric) not threadId (with prefix) in URLs

**Conversations don't load?**
- Fix 2: Verify parsing `response.data.items` not `response.data`

**Title stays "New Conversation"?**
- Fix 5: Ensure `generateTitleFromFirstMessage` is called with correct parameters

**WebSocket won't connect?**
- Fix 3: Use BackendWebSocketAdapter with proper conversationId extraction
- Check localStorage for `user_id` and `auth_token`

---

## Complete Implementation Time

- **Fix 1 & 2:** 5 minutes
- **Fix 4:** 10 minutes
- **Fix 5:** 5 minutes
- **Fix 3:** 10 minutes (optional)
- **Testing:** 10 minutes

**Total: 30-40 minutes for full implementation**

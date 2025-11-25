/**
 * Thread ID Utility Functions
 *
 * Provides consistent handling of thread ID formatting and conversion.
 * Thread IDs have the format: "thread_<conversation_id>"
 * This utility ensures consistent usage across the application.
 */

export const THREAD_ID_PREFIX = 'thread_';

/**
 * Create a thread ID with prefix from conversation ID
 *
 * @param conversationId - The conversation ID (number or string)
 * @returns Thread ID with "thread_" prefix
 *
 * @example
 * createThreadId(123) // returns "thread_123"
 */
export const createThreadId = (conversationId: number | string): string => {
  return `${THREAD_ID_PREFIX}${conversationId}`;
};

/**
 * Extract conversation ID from thread ID
 * Safely removes the "thread_" prefix if present
 *
 * @param threadId - The thread ID (with or without prefix)
 * @returns Conversation ID without prefix
 *
 * @example
 * getConversationId("thread_123") // returns "123"
 * getConversationId("123") // returns "123"
 */
export const getConversationId = (threadId: string): string => {
  if (threadId.startsWith(THREAD_ID_PREFIX)) {
    return threadId.substring(THREAD_ID_PREFIX.length);
  }
  return threadId;
};

/**
 * Get conversation ID as number
 * Useful for numeric API endpoints
 *
 * @param threadId - The thread ID
 * @returns Conversation ID as number
 *
 * @example
 * getConversationIdAsNumber("thread_123") // returns 123
 */
export const getConversationIdAsNumber = (threadId: string): number => {
  const id = getConversationId(threadId);
  return parseInt(id, 10);
};

/**
 * Ensure thread ID has the correct format
 * Idempotent: can be called multiple times safely
 *
 * @param id - The ID (with or without prefix)
 * @returns Thread ID with proper format
 *
 * @example
 * ensureThreadId("123") // returns "thread_123"
 * ensureThreadId("thread_123") // returns "thread_123"
 */
export const ensureThreadId = (id: string | number): string => {
  const idStr = String(id);
  return idStr.startsWith(THREAD_ID_PREFIX) ? idStr : createThreadId(idStr);
};

/**
 * Check if a string is a valid thread ID format
 *
 * @param id - The ID to check
 * @returns True if the ID has the "thread_" prefix
 *
 * @example
 * isThreadId("thread_123") // returns true
 * isThreadId("123") // returns false
 */
export const isThreadId = (id: string): boolean => {
  return id.startsWith(THREAD_ID_PREFIX) && id.length > THREAD_ID_PREFIX.length;
};

/**
 * Compare two thread IDs regardless of format
 * Safely compares IDs even if one has prefix and one doesn't
 *
 * @param threadId1 - First thread ID
 * @param threadId2 - Second thread ID
 * @returns True if both IDs refer to the same conversation
 *
 * @example
 * compareThreadIds("thread_123", "123") // returns true
 * compareThreadIds("thread_123", "thread_123") // returns true
 */
export const compareThreadIds = (threadId1: string, threadId2: string): boolean => {
  return getConversationId(threadId1) === getConversationId(threadId2);
};

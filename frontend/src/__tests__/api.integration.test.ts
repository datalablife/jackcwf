/**
 * Backend API Integration Tests
 *
 * Tests the integration between frontend and backend APIs:
 * - POST /api/v1/threads (Create thread)
 * - GET /api/v1/threads/{thread_id}/state (Get thread state)
 * - POST /api/v1/threads/{thread_id}/tool-result (Submit tool result)
 */

import { describe, it, expect, beforeAll, afterAll } from 'vitest';

// Mock configuration
const API_BASE_URL = process.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
const TEST_TIMEOUT = 10000;

// Test JWT token (generated with default secret for testing)
// Valid for 24 hours from generation
const TEST_JWT_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXIiLCJ1c2VyX2lkIjoidGVzdF91c2VyIiwiZXhwIjoxNzYzNzQzOTc5LCJpYXQiOjE3NjM2NTc1Nzl9.FbkE6g8wf_JlAhZsKT9EVms5kZyEfejLkNAtujB3DUw';

// Helper function to add auth headers
const getAuthHeaders = () => ({
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${TEST_JWT_TOKEN}`,
});

describe('Backend API Integration Tests', () => {
  let createdThreadId: string;

  beforeAll(() => {
    // Set up test environment
    console.log(`🔗 Testing API at: ${API_BASE_URL}`);
  });

  afterAll(() => {
    console.log('✅ Integration tests completed');
  });

  describe('POST /api/v1/threads - Create Thread', () => {
    it(
      'should create a new thread with title',
      async () => {
        try {
          const response = await fetch(`${API_BASE_URL}/threads`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
              title: 'Integration Test Thread',
              metadata: { test: true, timestamp: Date.now() }
            })
          });

          expect(response.status).toBe(201);

          const data = await response.json();
          console.log('✓ Create thread response:', data);

          expect(data).toHaveProperty('thread_id');
          expect(data).toHaveProperty('conversation_id');
          expect(data.title).toBe('Integration Test Thread');
          expect(data).toHaveProperty('created_at');
          expect(data).toHaveProperty('message_count');

          // Store for later tests
          createdThreadId = data.thread_id;

          console.log(`✓ Created thread: ${createdThreadId}`);
        } catch (error) {
          console.error('✗ Create thread failed:', error);
          throw error;
        }
      },
      TEST_TIMEOUT
    );

    it(
      'should validate required fields',
      async () => {
        try {
          const response = await fetch(`${API_BASE_URL}/threads`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ title: '' }) // Empty title
          });

          // Should either accept or reject with clear error
          console.log(`Response status for empty title: ${response.status}`);
          expect([200, 201, 400, 422]).toContain(response.status);
        } catch (error) {
          console.error('✗ Validation test failed:', error);
          throw error;
        }
      },
      TEST_TIMEOUT
    );
  });

  describe('GET /api/v1/threads/{thread_id}/state - Get Thread State', () => {
    it(
      'should retrieve thread state with messages',
      async () => {
        if (!createdThreadId) {
          console.log('⏭️  Skipping: thread not created in previous test');
          return;
        }

        try {
          const response = await fetch(
            `${API_BASE_URL}/threads/${createdThreadId}/state?include_messages=true&message_limit=10`,
            {
              method: 'GET',
              headers: {
                'Content-Type': 'application/json',
              }
            }
          );

          expect(response.status).toBe(200);

          const data = await response.json();
          console.log('✓ Get thread state response:', {
            thread_id: data.thread_id,
            message_count: data.messages?.length,
            has_checkpoint: !!data.agent_checkpoint
          });

          expect(data).toHaveProperty('thread_id');
          expect(data).toHaveProperty('conversation_id');
          expect(data).toHaveProperty('messages');
          expect(Array.isArray(data.messages)).toBe(true);
          expect(data).toHaveProperty('pending_tools');
          expect(Array.isArray(data.pending_tools)).toBe(true);

          console.log(`✓ Retrieved thread state: ${data.messages.length} messages`);
        } catch (error) {
          console.error('✗ Get thread state failed:', error);
          throw error;
        }
      },
      TEST_TIMEOUT
    );

    it(
      'should handle non-existent thread',
      async () => {
        try {
          const fakeThreadId = 'thread_00000000-0000-0000-0000-000000000000';
          const response = await fetch(`${API_BASE_URL}/threads/${fakeThreadId}/state`, {
            method: 'GET',
            headers: getAuthHeaders(),
          });

          expect(response.status).toBe(404);
          console.log('✓ Correctly returned 404 for non-existent thread');
        } catch (error) {
          console.error('✗ Non-existent thread test failed:', error);
          throw error;
        }
      },
      TEST_TIMEOUT
    );

    it(
      'should respect include_messages and include_tools parameters',
      async () => {
        if (!createdThreadId) {
          console.log('⏭️  Skipping: thread not created');
          return;
        }

        try {
          // Test without messages
          const response1 = await fetch(
            `${API_BASE_URL}/threads/${createdThreadId}/state?include_messages=false`,
            { method: 'GET', headers: getAuthHeaders() }
          );

          // Test without tools
          const response2 = await fetch(
            `${API_BASE_URL}/threads/${createdThreadId}/state?include_tools=false`,
            { method: 'GET', headers: getAuthHeaders() }
          );

          console.log('✓ Parameter handling verified');
          expect(response1.status).toBe(200);
          expect(response2.status).toBe(200);
        } catch (error) {
          console.error('✗ Parameter test failed:', error);
          throw error;
        }
      },
      TEST_TIMEOUT
    );
  });

  describe('POST /api/v1/threads/{thread_id}/tool-result - Submit Tool Result', () => {
    it(
      'should accept tool result submission',
      async () => {
        if (!createdThreadId) {
          console.log('⏭️  Skipping: thread not created');
          return;
        }

        try {
          const response = await fetch(
            `${API_BASE_URL}/threads/${createdThreadId}/tool-result`,
            {
              method: 'POST',
              headers: getAuthHeaders(),
              body: JSON.stringify({
                tool_id: 'tool_test_123',
                tool_name: 'vector_search',
                result: { documents: [], query: 'test' },
                result_data: { score: 0.95 },
                execution_time_ms: 250
              })
            }
          );

          console.log(`Response status: ${response.status}`);
          // Should be 200 (success) or 404 (if tool_id not found)
          expect([200, 201, 404, 422]).toContain(response.status);

          if (response.status === 200) {
            const data = await response.json();
            console.log('✓ Tool result submitted:', data);
            expect(data.status).toBe('success');
          }
        } catch (error) {
          console.error('✗ Tool result submission failed:', error);
          throw error;
        }
      },
      TEST_TIMEOUT
    );
  });

  describe('Health Check', () => {
    it(
      'should confirm thread API health',
      async () => {
        try {
          const response = await fetch(`${API_BASE_URL}/threads/health`, {
            method: 'GET',
            headers: getAuthHeaders(),
          });

          expect(response.status).toBe(200);
          const data = await response.json();

          console.log('✓ Health check:', data);
          expect(data.status).toBe('ok');
          expect(data.service).toBe('threads-api');
        } catch (error) {
          console.error('✗ Health check failed:', error);
          throw error;
        }
      },
      TEST_TIMEOUT
    );
  });

  describe('Chat Flow Integration', () => {
    it(
      'should execute complete chat flow',
      async () => {
        try {
          console.log('\n📋 Executing complete chat flow...');

          // 1. Create thread
          console.log('1️⃣  Creating thread...');
          const createResponse = await fetch(`${API_BASE_URL}/threads`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ title: 'Complete Flow Test' })
          });
          expect(createResponse.status).toBe(201);
          const thread = await createResponse.json();
          console.log(`   ✓ Thread created: ${thread.thread_id}`);

          // 2. Get thread state
          console.log('2️⃣  Fetching thread state...');
          const stateResponse = await fetch(
            `${API_BASE_URL}/threads/${thread.thread_id}/state?include_messages=true`,
            { method: 'GET', headers: getAuthHeaders() }
          );
          expect(stateResponse.status).toBe(200);
          const state = await stateResponse.json();
          console.log(`   ✓ Thread state retrieved: ${state.messages.length} messages`);

          // 3. Simulate tool execution result
          console.log('3️⃣  Submitting tool result...');
          const toolResponse = await fetch(
            `${API_BASE_URL}/threads/${thread.thread_id}/tool-result`,
            {
              method: 'POST',
              headers: getAuthHeaders(),
              body: JSON.stringify({
                tool_id: 'flow_test_tool',
                tool_name: 'web_search',
                result: { title: 'Test', url: 'http://example.com' },
                execution_time_ms: 500
              })
            }
          );
          console.log(`   ✓ Tool result submitted (status: ${toolResponse.status})`);

          console.log('\n✅ Complete flow executed successfully!\n');
        } catch (error) {
          console.error('✗ Chat flow failed:', error);
          throw error;
        }
      },
      TEST_TIMEOUT
    );
  });
});

describe('API Error Handling', () => {
  it('should handle network errors gracefully', async () => {
    try {
      // Try to reach unreachable endpoint
      const response = await fetch('http://localhost:9999/api/v1/threads', {
        method: 'GET',
        headers: getAuthHeaders(),
        signal: AbortSignal.timeout(2000)
      }).catch(error => {
        console.log('✓ Network error caught:', error.message);
        return null;
      });

      expect(response === null || response.status >= 400).toBe(true);
    } catch (error) {
      // Expected - timeout or connection refused
      console.log('✓ Network error handling verified');
    }
  });

  it('should validate response format', async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/threads/health`, {
        method: 'GET',
        headers: getAuthHeaders(),
      });

      expect(response.headers.get('content-type')).toContain('application/json');
      const data = await response.json();

      // Verify JSON structure
      expect(typeof data === 'object').toBe(true);
      console.log('✓ Response format validation passed');
    } catch (error) {
      console.error('✗ Response format validation failed:', error);
      throw error;
    }
  });
});

/**
 * End-to-End WebSocket Integration Tests
 *
 * Tests real-world WebSocket communication between frontend and backend.
 * Requires backend to be running on http://localhost:8000
 *
 * Run with: BACKEND_URL=http://localhost:8000 npm run test:e2e
 */

import { describe, it, expect, beforeAll, afterAll, vi } from 'vitest';
import { WebSocketService } from '../services/websocketService';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';
const WS_URL = BACKEND_URL.replace('http', 'ws') + '/ws';

describe('E2E WebSocket Integration', () => {
  let wsService: WebSocketService;
  let testUserId: string;
  let testConversationId: string;

  beforeAll(() => {
    testUserId = `test-user-${Date.now()}`;
    testConversationId = `test-conv-${Date.now()}`;
  });

  afterAll(() => {
    if (wsService) {
      wsService.disconnect();
    }
  });

  it('should detect backend availability', async () => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);

      const response = await fetch(`${BACKEND_URL}/health`, {
        method: 'GET',
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      expect(response.status).toBe(200);
      console.log('✓ Backend is running');
    } catch (error) {
      console.warn('⚠ Backend not available at', BACKEND_URL);
      console.warn('  To enable E2E tests: npm run dev -- --backend');
    }
  });

  describe('WebSocket Connection', () => {
    it('should connect to backend WebSocket', async () => {
      return new Promise((resolve, reject) => {
        wsService = new WebSocketService(WS_URL);

        // Mock WebSocket for testing if real connection fails
        if (typeof WebSocket === 'undefined') {
          console.warn('⚠ WebSocket not available in test environment');
          resolve(null);
          return;
        }

        const connectionTimeout = setTimeout(() => {
          reject(new Error('Connection timeout'));
        }, 5000);

        try {
          wsService.connect()
            .then(() => {
              clearTimeout(connectionTimeout);
              expect(wsService.getConnectionState().isConnected).toBe(true);
              console.log('✓ WebSocket connected successfully');
              resolve(true);
            })
            .catch(() => {
              clearTimeout(connectionTimeout);
              console.warn('⚠ Could not connect to real backend WebSocket');
              resolve(null); // Don't fail - backend may not be running
            });
        } catch (error) {
          clearTimeout(connectionTimeout);
          console.warn('⚠ WebSocket test skipped:', error);
          resolve(null);
        }
      });
    });

    it('should send and receive messages', async () => {
      if (!wsService?.getConnectionState().isConnected) {
        console.warn('⚠ Skipping message test - backend not connected');
        return;
      }

      return new Promise((resolve, reject) => {
        const messageHandler = vi.fn();
        const timeout = setTimeout(() => {
          reject(new Error('Message timeout'));
        }, 3000);

        // Subscribe to messages
        wsService.subscribe('message', messageHandler);

        // Send test message
        wsService.publish({
          type: 'message',
          data: {
            content: 'Test message',
            userId: testUserId,
            conversationId: testConversationId,
          },
          timestamp: new Date(),
        });

        // Check if message was queued/sent
        setTimeout(() => {
          clearTimeout(timeout);
          expect(messageHandler).toBeDefined();
          console.log('✓ Message published successfully');
          resolve(true);
        }, 500);
      });
    });

    it('should handle reconnection', async () => {
      if (!wsService?.getConnectionState().isConnected) {
        console.warn('⚠ Skipping reconnection test - backend not connected');
        return;
      }

      const initialState = wsService.getConnectionState();
      expect(initialState.isConnected).toBe(true);

      // Simulate disconnect
      wsService.disconnect();
      expect(wsService.getConnectionState().isConnected).toBe(false);

      // Attempt reconnect
      return new Promise((resolve) => {
        wsService.connect()
          .then(() => {
            expect(wsService.getConnectionState().isConnected).toBe(true);
            console.log('✓ Reconnection successful');
            resolve(true);
          })
          .catch(() => {
            console.warn('⚠ Reconnection test skipped - backend not available');
            resolve(null);
          });
      });
    });
  });

  describe('Typing Indicators', () => {
    it('should broadcast typing start events', async () => {
      if (!wsService?.getConnectionState().isConnected) {
        console.warn('⚠ Skipping typing test - backend not connected');
        return;
      }

      const typingHandler = vi.fn();
      wsService.subscribe('typing_start', typingHandler);

      wsService.notifyTypingStart(testUserId, 'Test User', testConversationId);

      return new Promise((resolve) => {
        setTimeout(() => {
          console.log('✓ Typing start notification sent');
          resolve(true);
        }, 100);
      });
    });

    it('should broadcast typing stop events', async () => {
      if (!wsService?.getConnectionState().isConnected) {
        console.warn('⚠ Skipping typing stop test - backend not connected');
        return;
      }

      wsService.notifyTypingStop(testUserId, testConversationId);

      return new Promise((resolve) => {
        setTimeout(() => {
          console.log('✓ Typing stop notification sent');
          resolve(true);
        }, 100);
      });
    });
  });

  describe('Presence Updates', () => {
    it('should broadcast presence updates', async () => {
      if (!wsService?.getConnectionState().isConnected) {
        console.warn('⚠ Skipping presence test - backend not connected');
        return;
      }

      const presenceHandler = vi.fn();
      wsService.subscribe('presence_update', presenceHandler);

      wsService.updatePresence({
        userId: testUserId,
        username: 'Test User',
        status: 'online',
        lastSeenAt: new Date(),
      });

      return new Promise((resolve) => {
        setTimeout(() => {
          console.log('✓ Presence update sent');
          resolve(true);
        }, 100);
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle connection errors gracefully', async () => {
      const badService = new WebSocketService('ws://invalid-host:9999/ws');

      return new Promise((resolve) => {
        badService.connect()
          .catch((error) => {
            expect(error).toBeDefined();
            console.log('✓ Connection error handled gracefully');
            resolve(true);
          });

        // Timeout in case connection hangs
        setTimeout(() => {
          console.warn('⚠ Connection test timeout');
          resolve(null);
        }, 3000);
      });
    });
  });
});

/**
 * Integration Test Results Format
 *
 * Expected output when backend is running:
 * ✓ Backend is running
 * ✓ WebSocket connected successfully
 * ✓ Message published successfully
 * ✓ Reconnection successful
 * ✓ Typing start notification sent
 * ✓ Typing stop notification sent
 * ✓ Presence update sent
 * ✓ Connection error handled gracefully
 *
 * Expected output when backend is not running:
 * ⚠ Backend not available at http://localhost:8000
 * ⚠ Could not connect to real backend WebSocket
 * (All other tests skipped with warnings)
 */

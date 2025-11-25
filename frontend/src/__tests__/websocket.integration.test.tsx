/**
 * WebSocket Integration Tests
 *
 * Tests for WebSocket service and useWebSocket hook
 * Covers:
 * - Connection management
 * - Event publishing and subscription
 * - Typing indicators
 * - Presence detection
 * - Error handling and reconnection
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import {
  WebSocketService,
  closeWebSocketService,
} from '../services/websocketService';
import { useWebSocket, useTypingIndicator } from '../hooks/useWebSocket';
import { WebSocketEvent, ChatMessage, PresenceUser } from '../types';

describe('WebSocketService', () => {
  let wsService: WebSocketService;
  let mockWs: any;

  beforeEach(() => {
    // Mock WebSocket
    mockWs = {
      readyState: 1, // OPEN
      send: vi.fn(),
      close: vi.fn(),
      onopen: null,
      onclose: null,
      onerror: null,
      onmessage: null,
    };

    global.WebSocket = vi.fn(() => mockWs) as any;

    wsService = new WebSocketService('ws://localhost:8000/ws');
  });

  afterEach(() => {
    if (wsService) {
      wsService.disconnect();
    }
    vi.clearAllMocks();
  });

  describe('Connection Management', () => {
    it('connects to WebSocket server', async () => {
      const promise = wsService.connect();

      expect(wsService.getConnectionState().isConnecting).toBe(true);

      mockWs.onopen();

      await promise;

      expect(wsService.getConnectionState().isConnected).toBe(true);
      expect(wsService.getConnectionState().isConnecting).toBe(false);
    });

    it('does not connect twice', async () => {
      const promise1 = wsService.connect();
      const promise2 = wsService.connect();

      mockWs.onopen();

      await promise1;
      await promise2;

      expect(wsService.getConnectionState().isConnected).toBe(true);
    });

    it('handles connection errors', async () => {
      const errorPromise = wsService.connect();

      mockWs.onerror('Connection failed');

      try {
        await errorPromise;
        expect.fail('Should have thrown');
      } catch (e) {
        expect(wsService.getConnectionState().error).toBeDefined();
      }
    });

    it('disconnects from WebSocket server', async () => {
      const promise = wsService.connect();
      mockWs.onopen();
      await promise;

      wsService.disconnect();

      expect(wsService.getConnectionState().isConnected).toBe(false);
      expect(mockWs.close).toHaveBeenCalled();
    });
  });

  describe('Event Publishing and Subscription', () => {
    it('publishes events', async () => {
      const promise = wsService.connect();
      mockWs.onopen();
      await promise;

      const event: WebSocketEvent = {
        type: 'message',
        data: { text: 'Hello' },
        timestamp: new Date(),
      };

      wsService.publish(event);

      expect(mockWs.send).toHaveBeenCalledWith(JSON.stringify(event));
    });

    it('queues messages before connection', () => {
      const event: WebSocketEvent = {
        type: 'message',
        data: { text: 'Hello' },
        timestamp: new Date(),
      };

      wsService.publish(event);

      // Message should be queued
      expect(mockWs.send).not.toHaveBeenCalled();
    });

    it('subscribes to events', async () => {
      const handler = vi.fn();
      const unsubscribe = wsService.subscribe('message', handler);

      const event: WebSocketEvent = {
        type: 'message',
        data: { text: 'Hello' },
        timestamp: new Date(),
      };

      const promise = wsService.connect();
      mockWs.onopen();
      await promise;

      mockWs.onmessage({ data: JSON.stringify(event) });

      expect(handler).toHaveBeenCalledWith(expect.objectContaining({ type: 'message' }));

      unsubscribe();
    });

    it('unsubscribes from events', async () => {
      const handler = vi.fn();
      const unsubscribe = wsService.subscribe('message', handler);
      unsubscribe();

      const event: WebSocketEvent = {
        type: 'message',
        data: { text: 'Hello' },
        timestamp: new Date(),
      };

      const promise = wsService.connect();
      mockWs.onopen();
      await promise;

      mockWs.onmessage({ data: JSON.stringify(event) });

      expect(handler).not.toHaveBeenCalled();
    });
  });

  describe('Typing Indicators', () => {
    it('notifies typing start', async () => {
      const promise = wsService.connect();
      mockWs.onopen();
      await promise;

      wsService.notifyTypingStart('user1', 'Alice', 'thread1');

      expect(mockWs.send).toHaveBeenCalledWith(
        expect.stringContaining('"type":"typing_start"'),
      );
    });

    it('notifies typing stop', async () => {
      const promise = wsService.connect();
      mockWs.onopen();
      await promise;

      wsService.notifyTypingStop('user1', 'thread1');

      expect(mockWs.send).toHaveBeenCalledWith(expect.stringContaining('"type":"typing_stop"'));
    });
  });

  describe('Presence Detection', () => {
    it('updates presence', async () => {
      const promise = wsService.connect();
      mockWs.onopen();
      await promise;

      const user: PresenceUser = {
        userId: 'user1',
        username: 'Alice',
        status: 'online',
        lastSeenAt: new Date(),
      };

      wsService.updatePresence(user);

      expect(mockWs.send).toHaveBeenCalledWith(
        expect.stringContaining('"type":"presence_update"'),
      );
    });

    it('handles presence updates', async () => {
      const handler = vi.fn();
      wsService.subscribe('presence_update', handler);

      const promise = wsService.connect();
      mockWs.onopen();
      await promise;

      const event: WebSocketEvent = {
        type: 'presence_update',
        data: {
          userId: 'user1',
          username: 'Alice',
          status: 'online',
          lastSeenAt: new Date(),
        },
        timestamp: new Date(),
      };

      mockWs.onmessage({ data: JSON.stringify(event) });

      expect(handler).toHaveBeenCalled();
    });
  });

  describe('Connection State', () => {
    it('tracks connection state', async () => {
      const handler = vi.fn();
      wsService.onConnectionStateChange(handler);

      const promise = wsService.connect();

      expect(handler).toHaveBeenCalledWith(
        expect.objectContaining({ isConnecting: true, isConnected: false }),
      );

      mockWs.onopen();
      await promise;

      expect(handler).toHaveBeenCalledWith(
        expect.objectContaining({ isConnecting: false, isConnected: true }),
      );
    });
  });
});

describe('useWebSocket Hook', () => {
  let mockWs: any;

  beforeEach(() => {
    mockWs = {
      readyState: 1, // OPEN
      send: vi.fn(),
      close: vi.fn(),
      onopen: null,
      onclose: null,
      onerror: null,
      onmessage: null,
    };

    global.WebSocket = vi.fn(() => mockWs) as any;
  });

  afterEach(() => {
    closeWebSocketService();
    vi.clearAllMocks();
  });

  it('connects on mount with autoConnect=true', async () => {
    const { result } = renderHook(() => useWebSocket({ autoConnect: true }));

    expect(result.current.isConnecting).toBe(true);

    mockWs.onopen();

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });
  });

  it('does not connect on mount with autoConnect=false', async () => {
    const { result } = renderHook(() => useWebSocket({ autoConnect: false }));

    expect(result.current.isConnected).toBe(false);
    expect(result.current.isConnecting).toBe(false);
  });

  it('sends messages', async () => {
    const { result } = renderHook(() => useWebSocket({ autoConnect: true }));

    mockWs.onopen();

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    const message: ChatMessage = {
      id: '1',
      threadId: 'thread1',
      role: 'user',
      content: 'Hello',
      timestamp: new Date(),
    };

    act(() => {
      result.current.sendMessage(message);
    });

    expect(mockWs.send).toHaveBeenCalled();
  });

  it('tracks typing users', async () => {
    const { result } = renderHook(() => useWebSocket({ autoConnect: true }));

    mockWs.onopen();

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    const typingEvent: WebSocketEvent = {
      type: 'typing_start',
      data: {
        userId: 'user1',
        username: 'Alice',
        threadId: 'thread1',
        startedAt: new Date(),
      },
      timestamp: new Date(),
    };

    mockWs.onmessage({ data: JSON.stringify(typingEvent) });

    await waitFor(() => {
      expect(result.current.typingUsers.length).toBe(1);
    });
  });

  it('calls onMessage callback', async () => {
    const onMessage = vi.fn();
    const { result } = renderHook(() =>
      useWebSocket({ autoConnect: true, onMessage }),
    );

    mockWs.onopen();

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    const message: ChatMessage = {
      id: '1',
      threadId: 'thread1',
      role: 'assistant',
      content: 'Hello',
      timestamp: new Date(),
    };

    const event: WebSocketEvent = {
      type: 'message',
      data: message as unknown as Record<string, unknown>,
      timestamp: new Date(),
    };

    mockWs.onmessage({ data: JSON.stringify(event) });

    await waitFor(() => {
      expect(onMessage).toHaveBeenCalled();
    });
  });
});

describe('useTypingIndicator Hook', () => {
  let mockWs: any;

  beforeEach(() => {
    mockWs = {
      readyState: 1, // OPEN
      send: vi.fn(),
      close: vi.fn(),
      onopen: null,
      onclose: null,
      onerror: null,
      onmessage: null,
    };

    global.WebSocket = vi.fn(() => mockWs) as any;
  });

  afterEach(() => {
    closeWebSocketService();
    vi.clearAllMocks();
  });

  it('notifies typing start', async () => {
    const { result } = renderHook(() =>
      useTypingIndicator('user1', 'Alice', 'thread1', 100),
    );

    mockWs.onopen();

    act(() => {
      result.current.startTyping();
    });

    await waitFor(() => {
      expect(mockWs.send).toHaveBeenCalled();
    });
  });

  it('stops typing on unmount', async () => {
    const { unmount } = renderHook(() =>
      useTypingIndicator('user1', 'Alice', 'thread1'),
    );

    mockWs.onopen();

    unmount();

    expect(mockWs.send).toHaveBeenCalled();
  });
});

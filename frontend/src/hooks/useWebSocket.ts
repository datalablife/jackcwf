/**
 * useWebSocket Hook
 *
 * Custom React hook for WebSocket integration
 * Features:
 * - Automatic connection management
 * - Event subscription with cleanup
 * - Connection state tracking
 * - Typing indicator management
 * - Presence detection
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import {
  WebSocketEvent,
  WebSocketConnectionState,
  TypingState,
  PresenceUser,
  ChatMessage,
} from '../types';
import { getWebSocketService } from '../services/websocketService';

interface UseWebSocketOptions {
  autoConnect?: boolean;
  onMessage?: (message: ChatMessage) => void;
  onTypingStart?: (typing: TypingState) => void;
  onTypingStop?: (userId: string, threadId: string) => void;
  onPresenceUpdate?: (user: PresenceUser) => void;
  onError?: (error: string) => void;
  wsUrl?: string;
}

/**
 * useWebSocket - Hook for WebSocket communication
 *
 * Manages WebSocket connection and event handling for React components
 *
 * @param options - Configuration options
 * @returns Object with connection state, methods, and typing indicators
 */
export function useWebSocket(options: UseWebSocketOptions = {}) {
  const {
    autoConnect = true,
    onMessage,
    onTypingStart,
    onTypingStop,
    onPresenceUpdate,
    onError,
    wsUrl,
  } = options;

  const wsServiceRef = useRef(getWebSocketService(wsUrl));
  const [connectionState, setConnectionState] = useState<WebSocketConnectionState>(
    wsServiceRef.current.getConnectionState(),
  );
  const [typingUsers, setTypingUsers] = useState<Map<string, TypingState>>(new Map());
  const [presenceUsers, setPresenceUsers] = useState<Map<string, PresenceUser>>(new Map());
  const unsubscribeRef = useRef<(() => void)[]>([]);

  /**
   * Handle incoming messages
   */
  const handleMessage = useCallback(
    (event: WebSocketEvent) => {
      if (event.type === 'message' && onMessage) {
        const message = event.data as unknown as ChatMessage;
        onMessage(message);
      }
    },
    [onMessage],
  );

  /**
   * Handle typing start events
   */
  const handleTypingStart = useCallback(
    (event: WebSocketEvent) => {
      const typing = event.data as unknown as TypingState;
      setTypingUsers((prev) => new Map(prev).set(typing.userId, typing));

      if (onTypingStart) {
        onTypingStart(typing);
      }
    },
    [onTypingStart],
  );

  /**
   * Handle typing stop events
   */
  const handleTypingStop = useCallback(
    (event: WebSocketEvent) => {
      const { userId } = event.data as { userId: string };
      setTypingUsers((prev) => {
        const next = new Map(prev);
        next.delete(userId);
        return next;
      });

      if (onTypingStop) {
        onTypingStop(userId, event.data.threadId as string);
      }
    },
    [onTypingStop],
  );

  /**
   * Handle presence updates
   */
  const handlePresenceUpdate = useCallback(
    (event: WebSocketEvent) => {
      const user = event.data as unknown as PresenceUser;
      setPresenceUsers((prev) => new Map(prev).set(user.userId, user));

      if (onPresenceUpdate) {
        onPresenceUpdate(user);
      }
    },
    [onPresenceUpdate],
  );

  /**
   * Handle connection state changes
   */
  const handleConnectionStateChange = useCallback(
    (state: WebSocketConnectionState) => {
      setConnectionState(state);

      if (state.error && onError) {
        onError(state.error);
      }
    },
    [onError],
  );

  /**
   * Connect to WebSocket
   */
  const connect = useCallback(async () => {
    try {
      await wsServiceRef.current.connect();
    } catch (error) {
      const errorMsg = `Failed to connect: ${error}`;
      if (onError) {
        onError(errorMsg);
      }
    }
  }, [onError]);

  /**
   * Disconnect from WebSocket
   */
  const disconnect = useCallback(() => {
    wsServiceRef.current.disconnect();
  }, []);

  /**
   * Send a chat message
   */
  const sendMessage = useCallback((message: ChatMessage) => {
    wsServiceRef.current.publish({
      type: 'message',
      data: message as unknown as Record<string, unknown>,
      timestamp: new Date(),
    });
  }, []);

  /**
   * Notify typing start
   */
  const notifyTypingStart = useCallback((userId: string, username: string, threadId: string) => {
    wsServiceRef.current.notifyTypingStart(userId, username, threadId);
  }, []);

  /**
   * Notify typing stop
   */
  const notifyTypingStop = useCallback((userId: string, threadId: string) => {
    wsServiceRef.current.notifyTypingStop(userId, threadId);
  }, []);

  /**
   * Update presence
   */
  const updatePresence = useCallback((user: PresenceUser) => {
    wsServiceRef.current.updatePresence(user);
  }, []);

  /**
   * Get typing users array
   */
  const getTypingUsersArray = useCallback(() => {
    return Array.from(typingUsers.values());
  }, [typingUsers]);

  /**
   * Get presence users array
   */
  const getPresenceUsersArray = useCallback(() => {
    return Array.from(presenceUsers.values());
  }, [presenceUsers]);

  /**
   * Set up event subscriptions
   */
  useEffect(() => {
    // Subscribe to events
    const unsubscribers: (() => void)[] = [];

    unsubscribers.push(
      wsServiceRef.current.subscribe('message', handleMessage),
      wsServiceRef.current.subscribe('typing_start', handleTypingStart),
      wsServiceRef.current.subscribe('typing_stop', handleTypingStop),
      wsServiceRef.current.subscribe('presence_update', handlePresenceUpdate),
      wsServiceRef.current.onConnectionStateChange(handleConnectionStateChange),
    );

    unsubscribeRef.current = unsubscribers;

    // Auto-connect if enabled
    if (autoConnect && !connectionState.isConnected && !connectionState.isConnecting) {
      connect();
    }

    // Cleanup subscriptions on unmount
    return () => {
      unsubscribeRef.current.forEach((unsubscribe) => {
        unsubscribe();
      });
    };
  }, [
    autoConnect,
    connectionState.isConnected,
    connectionState.isConnecting,
    connect,
    handleMessage,
    handleTypingStart,
    handleTypingStop,
    handlePresenceUpdate,
    handleConnectionStateChange,
  ]);

  return {
    // Connection state
    isConnected: connectionState.isConnected,
    isConnecting: connectionState.isConnecting,
    error: connectionState.error,
    lastConnectedAt: connectionState.lastConnectedAt,
    reconnectAttempts: connectionState.reconnectAttempts,

    // Methods
    connect,
    disconnect,
    sendMessage,
    notifyTypingStart,
    notifyTypingStop,
    updatePresence,

    // State getters
    typingUsers: getTypingUsersArray(),
    presenceUsers: getPresenceUsersArray(),
  };
}

/**
 * Custom hook for managing typing indicator
 *
 * @param userId - Current user ID
 * @param username - Current user name
 * @param threadId - Current thread ID
 * @param debounceMs - Debounce delay in milliseconds
 * @returns Object with typing state and handlers
 */
export function useTypingIndicator(
  userId: string,
  username: string,
  threadId: string,
  debounceMs: number = 300,
) {
  const ws = useWebSocket();
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isTypingRef = useRef(false);

  /**
   * Start typing
   */
  const startTyping = useCallback(() => {
    if (!isTypingRef.current) {
      isTypingRef.current = true;
      ws.notifyTypingStart(userId, username, threadId);
    }

    // Reset timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    // Stop typing after debounce delay
    typingTimeoutRef.current = setTimeout(() => {
      stopTyping();
    }, debounceMs);
  }, [userId, username, threadId, ws, debounceMs]);

  /**
   * Stop typing
   */
  const stopTyping = useCallback(() => {
    if (isTypingRef.current) {
      isTypingRef.current = false;
      ws.notifyTypingStop(userId, threadId);
    }

    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
      typingTimeoutRef.current = null;
    }
  }, [userId, threadId, ws]);

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      stopTyping();
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
    };
  }, [stopTyping]);

  return {
    startTyping,
    stopTyping,
    isTyping: isTypingRef.current,
    typingUsers: ws.typingUsers,
  };
}

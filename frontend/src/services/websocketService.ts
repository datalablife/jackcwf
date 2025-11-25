/**
 * WebSocket Service
 *
 * Manages WebSocket connections for real-time communication
 * Features:
 * - Automatic connection management
 * - Reconnection with exponential backoff
 * - Event subscription and publishing
 * - Typing indicators and presence detection
 * - Connection state tracking
 */

import {
  WebSocketEvent,
  WebSocketEventType,
  TypingState,
  PresenceUser,
  WebSocketConnectionState,
} from '../types';

type EventHandler = (event: WebSocketEvent) => void;
type ConnectionHandler = (state: WebSocketConnectionState) => void;

export class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectDelayMs: number = 1000;
  private messageQueue: WebSocketEvent[] = [];
  private eventHandlers: Map<WebSocketEventType, Set<EventHandler>> = new Map();
  private connectionHandlers: Set<ConnectionHandler> = new Set();
  private typingTimeouts: Map<string, NodeJS.Timeout> = new Map();
  private connectionState: WebSocketConnectionState = {
    isConnected: false,
    isConnecting: false,
    reconnectAttempts: 0,
    error: undefined,
  };
  private heartbeatInterval: NodeJS.Timeout | null = null;

  constructor(url: string) {
    this.url = url;
  }

  /**
   * Connect to WebSocket server
   */
  public connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.connectionState.isConnected || this.connectionState.isConnecting) {
        resolve();
        return;
      }

      this.connectionState.isConnecting = true;
      this.notifyConnectionStateChange();

      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          this.connectionState.isConnected = true;
          this.connectionState.isConnecting = false;
          this.connectionState.lastConnectedAt = new Date();
          this.connectionState.reconnectAttempts = 0;
          this.connectionState.error = undefined;
          this.reconnectAttempts = 0;

          this.notifyConnectionStateChange();
          this.flushMessageQueue();
          this.startHeartbeat();

          resolve();
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(event.data);
        };

        this.ws.onerror = (error) => {
          const errorMsg = `WebSocket error: ${error}`;
          this.connectionState.error = errorMsg;
          this.notifyConnectionStateChange();

          this.publish({
            type: 'error',
            data: { error: errorMsg },
            timestamp: new Date(),
          });

          reject(new Error(errorMsg));
        };

        this.ws.onclose = () => {
          this.connectionState.isConnected = false;
          this.connectionState.isConnecting = false;
          this.stopHeartbeat();
          this.notifyConnectionStateChange();

          this.attemptReconnect();
        };
      } catch (error) {
        const errorMsg = `Failed to create WebSocket: ${error}`;
        this.connectionState.error = errorMsg;
        this.connectionState.isConnecting = false;
        this.notifyConnectionStateChange();
        reject(new Error(errorMsg));
      }
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  public disconnect(): void {
    this.stopHeartbeat();

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.connectionState.isConnected = false;
    this.connectionState.isConnecting = false;
    this.notifyConnectionStateChange();
  }

  /**
   * Publish a WebSocket event
   */
  public publish(event: WebSocketEvent): void {
    if (!this.connectionState.isConnected) {
      this.messageQueue.push(event);
      return;
    }

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(event));
      } catch (error) {
        console.error('Failed to send message:', error);
        this.messageQueue.push(event);
      }
    } else {
      this.messageQueue.push(event);
    }
  }

  /**
   * Subscribe to WebSocket events
   */
  public subscribe(
    type: WebSocketEventType,
    handler: EventHandler,
  ): () => void {
    if (!this.eventHandlers.has(type)) {
      this.eventHandlers.set(type, new Set());
    }

    this.eventHandlers.get(type)!.add(handler);

    // Return unsubscribe function
    return () => {
      const handlers = this.eventHandlers.get(type);
      if (handlers) {
        handlers.delete(handler);
      }
    };
  }

  /**
   * Subscribe to connection state changes
   */
  public onConnectionStateChange(handler: ConnectionHandler): () => void {
    this.connectionHandlers.add(handler);

    // Return unsubscribe function
    return () => {
      this.connectionHandlers.delete(handler);
    };
  }

  /**
   * Notify all subscribers of a new event
   */
  private notifyEvent(event: WebSocketEvent): void {
    const handlers = this.eventHandlers.get(event.type);
    if (handlers) {
      handlers.forEach((handler) => {
        try {
          handler(event);
        } catch (error) {
          console.error('Error in event handler:', error);
        }
      });
    }

    // Also notify 'any' handlers if implemented
    const anyHandlers = this.eventHandlers.get('message');
    if (anyHandlers && event.type !== 'message') {
      anyHandlers.forEach((handler) => {
        try {
          handler(event);
        } catch (error) {
          console.error('Error in event handler:', error);
        }
      });
    }
  }

  /**
   * Notify all subscribers of connection state change
   */
  private notifyConnectionStateChange(): void {
    this.connectionHandlers.forEach((handler) => {
      try {
        handler(this.connectionState);
      } catch (error) {
        console.error('Error in connection handler:', error);
      }
    });
  }

  /**
   * Handle incoming WebSocket message
   */
  private handleMessage(data: string): void {
    try {
      const event = JSON.parse(data) as WebSocketEvent;
      event.timestamp = new Date(event.timestamp);

      // Handle typing indicators with auto-timeout
      if (event.type === 'typing_start') {
        const typingState = event.data as unknown as TypingState;
        const key = `${typingState.userId}-${typingState.threadId}`;

        // Clear existing timeout
        const existingTimeout = this.typingTimeouts.get(key);
        if (existingTimeout) {
          clearTimeout(existingTimeout);
        }

        // Set 3-second timeout for typing indicator
        const timeout = setTimeout(() => {
          this.publish({
            type: 'typing_stop',
            data: { userId: typingState.userId, threadId: typingState.threadId },
            timestamp: new Date(),
          });
          this.typingTimeouts.delete(key);
        }, 3000);

        this.typingTimeouts.set(key, timeout);
      }

      this.notifyEvent(event);
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }

  /**
   * Flush queued messages when connection is established
   */
  private flushMessageQueue(): void {
    while (this.messageQueue.length > 0) {
      const event = this.messageQueue.shift();
      if (event) {
        this.publish(event);
      }
    }
  }

  /**
   * Attempt to reconnect with exponential backoff
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.connectionState.error = 'Max reconnect attempts reached';
      this.notifyConnectionStateChange();
      return;
    }

    this.reconnectAttempts++;
    this.connectionState.reconnectAttempts = this.reconnectAttempts;
    this.notifyConnectionStateChange();

    const delay = this.reconnectDelayMs * Math.pow(2, this.reconnectAttempts - 1);

    setTimeout(() => {
      this.connect().catch((error) => {
        console.error('Reconnection failed:', error);
      });
    }, delay);
  }

  /**
   * Start sending heartbeat to keep connection alive
   */
  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.connectionState.isConnected && this.ws?.readyState === WebSocket.OPEN) {
        try {
          this.ws.send(JSON.stringify({ type: 'ping', timestamp: new Date() }));
        } catch (error) {
          console.error('Failed to send heartbeat:', error);
        }
      }
    }, 30000); // Every 30 seconds
  }

  /**
   * Stop heartbeat
   */
  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * Get current connection state
   */
  public getConnectionState(): WebSocketConnectionState {
    return { ...this.connectionState };
  }

  /**
   * Notify typing start
   */
  public notifyTypingStart(userId: string, username: string, threadId: string): void {
    this.publish({
      type: 'typing_start',
      data: { userId, username, threadId, startedAt: new Date() },
      timestamp: new Date(),
    });
  }

  /**
   * Notify typing stop
   */
  public notifyTypingStop(userId: string, threadId: string): void {
    this.publish({
      type: 'typing_stop',
      data: { userId, threadId },
      timestamp: new Date(),
    });
  }

  /**
   * Update presence
   */
  public updatePresence(user: PresenceUser): void {
    this.publish({
      type: 'presence_update',
      data: user as unknown as Record<string, unknown>,
      timestamp: new Date(),
    });
  }
}

// Singleton instance
let wsService: WebSocketService | null = null;

/**
 * Get or create WebSocket service instance
 */
export function getWebSocketService(url?: string): WebSocketService {
  if (!wsService) {
    const wsUrl = url || `${getWebSocketUrl()}/ws`;
    wsService = new WebSocketService(wsUrl);
  }
  return wsService;
}

/**
 * Get WebSocket URL based on environment
 */
function getWebSocketUrl(): string {
  if (typeof window === 'undefined') {
    return 'ws://localhost:8000';
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host;

  return `${protocol}//${host}`;
}

/**
 * Close WebSocket service
 */
export function closeWebSocketService(): void {
  if (wsService) {
    wsService.disconnect();
    wsService = null;
  }
}

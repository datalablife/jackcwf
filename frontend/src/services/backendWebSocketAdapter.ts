/**
 * Backend WebSocket Adapter
 *
 * Provides backend-compatible WebSocket communication layer
 * that wraps the generic WebSocketService to match backend expectations.
 *
 * Backend Protocol:
 * - Requires user_id in first message
 * - Supports: message, ping, typing_start, typing_stop, presence_update
 * - Returns: ready, agent_thinking, tool_call, tool_result, response, complete, error, pong
 */

import { WebSocketService } from './websocketService';
import { WebSocketEvent, ChatMessage, ToolCall } from '../types';

export interface BackendConnectOptions {
  conversationId: string;
  userId: string;
  username?: string;
  onMessage?: (message: ChatMessage) => void;
  onThinking?: (content: string, done: boolean) => void;
  onToolCall?: (toolCall: ToolCall) => void;
  onToolResult?: (callId: string, result: unknown) => void;
  onResponse?: (content: string, done: boolean) => void;
  onComplete?: (messageId: string, tokensUsed: number) => void;
  onError?: (error: string) => void;
  wsUrl?: string;
}

export class BackendWebSocketAdapter {
  private wsService: WebSocketService;
  private conversationId: string;
  private userId: string;
  private username: string;
  private isInitialized: boolean = false;
  private handlers: {
    onMessage?: (message: ChatMessage) => void;
    onThinking?: (content: string, done: boolean) => void;
    onToolCall?: (toolCall: ToolCall) => void;
    onToolResult?: (callId: string, result: unknown) => void;
    onResponse?: (content: string, done: boolean) => void;
    onComplete?: (messageId: string, tokensUsed: number) => void;
    onError?: (error: string) => void;
  } = {};

  constructor(options: BackendConnectOptions) {
    this.conversationId = options.conversationId;
    this.userId = options.userId;
    this.username = options.username || 'Anonymous';
    this.handlers = {
      onMessage: options.onMessage,
      onThinking: options.onThinking,
      onToolCall: options.onToolCall,
      onToolResult: options.onToolResult,
      onResponse: options.onResponse,
      onComplete: options.onComplete,
      onError: options.onError,
    };

    // Initialize WebSocket service with backend-compatible URL
    const wsUrl = options.wsUrl || `${this.getBackendWebSocketUrl()}/conversations/${this.conversationId}`;
    this.wsService = new WebSocketService(wsUrl);
  }

  /**
   * Get backend WebSocket URL based on environment
   */
  private getBackendWebSocketUrl(): string {
    if (typeof window === 'undefined') {
      return 'ws://localhost:8000/ws';
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;

    return `${protocol}//${host}/ws`;
  }

  /**
   * Connect to backend and initialize communication
   */
  async connect(): Promise<void> {
    try {
      // Connect to WebSocket
      await this.wsService.connect();

      // Send initial message with user_id (required by backend)
      this.wsService.publish({
        type: 'message',
        data: {
          type: 'initial',
          user_id: this.userId,
          username: this.username,
          conversation_id: this.conversationId,
        },
        timestamp: new Date(),
      });

      // Set up event handlers
      this.setupEventHandlers();
      this.isInitialized = true;
    } catch (error) {
      const errorMsg = `Failed to connect to backend: ${error}`;
      this.handlers.onError?.(errorMsg);
      throw error;
    }
  }

  /**
   * Set up handlers for backend events
   */
  private setupEventHandlers(): void {
    // Handle incoming messages
    this.wsService.subscribe('message', (event: WebSocketEvent) => {
      this.handleMessage(event);
    });

    // Handle backend-specific events
    this.wsService.subscribe('agent_thinking', (event: WebSocketEvent) => {
      const data = event.data as unknown as { content: string; done: boolean };
      this.handlers.onThinking?.(data.content, data.done);
    });

    this.wsService.subscribe('tool_call', (event: WebSocketEvent) => {
      const data = event.data as unknown as ToolCall;
      this.handlers.onToolCall?.(data);
    });

    this.wsService.subscribe('tool_result', (event: WebSocketEvent) => {
      const data = event.data as unknown as { call_id: string; result: unknown };
      this.handlers.onToolResult?.(data.call_id, data.result);
    });

    this.wsService.subscribe('response', (event: WebSocketEvent) => {
      const data = event.data as unknown as { content: string; done: boolean };
      this.handlers.onResponse?.(data.content, data.done);
    });

    this.wsService.subscribe('complete', (event: WebSocketEvent) => {
      const data = event.data as unknown as { message_id: string; tokens_used: number };
      this.handlers.onComplete?.(data.message_id, data.tokens_used);
    });

    this.wsService.subscribe('error', (event: WebSocketEvent) => {
      const data = event.data as unknown as { error: string };
      this.handlers.onError?.(data.error);
    });

    this.wsService.subscribe('pong', () => {
      // Handle heartbeat pong
    });
  }

  /**
   * Handle incoming messages
   */
  private handleMessage(event: WebSocketEvent): void {
    const data = event.data as unknown as Record<string, unknown>;

    // Handle ready/connection confirmation
    if (data.type === 'ready') {
      console.log('[Backend] Connection ready:', data.message);
      return;
    }

    // Handle regular messages
    if (data.type === 'message' && this.handlers.onMessage) {
      const message: ChatMessage = {
        id: (data.message_id as string) || `msg-${Date.now()}`,
        threadId: this.conversationId,
        role: (data.role as 'user' | 'assistant') || 'assistant',
        content: (data.content as string) || '',
        timestamp: new Date(data.timestamp as string || Date.now()),
      };
      this.handlers.onMessage(message);
    }
  }

  /**
   * Send a message to the backend
   */
  async sendMessage(content: string, includeRag: boolean = true): Promise<void> {
    if (!this.isInitialized) {
      throw new Error('WebSocket not connected. Call connect() first.');
    }

    this.wsService.publish({
      type: 'message',
      data: {
        type: 'message',
        content,
        include_rag: includeRag,
        user_id: this.userId,
        conversation_id: this.conversationId,
      },
      timestamp: new Date(),
    });
  }

  /**
   * Notify typing start
   */
  notifyTypingStart(): void {
    if (!this.isInitialized) return;

    this.wsService.notifyTypingStart(this.userId, this.username, this.conversationId);
  }

  /**
   * Notify typing stop
   */
  notifyTypingStop(): void {
    if (!this.isInitialized) return;

    this.wsService.notifyTypingStop(this.userId, this.conversationId);
  }

  /**
   * Send heartbeat ping
   */
  ping(): void {
    if (!this.isInitialized) return;

    this.wsService.publish({
      type: 'ping',
      data: {},
      timestamp: new Date(),
    });
  }

  /**
   * Get connection state
   */
  getConnectionState() {
    return this.wsService.getConnectionState();
  }

  /**
   * Disconnect from backend
   */
  disconnect(): void {
    this.wsService.disconnect();
    this.isInitialized = false;
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.isInitialized && this.wsService.getConnectionState().isConnected;
  }
}

/**
 * Example Usage:
 *
 * ```typescript
 * const adapter = new BackendWebSocketAdapter({
 *   conversationId: 'conv-123',
 *   userId: 'user-456',
 *   username: 'John Doe',
 *   onMessage: (msg) => console.log('Message:', msg),
 *   onResponse: (content, done) => console.log('Response:', content, 'Done:', done),
 *   onError: (error) => console.error('Error:', error),
 * });
 *
 * await adapter.connect();
 * adapter.notifyTypingStart();
 * await adapter.sendMessage('Hello, AI!');
 * adapter.notifyTypingStop();
 * ```
 */

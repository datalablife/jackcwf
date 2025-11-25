// Chat types
export type MessageRole = 'user' | 'assistant';

export interface ChatMessage {
  id: string;
  threadId: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
  toolCalls?: ToolCall[];
  toolResults?: ToolResult[];
  metadata?: Record<string, unknown>;
}

export interface ToolCall {
  toolId: string;
  toolName: string;
  toolInput: Record<string, unknown>;
  status: 'pending' | 'executing' | 'completed' | 'failed';
  result?: unknown;
  executionTimeMs?: number;
}

export interface ToolResult {
  toolId: string;
  toolName: string;
  result: unknown;
  isError: boolean;
  errorMessage?: string;
}

// Thread types
export interface Thread {
  threadId: string;
  conversationId: number;
  title: string;
  createdAt: Date;
  updatedAt: Date;
  messageCount: number;
  metadata?: Record<string, unknown>;
}

export interface ThreadState {
  threadId: string;
  messages: ChatMessage[];
  pendingTools: ToolCall[];
  agentCheckpoint?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

// Streaming types
export type StreamEventType =
  | 'chunk'
  | 'state_snapshot'
  | 'tool_call_start'
  | 'tool_call_result'
  | 'checkpoint_created'
  | 'error'
  | 'complete';

export interface StreamEvent {
  type: StreamEventType;
  data: Record<string, unknown>;
  timestamp?: Date;
}

export interface StreamEventWithState extends StreamEvent {
  state?: ThreadState;
  metadata?: {
    tokenUsage?: number;
    latencyMs?: number;
  };
}

// Tool types
export interface RAGSearchResult {
  documentId: number;
  documentName: string;
  content: string;
  score: number;
  source?: string;
  metadata?: Record<string, unknown>;
}

export interface DatabaseQueryResult {
  columns: string[];
  rows: Record<string, unknown>[];
  rowCount: number;
}

export interface WebSearchResult {
  title: string;
  url: string;
  snippet: string;
  source: string;
}

// API types
export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface ApiResponse<T = unknown> {
  data?: T;
  error?: ApiError;
  metadata?: {
    requestId?: string;
    timestamp?: Date;
  };
}

// Cache types
export interface CacheMetrics {
  hitRate: number;
  missRate: number;
  totalRequests: number;
  averageLatencyMs: number;
  savedCost?: number;
}

// Conversation types
export interface ConversationSummary {
  conversationId: number;
  summary: string;
  keyTopics: string[];
  messageCount: number;
  updatedAt: Date;
}

// UI state types
export interface ChatUIState {
  isLoading: boolean;
  error?: ApiError;
  selectedToolId?: string;
  sidebarOpen: boolean;
  debugMode?: boolean;
}

// WebSocket types
export type WebSocketEventType =
  | 'message'
  | 'typing_start'
  | 'typing_stop'
  | 'presence_update'
  | 'connection_status'
  | 'error'
  | 'reconnect'
  | 'ping'
  | 'pong'
  | 'agent_thinking'
  | 'tool_call'
  | 'tool_result'
  | 'response'
  | 'complete'
  | 'ready';

export interface WebSocketEvent {
  type: WebSocketEventType;
  data: Record<string, unknown>;
  timestamp: Date;
}

export interface PresenceUser {
  userId: string;
  username: string;
  status: 'online' | 'typing' | 'away' | 'offline';
  lastSeenAt: Date;
}

export interface TypingState {
  userId: string;
  username: string;
  threadId: string;
  startedAt: Date;
}

export interface WebSocketConnectionState {
  isConnected: boolean;
  isConnecting: boolean;
  lastConnectedAt?: Date;
  reconnectAttempts: number;
  error?: string;
}

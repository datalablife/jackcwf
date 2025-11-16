# API Reference - LangChain AI Conversation System

Complete API reference for the LangChain v1.0 AI Conversation System.

Base URL: `http://localhost:8000`

---

## Table of Contents

1. [Authentication](#authentication)
2. [Conversations](#conversations)
3. [Documents](#documents)
4. [Messages](#messages)
5. [Tools](#tools)
6. [WebSocket](#websocket)
7. [Health & Status](#health--status)

---

## Authentication

Currently using middleware-based authentication. The `user_id` is extracted from request state by the authentication middleware.

In production, implement JWT-based authentication and add the token to headers:

```
Authorization: Bearer <jwt-token>
```

---

## Conversations

### Create Conversation

**POST** `/api/conversations`

Create a new conversation.

**Request Body:**
```json
{
  "title": "My Conversation",
  "system_prompt": "You are a helpful assistant.",
  "model": "gpt-4-turbo",
  "metadata": {
    "custom_field": "value"
  }
}
```

**Response:** `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user123",
  "title": "My Conversation",
  "summary": null,
  "model": "gpt-4-turbo",
  "message_count": 0,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

---

### List Conversations

**GET** `/api/conversations`

List all conversations for the user.

**Query Parameters:**
- `skip` (int, default: 0): Number to skip for pagination
- `limit` (int, default: 10): Maximum results to return

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "user_id": "user123",
      "title": "My Conversation",
      "summary": null,
      "model": "gpt-4-turbo",
      "message_count": 5,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T11:00:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 10
}
```

---

### Get Conversation

**GET** `/api/conversations/{conversation_id}`

Get a specific conversation by ID.

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user123",
  "title": "My Conversation",
  "summary": "Discussion about AI",
  "model": "gpt-4-turbo",
  "message_count": 5,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

**Errors:**
- `404 Not Found`: Conversation not found or access denied

---

### Update Conversation

**PUT** `/api/conversations/{conversation_id}`

Update conversation title or summary.

**Request Body:**
```json
{
  "title": "Updated Title",
  "summary": "New summary"
}
```

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user123",
  "title": "Updated Title",
  "summary": "New summary",
  "model": "gpt-4-turbo",
  "message_count": 5,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T12:00:00Z"
}
```

---

### Delete Conversation

**DELETE** `/api/conversations/{conversation_id}`

Soft delete a conversation.

**Response:** `204 No Content`

---

### Get Conversation Messages

**GET** `/api/conversations/{conversation_id}/messages`

Get message history for a conversation.

**Query Parameters:**
- `limit` (int, default: 50): Maximum messages to return

**Response:** `200 OK`
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "messages": [
    {
      "role": "user",
      "content": "Hello",
      "tool_calls": null,
      "tool_results": null,
      "tokens_used": null,
      "created_at": "2024-01-15T10:31:00Z"
    },
    {
      "role": "assistant",
      "content": "Hi! How can I help you?",
      "tool_calls": null,
      "tool_results": null,
      "tokens_used": 25,
      "created_at": "2024-01-15T10:31:02Z"
    }
  ],
  "total_tokens": 25
}
```

---

### Send Message

**POST** `/api/conversations/{conversation_id}/messages`

Send a message to a conversation (non-streaming).

**Request Body:**
```json
{
  "content": "What is machine learning?",
  "include_rag": true
}
```

**Response:** `201 Created`
```json
{
  "message_id": "650e8400-e29b-41d4-a716-446655440000",
  "role": "user",
  "content": "What is machine learning?",
  "created_at": "2024-01-15T10:35:00Z"
}
```

Note: For real-time streaming responses, use the WebSocket endpoint instead.

---

## Documents

### Upload Document

**POST** `/api/documents`

Upload and process a document for RAG.

**Request:** `multipart/form-data`
- `file`: Document file (PDF, TXT, DOCX, MD, CSV)
- `metadata` (optional): JSON metadata string

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/documents" \
  -F "file=@document.pdf" \
  -F 'metadata={"source":"user_upload"}'
```

**Response:** `201 Created`
```json
{
  "id": "750e8400-e29b-41d4-a716-446655440000",
  "filename": "document.pdf",
  "status": "success",
  "total_chunks": 42,
  "message": "Document uploaded and processed successfully (42 chunks created)"
}
```

**Performance:** ≤ 5000ms target

**File Limits:**
- Max size: 50MB
- Supported types: PDF, TXT, DOCX, MD, CSV

---

### List Documents

**GET** `/api/documents`

List user's documents.

**Query Parameters:**
- `skip` (int, default: 0): Number to skip
- `limit` (int, default: 10): Maximum results
- `file_type` (string, optional): Filter by type (pdf, txt, docx, etc.)

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "750e8400-e29b-41d4-a716-446655440000",
      "filename": "document.pdf",
      "file_type": "pdf",
      "total_chunks": 42,
      "embedding_count": 42,
      "created_at": "2024-01-15T09:00:00Z",
      "metadata": {
        "source": "user_upload"
      }
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 10
}
```

---

### Get Document

**GET** `/api/documents/{document_id}`

Get document details.

**Response:** `200 OK`
```json
{
  "id": "750e8400-e29b-41d4-a716-446655440000",
  "filename": "document.pdf",
  "file_type": "pdf",
  "total_chunks": 42,
  "embedding_count": 42,
  "created_at": "2024-01-15T09:00:00Z",
  "metadata": {
    "source": "user_upload"
  }
}
```

---

### Delete Document

**DELETE** `/api/documents/{document_id}`

Soft delete a document and its embeddings.

**Response:** `204 No Content`

---

### Search Documents

**POST** `/api/documents/search`

Search documents using semantic similarity (RAG).

**Request Body:**
```json
{
  "query": "What is machine learning?",
  "limit": 5,
  "threshold": 0.7
}
```

**Parameters:**
- `query` (string, required): Search query
- `limit` (int, 1-20, default: 5): Maximum results
- `threshold` (float, 0-1, default: 0.7): Similarity threshold

**Response:** `200 OK`
```json
{
  "query": "What is machine learning?",
  "results": [
    {
      "document_id": "750e8400-e29b-41d4-a716-446655440000",
      "chunk_index": 5,
      "chunk_text": "Machine learning is a subset of artificial intelligence...",
      "similarity": 0.89,
      "metadata": {
        "source": "document",
        "chunk": 5
      }
    }
  ],
  "total": 1
}
```

**Performance:** ≤ 200ms P99 target

---

### Get Document Chunks

**GET** `/api/documents/{document_id}/chunks`

Get all chunks for a document.

**Query Parameters:**
- `skip` (int, default: 0): Number to skip
- `limit` (int, default: 100): Maximum chunks

**Response:** `200 OK`
```json
[
  {
    "document_id": "750e8400-e29b-41d4-a716-446655440000",
    "chunk_index": 0,
    "chunk_text": "Chapter 1: Introduction...",
    "similarity": 1.0,
    "metadata": {
      "source": "document",
      "chunk": 0
    }
  }
]
```

---

## Messages

### Get Message

**GET** `/api/conversations/{conversation_id}/messages/{message_id}`

Get a specific message with full details.

**Response:** `200 OK`
```json
{
  "id": "850e8400-e29b-41d4-a716-446655440000",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "role": "assistant",
  "content": "Machine learning is...",
  "tool_calls": {
    "search_documents": {
      "query": "machine learning",
      "limit": 5
    }
  },
  "tool_results": {
    "search_documents": "Found 3 relevant documents..."
  },
  "tokens_used": 150,
  "metadata": {},
  "created_at": "2024-01-15T10:32:00Z"
}
```

---

### Update Message

**PUT** `/api/conversations/{conversation_id}/messages/{message_id}`

Update message metadata, tool results, or token count.

**Request Body:**
```json
{
  "tool_results": {
    "additional_result": "value"
  },
  "tokens_used": 175,
  "metadata": {
    "custom_field": "value"
  }
}
```

**Response:** `200 OK`
(Same as Get Message response)

**Note:** Metadata updates are merged with existing metadata.

---

### Delete Message

**DELETE** `/api/conversations/{conversation_id}/messages/{message_id}`

Permanently delete a message.

**Response:** `204 No Content`

**Warning:** This is a hard delete and cannot be undone.

---

## Tools

### List Tools

**GET** `/api/tools`

Get all available tools with schemas.

**Response:** `200 OK`
```json
{
  "tools": [
    {
      "name": "search_documents",
      "description": "Search user's documents using semantic similarity",
      "parameters": {
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "description": "Search query"
          },
          "limit": {
            "type": "integer",
            "default": 5,
            "minimum": 1,
            "maximum": 20
          }
        },
        "required": ["query"]
      },
      "examples": [
        {
          "query": "machine learning",
          "limit": 5
        }
      ]
    },
    {
      "name": "query_database",
      "description": "Query database using natural language",
      "parameters": {...}
    },
    {
      "name": "web_search",
      "description": "Search the web for information",
      "parameters": {...}
    }
  ],
  "count": 3
}
```

---

### Execute Tool

**POST** `/api/tools/execute`

Execute a tool directly (requires admin access).

**Headers:**
- `X-Admin-Key`: Admin API key

**Request Body:**
```json
{
  "tool_name": "search_documents",
  "input": {
    "query": "machine learning",
    "limit": 5
  },
  "conversation_id": "optional-context-id"
}
```

**Response:** `200 OK`
```json
{
  "tool_name": "search_documents",
  "input": {
    "query": "machine learning",
    "limit": 5
  },
  "output": "1. Machine learning is...\n2. AI algorithms...",
  "success": true,
  "error": null,
  "execution_time_ms": 145.23
}
```

**Errors:**
- `403 Forbidden`: Invalid or missing admin key
- `404 Not Found`: Tool not found

---

## WebSocket

### Real-time Conversation

**WebSocket** `/ws/conversations/{conversation_id}`

Real-time bidirectional conversation with AI agent.

### Connection Example

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/conversations/{conversation_id}');

// First message MUST include user_id
ws.onopen = () => {
  ws.send(JSON.stringify({
    type: "message",
    content: "Hello!",
    include_rag: true,
    user_id: "user123"
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

### Message Protocol

#### Client → Server Messages

**1. Initial Message (Required):**
```json
{
  "type": "message",
  "content": "Your message",
  "include_rag": true,
  "user_id": "user123"
}
```

**2. Subsequent Messages:**
```json
{
  "type": "message",
  "content": "Your message",
  "include_rag": true
}
```

**3. Ping:**
```json
{
  "type": "ping"
}
```

#### Server → Client Messages

**1. Ready (Connection Established):**
```json
{
  "type": "ready",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Connected to conversation",
  "message_count": 10,
  "total_tokens": 1500
}
```

**2. Message Received:**
```json
{
  "type": "message_received",
  "message_id": "850e8400-e29b-41d4-a716-446655440000"
}
```

**3. Agent Thinking:**
```json
{
  "type": "agent_thinking",
  "content": "Processing your message...",
  "done": false
}
```

**4. Tool Call:**
```json
{
  "type": "tool_call",
  "tool_name": "search_documents",
  "tool_input": {
    "query": "machine learning",
    "limit": 5
  },
  "call_id": "call_123"
}
```

**5. Tool Result:**
```json
{
  "type": "tool_result",
  "call_id": "call_123",
  "result": "Found 3 relevant documents..."
}
```

**6. Response Chunk (Streaming):**
```json
{
  "type": "response",
  "content": "Machine learning is",
  "done": false
}
```

**7. Complete:**
```json
{
  "type": "complete",
  "message_id": "950e8400-e29b-41d4-a716-446655440000",
  "tokens_used": 150
}
```

**8. Error:**
```json
{
  "type": "error",
  "error": "Error message"
}
```

**9. Heartbeat:**
```json
{
  "type": "heartbeat"
}
```

**10. Pong (Response to Ping):**
```json
{
  "type": "pong"
}
```

### Connection Lifecycle

1. **Connect**: Client opens WebSocket connection
2. **Authenticate**: First message must include `user_id`
3. **Ready**: Server sends ready message
4. **Exchange**: Bidirectional message exchange
5. **Heartbeat**: Server sends heartbeat every 30s
6. **Disconnect**: Clean closure on client/server disconnect

---

## Health & Status

### Health Check

**GET** `/health`

Check if the service is healthy.

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "service": "LangChain AI Conversation API",
  "version": "1.0.0"
}
```

---

### Root

**GET** `/`

Get API information.

**Response:** `200 OK`
```json
{
  "message": "LangChain AI Conversation API",
  "version": "1.0.0",
  "docs": "/api/docs",
  "health": "/health",
  "endpoints": {
    "conversations": "/api/conversations",
    "documents": "/api/documents",
    "messages": "/api/conversations/{id}/messages",
    "tools": "/api/tools",
    "websocket": "/ws/conversations/{id}"
  }
}
```

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message",
  "errors": []  // Optional validation errors
}
```

### Common Status Codes

- `200 OK`: Success
- `201 Created`: Resource created
- `204 No Content`: Success with no response body
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Access denied
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

### Validation Error Example

```json
{
  "detail": "Validation error",
  "errors": [
    {
      "loc": ["body", "title"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Rate Limits

Currently no rate limiting is implemented. Consider adding rate limiting in production.

Recommended limits:
- API endpoints: 100 requests/minute
- WebSocket connections: 10 concurrent per user
- Document uploads: 10 per hour
- Tool executions: 50 per minute

---

## CORS

Configured origins in `ALLOWED_ORIGINS` environment variable.

Default: `http://localhost:3000,http://localhost:8000`

---

## Interactive Documentation

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json

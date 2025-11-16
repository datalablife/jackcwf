# Quick Start Guide - LangChain AI Conversation System

## Prerequisites

1. Python 3.11+
2. PostgreSQL with pgvector extension
3. OpenAI API key
4. UV package manager (optional but recommended)

## Installation

### 1. Clone and Setup

```bash
cd /mnt/d/工作区/云开发/working

# Install dependencies with uv
uv pip install -r requirements.txt

# Or with pip
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ai_conversation

# OpenAI
OPENAI_API_KEY=sk-your-api-key-here

# Server
PORT=8000
ENV=development
DEBUG=true
LOG_LEVEL=info

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Admin (for tool execution)
ADMIN_API_KEY=your-secret-admin-key
```

### 3. Initialize Database

```bash
# The database will be auto-initialized on first run
# Make sure PostgreSQL is running and the database exists
```

### 4. Run the Server

```bash
# With uvicorn directly
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Or with Python
python -m src.main
```

Server will start at: `http://localhost:8000`

API Documentation: `http://localhost:8000/api/docs`

---

## Quick Test Flow

### 1. Create a Conversation

```bash
curl -X POST "http://localhost:8000/api/conversations" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Conversation",
    "system_prompt": "You are a helpful AI assistant.",
    "model": "gpt-4-turbo"
  }'
```

Response:
```json
{
  "id": "conv-uuid-here",
  "title": "Test Conversation",
  "model": "gpt-4-turbo",
  "message_count": 0,
  "created_at": "2024-01-15T10:00:00Z"
}
```

### 2. Upload a Document

```bash
curl -X POST "http://localhost:8000/api/documents" \
  -F "file=@/path/to/document.pdf"
```

Response:
```json
{
  "id": "doc-uuid-here",
  "filename": "document.pdf",
  "status": "success",
  "total_chunks": 42,
  "message": "Document uploaded and processed successfully"
}
```

### 3. Search Documents

```bash
curl -X POST "http://localhost:8000/api/documents/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "limit": 3
  }'
```

### 4. Send a Message (REST)

```bash
curl -X POST "http://localhost:8000/api/conversations/conv-uuid-here/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Hello, can you help me?",
    "include_rag": true
  }'
```

### 5. Connect via WebSocket

**JavaScript Example:**

```javascript
// Connect to WebSocket
const conversationId = 'your-conv-uuid';
const ws = new WebSocket(`ws://localhost:8000/ws/conversations/${conversationId}`);

// Send initial message with user_id
ws.onopen = () => {
  ws.send(JSON.stringify({
    type: "message",
    content: "Hello!",
    include_rag: true,
    user_id: "user123"
  }));
};

// Listen for responses
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch(data.type) {
    case 'ready':
      console.log('Connected:', data.message);
      break;

    case 'agent_thinking':
      console.log('Agent thinking:', data.content);
      break;

    case 'tool_call':
      console.log('Tool called:', data.tool_name);
      break;

    case 'response':
      console.log('Response chunk:', data.content);
      if (data.done) {
        console.log('Response complete');
      }
      break;

    case 'complete':
      console.log('Message complete. Tokens used:', data.tokens_used);
      break;

    case 'error':
      console.error('Error:', data.error);
      break;
  }
};

// Send more messages
function sendMessage(content) {
  ws.send(JSON.stringify({
    type: "message",
    content: content,
    include_rag: true,
    user_id: "user123"
  }));
}
```

**Python Example:**

```python
import asyncio
import websockets
import json

async def chat():
    conversation_id = "your-conv-uuid"
    uri = f"ws://localhost:8000/ws/conversations/{conversation_id}"

    async with websockets.connect(uri) as websocket:
        # Send initial message
        await websocket.send(json.dumps({
            "type": "message",
            "content": "Hello!",
            "include_rag": True,
            "user_id": "user123"
        }))

        # Receive responses
        while True:
            message = await websocket.recv()
            data = json.loads(message)

            print(f"Received: {data['type']}")

            if data['type'] == 'complete':
                print(f"Tokens used: {data['tokens_used']}")
                break

asyncio.run(chat())
```

---

## Common Use Cases

### Use Case 1: Document Q&A System

```bash
# 1. Upload documents
curl -X POST "http://localhost:8000/api/documents" \
  -F "file=@manual.pdf"

# 2. Create conversation
curl -X POST "http://localhost:8000/api/conversations" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Product Manual Q&A",
    "system_prompt": "You help users understand the product manual. Use the search_documents tool to find relevant information."
  }'

# 3. Ask questions via WebSocket
# The agent will automatically use search_documents tool to find answers
```

### Use Case 2: Real-time Chat with Streaming

```javascript
// React component example
function ChatComponent() {
  const [messages, setMessages] = useState([]);
  const [currentResponse, setCurrentResponse] = useState('');

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/conversations/${conversationId}`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'response') {
        setCurrentResponse(prev => prev + data.content);

        if (data.done) {
          setMessages(prev => [...prev, {
            role: 'assistant',
            content: currentResponse + data.content
          }]);
          setCurrentResponse('');
        }
      }
    };

    return () => ws.close();
  }, [conversationId]);

  return (
    <div>
      {messages.map((msg, i) => (
        <div key={i}>{msg.content}</div>
      ))}
      {currentResponse && <div>{currentResponse}...</div>}
    </div>
  );
}
```

### Use Case 3: Tool Execution Testing

```bash
# List available tools
curl "http://localhost:8000/api/tools"

# Execute a tool (requires admin key)
curl -X POST "http://localhost:8000/api/tools/execute" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: your-admin-key" \
  -d '{
    "tool_name": "search_documents",
    "input": {
      "query": "machine learning",
      "limit": 5
    }
  }'
```

---

## API Exploration

Visit the interactive API documentation:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
pg_isready

# Check database exists
psql -l | grep ai_conversation

# Create database if needed
createdb ai_conversation

# Enable pgvector extension
psql ai_conversation -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Import Errors

```bash
# Reinstall dependencies
uv pip install -r requirements.txt --force-reinstall

# Or with pip
pip install -r requirements.txt --force-reinstall
```

### WebSocket Connection Failed

1. Check server is running on correct port
2. Ensure no firewall blocking WebSocket
3. Use correct protocol (ws:// for http, wss:// for https)
4. Include user_id in first message

### Tool Execution Permission Denied

1. Set ADMIN_API_KEY in environment
2. Include X-Admin-Key header in request
3. Or set ENV=development to bypass in dev mode

---

## Development Tips

### Enable Debug Logging

```bash
# In .env
DEBUG=true
LOG_LEVEL=debug
```

### Auto-reload on Changes

```bash
uvicorn src.main:app --reload
```

### Test with cURL

```bash
# Get all conversations
curl "http://localhost:8000/api/conversations"

# Get specific conversation
curl "http://localhost:8000/api/conversations/{id}"

# Delete conversation
curl -X DELETE "http://localhost:8000/api/conversations/{id}"
```

### Monitor Logs

```bash
# The server logs all requests and important events
# Watch for:
# - "Processing message for conversation..."
# - "Tool {name} called with query..."
# - "Document search completed in X ms"
```

---

## Next Steps

1. **Integrate Frontend**: Connect your React/Vue/Angular app
2. **Add Authentication**: Implement JWT-based auth
3. **Customize Tools**: Add your own tools to the agent
4. **Deploy**: Use Docker or cloud platforms
5. **Monitor**: Add metrics and logging

---

## Additional Resources

- LangChain Documentation: https://python.langchain.com/
- FastAPI Documentation: https://fastapi.tiangolo.com/
- OpenAI API Reference: https://platform.openai.com/docs/api-reference

---

## Support

For issues or questions:
1. Check the logs for error details
2. Review the API documentation at `/api/docs`
3. Consult IMPLEMENTATION_SUMMARY.md for detailed architecture info

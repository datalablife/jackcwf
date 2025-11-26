# WebSocket 403 Forbidden - 诊断与修复方案

**日期**: 2025-11-25
**状态**: 🔍 **诊断完成 | 需要实施修复**

---

## 📊 问题诊断结果

### ✅ 已验证正确的部分

#### 1. Backend Authentication Middleware - ✅ 正确修改
```bash
$ grep -n '"/ws"' src/middleware/auth_middleware.py
35:        "/ws",  # WebSocket endpoint - has its own authentication via user_id
240:        if path.startswith("/ws"):
```

**状态**: ✅ Middleware 修改已正确应用到源代码

#### 2. WebSocket Route 配置 - ✅ 正确
```
实际路径: /ws/conversations/{conversation_id}
Router: src/api/websocket_routes.py (line 107)
已注册到 main.py (line 274)
```

### 🔴 发现的问题

#### 问题 1: Backend 进程需要重启
**原因**: Python middleware 是在应用启动时加载的，代码修改后需要重新启动进程才能生效

**当前状态**: 旧的 middleware 配置仍在内存中运行

#### 问题 2: 前端连接路径错误
**当前**: `ws://localhost:8000/ws?token=null`
**应该**: `ws://localhost:8000/ws/conversations/{conversation_id}`

#### 问题 3: 前端认证方式错误
**当前**: 在查询参数中发送 `token=null`
**应该**: 在 WebSocket 第一条消息中发送 `user_id`

---

## 🛠️ 修复步骤

### Step 1: 重启 Backend ✅

运行以下命令重启后端（在项目根目录）：

```bash
# 杀死现有进程
lsof -i :8000 | grep -v COMMAND | awk '{print $2}' | xargs kill -9 2>/dev/null || true

# 等待2秒
sleep 2

# 启动新的后端进程
source .venv/bin/activate
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

**预期输出**:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**验证方式** (在另一个终端):
```bash
curl -I http://localhost:8000/health
# 应该返回 200 OK（不返回 401）
```

---

### Step 2: 修复前端 WebSocket 连接 🔧

#### 当前错误的实现（基于日志）:
```javascript
// ❌ 错误 - 路径不完整，且 token 方式错误
const ws = new WebSocket('ws://localhost:8000/ws?token=null');
```

#### 正确的实现:

**文件**: `frontend/src/services/backendWebSocketAdapter.ts`

修改 `getBackendWebSocketUrl()` 方法：

```typescript
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
```

这已经是正确的了！关键是要确保完整路径包含 conversation ID：

```typescript
// Line 61 - 这里构建完整路径
const wsUrl = options.wsUrl || `${this.getBackendWebSocketUrl()}/conversations/${this.conversationId}`;
```

**验证方式**:
```javascript
// 在浏览器控制台测试
const conversationId = 'test-uuid-here';
const ws = new WebSocket(`ws://localhost:8000/ws/conversations/${conversationId}`);

ws.onopen = () => {
  console.log('✅ WebSocket connected!');
  // 发送初始认证消息
  ws.send(JSON.stringify({
    type: 'initial',
    user_id: 'test-user-123',
    username: 'Test User',
    conversation_id: conversationId
  }));
};

ws.onmessage = (event) => {
  console.log('📨 Message:', JSON.parse(event.data));
};

ws.onerror = (error) => {
  console.error('❌ WebSocket error:', error);
};
```

---

### Step 3: 验证认证流程 ✅

#### Backend 认证流程 (正确的):

1. **WebSocket 升级**
   ```
   WebSocket GET /ws/conversations/{id}
   ↓
   AuthenticationMiddleware checks: path.startswith("/ws") ?
   ↓
   YES → ALLOW (bypass auth check)
   ↓
   Reach WebSocket handler
   ```

2. **连接建立**
   ```python
   await websocket.accept()  # Accept connection
   ```

3. **应用层认证**
   ```python
   initial_data = await websocket.receive_json()

   # 检查 user_id
   if "user_id" not in initial_data:
       await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
       return

   # 验证用户拥有该对话
   conversation = await conv_service.conv_repo.get_user_conversation(
       user_id,
       conversation_id
   )

   if not conversation:
       await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
       return
   ```

---

## 📋 完整修复清单

- [ ] **后端**:
  - [ ] 停止当前运行的 uvicorn 进程
  - [ ] 重启后端: `python -m uvicorn src.main:app --host 0.0.0.0 --port 8000`
  - [ ] 验证健康检查: `curl http://localhost:8000/health`
  - [ ] 检查 WebSocket 路径已注册

- [ ] **前端**:
  - [ ] 确认 `BackendWebSocketAdapter` 的路径正确（应该是 `/ws/conversations/{id}`）
  - [ ] 确认发送的第一条消息包含 `user_id`
  - [ ] 移除查询参数中的 `token=null`
  - [ ] 测试 WebSocket 连接

- [ ] **测试验证**:
  - [ ] 后端 `/health` 端点返回 200
  - [ ] WebSocket 连接不返回 403 Forbidden
  - [ ] WebSocket 接收到 `ready` 消息

---

## 🧪 测试脚本

### Python WebSocket 测试脚本

创建 `test_websocket_detailed.py`:

```python
#!/usr/bin/env python3
import asyncio
import websockets
import json
import uuid

async def test_websocket():
    """Test WebSocket connection after middleware fix."""

    conversation_id = str(uuid.uuid4())
    user_id = f"test-user-{uuid.uuid4().hex[:8]}"

    ws_url = f"ws://localhost:8000/ws/conversations/{conversation_id}"

    print(f"Testing WebSocket at: {ws_url}")
    print(f"User ID: {user_id}")
    print()

    try:
        async with websockets.connect(ws_url, timeout=5) as websocket:
            print("✅ WebSocket connected!")

            # Send initial authentication message
            auth_msg = {
                "type": "initial",
                "user_id": user_id,
                "username": "Test User",
                "conversation_id": conversation_id,
            }

            await websocket.send(json.dumps(auth_msg))
            print("✅ Sent authentication message")

            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            data = json.loads(response)

            print(f"✅ Received response: {data.get('type')}")
            print(f"   Full message: {data}")

            if data.get("type") == "ready":
                print("\n🎉 SUCCESS! WebSocket is working!")
                return True
            elif data.get("type") == "error":
                print(f"\n❌ Server error: {data.get('error')}")
                return False

    except asyncio.TimeoutError:
        print("❌ Timeout - backend may not be running")
        return False
    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_websocket())
    exit(0 if result else 1)
```

使用方法:
```bash
python test_websocket_detailed.py
```

---

## 🔍 诊断检查清单

在启动后端后，运行以下检查：

```bash
# 1. 检查后端是否正在运行
lsof -i :8000

# 2. 检查健康检查端点（不需要认证）
curl -I http://localhost:8000/health
# 预期: 200 OK

# 3. 检查 metrics 端点（不需要认证）
curl -I http://localhost:8000/metrics
# 预期: 200 OK

# 4. 检查 WebSocket 升级（只需检查升级，不需要完整连接）
curl -I -H "Upgrade: websocket" -H "Connection: Upgrade" \
  http://localhost:8000/ws/conversations/test
# 预期: 应该获得 WebSocket 升级响应或 404，NOT 401/403
```

---

## 📊 架构验证

### 请求流程（修复后）

```
前端 → WebSocket 升级请求
        GET /ws/conversations/{id}
        ↓
        AuthenticationMiddleware
        └─ path.startswith("/ws")?
           └─ YES → ALLOW (绕过认证检查)
        ↓
        WebSocket Handler
        ├─ Accept connection
        ├─ Wait for initial message with user_id
        ├─ Verify user owns conversation
        ├─ Send "ready" message
        ↓
前端 ← Connection established ✅
```

---

## ⚠️ 常见错误

### 错误 1: 仍然获得 403
**原因**: Backend 进程未重启（旧 middleware 仍在运行）
**解决**:
```bash
kill -9 $(lsof -i :8000 | grep -v COMMAND | awk '{print $2}')
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### 错误 2: WebSocket 连接成功但收不到消息
**原因**: 未发送认证消息（user_id）
**解决**: 确保第一条消息包含 `user_id` 字段

### 错误 3: 连接被拒绝 (1008 Policy Violation)
**原因**: user_id 不匹配或用户不拥有该对话
**解决**: 使用有效的 user_id 和对应的 conversation_id

---

## ✅ 成功标志

修复成功时，你应该看到：

**后端日志**:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**WebSocket 连接日志**:
```
WebSocket /ws/conversations/{id} - accepted
# (NOT 403 Forbidden)
```

**前端/测试脚本输出**:
```
✅ WebSocket connected!
✅ Sent authentication message
✅ Received response: ready
🎉 SUCCESS! WebSocket is working!
```

---

## 📞 后续步骤

1. ✅ 实施本诊断中的所有修复步骤
2. ✅ 运行测试脚本验证连接
3. ✅ 在前端启动 React 开发服务器
4. ✅ 测试实时聊天功能

---

**状态**: 🔧 **准备好实施修复**
**需要操作**: 重启后端 + 验证 WebSocket 连接


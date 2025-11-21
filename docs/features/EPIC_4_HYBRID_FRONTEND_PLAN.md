# EPIC 4: 混合前端 - Agent-Chat-UI 启发 + 自定义 Vite 实现

**版本**: 2.0 (方案 C: 混合方案)
**创建日期**: 2025-11-20
**状态**: 待批准
**预算**: $18,000 - $22,000
**时间线**: 3-4 周 MVP + 1 周完整功能
**前置条件**: Epic 1-3 后端已完成，API 稳定

---

## 🎯 Executive Summary

### 方案 C: 混合方案核心理念

**不是**: 直接采用 agent-chat-ui 并创建适配器层
**而是**: 使用 Vite + React 从头构建，但借鉴 agent-chat-ui 的设计模式和 UI 组件设计

### 优势分析

| 维度 | 完全自定义 | Agent-Chat-UI | 混合方案 (方案 C) |
|------|-----------|--------------|------------------|
| **开发成本** | $62,100 | $77,000 | **$18,000-22,000** ✅ |
| **开发周期** | 5 周 | 9 周 | **3-4 周** ✅ |
| **兼容性** | 10/10 | 4/10 | **10/10** ✅ |
| **维护成本** | 低 | 高 (适配器) | **低** ✅ |
| **设计质量** | 需从零设计 | 官方设计 | **借鉴最佳实践** ✅ |

### 关键决策

1. **UI 设计**: 借鉴 agent-chat-ui 的组件布局和交互模式
2. **技术栈**: 保持 Vite + React + Tailark (与后端完美兼容)
3. **组件实现**: 自己编写代码 (不使用 agent-chat-ui 源码)
4. **API 集成**: 直接对接 FastAPI 后端 (无需适配器层)

---

## 📊 成本分解 (目标: $18K-22K)

### Phase 1: 准备阶段 (Week 1, $6,000)

```
Task 4.0.1: 后端 Staging 部署验证        $2,000 (1 day)
Task 4.0.2: Agent-Chat-UI 设计研究       $2,000 (1 day)
Task 4.0.3: Vite + Tailark 环境配置      $2,000 (1 day)
────────────────────────────────────────────────────
Subtotal Phase 1:                        $6,000
```

### Phase 2: 核心 UI 开发 (Week 2, $7,000)

```
Task 4.1.1: ChatInterface 组件           $3,000 (2 days)
Task 4.1.2: ChatInput + 消息发送         $2,000 (1 day)
Task 4.1.3: ConversationList 侧边栏      $2,000 (1 day)
────────────────────────────────────────────────────
Subtotal Phase 2:                        $7,000
```

### Phase 3: 高级功能 (Week 3, $5,000)

```
Task 4.2.1: 文档上传 UI                  $2,000 (1 day)
Task 4.2.2: Tool Renderer (RAG 显示)     $2,000 (1 day)
Task 4.2.3: WebSocket 流式集成           $1,000 (0.5 day)
────────────────────────────────────────────────────
Subtotal Phase 3:                        $5,000
```

### Phase 4: 优化与部署 (Week 4, $2,000-4,000)

```
Task 4.3.1: 响应式设计 + 暗色模式        $1,000 (0.5 day)
Task 4.3.2: 性能优化 (Lighthouse 90+)    $1,000 (0.5 day)
Task 4.3.3: E2E 测试 + 部署              $2,000 (1 day, 可选)
────────────────────────────────────────────────────
Subtotal Phase 4:                        $2,000-4,000
```

### 总成本

```
MVP 路径 (3 周):           $18,000 ✅
完整路径 (4 周):           $20,000-22,000 ✅
缓冲 (15%):                +$3,000
────────────────────────────────────────────────────
总计:                      $18,000-22,000
```

---

## 🗓️ 时间线: 3-4 周交付

### Week 1: 准备与设计研究

```
Day 1 (Mon):     后端 Staging 部署 + 负载测试
Day 2 (Tue):     研究 agent-chat-ui 源码 (布局、组件、交互)
                 - 聊天界面布局
                 - Tool 调用可视化
                 - Artifact 侧边栏模式
Day 3 (Wed):     Vite + React 19 + Tailark 脚手架
Day 4 (Thu):     设计系统映射 (agent-chat-ui → Tailark)
Day 5 (Fri):     Mock API + 开发环境验证
────────────────────────────────────────────────────
Milestone M1: 环境就绪 + 设计方案确定
```

### Week 2: 核心 UI 实现

```
Day 6-7 (Mon-Tue):   ChatInterface 组件
                      - 消息列表
                      - 流式显示
                      - Tool 调用卡片 (借鉴 agent-chat-ui 设计)

Day 8 (Wed):         ChatInput 组件
                      - 输入框 + 文件上传按钮
                      - 提交逻辑
                      - Zod 验证

Day 9-10 (Thu-Fri):  ConversationList 侧边栏
                      - 对话列表
                      - 新建对话
                      - 搜索和过滤
────────────────────────────────────────────────────
Milestone M2: 基础对话功能可 Demo
```

### Week 3: 高级功能 + RAG 集成

```
Day 11-12 (Mon-Tue): 文档上传 UI
                      - React Dropzone
                      - 上传进度
                      - 文档列表

Day 13 (Wed):        Tool Renderer (RAG 显示)
                      - 语义搜索结果卡片
                      - 文档引用可视化
                      - 借鉴 agent-chat-ui 的 Artifact 设计

Day 14-15 (Thu-Fri): WebSocket 集成
                      - 实时流式响应
                      - 错误处理
                      - 重连逻辑
────────────────────────────────────────────────────
Milestone M3: 功能完整的 MVP
```

### Week 4: 优化与生产部署 (可选)

```
Day 16 (Mon):       响应式设计 + 暗色模式
Day 17 (Tue):       性能优化
                     - Code splitting
                     - Lighthouse 审计
Day 18-19 (Wed-Thu): E2E 测试 (Playwright)
Day 20 (Fri):       生产部署 + 文档
────────────────────────────────────────────────────
Milestone M4: 生产就绪
```

---

## 📋 PHASE 1: 准备与设计研究 (Week 1, 3 SP)

### Story 4.0: Staging 验证与设计准备

**故事点**: 3
**优先级**: P0 (阻塞)
**持续时间**: Week 1
**团队**: Backend Lead + Frontend Lead

---

#### Task 4.0.1: 后端 Staging 部署与负载测试

**故事点**: 1
**负责人**: Backend Lead
**持续时间**: 1 day

**目标**: 确保后端 API 在生产环境稳定可靠

**Acceptance Criteria**:

```gherkin
Given: Epic 1-3 后端代码完成
When: 部署到 Coolify Staging 环境
Then:
  - [ ] 所有 25 个 API 端点响应正常
  - [ ] 健康检查 /health 返回 200 OK
  - [ ] WebSocket 连接成功
  - [ ] RAG 搜索端点 ≤200ms P99
  - [ ] 并发 50 用户无错误
  - [ ] 数据库连接池稳定
```

**实施步骤**:

```bash
# 1. 部署到 Staging
cd /mnt/d/工作区/云开发/working
git checkout -b staging/epic4-prep
git push origin staging/epic4-prep

# 2. Coolify 部署配置
# (参考 .coolify/deployment.yaml)

# 3. 负载测试 (k6)
k6 run tests/load/conversation-api.js \
  --vus 50 \
  --duration 5m \
  --out json=load-test-results.json

# 4. 验证性能目标
python scripts/validate_performance.py load-test-results.json
```

**性能目标**:

| 端点 | P50 | P95 | P99 |
|------|-----|-----|-----|
| POST /conversations | <100ms | <250ms | <500ms |
| POST /messages | <200ms | <500ms | <1000ms |
| GET /embeddings/search | <100ms | <150ms | <200ms |
| WebSocket 消息延迟 | <50ms | <100ms | <200ms |

**交付物**:

- [ ] Staging 环境 URL: `https://staging-api.yourproject.com`
- [ ] 负载测试报告: `docs/testing/STAGING_LOAD_TEST_REPORT.md`
- [ ] API 文档: `docs/api/STAGING_API_REFERENCE.md`

---

#### Task 4.0.2: Agent-Chat-UI 源码研究与设计映射

**故事点**: 1
**负责人**: Frontend Lead
**持续时间**: 1 day

**目标**: 理解 agent-chat-ui 的设计模式，映射到 Tailark 设计系统

**Acceptance Criteria**:

```gherkin
Given: agent-chat-ui GitHub 仓库
When: 分析源码和 UI 设计
Then:
  - [ ] 识别 5 个核心组件设计模式
  - [ ] 创建 Tailark 映射文档
  - [ ] 提取 UI 交互流程图
  - [ ] 记录值得借鉴的功能点
  - [ ] 避免的反模式清单
```

**研究重点**:

1. **聊天界面布局**
   ```
   研究文件: src/app/thread/[id]/page.tsx
   关注点:
   - 三栏布局 (侧边栏 + 聊天 + Artifact)
   - 响应式断点处理
   - 消息列表渲染优化
   ```

2. **Tool 调用可视化**
   ```
   研究文件: src/components/ToolInvocation.tsx
   关注点:
   - 折叠卡片设计
   - JSON 格式化显示
   - 状态指示器 (pending/success/error)
   ```

3. **流式响应处理**
   ```
   研究文件: src/hooks/useStreamingMessage.ts
   关注点:
   - SSE 事件处理
   - 增量内容拼接
   - 打字机效果实现
   ```

4. **Artifact 侧边栏**
   ```
   研究文件: src/components/ArtifactPanel.tsx
   关注点:
   - 侧边栏显示/隐藏逻辑
   - Artifact 渲染器
   - 可调整宽度
   ```

5. **对话管理**
   ```
   研究文件: src/components/ThreadList.tsx
   关注点:
   - 列表排序和过滤
   - 搜索实现
   - 分页策略
   ```

**输出文档**: `/docs/design/AGENT_CHAT_UI_DESIGN_MAPPING.md`

```markdown
# Agent-Chat-UI 设计映射到 Tailark

## 1. 聊天界面布局

### agent-chat-ui 原设计
- 三栏布局: 240px sidebar + flex main + 400px artifact
- 断点: <768px 隐藏 sidebar, <1024px 隐藏 artifact

### Tailark 映射
- 使用 Tailark Grid System
- 自定义断点: sm/md/lg/xl
- 颜色: primary/secondary/accent

## 2. Tool 调用卡片

### agent-chat-ui 原设计
```tsx
<div className="tool-card bg-gray-100 rounded-lg p-4">
  <div className="header flex justify-between">
    <span className="tool-name">search_documents</span>
    <button>Collapse</button>
  </div>
  <pre className="tool-input">{JSON.stringify(input)}</pre>
  <div className="tool-output">{output}</div>
</div>
```

### Tailark 映射
```tsx
<TailarkCard variant="outlined" className="tool-card">
  <TailarkCardHeader
    title={toolName}
    action={<TailarkIconButton>Collapse</TailarkIconButton>}
  />
  <TailarkCodeBlock language="json">{input}</TailarkCodeBlock>
  <TailarkText>{output}</TailarkText>
</TailarkCard>
```

## 3. 流式响应

### agent-chat-ui 方法
- 使用 SSE
- 增量拼接 `messageContent += chunk`
- CSS 打字机动画

### Tailark 实现
- 保持 SSE (已在后端实现)
- Zustand store 管理消息状态
- Tailark Animation utilities

## 4. 值得借鉴的功能

✅ Tool 调用折叠卡片 (提高可读性)
✅ Artifact 侧边栏模式 (文档预览)
✅ 消息搜索和过滤 (UX 提升)
✅ 时间旅行调试 UI (可选 Phase 2)

## 5. 避免的反模式

❌ 大组件文件 (>500 行)
❌ 紧耦合到 LangGraph SDK (我们用 FastAPI)
❌ 缺少 TypeScript 严格模式
❌ 没有单元测试
```

**交付物**:

- [ ] 设计映射文档
- [ ] Figma 线框图 (基于 agent-chat-ui 灵感)
- [ ] 组件清单 (20-25 个组件)

---

#### Task 4.0.3: Vite + React 19 + Tailark 技术栈验证

**故事点**: 1
**负责人**: Frontend Developer
**持续时间**: 1 day

**目标**: 搭建开发环境并验证技术栈兼容性

**Acceptance Criteria**:

```gherkin
Given: Vite 6, React 19, Tailark 最新版
When: 创建项目脚手架
Then:
  - [ ] npm run dev 成功启动
  - [ ] Tailark 组件正常渲染
  - [ ] TypeScript 严格模式通过
  - [ ] Zustand + TanStack Query 集成
  - [ ] 热重载工作正常
  - [ ] Mock API 可调用
```

**实施步骤**:

```bash
# 1. 创建 Vite 项目
cd /mnt/d/工作区/云开发/working
npm create vite@latest frontend -- --template react-ts

cd frontend

# 2. 安装依赖
npm install \
  react@19.0.0 \
  react-dom@19.0.0 \
  @tanstack/react-query \
  zustand \
  react-hook-form \
  zod \
  socket.io-client \
  tailwindcss \
  @tailark/ui

# 3. 配置 TypeScript
cat > tsconfig.json <<EOF
{
  "compilerOptions": {
    "target": "ES2020",
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "skipLibCheck": true
  }
}
EOF

# 4. 配置 Tailwind + Tailark
npx tailwindcss init -p
# 编辑 tailwind.config.js 添加 Tailark 预设

# 5. Mock API 服务器 (MSW)
npm install -D msw
npx msw init public/
```

**项目结构**:

```
frontend/
├── src/
│   ├── components/
│   │   ├── chat/
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── ChatInput.tsx
│   │   │   └── MessageList.tsx
│   │   ├── conversation/
│   │   │   └── ConversationList.tsx
│   │   ├── document/
│   │   │   └── DocumentUpload.tsx
│   │   └── shared/
│   │       ├── ToolCard.tsx
│   │       └── ArtifactPanel.tsx
│   ├── services/
│   │   ├── api.ts
│   │   └── websocket.ts
│   ├── stores/
│   │   ├── conversation.ts
│   │   └── message.ts
│   ├── hooks/
│   │   ├── useChat.ts
│   │   └── useWebSocket.ts
│   ├── types/
│   │   └── api.d.ts
│   └── main.tsx
├── public/
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

**验证测试**:

```tsx
// src/App.tsx - 验证 Tailark 工作
import { TailarkButton, TailarkCard } from '@tailark/ui';

export default function App() {
  return (
    <div className="p-8">
      <TailarkCard>
        <h1 className="text-2xl font-bold">
          Epic 4 Frontend - 技术栈验证
        </h1>
        <TailarkButton variant="primary">
          测试按钮
        </TailarkButton>
      </TailarkCard>
    </div>
  );
}
```

**交付物**:

- [ ] 可运行的前端项目
- [ ] 依赖版本锁定 (package-lock.json)
- [ ] 开发环境文档: `frontend/README.md`

---

## 📋 PHASE 2: 核心 UI 开发 (Week 2, 5 SP)

### Story 4.1: 聊天核心功能实现

**故事点**: 5
**优先级**: P0 (阻塞)
**持续时间**: Week 2
**团队**: Frontend Lead + Frontend Developer

---

#### Task 4.1.1: ChatInterface 和消息显示组件

**故事点**: 2
**负责人**: Frontend Lead
**持续时间**: 2 days

**目标**: 实现聊天界面主组件和消息列表

**Acceptance Criteria**:

```gherkin
Given: 用户进入对话页面
When: 加载消息历史
Then:
  - [ ] 显示完整消息列表 (用户 + 助手)
  - [ ] 支持流式消息实时显示
  - [ ] Tool 调用渲染为折叠卡片
  - [ ] 滚动到最新消息
  - [ ] 加载状态显示
  - [ ] 错误处理和重试
```

**组件设计**:

```tsx
// src/components/chat/ChatInterface.tsx

import { useParams } from 'react-router-dom';
import { useChat } from '@/hooks/useChat';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { TailarkCard, TailarkSpinner } from '@tailark/ui';

export function ChatInterface() {
  const { conversationId } = useParams<{ conversationId: string }>();
  const {
    messages,
    isLoading,
    error,
    sendMessage,
    retryLastMessage
  } = useChat(conversationId);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <TailarkSpinner size="large" />
      </div>
    );
  }

  if (error) {
    return (
      <TailarkCard variant="error">
        <p>加载失败: {error.message}</p>
        <button onClick={retryLastMessage}>重试</button>
      </TailarkCard>
    );
  }

  return (
    <div className="flex flex-col h-screen">
      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto p-4">
        <MessageList messages={messages} />
      </div>

      {/* 输入框 */}
      <div className="border-t p-4">
        <ChatInput onSend={sendMessage} />
      </div>
    </div>
  );
}
```

```tsx
// src/components/chat/MessageList.tsx

import { Message } from '@/types/api';
import { MessageBubble } from './MessageBubble';
import { ToolCard } from '@/components/shared/ToolCard';

interface MessageListProps {
  messages: Message[];
}

export function MessageList({ messages }: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="space-y-4">
      {messages.map((message) => (
        <div key={message.id}>
          {/* 普通消息 */}
          <MessageBubble
            role={message.role}
            content={message.content}
            timestamp={message.created_at}
          />

          {/* Tool 调用 (借鉴 agent-chat-ui 设计) */}
          {message.tool_calls?.map((tool) => (
            <ToolCard
              key={tool.id}
              name={tool.name}
              input={tool.input}
              output={tool.output}
              status={tool.status}
            />
          ))}
        </div>
      ))}
      <div ref={messagesEndRef} />
    </div>
  );
}
```

```tsx
// src/components/chat/MessageBubble.tsx

import { TailarkCard, TailarkText } from '@tailark/ui';
import { formatDistanceToNow } from 'date-fns';

interface MessageBubbleProps {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

export function MessageBubble({ role, content, timestamp }: MessageBubbleProps) {
  const isUser = role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <TailarkCard
        className={`max-w-[70%] ${
          isUser
            ? 'bg-primary-500 text-white'
            : 'bg-gray-100 dark:bg-gray-800'
        }`}
      >
        <TailarkText className="whitespace-pre-wrap">
          {content}
        </TailarkText>
        <TailarkText variant="caption" className="mt-2 opacity-70">
          {formatDistanceToNow(new Date(timestamp), { addSuffix: true })}
        </TailarkText>
      </TailarkCard>
    </div>
  );
}
```

**流式消息处理**:

```tsx
// src/hooks/useChat.ts

import { useEffect, useState } from 'react';
import { useWebSocket } from './useWebSocket';
import { useChatStore } from '@/stores/chat';

export function useChat(conversationId: string) {
  const { messages, addMessage, updateMessage } = useChatStore();
  const { connected, sendMessage: wsSend } = useWebSocket(conversationId);

  useEffect(() => {
    // 监听 WebSocket 流式事件
    socket.on('message_delta', (delta: { content: string }) => {
      // 增量更新消息内容
      updateMessage((prev) => ({
        ...prev,
        content: prev.content + delta.content
      }));
    });

    return () => {
      socket.off('message_delta');
    };
  }, [conversationId]);

  const sendMessage = async (content: string) => {
    // 立即显示用户消息
    addMessage({
      id: crypto.randomUUID(),
      role: 'user',
      content,
      created_at: new Date().toISOString()
    });

    // 发送到后端
    wsSend({ type: 'user_message', content });
  };

  return {
    messages: messages[conversationId] || [],
    isLoading: !connected,
    sendMessage
  };
}
```

**Tool 调用卡片** (借鉴 agent-chat-ui):

```tsx
// src/components/shared/ToolCard.tsx

import { useState } from 'react';
import {
  TailarkCard,
  TailarkCardHeader,
  TailarkIconButton,
  TailarkCodeBlock
} from '@tailark/ui';
import { ChevronDown, ChevronUp } from 'lucide-react';

interface ToolCardProps {
  name: string;
  input: any;
  output: any;
  status: 'pending' | 'success' | 'error';
}

export function ToolCard({ name, input, output, status }: ToolCardProps) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <TailarkCard
      variant="outlined"
      className={`my-2 ${
        status === 'error' ? 'border-red-500' : 'border-blue-500'
      }`}
    >
      <TailarkCardHeader
        title={
          <div className="flex items-center gap-2">
            <span className="font-mono text-sm">{name}</span>
            <StatusBadge status={status} />
          </div>
        }
        action={
          <TailarkIconButton onClick={() => setCollapsed(!collapsed)}>
            {collapsed ? <ChevronDown /> : <ChevronUp />}
          </TailarkIconButton>
        }
      />

      {!collapsed && (
        <div className="p-4 space-y-2">
          <div>
            <p className="text-sm font-semibold mb-1">Input:</p>
            <TailarkCodeBlock language="json">
              {JSON.stringify(input, null, 2)}
            </TailarkCodeBlock>
          </div>

          {output && (
            <div>
              <p className="text-sm font-semibold mb-1">Output:</p>
              <TailarkCodeBlock language="json">
                {JSON.stringify(output, null, 2)}
              </TailarkCodeBlock>
            </div>
          )}
        </div>
      )}
    </TailarkCard>
  );
}
```

**交付物**:

- [ ] ChatInterface 组件
- [ ] MessageList 组件
- [ ] MessageBubble 组件
- [ ] ToolCard 组件
- [ ] useChat hook
- [ ] 单元测试 (Jest)

---

#### Task 4.1.2: ChatInput 输入框和表单验证

**故事点**: 1
**负责人**: Frontend Developer
**持续时间**: 1 day

**目标**: 实现消息输入框和表单提交逻辑

**Acceptance Criteria**:

```gherkin
Given: 用户在聊天界面
When: 输入消息并提交
Then:
  - [ ] 输入框支持多行文本
  - [ ] Enter 发送, Shift+Enter 换行
  - [ ] 空消息拦截 (Zod 验证)
  - [ ] 发送中禁用输入
  - [ ] 文件上传按钮显示
  - [ ] 字符计数显示
```

**组件实现**:

```tsx
// src/components/chat/ChatInput.tsx

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { TailarkTextarea, TailarkButton, TailarkIcon } from '@tailark/ui';
import { Send, Paperclip } from 'lucide-react';

const messageSchema = z.object({
  content: z.string().min(1, '消息不能为空').max(4000, '消息过长')
});

interface ChatInputProps {
  onSend: (content: string) => Promise<void>;
  disabled?: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isSubmitting }
  } = useForm({
    resolver: zodResolver(messageSchema)
  });

  const content = watch('content', '');

  const onSubmit = async (data: { content: string }) => {
    await onSend(data.content);
    reset();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(onSubmit)();
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="relative">
      <TailarkTextarea
        {...register('content')}
        placeholder="输入消息... (Shift+Enter 换行)"
        rows={3}
        disabled={disabled || isSubmitting}
        onKeyDown={handleKeyDown}
        error={errors.content?.message}
        className="pr-24"
      />

      <div className="absolute bottom-2 right-2 flex items-center gap-2">
        {/* 字符计数 */}
        <span className="text-xs text-gray-500">
          {content.length} / 4000
        </span>

        {/* 文件上传按钮 */}
        <TailarkButton
          variant="ghost"
          size="small"
          type="button"
          onClick={() => {/* 打开文件选择 */}}
        >
          <TailarkIcon icon={Paperclip} />
        </TailarkButton>

        {/* 发送按钮 */}
        <TailarkButton
          variant="primary"
          size="small"
          type="submit"
          disabled={disabled || isSubmitting || !content.trim()}
        >
          <TailarkIcon icon={Send} />
          发送
        </TailarkButton>
      </div>
    </form>
  );
}
```

**交付物**:

- [ ] ChatInput 组件
- [ ] Zod 验证 schema
- [ ] 单元测试

---

#### Task 4.1.3: ConversationList 对话侧边栏

**故事点**: 2
**负责人**: Frontend Lead
**持续时间**: 1 day

**目标**: 实现对话列表和管理功能

**Acceptance Criteria**:

```gherkin
Given: 用户打开应用
When: 查看对话列表
Then:
  - [ ] 显示所有对话 (分页)
  - [ ] 新建对话按钮
  - [ ] 搜索对话 (按标题)
  - [ ] 删除对话 (带确认)
  - [ ] 当前对话高亮
  - [ ] 响应式隐藏 (<768px)
```

**组件实现**:

```tsx
// src/components/conversation/ConversationList.tsx

import { useConversations } from '@/hooks/useConversations';
import { TailarkList, TailarkListItem, TailarkButton, TailarkInput } from '@tailark/ui';
import { Plus, Search, Trash2 } from 'lucide-react';

export function ConversationList() {
  const {
    conversations,
    currentId,
    createConversation,
    deleteConversation,
    searchQuery,
    setSearchQuery
  } = useConversations();

  return (
    <div className="w-64 border-r flex flex-col h-screen">
      {/* 头部 */}
      <div className="p-4 border-b">
        <TailarkButton
          variant="primary"
          fullWidth
          onClick={createConversation}
        >
          <Plus className="mr-2" />
          新建对话
        </TailarkButton>

        <TailarkInput
          placeholder="搜索对话..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="mt-2"
          icon={<Search />}
        />
      </div>

      {/* 对话列表 */}
      <div className="flex-1 overflow-y-auto">
        <TailarkList>
          {conversations.map((conv) => (
            <TailarkListItem
              key={conv.id}
              selected={conv.id === currentId}
              onClick={() => navigateToConversation(conv.id)}
              secondaryAction={
                <TailarkIconButton
                  onClick={() => deleteConversation(conv.id)}
                >
                  <Trash2 />
                </TailarkIconButton>
              }
            >
              <div>
                <p className="font-medium truncate">{conv.title}</p>
                <p className="text-sm text-gray-500">
                  {formatDistanceToNow(new Date(conv.updated_at))}
                </p>
              </div>
            </TailarkListItem>
          ))}
        </TailarkList>
      </div>
    </div>
  );
}
```

**状态管理** (Zustand):

```tsx
// src/stores/conversation.ts

import { create } from 'zustand';
import { api } from '@/services/api';

interface ConversationStore {
  conversations: Conversation[];
  currentId: string | null;
  searchQuery: string;

  loadConversations: () => Promise<void>;
  createConversation: () => Promise<string>;
  deleteConversation: (id: string) => Promise<void>;
  setSearchQuery: (query: string) => void;
}

export const useConversationStore = create<ConversationStore>((set, get) => ({
  conversations: [],
  currentId: null,
  searchQuery: '',

  loadConversations: async () => {
    const data = await api.get('/conversations');
    set({ conversations: data });
  },

  createConversation: async () => {
    const newConv = await api.post('/conversations', {
      title: '新对话',
      system_prompt: 'You are a helpful assistant.'
    });
    set((state) => ({
      conversations: [newConv, ...state.conversations],
      currentId: newConv.id
    }));
    return newConv.id;
  },

  deleteConversation: async (id) => {
    await api.delete(`/conversations/${id}`);
    set((state) => ({
      conversations: state.conversations.filter((c) => c.id !== id)
    }));
  },

  setSearchQuery: (query) => set({ searchQuery: query })
}));
```

**交付物**:

- [ ] ConversationList 组件
- [ ] Zustand store
- [ ] 单元测试

---

## 📋 PHASE 3: 高级功能 (Week 3, 4 SP)

### Story 4.2: 文档管理与 RAG 集成

**故事点**: 4
**优先级**: P0 (阻塞)
**持续时间**: Week 3

---

#### Task 4.2.1: 文档上传 UI (React Dropzone)

**故事点**: 2
**负责人**: Frontend Developer
**持续时间**: 1 day

**目标**: 实现文件拖放上传界面

**Acceptance Criteria**:

```gherkin
Given: 用户在对话中
When: 上传文档 (PDF/TXT/MD)
Then:
  - [ ] 支持拖放上传
  - [ ] 支持点击选择文件
  - [ ] 文件类型验证
  - [ ] 上传进度显示
  - [ ] 上传成功提示
  - [ ] 错误处理
```

**组件实现**:

```tsx
// src/components/document/DocumentUpload.tsx

import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { TailarkCard, TailarkProgress, TailarkButton } from '@tailark/ui';
import { Upload, File } from 'lucide-react';

export function DocumentUpload() {
  const { uploadDocument, uploadProgress, isUploading } = useDocumentUpload();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    acceptedFiles.forEach((file) => {
      uploadDocument(file);
    });
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'text/markdown': ['.md']
    },
    maxSize: 10 * 1024 * 1024 // 10MB
  });

  return (
    <TailarkCard>
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-primary-500 bg-primary-50'
            : 'border-gray-300 hover:border-primary-400'
        }`}
      >
        <input {...getInputProps()} />

        <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />

        {isDragActive ? (
          <p className="text-primary-600 font-medium">
            拖放文件到这里...
          </p>
        ) : (
          <div>
            <p className="text-gray-700 font-medium mb-2">
              拖放文件或点击选择
            </p>
            <p className="text-sm text-gray-500">
              支持 PDF, TXT, MD (最大 10MB)
            </p>
          </div>
        )}

        {isUploading && (
          <div className="mt-4">
            <TailarkProgress value={uploadProgress} />
            <p className="text-sm text-gray-500 mt-2">
              上传中... {uploadProgress}%
            </p>
          </div>
        )}
      </div>
    </TailarkCard>
  );
}
```

**上传逻辑**:

```tsx
// src/hooks/useDocumentUpload.ts

import { useState } from 'react';
import { api } from '@/services/api';

export function useDocumentUpload() {
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);

  const uploadDocument = async (file: File) => {
    setIsUploading(true);
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('file', file);

    try {
      await api.post('/documents/upload', formData, {
        onUploadProgress: (progressEvent) => {
          const progress = Math.round(
            (progressEvent.loaded * 100) / (progressEvent.total || 1)
          );
          setUploadProgress(progress);
        }
      });

      // 上传成功
      toast.success(`${file.name} 上传成功`);
    } catch (error) {
      toast.error(`上传失败: ${error.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  return { uploadDocument, uploadProgress, isUploading };
}
```

**交付物**:

- [ ] DocumentUpload 组件
- [ ] useDocumentUpload hook
- [ ] 文件验证逻辑

---

#### Task 4.2.2: Tool Renderer - RAG 搜索结果显示

**故事点**: 1
**负责人**: Frontend Lead
**持续时间**: 1 day

**目标**: 可视化 RAG 搜索结果 (借鉴 agent-chat-ui Artifact 设计)

**Acceptance Criteria**:

```gherkin
Given: Agent 执行 search_documents tool
When: 显示搜索结果
Then:
  - [ ] 显示文档来源
  - [ ] 显示相似度分数
  - [ ] 高亮匹配文本
  - [ ] 可展开查看完整内容
  - [ ] 点击跳转到文档
```

**组件实现**:

```tsx
// src/components/rag/RAGResultCard.tsx

import { TailarkCard, TailarkBadge, TailarkButton } from '@tailark/ui';
import { FileText, ExternalLink } from 'lucide-react';

interface RAGResult {
  id: string;
  chunk_text: string;
  metadata: {
    filename: string;
    page: number;
  };
  score: number;
}

export function RAGResultCard({ result }: { result: RAGResult }) {
  return (
    <TailarkCard variant="outlined" className="border-l-4 border-l-blue-500">
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-blue-500" />
          <span className="font-medium text-sm">
            {result.metadata.filename}
          </span>
          <TailarkBadge variant="info">
            Page {result.metadata.page}
          </TailarkBadge>
        </div>

        <TailarkBadge
          variant={result.score > 0.8 ? 'success' : 'default'}
        >
          {(result.score * 100).toFixed(1)}% 匹配
        </TailarkBadge>
      </div>

      <p className="text-sm text-gray-700 line-clamp-3">
        {result.chunk_text}
      </p>

      <TailarkButton
        variant="text"
        size="small"
        className="mt-2"
        onClick={() => navigateToDocument(result.id)}
      >
        查看完整文档
        <ExternalLink className="ml-1 h-3 w-3" />
      </TailarkButton>
    </TailarkCard>
  );
}
```

**集成到 ToolCard**:

```tsx
// 在 ToolCard 中特殊处理 search_documents

if (name === 'search_documents' && output) {
  return (
    <div className="space-y-2">
      {output.results.map((result: RAGResult) => (
        <RAGResultCard key={result.id} result={result} />
      ))}
    </div>
  );
}
```

**交付物**:

- [ ] RAGResultCard 组件
- [ ] 集成到 ToolCard

---

#### Task 4.2.3: WebSocket 流式集成

**故事点**: 1
**负责人**: Frontend Developer
**持续时间**: 0.5 day

**目标**: 实现 WebSocket 实时通信

**Acceptance Criteria**:

```gherkin
Given: 用户发送消息
When: 后端流式响应
Then:
  - [ ] 实时显示增量内容
  - [ ] 连接断开自动重连
  - [ ] 错误提示显示
  - [ ] 连接状态指示器
```

**实现**:

```tsx
// src/hooks/useWebSocket.ts

import { useEffect, useRef } from 'react';
import { io, Socket } from 'socket.io-client';

export function useWebSocket(conversationId: string) {
  const socketRef = useRef<Socket | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    // 连接 WebSocket
    const socket = io(import.meta.env.VITE_WS_URL, {
      query: { conversation_id: conversationId },
      auth: { token: getAuthToken() }
    });

    socket.on('connect', () => {
      setConnected(true);
      console.log('WebSocket 已连接');
    });

    socket.on('disconnect', () => {
      setConnected(false);
      console.log('WebSocket 断开');
    });

    socket.on('message_delta', (delta: { content: string }) => {
      // 更新消息内容
      useChatStore.getState().appendToLastMessage(delta.content);
    });

    socket.on('tool_call_start', (tool: ToolCall) => {
      useChatStore.getState().addToolCall(tool);
    });

    socket.on('error', (error: any) => {
      toast.error(`WebSocket 错误: ${error.message}`);
    });

    socketRef.current = socket;

    return () => {
      socket.disconnect();
    };
  }, [conversationId]);

  const sendMessage = (data: any) => {
    socketRef.current?.emit('user_message', data);
  };

  return { connected, sendMessage };
}
```

**连接状态指示器**:

```tsx
// src/components/chat/ConnectionStatus.tsx

export function ConnectionStatus({ connected }: { connected: boolean }) {
  return (
    <div className="flex items-center gap-2 text-sm">
      <div
        className={`h-2 w-2 rounded-full ${
          connected ? 'bg-green-500' : 'bg-red-500'
        }`}
      />
      <span className="text-gray-600">
        {connected ? '已连接' : '未连接'}
      </span>
    </div>
  );
}
```

**交付物**:

- [ ] useWebSocket hook
- [ ] ConnectionStatus 组件

---

## 📋 PHASE 4: 优化与部署 (Week 4, 2 SP, 可选)

### Story 4.3: 生产优化与上线

**故事点**: 2
**优先级**: P1 (高)
**持续时间**: Week 4 (可选)

---

#### Task 4.3.1: 响应式设计 + 暗色模式

**故事点**: 0.5
**完成标准**:

- [ ] 移动端 (<768px) 适配
- [ ] 平板 (768px-1024px) 适配
- [ ] 桌面端 (>1024px) 适配
- [ ] 暗色模式切换
- [ ] 系统偏好检测

**实现**:

```tsx
// src/hooks/useDarkMode.ts

import { useEffect } from 'react';
import { useLocalStorage } from './useLocalStorage';

export function useDarkMode() {
  const [darkMode, setDarkMode] = useLocalStorage('darkMode', false);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  return [darkMode, setDarkMode] as const;
}
```

---

#### Task 4.3.2: 性能优化 (Lighthouse 90+)

**故事点**: 0.5
**完成标准**:

- [ ] Code splitting (React.lazy)
- [ ] 图片优化
- [ ] Bundle 分析
- [ ] Lighthouse 评分 ≥90

**实现**:

```tsx
// src/routes.tsx

import { lazy } from 'react';

const ChatInterface = lazy(() => import('@/components/chat/ChatInterface'));
const DocumentUpload = lazy(() => import('@/components/document/DocumentUpload'));

export const routes = [
  {
    path: '/chat/:id',
    component: ChatInterface
  },
  {
    path: '/documents',
    component: DocumentUpload
  }
];
```

---

#### Task 4.3.3: E2E 测试 + 部署

**故事点**: 1
**完成标准**:

- [ ] Playwright E2E 测试
- [ ] CI/CD 配置 (GitHub Actions)
- [ ] 生产部署 (Coolify)

**E2E 测试示例**:

```typescript
// e2e/chat.spec.ts

import { test, expect } from '@playwright/test';

test('发送消息并接收响应', async ({ page }) => {
  await page.goto('/chat/test-conversation');

  // 输入消息
  await page.fill('[data-testid="chat-input"]', '你好');
  await page.click('[data-testid="send-button"]');

  // 验证消息显示
  await expect(page.locator('.message-bubble').last()).toContainText('你好');

  // 等待 AI 响应
  await page.waitForSelector('.message-bubble:has-text("助手")');
});
```

---

## 📊 总体工作量估算

### Story Points 总结

| Phase | Story | SP | 工作日 |
|-------|-------|----|----|
| 1 | 准备与设计研究 | 3 | 1.5 |
| 2 | 核心 UI 开发 | 5 | 2.5 |
| 3 | 高级功能 | 4 | 2 |
| 4 | 优化与部署 (可选) | 2 | 1 |
| **总计** | **4 Stories** | **14** | **7** |

**时间换算**:
- 1 SP = 0.5 工作日
- 14 SP = 7 工作日 = **3-4 周** (考虑缓冲)

### 成本总结

| 类别 | 成本 |
|------|------|
| **Phase 1** (准备) | $6,000 |
| **Phase 2** (核心 UI) | $7,000 |
| **Phase 3** (高级功能) | $5,000 |
| **Phase 4** (优化, 可选) | $2,000-4,000 |
| **总计 (MVP)** | **$18,000** ✅ |
| **总计 (完整)** | **$20,000-22,000** ✅ |

---

## 🔗 任务依赖关系

```
Task 4.0.1 (Staging 验证)
    ↓
Task 4.0.2 (设计研究) → Task 4.0.3 (环境配置)
    ↓                         ↓
Task 4.1.1 (ChatInterface) ← Task 4.1.2 (ChatInput)
    ↓                         ↓
Task 4.1.3 (ConversationList)
    ↓
Task 4.2.1 (文档上传) → Task 4.2.2 (RAG 显示)
    ↓                         ↓
Task 4.2.3 (WebSocket 集成)
    ↓
Task 4.3.1 (响应式) → Task 4.3.2 (性能优化) → Task 4.3.3 (E2E 测试)
```

---

## ✅ 完成标准 (Definition of Done)

每个 Task 完成必须满足:

- [ ] 代码实现完成并符合 Tailark 设计规范
- [ ] TypeScript 严格模式通过 (零 `any` 类型)
- [ ] 组件单元测试覆盖率 ≥80%
- [ ] ESLint + Prettier 无错误
- [ ] 代码审查通过 (≥1 reviewer)
- [ ] 相关文档更新 (组件 README)
- [ ] Lighthouse 性能评分 ≥90 (最终版)
- [ ] 可访问性检查通过 (ARIA 标签)

---

## 🎯 验收标准 (Acceptance Criteria)

### Epic 4 整体验收

```gherkin
Given: 用户访问前端应用
When: 执行核心流程
Then:
  # 对话功能
  - [ ] 可以新建对话
  - [ ] 可以发送消息并接收流式响应
  - [ ] Tool 调用正确显示
  - [ ] 消息历史正常加载

  # 文档功能
  - [ ] 可以上传文档 (PDF/TXT/MD)
  - [ ] 上传进度正确显示
  - [ ] RAG 搜索结果可视化

  # 性能
  - [ ] 首屏加载 ≤2s
  - [ ] WebSocket 消息延迟 ≤50ms
  - [ ] Lighthouse 评分 ≥90

  # 兼容性
  - [ ] Chrome/Firefox/Safari/Edge 正常工作
  - [ ] 移动端 (iOS/Android) 正常显示
  - [ ] 暗色模式正常切换

  # 用户体验
  - [ ] 错误提示友好
  - [ ] 加载状态清晰
  - [ ] 响应式布局流畅
```

---

## 🚨 风险与缓解策略

### 风险 1: Agent-Chat-UI 设计难以映射到 Tailark

**概率**: 30%
**影响**: 中等
**缓解**:
- Week 1 深入研究 agent-chat-ui 源码
- 提前创建设计映射文档
- 如果映射困难,回退到完全自定义设计

### 风险 2: 后端 API 不稳定

**概率**: 40%
**影响**: 高
**缓解**:
- Task 4.0.1 强制执行 Staging 验证
- API 冻结后才开始前端开发
- 使用 Mock API 并行开发

### 风险 3: WebSocket 集成复杂度超预期

**概率**: 20%
**影响**: 中等
**缓解**:
- 后端已实现 6 种 WebSocket 事件
- 使用成熟的 Socket.IO 客户端
- 预留 0.5 天缓冲时间

### 风险 4: Tailark 组件功能不足

**概率**: 10%
**影响**: 低
**缓解**:
- 提前验证 Tailark 组件库
- 可以自定义扩展 Tailark 组件
- 最坏情况:使用 Headless UI + Tailwind

---

## 📦 交付物清单

### 代码交付物

- [ ] `/frontend/src/` - 完整前端代码
- [ ] `/frontend/tests/` - 单元测试 + E2E 测试
- [ ] `/frontend/package.json` - 依赖版本锁定
- [ ] `/frontend/vite.config.ts` - 构建配置
- [ ] `/frontend/.env.example` - 环境变量模板

### 文档交付物

- [ ] `/docs/design/AGENT_CHAT_UI_DESIGN_MAPPING.md` - 设计映射文档
- [ ] `/docs/frontend/COMPONENT_LIBRARY.md` - 组件库文档
- [ ] `/docs/frontend/DEPLOYMENT_GUIDE.md` - 部署指南
- [ ] `/docs/testing/E2E_TEST_REPORT.md` - E2E 测试报告
- [ ] `/frontend/README.md` - 开发者快速开始

### 部署交付物

- [ ] 生产部署 URL: `https://app.yourproject.com`
- [ ] Staging 环境 URL: `https://staging.yourproject.com`
- [ ] CI/CD Pipeline (GitHub Actions)
- [ ] Lighthouse 报告

---

## 🔄 与原 Epic 4 计划对比

### 原 Epic 4 (完全自定义)

```
时间: 5 周
成本: $62,100
Story Points: 26 SP
方法: 从零设计和实现
```

### Epic 4 v2.0 (混合方案)

```
时间: 3-4 周 ✅ (-1-2 周)
成本: $18,000-22,000 ✅ (-$40,000+)
Story Points: 14 SP ✅ (-12 SP)
方法: 借鉴 agent-chat-ui 设计,Vite 实现
```

### 节省的资源

- **时间节省**: 1-2 周 (20-40%)
- **成本节省**: $40,000+ (65%)
- **风险降低**: 设计已验证 (agent-chat-ui 2000+ stars)

---

## 📈 下一步行动

### 立即行动 (本周)

1. **[ ] 决策批准**: 确认采用混合方案 (方案 C)
2. **[ ] 预算确认**: 批准 $18K-22K 预算
3. **[ ] 团队配置**: 确认 1 Frontend Lead + 1 Frontend Developer
4. **[ ] Staging 部署**: 执行 Task 4.0.1

### Week 1 行动

5. **[ ] 设计研究**: 执行 Task 4.0.2 (研究 agent-chat-ui)
6. **[ ] 环境搭建**: 执行 Task 4.0.3 (Vite + Tailark)
7. **[ ] 设计映射**: 创建 AGENT_CHAT_UI_DESIGN_MAPPING.md
8. **[ ] Figma 设计**: 创建 UI 原型

---

## 📊 关键成功因素

### 必须满足 (MVP)

- [x] 后端 API 稳定 (Epic 1-3 已完成)
- [ ] Agent-Chat-UI 设计研究完成
- [ ] Vite + Tailark 环境验证通过
- [ ] 3 周交付核心功能

### 加分项 (完整版)

- [ ] Lighthouse 90+ 评分
- [ ] E2E 测试覆盖率 ≥70%
- [ ] 暗色模式实现
- [ ] 移动端优化

---

## 🎯 总结

### 方案 C (混合方案) 优势

1. **成本低**: $18K-22K vs $62K (完全自定义) vs $77K (agent-chat-ui 适配)
2. **周期短**: 3-4 周 vs 5 周 vs 9 周
3. **风险低**: 借鉴验证设计 + 保持技术栈兼容性
4. **质量高**: Tailark 设计系统 + agent-chat-ui 最佳实践

### 推荐理由

**混合方案是最佳选择,因为**:
- 保留了 Vite + React + Tailark 技术栈 (与后端 100% 兼容)
- 借鉴了 agent-chat-ui 的成熟设计模式 (无需从零设计)
- 避免了适配器层的维护负担 (直接对接 FastAPI)
- 节省了 40% 时间和 65% 成本 (相比完全自定义)

---

**版本**: 2.0 (混合方案)
**状态**: 待批准
**下一步**: 获得预算批准 → 开始 Task 4.0.1
**预期完成**: 3-4 周后
**信心度**: 85% (高)

---

**文档创建**: 2025-11-20
**作者**: Claude Code (Rapid Prototyper)
**审阅**: 待审阅
**批准**: 待批准

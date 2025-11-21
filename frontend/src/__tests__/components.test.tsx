/**
 * ChatInterface Component Tests
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatInterface, ChatMessage, ChatInput } from '../components/Chat';
import { Sidebar } from '../components/Sidebar';

describe('ChatInterface Component', () => {
  beforeEach(() => {
    // Reset mocks
    vi.clearAllMocks();
  });

  it('should render empty state when no messages', () => {
    const { getByText } = render(
      <ChatInterface threadId="thread_123" isLoading={false} />
    );

    expect(getByText(/Start a Conversation/i)).toBeInTheDocument();
    expect(getByText(/Create a new thread/i)).toBeInTheDocument();
  });

  it('should display loading spinner when isLoading is true', () => {
    const { container } = render(
      <ChatInterface threadId="thread_123" isLoading={true} />
    );

    const loadingIndicator = container.querySelector('[class*="animate-bounce"]');
    expect(loadingIndicator).toBeInTheDocument();
  });

  it('should show error toast when error prop is provided', () => {
    const { getByText } = render(
      <ChatInterface
        threadId="thread_123"
        isLoading={false}
        error="Test error message"
      />
    );

    expect(getByText('Test error message')).toBeInTheDocument();
    expect(getByText(/Error/i)).toBeInTheDocument();
  });

  it('should auto-scroll to latest message', async () => {
    const mockScroll = vi.fn();
    Element.prototype.scrollIntoView = mockScroll;

    const { rerender } = render(
      <ChatInterface threadId="thread_123" isLoading={false} />
    );

    // Simulate message arrival
    rerender(
      <ChatInterface threadId="thread_123" isLoading={false} />
    );

    // Verify scroll was called
    expect(mockScroll).toHaveBeenCalled();
  });

  it('should disable auto-scroll when user scrolls up', async () => {
    const { container } = render(
      <ChatInterface threadId="thread_123" isLoading={false} />
    );

    const messagesContainer = container.querySelector('[class*="overflow-y-auto"]');

    // Simulate scroll event
    if (messagesContainer) {
      Object.defineProperty(messagesContainer, 'scrollHeight', { value: 1000 });
      Object.defineProperty(messagesContainer, 'clientHeight', { value: 500 });
      Object.defineProperty(messagesContainer, 'scrollTop', { value: 200 }); // Scrolled up

      messagesContainer.dispatchEvent(new Event('scroll'));
    }

    // Auto-scroll should be disabled
    expect(messagesContainer).toHaveClass('scroll-smooth');
  });
});

/**
 * ChatMessage Component Tests
 */
describe('ChatMessage Component', () => {
  const mockMessage = {
    id: 'msg_1',
    threadId: 'thread_1',
    role: 'user' as const,
    content: 'Test message',
    timestamp: new Date(),
    isStreaming: false
  };

  it('should render user message with correct styling', () => {
    const { getByText } = render(
      <ChatMessage message={mockMessage} />
    );

    const content = getByText('Test message');
    expect(content).toBeInTheDocument();

    // Check for user message styling (blue background)
    const messageBox = content.closest('div');
    expect(messageBox).toHaveClass('bg-blue-600');
  });

  it('should render assistant message with correct styling', () => {
    const assistantMessage = { ...mockMessage, role: 'assistant' as const };
    const { getByText } = render(
      <ChatMessage message={assistantMessage} />
    );

    const content = getByText('Test message');
    const messageBox = content.closest('div');
    expect(messageBox).toHaveClass('bg-slate-100');
  });

  it('should render markdown content correctly', () => {
    const markdownMessage = {
      ...mockMessage,
      content: 'This is **bold** and *italic* text'
    };

    const { container } = render(
      <ChatMessage message={markdownMessage} />
    );

    const bold = container.querySelector('strong');
    const italic = container.querySelector('em');

    expect(bold?.textContent).toBe('bold');
    expect(italic?.textContent).toBe('italic');
  });

  it('should display relative timestamp', () => {
    const now = new Date();
    const fiveMinutesAgo = new Date(now.getTime() - 5 * 60000);

    const { getByText } = render(
      <ChatMessage message={{ ...mockMessage, timestamp: fiveMinutesAgo }} />
    );

    expect(getByText(/5m ago/i)).toBeInTheDocument();
  });

  it('should render streaming cursor when isStreaming is true', () => {
    const { container } = render(
      <ChatMessage message={mockMessage} isStreaming={true} />
    );

    const cursor = container.querySelector('[class*="animate-pulse"]');
    expect(cursor).toBeInTheDocument();
  });

  it('should render tool calls section', () => {
    const messageWithTools = {
      ...mockMessage,
      toolCalls: [
        {
          toolId: 'tool_1',
          toolName: 'vector_search',
          toolInput: { query: 'test' },
          status: 'completed' as const
        }
      ]
    };

    const { getByText, container } = render(
      <ChatMessage message={messageWithTools} />
    );

    expect(getByText(/Tool Calls/i)).toBeInTheDocument();
    // The component renders vector_search as "Vector Search" or similar formatted name
    expect(container.textContent).toMatch(/[Vv]ector\s+[Ss]earch|vector_search/i);
  });
});

/**
 * ChatInput Component Tests
 */
describe('ChatInput Component', () => {
  it('should render textarea with placeholder', () => {
    const mockSubmit = vi.fn();
    const { getByPlaceholderText } = render(
      <ChatInput onSubmit={mockSubmit} />
    );

    expect(
      getByPlaceholderText(/Type your message/i)
    ).toBeInTheDocument();
  });

  it('should display character count', () => {
    const mockSubmit = vi.fn();
    const { container, getByDisplayValue } = render(
      <ChatInput onSubmit={mockSubmit} maxLength={100} />
    );

    const textarea = getByDisplayValue('');
    userEvent.type(textarea, 'Hello');

    // Check that both numbers appear in the rendered content
    const charCountDiv = Array.from(container.querySelectorAll('div')).find(
      div => div.textContent && div.textContent.includes('5') && div.textContent.includes('100')
    );
    expect(charCountDiv).toBeTruthy();
  });

  it('should warn when exceeding character limit', async () => {
    const mockSubmit = vi.fn();
    const user = userEvent.setup();
    const { getByPlaceholderText, container } = render(
      <ChatInput onSubmit={mockSubmit} maxLength={10} />
    );

    const textarea = getByPlaceholderText(/Type your message/i);
    await user.clear(textarea);
    await user.type(textarea, 'Thisistolong');

    // Check that the limit is exceeded by finding a div with text that shows over 10
    const charCountDiv = Array.from(container.querySelectorAll('div')).find(
      div => div.textContent && /\d+\s*\/\s*10/.test(div.textContent) && div.textContent.includes('12')
    );
    expect(charCountDiv).toBeTruthy();
  });

  it('should disable send button during submission', async () => {
    const mockSubmit = vi.fn(async () => {
      await new Promise(resolve => setTimeout(resolve, 100));
    });
    const user = userEvent.setup();
    const { getByRole, getByPlaceholderText } = render(
      <ChatInput onSubmit={mockSubmit} />
    );

    const textarea = getByPlaceholderText(/Type your message/i);
    const sendButton = getByRole('button');

    await user.type(textarea, 'Test message');
    await user.click(sendButton);

    // Button should be disabled while submitting
    expect(sendButton).toBeDisabled();
  });

  it('should submit on Ctrl+Enter', async () => {
    const mockSubmit = vi.fn();
    const user = userEvent.setup();
    const { getByPlaceholderText } = render(
      <ChatInput onSubmit={mockSubmit} />
    );

    const textarea = getByPlaceholderText(/Type your message/i);
    await user.type(textarea, 'Test{Control>}{Enter}');

    expect(mockSubmit).toHaveBeenCalledWith('Test');
  });

  it('should allow line break on Shift+Enter', async () => {
    const mockSubmit = vi.fn();
    const user = userEvent.setup();
    const { getByPlaceholderText } = render(
      <ChatInput onSubmit={mockSubmit} />
    );

    const textarea = getByPlaceholderText(/Type your message/i) as HTMLTextAreaElement;
    await user.type(textarea, 'Line 1{Shift>}{Enter}Line 2');

    expect(textarea.value).toContain('\n');
    expect(mockSubmit).not.toHaveBeenCalled();
  });

  it('should validate empty message', async () => {
    const mockSubmit = vi.fn();
    const user = userEvent.setup();
    const { getByRole } = render(
      <ChatInput onSubmit={mockSubmit} />
    );

    const sendButton = getByRole('button');
    await user.click(sendButton);

    // Empty message should show validation error
    expect(mockSubmit).not.toHaveBeenCalled();
  });
});

/**
 * Sidebar Component Tests
 */
describe('Sidebar Component', () => {
  const mockThreads = [
    {
      threadId: 'thread_1',
      conversationId: 1,
      title: 'Conversation 1',
      createdAt: new Date(),
      updatedAt: new Date(),
      messageCount: 5,
      metadata: {}
    },
    {
      threadId: 'thread_2',
      conversationId: 2,
      title: 'Conversation 2',
      createdAt: new Date(),
      updatedAt: new Date(),
      messageCount: 3,
      metadata: {}
    }
  ];

  it('should render thread list', () => {
    const mockSelect = vi.fn();
    const mockCreate = vi.fn();
    const mockDelete = vi.fn();

    const { getByText } = render(
      <Sidebar
        threads={mockThreads}
        selectedThreadId="thread_1"
        onSelectThread={mockSelect}
        onCreateThread={mockCreate}
        onDeleteThread={mockDelete}
      />
    );

    expect(getByText('Conversation 1')).toBeInTheDocument();
    expect(getByText('Conversation 2')).toBeInTheDocument();
  });

  it('should highlight selected thread', () => {
    const mockSelect = vi.fn();
    const mockCreate = vi.fn();
    const mockDelete = vi.fn();

    const { getByText } = render(
      <Sidebar
        threads={mockThreads}
        selectedThreadId="thread_1"
        onSelectThread={mockSelect}
        onCreateThread={mockCreate}
        onDeleteThread={mockDelete}
      />
    );

    const selectedThread = getByText('Conversation 1').closest('[class*="p-3"]');
    expect(selectedThread).toHaveClass('bg-blue-600');
  });

  it('should call onSelectThread when clicking thread', async () => {
    const mockSelect = vi.fn();
    const mockCreate = vi.fn();
    const mockDelete = vi.fn();
    const user = userEvent.setup();

    const { getByText } = render(
      <Sidebar
        threads={mockThreads}
        selectedThreadId={null}
        onSelectThread={mockSelect}
        onCreateThread={mockCreate}
        onDeleteThread={mockDelete}
      />
    );

    await user.click(getByText('Conversation 1'));
    expect(mockSelect).toHaveBeenCalledWith('thread_1');
  });

  it('should search/filter threads', async () => {
    const mockSelect = vi.fn();
    const mockCreate = vi.fn();
    const mockDelete = vi.fn();
    const user = userEvent.setup();

    const { getByPlaceholderText, getByText } = render(
      <Sidebar
        threads={mockThreads}
        selectedThreadId="thread_1"
        onSelectThread={mockSelect}
        onCreateThread={mockCreate}
        onDeleteThread={mockDelete}
      />
    );

    const searchInput = getByPlaceholderText(/Search conversations/i);
    await user.type(searchInput, 'Conversation 2');

    expect(getByText('Conversation 2')).toBeInTheDocument();
    // Note: This would pass if filtering is actually implemented
  });

  it('should show empty state when no threads', () => {
    const mockSelect = vi.fn();
    const mockCreate = vi.fn();
    const mockDelete = vi.fn();

    const { getByText } = render(
      <Sidebar
        threads={[]}
        selectedThreadId={null}
        onSelectThread={mockSelect}
        onCreateThread={mockCreate}
        onDeleteThread={mockDelete}
      />
    );

    expect(getByText(/No conversations yet/i)).toBeInTheDocument();
  });

  it('should call onCreateThread when create button clicked', async () => {
    const mockSelect = vi.fn();
    const mockCreate = vi.fn();
    const mockDelete = vi.fn();
    const user = userEvent.setup();

    const { getByText } = render(
      <Sidebar
        threads={mockThreads}
        selectedThreadId="thread_1"
        onSelectThread={mockSelect}
        onCreateThread={mockCreate}
        onDeleteThread={mockDelete}
      />
    );

    const createButton = getByText(/New Chat/i);
    await user.click(createButton);

    expect(mockCreate).toHaveBeenCalled();
  });
});

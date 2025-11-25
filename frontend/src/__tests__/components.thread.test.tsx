/**
 * ThreadList and ThreadDetail Component Tests
 *
 * Tests for the new Thread management components
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThreadList } from '../components/Thread/ThreadList';
import { ThreadDetail } from '../components/Thread/ThreadDetail';
import { Thread } from '../types';

describe('ThreadList Component', () => {
  const mockThreads: Thread[] = [
    {
      threadId: 'thread_1',
      conversationId: 1,
      title: 'React Hooks Discussion',
      createdAt: new Date('2025-11-24'),
      updatedAt: new Date('2025-11-24'),
      messageCount: 5,
    },
    {
      threadId: 'thread_2',
      conversationId: 2,
      title: 'TypeScript Best Practices',
      createdAt: new Date('2025-11-23'),
      updatedAt: new Date('2025-11-23'),
      messageCount: 3,
    },
  ];

  const mockHandlers = {
    onSelectThread: vi.fn(),
    onCreateThread: vi.fn(),
    onDeleteThread: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders thread list with threads', () => {
    render(
      <ThreadList
        threads={mockThreads}
        selectedThreadId="thread_1"
        {...mockHandlers}
      />
    );

    expect(screen.getByText('React Hooks Discussion')).toBeInTheDocument();
    expect(screen.getByText('TypeScript Best Practices')).toBeInTheDocument();
  });

  it('renders empty state when no threads', () => {
    render(
      <ThreadList
        threads={[]}
        selectedThreadId={null}
        {...mockHandlers}
      />
    );

    expect(screen.getByText('No chats yet')).toBeInTheDocument();
  });

  it('calls onSelectThread when thread is clicked', async () => {
    const user = userEvent.setup();
    render(
      <ThreadList
        threads={mockThreads}
        selectedThreadId={null}
        {...mockHandlers}
      />
    );

    const threadButton = screen.getByText('React Hooks Discussion');
    await user.click(threadButton);

    expect(mockHandlers.onSelectThread).toHaveBeenCalledWith('thread_1');
  });

  it('calls onCreateThread when create button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <ThreadList
        threads={mockThreads}
        selectedThreadId={null}
        {...mockHandlers}
      />
    );

    const createButton = screen.getByText('New Chat');
    await user.click(createButton);

    expect(mockHandlers.onCreateThread).toHaveBeenCalled();
  });

  it('filters threads by search query', async () => {
    const user = userEvent.setup();
    render(
      <ThreadList
        threads={mockThreads}
        selectedThreadId={null}
        {...mockHandlers}
      />
    );

    const searchInput = screen.getByPlaceholderText('Search chats...');
    await user.type(searchInput, 'React');

    expect(screen.getByText('React Hooks Discussion')).toBeInTheDocument();
    expect(screen.queryByText('TypeScript Best Practices')).not.toBeInTheDocument();
  });

  it('clears search when X button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <ThreadList
        threads={mockThreads}
        selectedThreadId={null}
        {...mockHandlers}
      />
    );

    const searchInput = screen.getByPlaceholderText('Search chats...');
    await user.type(searchInput, 'React');

    const clearButton = screen.getByRole('button', { name: 'Clear search' });
    await user.click(clearButton);

    expect((searchInput as HTMLInputElement).value).toBe('');
  });

  it('shows delete confirmation on first click', async () => {
    const user = userEvent.setup();
    render(
      <ThreadList
        threads={mockThreads}
        selectedThreadId={null}
        {...mockHandlers}
      />
    );

    const threadItem = screen.getByText('React Hooks Discussion').closest('div[role="button"]') as HTMLElement;
    const deleteButton = within(threadItem).getByRole('button', { name: 'Delete chat' });

    await user.click(deleteButton);

    // Confirm button should appear
    const confirmButton = within(threadItem).getByRole('button', { name: 'Delete' });
    expect(confirmButton).toBeInTheDocument();
  });

  it('calls onDeleteThread when delete is confirmed', async () => {
    const user = userEvent.setup();
    render(
      <ThreadList
        threads={mockThreads}
        selectedThreadId={null}
        {...mockHandlers}
      />
    );

    const threadItem = screen.getByText('React Hooks Discussion').closest('div[role="button"]') as HTMLElement;
    let deleteButton = within(threadItem).getByRole('button', { name: 'Delete chat' });

    await user.click(deleteButton);

    const confirmButton = within(threadItem).getByRole('button', { name: 'Delete' });
    await user.click(confirmButton);

    expect(mockHandlers.onDeleteThread).toHaveBeenCalledWith('thread_1');
  });

  it('highlights selected thread', () => {
    render(
      <ThreadList
        threads={mockThreads}
        selectedThreadId="thread_1"
        {...mockHandlers}
      />
    );

    const selectedThread = screen.getByText('React Hooks Discussion').closest('div[role="button"]') as HTMLElement;
    expect(selectedThread).toHaveClass('bg-primary/10');
  });

  it('displays loading state', () => {
    render(
      <ThreadList
        threads={[]}
        selectedThreadId={null}
        isLoading={true}
        {...mockHandlers}
      />
    );

    expect(screen.getByText('Loading chats...')).toBeInTheDocument();
  });

  it('shows thread count at bottom', () => {
    render(
      <ThreadList
        threads={mockThreads}
        selectedThreadId={null}
        {...mockHandlers}
      />
    );

    expect(screen.getByText('2 chats')).toBeInTheDocument();
  });

  it('sorts threads by most recent first', () => {
    const unsortedThreads: Thread[] = [
      { ...mockThreads[1], updatedAt: new Date('2025-11-23') } as Thread,
      { ...mockThreads[0], updatedAt: new Date('2025-11-24') } as Thread,
    ];

    render(
      <ThreadList
        threads={unsortedThreads}
        selectedThreadId={null}
        {...mockHandlers}
      />
    );

    const items = screen.getAllByText(/Discussion|Practices/);
    expect(items[0]).toHaveTextContent('React Hooks Discussion');
    expect(items[1]).toHaveTextContent('TypeScript Best Practices');
  });
});

describe('ThreadDetail Component', () => {
  const mockThread: Thread = {
    threadId: 'thread_1',
    conversationId: 42,
    title: 'React Hooks Discussion',
    createdAt: new Date('2025-11-24'),
    updatedAt: new Date('2025-11-24'),
    messageCount: 15,
    metadata: {
      tags: ['react', 'hooks'],
      priority: 'high',
    },
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders thread details', () => {
    render(<ThreadDetail thread={mockThread} />);

    expect(screen.getByText('React Hooks Discussion')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByText('15')).toBeInTheDocument();
  });

  it('shows empty state when no thread is selected', () => {
    render(<ThreadDetail thread={null} />);

    expect(screen.getByText('No thread selected')).toBeInTheDocument();
  });

  it('allows editing thread title', async () => {
    const user = userEvent.setup();
    render(<ThreadDetail thread={mockThread} />);

    const titleContainer = screen.getByText('React Hooks Discussion').closest('div');
    await user.click(titleContainer!);

    const input = screen.getByDisplayValue('React Hooks Discussion') as HTMLInputElement;
    expect(input).toBeInTheDocument();
  });

  it('copies thread ID to clipboard', async () => {
    const user = userEvent.setup();
    const writeTextMock = vi.fn().mockResolvedValue(undefined);

    // Mock clipboard API
    vi.spyOn(navigator.clipboard, 'writeText').mockImplementation(writeTextMock);

    render(<ThreadDetail thread={mockThread} />);

    const button = screen.getByText('Copy Thread ID');
    await user.click(button);

    expect(writeTextMock).toHaveBeenCalledWith('42');
  });

  it('displays metadata when present', () => {
    render(<ThreadDetail thread={mockThread} />);

    expect(screen.getByText('Metadata')).toBeInTheDocument();
    // The metadata JSON should be displayed
    const metadataText = screen.getByText(/tags/);
    expect(metadataText).toBeInTheDocument();
  });

  it('does not display metadata section when empty', () => {
    const threadWithoutMetadata = { ...mockThread, metadata: {} };
    render(<ThreadDetail thread={threadWithoutMetadata} />);

    expect(screen.queryByText('Metadata')).not.toBeInTheDocument();
  });

  it('shows loading state', () => {
    render(<ThreadDetail thread={null} isLoading={true} />);

    expect(screen.getByText('Loading thread...')).toBeInTheDocument();
  });

  it('displays formatted timestamps', () => {
    render(<ThreadDetail thread={mockThread} />);

    expect(screen.getByText('Created')).toBeInTheDocument();
    expect(screen.getByText('Last Updated')).toBeInTheDocument();
  });
});

import { useState, useEffect } from 'react';
import { useChatStore, useThreadsStore, useUIStore } from './store';
import { useChat, useThread, useTypingIndicator, useAutoTitle } from './hooks';
import { conversationApi } from './services/api';
import { ChatInterface, ChatInput } from './components/Chat';
import { Sidebar } from './components/Sidebar';
import { ThemeToggle } from './components/Theme/ThemeToggle';
import './index.css';

/**
 * Main App Component
 *
 * Integrates:
 * - Sidebar with thread list
 * - ChatInterface for messages
 * - ChatInput for message submission
 * - State management with Zustand
 * - API integration with thread API
 */
export default function App() {
  const [isInitializing, setIsInitializing] = useState(true);
  const [chatError, setChatError] = useState<string | null>(null);
  const [firstMessageSent, setFirstMessageSent] = useState<Set<string>>(new Set());

  // Store state
  const { threads, selectedThreadId, setThreads, setSelectedThread, isLoading } = useThreadsStore();
  const { addMessage, messages } = useChatStore();
  const { isLoading: isChatLoading, theme } = useUIStore();

  // Hooks
  const { sendMessage: sendChatMessage } = useChat(selectedThreadId || '');
  const { createThread } = useThread();
  const { generateTitleFromContent } = useAutoTitle();

  // Setup typing indicator for selected thread
  useTypingIndicator(selectedThreadId || '');

  // Initialize theme on app mount
  useEffect(() => {
    const htmlElement = document.documentElement;
    if (theme === 'dark') {
      htmlElement.classList.add('dark');
    } else {
      htmlElement.classList.remove('dark');
    }
  }, [theme]);

  // Load conversations on app mount
  useEffect(() => {
    const loadConversations = async () => {
      try {
        setIsInitializing(true);
        const response = await conversationApi.getConversations();

        if (response.data && Array.isArray(response.data)) {
          const mappedThreads: typeof threads = (response.data as any[]).map((conv: any) => ({
            threadId: `thread_${conv.id}`,
            conversationId: conv.id,
            title: conv.title || 'Untitled Conversation',
            createdAt: new Date(conv.created_at),
            updatedAt: new Date(conv.updated_at),
            messageCount: conv.message_count || 0,
            metadata: conv.meta || {}
          }));

          setThreads(mappedThreads);

          // Auto-select first thread if available
          if (mappedThreads.length > 0 && mappedThreads[0]) {
            setSelectedThread(mappedThreads[0].threadId);
          }
        }
      } catch (error) {
        console.error('Failed to load conversations:', error);
        setChatError('Failed to load conversations. Please try again.');
      } finally {
        setIsInitializing(false);
      }
    };

    loadConversations();
  }, [setThreads, setSelectedThread]);

  // Handle create new thread
  const handleCreateThread = async () => {
    try {
      const newThreadData = await createThread(`New Conversation ${threads.length + 1}`);
      if (newThreadData && typeof newThreadData === 'object') {
        const convData = newThreadData as any;
        const newThread = {
          threadId: `thread_${convData.id}`,
          conversationId: convData.id,
          title: convData.title || `New Conversation ${threads.length + 1}`,
          createdAt: new Date(convData.created_at),
          updatedAt: new Date(convData.updated_at),
          messageCount: 0,
          metadata: convData.meta || {}
        };
        setThreads([...threads, newThread]);
        setSelectedThread(newThread.threadId);
        setChatError(null);
      }
    } catch (error) {
      console.error('Failed to create thread:', error);
      setChatError('Failed to create new conversation');
    }
  };

  // Handle delete thread
  const handleDeleteThread = async (threadId: string) => {
    try {
      // TODO: Call API to delete conversation
      // await conversationApi.deleteConversation(threadId);

      const updatedThreads = threads.filter((t) => t.threadId !== threadId);
      setThreads(updatedThreads);

      // Select another thread if the deleted one was selected
      if (selectedThreadId === threadId && updatedThreads.length > 0 && updatedThreads[0]) {
        setSelectedThread(updatedThreads[0].threadId);
      } else if (updatedThreads.length === 0) {
        setSelectedThread(null);
      }

      setChatError(null);
    } catch (error) {
      console.error('Failed to delete thread:', error);
      setChatError('Failed to delete conversation');
    }
  };

  // Handle send message
  const handleSendMessage = async (message: string) => {
    if (!selectedThreadId) {
      setChatError('Please select a conversation first');
      return;
    }

    try {
      setChatError(null);

      // Add user message to store immediately
      addMessage(selectedThreadId, {
        id: `msg_${Date.now()}`,
        threadId: selectedThreadId,
        role: 'user',
        content: message,
        timestamp: new Date(),
        isStreaming: false
      });

      // Auto-generate title for first message in this thread
      if (!firstMessageSent.has(selectedThreadId)) {
        setFirstMessageSent(prev => new Set([...prev, selectedThreadId]));
        const threadMessages = messages[selectedThreadId] || [];
        if (threadMessages.length === 1) { // Only user message so far
          // Extract conversationId from threadId (format: thread_<conversationId>)
          const conversationId = selectedThreadId.replace('thread_', '');
          // Generate title asynchronously (don't block message sending)
          generateTitleFromContent(selectedThreadId, conversationId, message);
        }
      }

      // Send to AI
      await sendChatMessage(message);
    } catch (error) {
      console.error('Failed to send message:', error);
      setChatError(error instanceof Error ? error.message : 'Failed to send message');
    }
  };

  // Loading state
  if (isInitializing) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-slate-50 to-slate-100">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-slate-300 border-t-blue-600 mb-4"></div>
          <h2 className="text-xl font-semibold text-slate-900 mb-2">Initializing Chat</h2>
          <p className="text-slate-600">Loading your conversations...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 dark:bg-slate-950 transition-colors">
      {/* Sidebar */}
      <Sidebar
        threads={threads}
        selectedThreadId={selectedThreadId}
        onSelectThread={setSelectedThread}
        onCreateThread={handleCreateThread}
        onDeleteThread={handleDeleteThread}
        isLoading={isLoading}
      />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header with Theme Toggle */}
        <div className="h-14 border-b border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 flex items-center justify-end px-4 gap-2">
          <ThemeToggle />
        </div>

        {selectedThreadId ? (
          <>
            {/* Chat Messages */}
            <ChatInterface
              threadId={selectedThreadId}
              isLoading={isChatLoading}
              error={chatError}
            />

            {/* Chat Input */}
            <ChatInput
              onSubmit={handleSendMessage}
              isLoading={isChatLoading}
              placeholder="Type your message... (Cmd/Ctrl + Enter to send)"
              maxLength={2000}
            />
          </>
        ) : (
          /* Empty State */
          <div className="flex-1 flex flex-col items-center justify-center">
            <div className="text-center max-w-md">
              <div className="text-6xl mb-4">💬</div>
              <h2 className="text-3xl font-bold text-slate-900 dark:text-slate-100 mb-3">No Conversation Selected</h2>
              <p className="text-slate-600 dark:text-slate-400 mb-6">
                Create a new conversation or select one from the sidebar to get started with the AI assistant.
              </p>
              <button
                onClick={handleCreateThread}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors dark:bg-blue-500 dark:hover:bg-blue-600"
              >
                ➕ Create New Chat
              </button>
            </div>
          </div>
        )}

        {/* Error Notification */}
        {chatError && (
          <div className="border-t border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950 px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-xl">⚠️</span>
              <p className="text-red-900 dark:text-red-100">{chatError}</p>
            </div>
            <button
              onClick={() => setChatError(null)}
              className="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 font-semibold"
            >
              ✕
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

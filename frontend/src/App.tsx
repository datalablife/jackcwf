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

        // Handle both response.data (direct array) and response.data.items (ConversationListResponse)
        const conversations = Array.isArray(response.data)
          ? response.data
          : (response.data?.items || []);

        if (conversations && Array.isArray(conversations)) {
          const mappedThreads: typeof threads = (conversations as any[]).map((conv: any) => ({
            threadId: `thread_${conv.id}`,
            conversationId: conv.id,
            title: conv.title || 'Untitled Conversation',
            createdAt: new Date(conv.created_at),
            updatedAt: new Date(conv.updated_at),
            messageCount: conv.message_count || 0,
            metadata: conv.metadata || conv.meta || {}
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
    console.log('[DEBUG] handleCreateThread called, current threads:', threads.length);
    try {
      const newThreadData = await createThread(`New Conversation ${threads.length + 1}`);
      console.log('[DEBUG] createThread response:', newThreadData);
      if (newThreadData && typeof newThreadData === 'object') {
        const convData = newThreadData as any;
        console.log('[DEBUG] convData:', convData);
        const newThread = {
          threadId: `thread_${convData.id}`,
          conversationId: convData.id,
          title: convData.title || `New Conversation ${threads.length + 1}`,
          createdAt: new Date(convData.created_at),
          updatedAt: new Date(convData.updated_at),
          messageCount: 0,
          metadata: convData.meta || {}
        };
        console.log('[DEBUG] newThread created:', newThread);
        setThreads([...threads, newThread]);
        setSelectedThread(newThread.threadId);
        setChatError(null);
        console.log('[DEBUG] State updated, new threads count:', threads.length + 1);
      } else {
        console.log('[DEBUG] newThreadData is not valid object:', newThreadData);
      }
    } catch (error) {
      console.error('[DEBUG] Failed to create thread:', error);
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

  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  // Loading state
  if (isInitializing) {
    return (
      <div className="flex items-center justify-center h-screen w-screen bg-background">
        <div className="flex flex-col items-center gap-4">
          <div className="relative flex h-12 w-12">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary/20 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-12 w-12 bg-primary/10 items-center justify-center">
              <div className="h-6 w-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            </span>
          </div>
          <p className="text-muted-foreground font-medium animate-pulse">Initializing Workspace...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground">
      {/* Sidebar */}
      <div
        className={`${isSidebarOpen ? 'w-[260px]' : 'w-0'
          } bg-black/5 dark:bg-black/20 border-r border-black/5 dark:border-white/5 transition-all duration-300 ease-in-out overflow-hidden flex-shrink-0 relative`}
      >
        <div className="w-[260px] h-full">
          <Sidebar
            threads={threads}
            selectedThreadId={selectedThreadId}
            onSelectThread={setSelectedThread}
            onCreateThread={handleCreateThread}
            onDeleteThread={handleDeleteThread}
            isLoading={isLoading}
            onClose={() => setIsSidebarOpen(false)}
          />
        </div>
      </div>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col overflow-hidden relative bg-white dark:bg-[#212121]">
        {/* Header */}
        <header className="h-14 flex items-center justify-between px-3 absolute top-0 left-0 right-0 z-10">
          <div className="flex items-center gap-2">
            {!isSidebarOpen && (
              <button
                onClick={() => setIsSidebarOpen(true)}
                className="p-2 rounded-lg hover:bg-black/5 dark:hover:bg-white/5 text-muted-foreground hover:text-foreground transition-colors"
                title="Open sidebar"
              >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="icon-md">
                  <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M9 3V21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
            )}
            <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground/80 hover:bg-black/5 dark:hover:bg-white/5 px-3 py-2 rounded-lg cursor-pointer transition-colors">
              <span>ChatGPT 4o</span>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="opacity-50">
                <path d="M6 9l6 6 6-6" />
              </svg>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <ThemeToggle />
            <div className="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center text-white font-medium text-sm">
              U
            </div>
          </div>
        </header>

        {selectedThreadId ? (
          <>
            {/* Chat Messages */}
            <div className="flex-1 overflow-hidden pt-14 pb-4">
              <ChatInterface
                threadId={selectedThreadId}
                isLoading={isChatLoading}
                error={chatError}
              />
            </div>

            {/* Chat Input */}
            <div className="p-4 pt-0 max-w-3xl mx-auto w-full">
              <ChatInput
                onSubmit={handleSendMessage}
                isLoading={isChatLoading}
                placeholder="Message ChatGPT..."
                maxLength={4000}
              />
              <div className="text-center mt-2">
                <p className="text-xs text-muted-foreground/60">
                  ChatGPT can make mistakes. Check important info.
                </p>
              </div>
            </div>
          </>
        ) : (
          /* Empty State */
          <div className="flex-1 flex flex-col items-center justify-center p-8 text-center pt-14">
            <div className="max-w-2xl w-full space-y-8">
              <div className="flex flex-col items-center gap-6">
                <div className="w-12 h-12 rounded-full bg-white dark:bg-white/10 shadow-sm flex items-center justify-center mb-2">
                  <svg width="24" height="24" viewBox="0 0 41 41" fill="none" xmlns="http://www.w3.org/2000/svg" className="text-black dark:text-white">
                    <path d="M37.5324 16.8707C37.9808 15.5241 38.1363 14.0974 37.9886 12.6859C37.8409 11.2744 37.3934 9.91076 36.676 8.6871C35.9585 7.46344 34.9877 6.40639 33.8287 5.58748C32.6697 4.76857 31.3482 4.20659 29.9515 3.93963C28.5548 3.67267 27.1147 3.7068 25.7283 4.03975C24.3419 4.3727 23.0405 4.99694 21.9112 5.87068C20.7819 6.74443 19.8497 7.84771 19.1772 9.10646C18.5047 10.3652 18.1074 11.7506 18.0116 13.1693H18.0076V13.1853C15.2924 13.1853 12.6889 14.2629 10.769 16.1812C8.84915 18.0995 7.77063 20.7011 7.77063 23.4147V23.4387C6.35381 23.5356 4.96996 23.9339 3.71261 24.6073C2.45526 25.2807 1.35284 26.2141 0.480285 27.3438C-0.392272 28.4735 -1.01538 29.7753 -1.34707 31.1619C-1.67876 32.5485 -1.71158 33.9887 -1.44334 35.3854C-1.1751 36.7821 -0.612023 38.1035 0.207858 39.2622C1.02774 40.4209 2.08605 41.3912 3.31077 42.108C4.53549 42.8249 5.89998 43.2716 7.31228 43.4185C8.72458 43.5654 10.1519 43.4091 11.4988 42.9599L11.5148 42.9519C11.6988 43.8359 12.0748 44.6639 12.6148 45.3719C13.1548 46.0799 13.8428 46.6479 14.6268 47.0319C15.4108 47.4159 16.2668 47.6039 17.1308 47.5839C17.9948 47.5639 18.8428 47.3359 19.6108 46.9159L34.6108 38.2559C35.3668 37.8199 36.0028 37.2039 36.4628 36.4639C36.9228 35.7239 37.1908 34.8839 37.2428 34.0199V33.9959C38.6596 33.899 40.0435 33.5007 41.3008 32.8273C42.5582 32.1539 43.6606 31.2205 44.5332 30.0908C45.4057 28.9611 46.0288 27.6593 46.3605 26.2727C46.6922 24.8861 46.725 23.4459 46.4568 22.0492C46.1886 20.6525 45.6255 19.3311 44.8056 18.1724C43.9857 17.0137 42.9274 16.0434 41.7027 15.3266C40.478 14.6097 39.1135 14.163 37.7012 14.0161C36.2889 13.8692 34.8616 14.0255 33.5147 14.4747L33.4987 14.4827C33.3147 13.5987 32.9387 12.7707 32.3987 12.0627C31.8587 11.3547 31.1707 10.7867 30.3867 10.4027C29.6027 10.0187 28.7467 9.8307 27.8827 9.8507C27.0187 9.8707 26.1707 10.0987 25.4027 10.5187L10.4027 19.1787C9.6467 19.6147 9.0107 20.2307 8.5507 20.9707C8.0907 21.7107 7.8227 22.5507 7.7707 23.4147V23.4387H7.77063ZM22.4988 29.8707V19.8707L31.1588 14.8707L39.8188 19.8707V29.8707L31.1588 34.8707L22.4988 29.8707Z" fill="currentColor" />
                  </svg>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 w-full">
                <button onClick={() => handleSendMessage("Help me write a story")} className="p-4 rounded-xl border border-black/10 dark:border-white/10 hover:bg-black/5 dark:hover:bg-white/5 text-left transition-colors">
                  <div className="font-medium mb-1">Help me write</div>
                  <div className="text-sm text-muted-foreground">a story about a robot</div>
                </button>
                <button onClick={() => handleSendMessage("Explain quantum physics")} className="p-4 rounded-xl border border-black/10 dark:border-white/10 hover:bg-black/5 dark:hover:bg-white/5 text-left transition-colors">
                  <div className="font-medium mb-1">Explain</div>
                  <div className="text-sm text-muted-foreground">quantum physics simply</div>
                </button>
                <button onClick={() => handleSendMessage("Plan a trip to Japan")} className="p-4 rounded-xl border border-black/10 dark:border-white/10 hover:bg-black/5 dark:hover:bg-white/5 text-left transition-colors">
                  <div className="font-medium mb-1">Plan a trip</div>
                  <div className="text-sm text-muted-foreground">to Japan for 2 weeks</div>
                </button>
                <button onClick={() => handleSendMessage("Debug this code")} className="p-4 rounded-xl border border-black/10 dark:border-white/10 hover:bg-black/5 dark:hover:bg-white/5 text-left transition-colors">
                  <div className="font-medium mb-1">Debug</div>
                  <div className="text-sm text-muted-foreground">this Python code snippet</div>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Error Notification */}
        {chatError && (
          <div className="absolute bottom-24 left-1/2 -translate-x-1/2 z-50 animate-enter">
            <div className="bg-destructive/90 text-destructive-foreground px-4 py-3 rounded-lg shadow-lg backdrop-blur-md flex items-center gap-3">
              <span className="text-lg">⚠️</span>
              <p className="font-medium text-sm">{chatError}</p>
              <button
                onClick={() => setChatError(null)}
                className="ml-2 hover:bg-white/20 p-1 rounded transition-colors"
              >
                ✕
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

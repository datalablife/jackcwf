import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { ChatMessage, Thread, CacheMetrics, ChatUIState } from '../types';

// Chat Store - 管理消息和对话状态
interface ChatState {
  messages: Record<string, ChatMessage[]>; // threadId -> messages
  currentThreadId: string | null;
  isLoading: boolean;
  error: string | null;
  cacheMetrics: CacheMetrics | null;
  typingUsers: Record<string, Set<string>>; // threadId -> Set of typing user names
  searchQuery: string; // 搜索查询文本

  // Actions
  setCurrentThread: (threadId: string) => void;
  addMessage: (threadId: string, message: ChatMessage) => void;
  updateStreamingMessage: (threadId: string, chunk: string) => void;
  finalizeStreamingMessage: (threadId: string) => void;
  clearMessages: (threadId: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setCacheMetrics: (metrics: CacheMetrics) => void;
  addTypingUser: (threadId: string, userName: string) => void;
  removeTypingUser: (threadId: string, userName: string) => void;
  clearTypingUsers: (threadId: string) => void;
  setSearchQuery: (query: string) => void;
}

export const useChatStore = create<ChatState>()(
  persist(
    (set) => ({
      messages: {},
      currentThreadId: null,
      isLoading: false,
      error: null,
      cacheMetrics: null,
      typingUsers: {},
      searchQuery: '',

      setCurrentThread: (threadId) => set({ currentThreadId: threadId }),

      addMessage: (threadId, message) =>
        set((state) => ({
          messages: {
            ...state.messages,
            [threadId]: [...(state.messages[threadId] || []), message],
          },
        })),

      updateStreamingMessage: (threadId, chunk) =>
        set((state) => {
          const threadMessages = state.messages[threadId] || [];
          if (threadMessages.length === 0) return state;

          const lastMessage = threadMessages[threadMessages.length - 1];
          if (lastMessage && lastMessage.isStreaming) {
            const updatedMessages = [...threadMessages];
            updatedMessages[updatedMessages.length - 1] = {
              ...lastMessage,
              content: lastMessage.content + chunk,
            };
            return {
              messages: {
                ...state.messages,
                [threadId]: updatedMessages,
              },
            };
          }
          return state;
        }),

      finalizeStreamingMessage: (threadId) =>
        set((state) => {
          const threadMessages = state.messages[threadId] || [];
          if (threadMessages.length === 0) return state;

          const lastMessage = threadMessages[threadMessages.length - 1];
          if (lastMessage) {
            const updatedMessages = [...threadMessages];
            updatedMessages[updatedMessages.length - 1] = {
              ...lastMessage,
              isStreaming: false,
            };
            return {
              messages: {
                ...state.messages,
                [threadId]: updatedMessages,
              },
            };
          }
          return state;
        }),

      clearMessages: (threadId) =>
        set((state) => {
          const { [threadId]: _, ...rest } = state.messages;
          return { messages: rest };
        }),

      setLoading: (loading) => set({ isLoading: loading }),

      setError: (error) => set({ error }),

      setCacheMetrics: (metrics) => set({ cacheMetrics: metrics }),

      addTypingUser: (threadId, userName) =>
        set((state) => ({
          typingUsers: {
            ...state.typingUsers,
            [threadId]: new Set([...(state.typingUsers[threadId] || []), userName]),
          },
        })),

      removeTypingUser: (threadId, userName) =>
        set((state) => {
          const typingSet = new Set(state.typingUsers[threadId] || []);
          typingSet.delete(userName);
          return {
            typingUsers: {
              ...state.typingUsers,
              [threadId]: typingSet,
            },
          };
        }),

      clearTypingUsers: (threadId) =>
        set((state) => ({
          typingUsers: {
            ...state.typingUsers,
            [threadId]: new Set(),
          },
        })),

      setSearchQuery: (query) => set({ searchQuery: query }),
    }),
    {
      name: 'chat-storage',
      partialize: (state) => ({
        currentThreadId: state.currentThreadId,
        messages: state.messages,
      }),
    }
  )
);

// Threads Store - Manages thread/conversation list
interface ThreadsState {
  threads: Thread[];
  selectedThreadId: string | null;
  isLoading: boolean;

  // Actions
  setThreads: (threads: Thread[]) => void;
  addThread: (thread: Thread) => void;
  removeThread: (threadId: string) => void;
  updateThread: (threadId: string, thread: Partial<Thread>) => void;
  setSelectedThread: (threadId: string | null) => void;
  setLoading: (loading: boolean) => void;
}

export const useThreadsStore = create<ThreadsState>((set) => ({
  threads: [],
  selectedThreadId: null,
  isLoading: false,

  setThreads: (threads) => set({ threads }),

  addThread: (thread) =>
    set((state) => ({
      threads: [thread, ...state.threads],
    })),

  removeThread: (threadId) =>
    set((state) => ({
      threads: state.threads.filter((t) => t.threadId !== threadId),
    })),

  updateThread: (threadId, updates) =>
    set((state) => ({
      threads: state.threads.map((t) =>
        t.threadId === threadId ? { ...t, ...updates } : t
      ),
    })),

  setSelectedThread: (threadId) => set({ selectedThreadId: threadId }),

  setLoading: (loading) => set({ isLoading: loading }),
}));

// UI Store - 管理 UI 状态
interface UIState extends ChatUIState {
  // 状态
  theme: 'light' | 'dark';

  // Actions
  setSidebarOpen: (open: boolean) => void;
  setSelectedToolId: (toolId: string | undefined) => void;
  setDebugMode: (enabled: boolean) => void;
  setLoading: (loading: boolean) => void;
  setTheme: (theme: 'light' | 'dark') => void;
  toggleTheme: () => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      isLoading: false,
      sidebarOpen: true,
      error: undefined,
      selectedToolId: undefined,
      debugMode: false,
      theme: 'light',

      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      setSelectedToolId: (toolId) => set({ selectedToolId: toolId }),
      setDebugMode: (enabled) => set({ debugMode: enabled }),
      setLoading: (loading) => set({ isLoading: loading }),

      setTheme: (theme) => set({ theme }),
      toggleTheme: () =>
        set((state) => ({
          theme: state.theme === 'light' ? 'dark' : 'light',
        })),
    }),
    {
      name: 'ui-storage',
      partialize: (state) => ({
        theme: state.theme,
        sidebarOpen: state.sidebarOpen,
      }),
    }
  )
);

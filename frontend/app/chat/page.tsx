'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/Header';
import { getToken, getUserIdFromToken } from '@/lib/auth';
import { apiFetch, AuthError } from '@/lib/api';
import { VoiceRecorder } from '@/components/VoiceRecorder';
import { TextToSpeech } from '@/components/TextToSpeech';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  tool_calls?: Array<{ tool: string; params: any; result: any }>;
}

interface Conversation {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
  message_count?: number;
}

type FolderState = {
  open: boolean;
};

// Helper to get tool action description
const getToolActionDescription = (tool: string, params: any, result: any): string => {
  switch (tool) {
    case 'add_task':
      return `✅ Task "${params.title || result?.title || 'created'}" added successfully`;
    case 'update_task':
      const updates = [];
      if (params.title) updates.push(`title: "${params.title}"`);
      if (params.description !== undefined) updates.push(`description updated`);
      if (params.priority) updates.push(`priority: ${params.priority}`);
      if (params.due_date) updates.push(`due date: ${new Date(params.due_date).toLocaleString()}`);
      if (params.due_date === null || params.due_date === '') updates.push(`due date removed`);
      if (params.completed !== undefined) updates.push(`completed: ${params.completed ? 'Yes' : 'No'}`);
      return `✅ Task #${params.task_id} updated: ${updates.join(', ') || 'updated'}`;
    case 'delete_task':
      return `🗑️ Task #${params.task_id} deleted successfully`;
    case 'complete_task':
      return `✅ Task #${params.task_id} marked as complete`;
    case 'list_tasks':
      const count = result?.tasks?.length || 0;
      return `📋 Listed ${count} task${count !== 1 ? 's' : ''}`;
    case 'find_task':
      return `🔍 Found task: "${result?.title || params.query}"`;
    case 'set_task_deadline':
      if (params.due_date) {
        return `📅 Due date set for task #${params.task_id}: ${new Date(params.due_date).toLocaleString()}`;
      } else {
        return `📅 Due date removed from task #${params.task_id}`;
      }
    default:
      return `🔧 ${tool} executed`;
  }
};

// Generate conversation title from first message
const generateConversationTitle = (message: string): string => {
  const trimmed = message.trim();
  if (trimmed.length > 50) {
    return trimmed.substring(0, 50) + '...';
  }
  return trimmed || 'New Chat';
};

export default function ChatPage() {
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userId, setUserId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [loadingConversations, setLoadingConversations] = useState(false);
  const [folder, setFolder] = useState<FolderState>({ open: true });
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const localMessageSeqRef = useRef(0);

  const makeLocalMessageId = (prefix: string): string => {
    localMessageSeqRef.current += 1;
    return `${prefix}-${Date.now()}-${localMessageSeqRef.current}`;
  };

  useEffect(() => {
    const token = getToken();
    const user = getUserIdFromToken();
    
    if (!token || !user) {
      router.replace('/login');
      return;
    }
    
    setIsAuthenticated(true);
    setUserId(user);
    
    // Mobile UX: default to sidebar closed on small screens
    try {
      if (typeof window !== 'undefined' && window.innerWidth < 768) {
        setSidebarOpen(false);
      }
    } catch {}

    // Load conversations list and latest conversation
    const initializeChat = async () => {
      try {
        await loadConversations(user);
        await loadLatestConversation(user);
      } catch (error) {
        console.error('Failed to initialize chat:', error);
      }
    };
    
    initializeChat();
  }, [router]);

  const loadConversations = async (userId: string) => {
    setLoadingConversations(true);
    try {
      // Conversations are user-scoped via JWT, not via userId path
      const response = await apiFetch(`/api/conversations`) as any;
      if (response.conversations) {
        setConversations(response.conversations);
      }
    } catch (error) {
      console.error('Failed to load conversations:', error);
    } finally {
      setLoadingConversations(false);
    }
  };

  const deleteConversation = async (convId: number) => {
    if (!userId) return;
    const ok = confirm('Delete this chat? This cannot be undone.');
    if (!ok) return;

    try {
      await apiFetch(`/api/conversations/${convId}`, { method: 'DELETE' });
      // If we deleted the currently open conversation, reset view
      if (conversationId === convId) {
        setConversationId(null);
        setMessages([]);
      }
      await loadConversations(userId);
      // If nothing selected, load latest available
      if (!conversationId || conversationId === convId) {
        await loadLatestConversation(userId);
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error);
    }
  };

  const deleteAllConversations = async () => {
    if (!userId) return;
    const ok = confirm('Delete ALL chats? This will remove your full chat history.');
    if (!ok) return;

    try {
      await apiFetch(`/api/conversations`, { method: 'DELETE' });
      setConversationId(null);
      setMessages([]);
      await loadConversations(userId);
    } catch (error) {
      console.error('Failed to delete all conversations:', error);
    }
  };

  const loadLatestConversation = async (userId: string) => {
    try {
      // Prefer dedicated endpoint
      const latest = await apiFetch(`/api/conversations/latest`) as any;
      if (latest?.conversation_id) {
        await loadConversation(userId, latest.conversation_id);
      } else {
        // Fallback: load first from list endpoint
        const response = await apiFetch(`/api/conversations`) as any;
        if (response.conversations && response.conversations.length > 0) {
          const latestConversation = response.conversations[0];
          await loadConversation(userId, latestConversation.id);
        }
      }
    } catch (error) {
      console.error('Failed to load latest conversation:', error);
    }
  };

  const loadConversation = async (userId: string, convId: number) => {
    try {
      setConversationId(convId);
      // Mobile UX: close sidebar after selecting a conversation
      try {
        if (typeof window !== 'undefined' && window.innerWidth < 768) {
          setSidebarOpen(false);
        }
      } catch {}
      const messagesResponse = await apiFetch(`/api/conversations/${convId}/messages`) as any;
      if (messagesResponse.messages) {
        const loadedMessages: Message[] = messagesResponse.messages.map((msg: any, idx: number) => ({
          id: msg.id?.toString() || makeLocalMessageId(`loaded-${idx}`),
          role: (msg.sender || msg.role) === 'user' ? 'user' : 'assistant',
          content: msg.message || msg.content || '',
          timestamp: new Date(msg.created_at),
          tool_calls: msg.tool_calls || null,
        }));
        setMessages(loadedMessages);
      } else {
        setMessages([]);
      }
    } catch (error) {
      console.error('Failed to load conversation:', error);
    }
  };

  const startNewChat = () => {
    setConversationId(null);
    setMessages([]);
    setInputMessage('');
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!inputMessage.trim() || !userId || isLoading) return;

    const userMessage: Message = {
      id: makeLocalMessageId('user'),
      role: 'user',
      content: inputMessage,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const currentInput = inputMessage;
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await apiFetch(`/api/${userId}/chat`, {
        method: 'POST',
        body: JSON.stringify({
          message: currentInput,
          conversation_id: conversationId,
        }),
      }) as any;

      // Update conversation ID if new conversation was created
      const finalConvId = response.conversation_id || conversationId;
      if (response.conversation_id && response.conversation_id !== conversationId) {
        setConversationId(response.conversation_id);
      }

      // Reload conversations list to update titles/timestamps
      await loadConversations(userId);
      
      // Reload current conversation from DB to get all persisted messages (including tool_calls)
      // This ensures chat history is properly loaded and persisted
      if (finalConvId) {
        await loadConversation(userId, finalConvId);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage: Message = {
        id: makeLocalMessageId('error'),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isAuthenticated || !userId) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-theme-background">
        <div className="text-center">
          <p className="text-theme-secondary">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <Header />
      <div className="flex min-h-screen bg-theme-background">
        {/* Mobile backdrop for sidebar */}
        {sidebarOpen ? (
          <button
            type="button"
            aria-label="Close sidebar"
            onClick={() => setSidebarOpen(false)}
            className="fixed inset-0 z-30 bg-black/40 md:hidden"
          />
        ) : null}

        {/* Sidebar - Fixed on all screen sizes, toggleable on all sizes */}
        <div
          className={`${
            // Mobile: overlay sidebar
            sidebarOpen
              ? 'w-64 fixed inset-y-0 left-0 z-40 translate-x-0'
              : 'w-0 -translate-x-full'
          } md:fixed md:inset-y-0 md:left-0 md:z-40 transition-all duration-300 border-r border-theme bg-theme-surface overflow-hidden flex flex-col ${
            sidebarOpen ? 'md:w-64' : 'md:w-0'
          }`}
        >
          <div className="p-4 border-b border-theme">
            <button
              onClick={startNewChat}
              className="w-full px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors flex items-center gap-2 justify-center shadow-sm"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              New Chat
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-2">
            {/* Single folder container */}
            <div className="rounded-xl border border-theme bg-theme-card/40 overflow-hidden">
              <div className="flex items-center justify-between px-3 py-2 border-b border-theme">
                <button
                  type="button"
                  onClick={() => setFolder((f) => ({ ...f, open: !f.open }))}
                  className="flex items-center gap-2 text-sm font-semibold text-theme-primary"
                >
                  <span className="inline-flex h-6 w-6 items-center justify-center rounded-lg bg-theme-surface border border-theme">
                    {folder.open ? '▾' : '▸'}
                  </span>
                  Chats
                  <span className="text-xs font-normal text-theme-tertiary">({conversations.length})</span>
                </button>
                <button
                  type="button"
                  onClick={deleteAllConversations}
                  className="text-xs px-2 py-1 rounded-md border border-theme hover:bg-theme-surface text-red-400 hover:text-red-300"
                  title="Delete all chats"
                >
                  Delete All
                </button>
              </div>

              {folder.open ? (
                <div className="p-1">
                  {loadingConversations ? (
                    <div className="text-center text-theme-tertiary text-sm py-4">Loading...</div>
                  ) : conversations.length === 0 ? (
                    <div className="text-center text-theme-tertiary text-sm py-4">No chats yet</div>
                  ) : (
                    <div className="space-y-1">
                      {conversations.map((conv) => (
                        <div
                          key={conv.id}
                          className={`group flex items-stretch rounded-lg border ${
                            conversationId === conv.id
                              ? 'bg-blue-500/15 border-blue-500/30'
                              : 'border-transparent hover:border-theme hover:bg-theme-surface'
                          }`}
                        >
                          <button
                            onClick={() => loadConversation(userId, conv.id)}
                            className="flex-1 text-left px-3 py-2"
                          >
                            <div className="text-sm font-medium truncate text-theme-primary">
                              {conv.title || `Chat ${conv.id}`}
                            </div>
                            <div className="text-xs text-theme-tertiary mt-1">
                              {new Date(conv.updated_at).toLocaleDateString()}
                            </div>
                          </button>
                          <button
                            type="button"
                            onClick={() => deleteConversation(conv.id)}
                            className="hidden md:flex items-center px-2 text-theme-tertiary hover:text-red-300 opacity-0 group-hover:opacity-100 transition-opacity"
                            title="Delete chat"
                          >
                            🗑
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ) : null}
            </div>
          </div>
        </div>

        {/* Main Chat Area - Add left margin on desktop when sidebar is open */}
        <div className={`flex-1 flex flex-col min-w-0 transition-all duration-300 ${sidebarOpen ? 'md:ml-64' : 'md:ml-0'}`}>
          {/* Top Bar - Fixed below Header */}
          <div className={`border-b border-theme bg-theme-surface/80 backdrop-blur px-3 sm:px-4 py-3 flex items-center justify-between fixed top-16 z-40 transition-all duration-300 ${sidebarOpen ? 'md:left-64' : 'left-0'} right-0`}>
            <div className="flex items-center gap-2">
              <button
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  setSidebarOpen(!sidebarOpen);
                }}
                className="p-2 hover:bg-theme-card rounded-lg transition-colors text-theme-secondary hover:text-theme-primary cursor-pointer relative z-50"
                aria-label="Toggle sidebar"
                type="button"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
              <button
                onClick={startNewChat}
                className="px-3 py-1.5 text-sm bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors flex items-center gap-1.5 shadow-sm"
                aria-label="Start new chat"
                type="button"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                New Chat
              </button>
            </div>
            <h1 className="text-base sm:text-lg font-semibold text-theme-primary">AI Chat Assistant</h1>
            <div className="w-9"></div>
          </div>

          {/* Messages Area - Add padding-top for fixed Header and top bar */}
          <div className="flex-1 overflow-y-auto px-3 sm:px-4 py-4 sm:py-6 mt-[112px]">
            <div className="mx-auto w-full max-w-4xl space-y-4">
            {messages.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center text-theme-secondary max-w-2xl">
                  <p className="text-2xl sm:text-3xl mb-3">👋 Welcome!</p>
                  <p className="text-base mb-2">Start a conversation to manage your tasks with AI</p>
                  <p className="text-sm mt-4 text-theme-tertiary">Try: &quot;Add a task to buy groceries&quot; or &quot;Show my tasks&quot;</p>
                </div>
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[88%] sm:max-w-[75%] lg:max-w-[60%] rounded-2xl px-4 py-3 shadow-sm border border-theme/60 ${
                      message.role === 'user'
                        ? 'bg-gradient-to-br from-blue-700 to-indigo-700 dark:from-blue-500 dark:to-indigo-500 text-white border-transparent shadow-lg'
                        : 'bg-theme-surface text-theme-primary'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-sm whitespace-pre-wrap break-words flex-1 font-semibold text-white">{message.content}</p>
                      {message.role === 'assistant' && message.content.trim() && (
                        <div className="flex-shrink-0 mt-1">
                          <TextToSpeech text={message.content} />
                        </div>
                      )}
                    </div>
                    {message.tool_calls && message.tool_calls.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-theme">
                        <p className="text-xs font-semibold mb-2 opacity-90">
                          ✅ Actions completed:
                        </p>
                        <div className="space-y-1.5">
                          {message.tool_calls.map((tool, idx) => {
                            const description = getToolActionDescription(
                              tool.tool,
                              tool.params || {},
                              tool.result || {}
                            );
                            return (
                              <div
                                key={idx}
                                className={`text-xs p-2 rounded-lg ${
                                  message.role === 'user'
                                    ? 'bg-blue-500/30 dark:bg-blue-400/20 text-white'
                                    : 'bg-green-500/10 text-green-600 dark:text-green-400'
                                }`}
                              >
                                {description}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                    <p className={`text-xs mt-2 ${message.role === 'user' ? 'text-white/90 dark:text-blue-100' : 'text-theme-tertiary'}`}>
                      {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
              ))
            )}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-theme-surface rounded-2xl px-4 py-3">
                  <div className="flex items-center gap-2 text-theme-secondary">
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                        fill="none"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    <span className="text-sm">AI is thinking...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Input Area */}
          <div className="sticky bottom-0 z-20 border-t border-theme bg-theme-surface/90 backdrop-blur px-3 sm:px-4 py-3 pb-[calc(env(safe-area-inset-bottom)+12px)]">
            <form onSubmit={handleSendMessage} className="mx-auto w-full max-w-4xl flex gap-2">
              <div className="flex-1 flex items-center gap-2">
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder="Type your message... (e.g., 'Update task 1 title to Buy groceries')"
                  disabled={isLoading}
                  className="flex-1 px-4 py-3 rounded-2xl border border-theme bg-theme-card text-theme-primary placeholder:text-theme-tertiary focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                  style={{
                    backgroundColor: 'var(--bg-card)',
                    color: 'var(--text-primary)',
                    borderColor: 'var(--border-color)',
                  }}
                />
                <div className="flex-shrink-0">
                  <VoiceRecorder
                    onTranscription={(text) => {
                      setInputMessage(text);
                    }}
                    disabled={isLoading}
                  />
                </div>
              </div>
              <button
                type="submit"
                disabled={isLoading || !inputMessage.trim()}
                className="px-6 py-3 bg-blue-500 text-white rounded-xl hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
              >
                {isLoading ? (
                  <span className="flex items-center gap-2">
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                        fill="none"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    Sending...
                  </span>
                ) : (
                  'Send'
                )}
              </button>
            </form>
          </div>
        </div>
      </div>
    </>
  );
}

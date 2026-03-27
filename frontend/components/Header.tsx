'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/useAuth';
import { getToken, getUserIdFromToken } from '@/lib/auth';

interface Notification {
  id: number;
  title: string;
  message: string;
  reminder_type: string;
  is_read: boolean;
  created_at: string;
}

export function Header() {
  const router = useRouter();
  const { user, logout } = useAuth();
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');
  const [showDropdown, setShowDropdown] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const notifRef = useRef<HTMLDivElement>(null);

  const unreadCount = notifications.filter(n => !n.is_read).length;

  // Fetch notifications
  const fetchNotifications = async () => {
    try {
      const token = getToken();
      const userId = getUserIdFromToken();
      if (!token || !userId) return;
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
      const res = await fetch(`${apiUrl}/api/users/${userId}/notifications?limit=20`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setNotifications(data);
      }
    } catch (_) {}
  };

  const markAsRead = async (id: number) => {
    try {
      const token = getToken();
      const userId = getUserIdFromToken();
      if (!token || !userId) return;
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
      await fetch(`${apiUrl}/api/users/${userId}/notifications/${id}/read`, {
        method: 'PATCH',
        headers: { Authorization: `Bearer ${token}` },
      });
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
    } catch (_) {}
  };

  const markAllRead = async () => {
    notifications.filter(n => !n.is_read).forEach(n => markAsRead(n.id));
  };

  useEffect(() => {
    fetchNotifications();
    // Poll every 30 seconds for new notifications
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  // Close notification panel on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
        setShowNotifications(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // Load theme from localStorage on mount
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' || 'dark';
    setTheme(savedTheme);
    document.documentElement.classList.toggle('light', savedTheme === 'light');
  }, []);

  // Toggle theme
  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    document.documentElement.classList.toggle('light', newTheme === 'light');
  };

  // Handle logout
  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  // Get user initials for avatar
  const getInitials = (name?: string | null, email?: string | null) => {
    if (name) {
      return name
        .split(' ')
        .map(n => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2);
    }
    if (email) {
      return email.slice(0, 2).toUpperCase();
    }
    return 'U';
  };

  return (
    <header className="sticky top-0 z-[100] backdrop-blur-sm border-b" style={{
      backgroundColor: theme === 'light' ? 'rgba(255, 255, 255, 0.95)' : 'rgba(15, 23, 42, 0.95)',
      borderBottomColor: theme === 'light' ? '#e2e8f0' : '#334155'
    }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo/Brand */}
          <div className="flex items-center gap-3">
            <div className="bg-gradient-to-br from-blue-500 to-purple-600 p-2 rounded-lg">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
                stroke="currentColor"
                className="w-6 h-6"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296 3.746 3.746 0 013.296-1.043A3.746 3.746 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 013.296 1.043 3.746 3.746 0 011.043 3.296A3.745 3.745 0 0121 12z"
                />
              </svg>
            </div>
            <div>
              <h1 className="text-lg font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
                TaskMate AI
              </h1>
            </div>
          </div>

          {/* Right side: Notifications + Theme toggle + User menu */}
          <div className="flex items-center gap-4">
            {/* Notification Bell */}
            <div className="relative" ref={notifRef}>
              <button
                onClick={() => { setShowNotifications(!showNotifications); if (!showNotifications) fetchNotifications(); }}
                className="relative p-2 rounded-lg transition-colors duration-200"
                style={{ backgroundColor: theme === 'light' ? '#f1f5f9' : '#1e293b' }}
                aria-label="Notifications"
              >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5" style={{ color: theme === 'light' ? '#475569' : '#94a3b8' }}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
                </svg>
                {unreadCount > 0 && (
                  <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center font-bold">
                    {unreadCount > 9 ? '9+' : unreadCount}
                  </span>
                )}
              </button>

              {/* Notification Dropdown */}
              {showNotifications && (
                <div className="absolute right-0 mt-2 w-80 rounded-xl shadow-2xl border z-50 overflow-hidden" style={{ backgroundColor: theme === 'light' ? '#ffffff' : '#1e293b', borderColor: theme === 'light' ? '#e2e8f0' : '#334155' }}>
                  <div className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: theme === 'light' ? '#e2e8f0' : '#334155' }}>
                    <h3 className="font-semibold text-sm" style={{ color: theme === 'light' ? '#0f172a' : '#f1f5f9' }}>Notifications</h3>
                    {unreadCount > 0 && (
                      <button onClick={markAllRead} className="text-xs text-blue-400 hover:text-blue-300">Mark all read</button>
                    )}
                  </div>
                  <div className="max-h-72 overflow-y-auto">
                    {notifications.length === 0 ? (
                      <div className="px-4 py-6 text-center text-sm" style={{ color: theme === 'light' ? '#94a3b8' : '#64748b' }}>
                        No notifications yet
                      </div>
                    ) : (
                      notifications.map(n => (
                        <div
                          key={n.id}
                          onClick={() => !n.is_read && markAsRead(n.id)}
                          className="px-4 py-3 border-b cursor-pointer hover:opacity-80 transition-opacity"
                          style={{
                            borderColor: theme === 'light' ? '#f1f5f9' : '#334155',
                            backgroundColor: n.is_read ? 'transparent' : (theme === 'light' ? '#eff6ff' : '#1e3a5f'),
                          }}
                        >
                          <p className="text-sm font-medium" style={{ color: theme === 'light' ? '#0f172a' : '#f1f5f9' }}>{n.title}</p>
                          <p className="text-xs mt-0.5" style={{ color: theme === 'light' ? '#64748b' : '#94a3b8' }}>{n.message}</p>
                          <p className="text-xs mt-1 opacity-60" style={{ color: theme === 'light' ? '#94a3b8' : '#64748b' }}>
                            {new Date(n.created_at).toLocaleString()}
                          </p>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg transition-colors duration-200"
              style={{
                backgroundColor: theme === 'light' ? '#f1f5f9' : '#1e293b',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = theme === 'light' ? '#e2e8f0' : '#334155';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = theme === 'light' ? '#f1f5f9' : '#1e293b';
              }}
              aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              {theme === 'dark' ? (
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={1.5}
                  stroke="currentColor"
                  className="w-5 h-5 text-yellow-400"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z"
                  />
                </svg>
              ) : (
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={1.5}
                  stroke="currentColor"
                  className="w-5 h-5 text-slate-400"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z"
                  />
                </svg>
              )}
            </button>

            {/* User Menu */}
            <div className="relative">
              <button
                onClick={() => setShowDropdown(!showDropdown)}
                className="flex items-center gap-3 p-2 rounded-lg transition-colors duration-200"
                style={{
                  backgroundColor: showDropdown ? (theme === 'light' ? '#f1f5f9' : '#1e293b') : 'transparent',
                }}
                onMouseEnter={(e) => {
                  if (!showDropdown) {
                    e.currentTarget.style.backgroundColor = theme === 'light' ? '#f1f5f9' : '#1e293b';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!showDropdown) {
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }
                }}
              >
                {/* Avatar */}
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center font-semibold text-white shadow-lg">
                  {user ? getInitials(user.name, user.email) : 'U'}
                </div>
                {/* User info (hidden on mobile) */}
                <div className="hidden md:block text-left">
                  <p className="text-sm font-medium" style={{ color: theme === 'light' ? '#0f172a' : '#f1f5f9' }}>
                    {user?.name || 'User'}
                  </p>
                  <p className="text-xs" style={{ color: theme === 'light' ? '#64748b' : '#94a3b8' }}>
                    {user?.email}
                  </p>
                </div>
                {/* Dropdown arrow */}
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={1.5}
                  stroke="currentColor"
                  className={`w-4 h-4 transition-transform duration-200 ${showDropdown ? 'rotate-180' : ''}`}
                  style={{ color: theme === 'light' ? '#64748b' : '#94a3b8' }}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                </svg>
              </button>

              {/* Dropdown Menu */}
              {showDropdown && (
                <div
                  className="dropdown-menu absolute right-0 mt-2 w-56 rounded-lg shadow-xl py-1 z-[110]"
                  style={{
                    backgroundColor: theme === 'light' ? '#ffffff' : '#1e293b',
                    borderWidth: '1px',
                    borderStyle: 'solid',
                    borderColor: theme === 'light' ? '#e2e8f0' : '#334155',
                    boxShadow: theme === 'light' ? '0 4px 6px -1px rgba(0, 0, 0, 0.1)' : '0 20px 25px -5px rgba(0, 0, 0, 0.5)'
                  }}
                >
                  {/* User info in dropdown (mobile) */}
                  <div
                    className="md:hidden px-4 py-3 border-b"
                    style={{ borderBottomColor: theme === 'light' ? '#e2e8f0' : '#334155' }}
                  >
                    <p className="text-sm font-medium" style={{ color: theme === 'light' ? '#0f172a' : '#f1f5f9' }}>
                      {user?.name || 'User'}
                    </p>
                    <p className="text-xs" style={{ color: theme === 'light' ? '#64748b' : '#94a3b8' }}>
                      {user?.email}
                    </p>
                  </div>

                  {/* Menu items */}
                  <button
                    onClick={() => router.push('/tasks')}
                    className="w-full text-left px-4 py-2 text-sm flex items-center gap-2 transition-colors duration-150"
                    style={{ color: theme === 'light' ? '#334155' : '#cbd5e1' }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = theme === 'light' ? '#f8fafc' : '#334155';
                      e.currentTarget.style.color = theme === 'light' ? '#0f172a' : '#f1f5f9';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'transparent';
                      e.currentTarget.style.color = theme === 'light' ? '#334155' : '#cbd5e1';
                    }}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z" />
                    </svg>
                    My Tasks
                  </button>

                  <button
                    onClick={() => router.push('/chat')}
                    className="w-full text-left px-4 py-2 text-sm flex items-center gap-2 transition-colors duration-150"
                    style={{ color: theme === 'light' ? '#334155' : '#cbd5e1' }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = theme === 'light' ? '#f8fafc' : '#334155';
                      e.currentTarget.style.color = theme === 'light' ? '#0f172a' : '#f1f5f9';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'transparent';
                      e.currentTarget.style.color = theme === 'light' ? '#334155' : '#cbd5e1';
                    }}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    AI Chat Assistant
                  </button>

                  <div className="border-t my-1" style={{ borderTopColor: theme === 'light' ? '#e2e8f0' : '#334155' }}></div>

                  <button
                    onClick={handleLogout}
                    className="w-full text-left px-4 py-2 text-sm flex items-center gap-2 transition-colors duration-150"
                    style={{ color: '#ef4444' }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = theme === 'light' ? '#fef2f2' : '#334155';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'transparent';
                    }}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15M12 9l-3 3m0 0l3 3m-3-3h12.75" />
                    </svg>
                    Logout
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Click outside to close dropdown */}
      {showDropdown && (
        <div
          className="fixed inset-0 z-[105]"
          onClick={() => setShowDropdown(false)}
        />
      )}
    </header>
  );
}

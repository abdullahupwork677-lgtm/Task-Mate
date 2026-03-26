/**
 * In-App Notifications Component
 *
 * Displays notification bell icon with badge and dropdown list of notifications.
 *
 * Phase V - Due Dates & Reminders
 * User Story 5: Multi-Channel Notifications
 * Tasks: T159-T162
 */

'use client';

import { useState, useEffect } from 'react';
import { Bell } from 'lucide-react';

// T160: Notification interface matching backend schema
interface InAppNotification {
  id: number;
  user_id: string;
  task_id: number;
  title: string;
  message: string;
  reminder_type: string;
  is_read: boolean;
  created_at: string;
  event_id: string;
}

interface InAppNotificationsProps {
  userId: string;
  token: string;
}

export default function InAppNotifications({ userId, token }: InAppNotificationsProps) {
  const [notifications, setNotifications] = useState<InAppNotification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // T160: Fetch notifications from API
  const fetchNotifications = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/users/${userId}/notifications`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch notifications: ${response.statusText}`);
      }

      const data = await response.json();
      setNotifications(data);

      // T161: Calculate unread count
      const unread = data.filter((n: InAppNotification) => !n.is_read).length;
      setUnreadCount(unread);
    } catch (err) {
      console.error('Error fetching notifications:', err);
      setError(err instanceof Error ? err.message : 'Failed to load notifications');
    } finally {
      setLoading(false);
    }
  };

  // T162: Mark notification as read
  const markAsRead = async (notificationId: number) => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/users/${userId}/notifications/${notificationId}/read`,
        {
          method: 'PATCH',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to mark notification as read: ${response.statusText}`);
      }

      // Update local state
      setNotifications(prev =>
        prev.map(n =>
          n.id === notificationId ? { ...n, is_read: true } : n
        )
      );

      // Update unread count
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (err) {
      console.error('Error marking notification as read:', err);
    }
  };

  // T162: Mark all as read
  const markAllAsRead = async () => {
    const unreadNotifications = notifications.filter(n => !n.is_read);

    // Mark each unread notification
    await Promise.all(
      unreadNotifications.map(n => markAsRead(n.id))
    );
  };

  // Fetch notifications on mount and periodically
  useEffect(() => {
    fetchNotifications();

    // Poll for new notifications every 30 seconds
    const interval = setInterval(fetchNotifications, 30000);

    return () => clearInterval(interval);
  }, [userId, token]);

  // Format timestamp
  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString();
  };

  return (
    <div className="relative">
      {/* T159: Notification bell button with badge */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-600 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-full"
        aria-label={`Notifications (${unreadCount} unread)`}
      >
        <Bell className="h-6 w-6" />

        {/* T161: Badge with unread count */}
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 bg-red-600 rounded-full">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* T159: Dropdown notification list */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-lg ring-1 ring-black ring-opacity-5 z-50">
          {/* Header */}
          <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">
              Notifications
            </h3>
            {unreadCount > 0 && (
              <button
                onClick={markAllAsRead}
                className="text-sm text-blue-600 hover:text-blue-800 font-medium"
              >
                Mark all as read
              </button>
            )}
          </div>

          {/* Notification list */}
          <div className="max-h-96 overflow-y-auto">
            {loading && notifications.length === 0 ? (
              <div className="px-4 py-8 text-center text-gray-500">
                Loading notifications...
              </div>
            ) : error ? (
              <div className="px-4 py-8 text-center text-red-500">
                {error}
              </div>
            ) : notifications.length === 0 ? (
              <div className="px-4 py-8 text-center text-gray-500">
                No notifications yet
              </div>
            ) : (
              notifications.map(notification => (
                <div
                  key={notification.id}
                  className={`px-4 py-3 border-b border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors ${
                    !notification.is_read ? 'bg-blue-50' : ''
                  }`}
                  onClick={() => !notification.is_read && markAsRead(notification.id)}
                >
                  {/* Title with urgency indicator */}
                  <div className="flex items-start justify-between mb-1">
                    <h4 className={`text-sm font-medium ${
                      notification.title.includes('[URGENT]')
                        ? 'text-red-600'
                        : 'text-gray-900'
                    }`}>
                      {notification.title}
                    </h4>
                    {!notification.is_read && (
                      <span className="ml-2 inline-block w-2 h-2 bg-blue-600 rounded-full flex-shrink-0 mt-1" />
                    )}
                  </div>

                  {/* Message */}
                  <p className="text-sm text-gray-600 mb-2">
                    {notification.message}
                  </p>

                  {/* Footer: timestamp and task link */}
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>{formatTimestamp(notification.created_at)}</span>
                    <a
                      href={`/tasks/${notification.task_id}`}
                      className="text-blue-600 hover:text-blue-800 font-medium"
                      onClick={(e) => e.stopPropagation()}
                    >
                      View task →
                    </a>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          {notifications.length > 0 && (
            <div className="px-4 py-3 border-t border-gray-200 text-center">
              <a
                href="/notifications"
                className="text-sm text-blue-600 hover:text-blue-800 font-medium"
              >
                View all notifications
              </a>
            </div>
          )}
        </div>
      )}

      {/* Click outside to close */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
}

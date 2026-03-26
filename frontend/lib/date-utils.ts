/**
 * Date Utilities for Due Dates & Reminders
 *
 * Provides formatting and calculation functions for due dates.
 */

import { format, formatDistanceToNow, isPast, parseISO } from 'date-fns';

/**
 * Format a due date for display
 * @param dueDateStr - ISO date string or Date object
 * @returns Formatted date string (e.g., "Feb 15 at 2:00 PM")
 */
export function formatDueDate(dueDateStr: string | Date): string {
  const date = typeof dueDateStr === 'string' ? parseISO(dueDateStr) : dueDateStr;
  return format(date, "MMM d 'at' h:mm a");
}

/**
 * Calculate overdue duration in human-readable format
 * @param dueDateStr - ISO date string or Date object
 * @returns Human-readable duration (e.g., "2 days ago", "3 hours ago")
 */
export function calculateOverdue(dueDateStr: string | Date): string {
  const date = typeof dueDateStr === 'string' ? parseISO(dueDateStr) : dueDateStr;

  if (!isPast(date)) {
    return '';
  }

  return formatDistanceToNow(date, { addSuffix: true });
}

/**
 * Check if a date is overdue
 * @param dueDateStr - ISO date string or Date object
 * @returns True if date is in the past
 */
export function isOverdue(dueDateStr: string | Date): boolean {
  const date = typeof dueDateStr === 'string' ? parseISO(dueDateStr) : dueDateStr;
  return isPast(date);
}

/**
 * Calculate time remaining until due date
 * @param dueDateStr - ISO date string or Date object
 * @returns Human-readable time remaining (e.g., "in 2 days", "in 3 hours")
 */
export function calculateTimeRemaining(dueDateStr: string | Date): string {
  const date = typeof dueDateStr === 'string' ? parseISO(dueDateStr) : dueDateStr;

  if (isPast(date)) {
    return '';
  }

  return formatDistanceToNow(date, { addSuffix: true });
}

/**
 * Date Filter Utilities
 *
 * Client-side date range calculation and filtering utilities for due date filters.
 * Complements backend date_utils.py with TypeScript implementations.
 *
 * Phase: 004-search-filter
 * Task: T036 (US5)
 *
 * @example
 * ```typescript
 * const { start, end } = getTodayRange();
 * const isLate = isOverdue(task.due_date, task.completed);
 * const duration = calculateOverdueDuration(task.due_date);
 * ```
 */

/**
 * Date range tuple [start, end]
 */
export type DateRange = [Date, Date];

/**
 * Get start and end of today (local timezone)
 *
 * @returns Tuple of [today_start, today_end] as Date objects
 *
 * @example
 * ```typescript
 * const [start, end] = getTodayRange();
 * // start: Today at 00:00:00
 * // end: Tomorrow at 00:00:00
 * ```
 */
export function getTodayRange(): DateRange {
  const now = new Date();
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0, 0);
  const todayEnd = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1, 0, 0, 0, 0);
  return [todayStart, todayEnd];
}

/**
 * Get start and end of current week (Monday to Sunday)
 *
 * @returns Tuple of [week_start, week_end] as Date objects
 *
 * @example
 * ```typescript
 * const [start, end] = getWeekRange();
 * // start: Monday of current week at 00:00:00
 * // end: Next Monday at 00:00:00 (7 days later)
 * ```
 */
export function getWeekRange(): DateRange {
  const now = new Date();
  const dayOfWeek = now.getDay(); // 0 (Sunday) to 6 (Saturday)

  // Calculate days to subtract to get to Monday (1)
  // If Sunday (0), go back 6 days; otherwise go back (dayOfWeek - 1) days
  const daysToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;

  const weekStart = new Date(now.getFullYear(), now.getMonth(), now.getDate() - daysToMonday, 0, 0, 0, 0);
  const weekEnd = new Date(weekStart.getTime());
  weekEnd.setDate(weekStart.getDate() + 7);

  return [weekStart, weekEnd];
}

/**
 * Get start and end of current month
 *
 * @returns Tuple of [month_start, month_end] as Date objects
 *
 * @example
 * ```typescript
 * const [start, end] = getMonthRange();
 * // start: First day of current month at 00:00:00
 * // end: First day of next month at 00:00:00
 * ```
 */
export function getMonthRange(): DateRange {
  const now = new Date();
  const monthStart = new Date(now.getFullYear(), now.getMonth(), 1, 0, 0, 0, 0);
  const monthEnd = new Date(now.getFullYear(), now.getMonth() + 1, 1, 0, 0, 0, 0);
  return [monthStart, monthEnd];
}

/**
 * Check if a task is overdue
 *
 * A task is overdue if:
 * - It has a due date
 * - The due date is in the past (< now)
 * - The task is not completed
 *
 * @param dueDate - Task due date (ISO string or Date object)
 * @param completed - Whether task is completed
 * @returns True if task is overdue, False otherwise
 *
 * @example
 * ```typescript
 * const task = { due_date: "2026-02-01T00:00:00Z", completed: false };
 * const overdue = isOverdue(task.due_date, task.completed);
 * // overdue: true (if current date is after 2026-02-01)
 * ```
 */
export function isOverdue(dueDate: string | Date | null | undefined, completed: boolean = false): boolean {
  if (!dueDate || completed) {
    return false;
  }

  const dueDateObj = typeof dueDate === 'string' ? new Date(dueDate) : dueDate;
  const now = new Date();

  return dueDateObj < now;
}

/**
 * Calculate human-readable overdue duration
 *
 * @param dueDate - Task due date (must be in the past)
 * @returns Human-readable duration like "2 days", "3 hours", "45 minutes"
 *
 * @example
 * ```typescript
 * const pastDate = new Date(Date.now() - 2 * 24 * 60 * 60 * 1000); // 2 days ago
 * const duration = calculateOverdueDuration(pastDate);
 * // duration: "2 days"
 * ```
 */
export function calculateOverdueDuration(dueDate: string | Date): string {
  const dueDateObj = typeof dueDate === 'string' ? new Date(dueDate) : dueDate;
  const now = new Date();
  const deltaMs = now.getTime() - dueDateObj.getTime();
  const totalSeconds = Math.floor(deltaMs / 1000);

  if (totalSeconds < 60) {
    return "less than a minute";
  } else if (totalSeconds < 3600) {
    // Less than 1 hour
    const minutes = Math.floor(totalSeconds / 60);
    return `${minutes} minute${minutes !== 1 ? 's' : ''}`;
  } else if (totalSeconds < 86400) {
    // Less than 1 day
    const hours = Math.floor(totalSeconds / 3600);
    return `${hours} hour${hours !== 1 ? 's' : ''}`;
  } else {
    // Days
    const days = Math.floor(totalSeconds / 86400);
    return `${days} day${days !== 1 ? 's' : ''}`;
  }
}

/**
 * Get date range for a due date filter type
 *
 * @param filterType - One of 'today', 'this_week', 'this_month'
 * @returns Tuple of [range_start, range_end] as Date objects
 * @throws Error if filter_type is not recognized
 *
 * @example
 * ```typescript
 * const [start, end] = formatDateRange('today');
 * // Returns today's date range
 *
 * const [weekStart, weekEnd] = formatDateRange('this_week');
 * // Returns current week's date range
 * ```
 */
export function formatDateRange(filterType: 'today' | 'this_week' | 'this_month'): DateRange {
  switch (filterType) {
    case 'today':
      return getTodayRange();
    case 'this_week':
      return getWeekRange();
    case 'this_month':
      return getMonthRange();
    default:
      throw new Error(`Unknown filter type: ${filterType}`);
  }
}

/**
 * Check if a date falls within a range (inclusive start, exclusive end)
 *
 * @param date - Date to check
 * @param rangeStart - Start of range (inclusive)
 * @param rangeEnd - End of range (exclusive)
 * @returns True if date is in range, False otherwise
 *
 * @example
 * ```typescript
 * const now = new Date();
 * const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000);
 * const tomorrow = new Date(Date.now() + 2 * 24 * 60 * 60 * 1000);
 *
 * isDateInRange(now, yesterday, tomorrow); // true
 * isDateInRange(yesterday, now, tomorrow); // false
 * ```
 */
export function isDateInRange(date: Date, rangeStart: Date, rangeEnd: Date): boolean {
  return date >= rangeStart && date < rangeEnd;
}

/**
 * Check if a task's due date matches a filter
 *
 * @param dueDate - Task due date (ISO string or Date)
 * @param filterType - Filter type to check
 * @returns True if task matches filter, False otherwise
 *
 * @example
 * ```typescript
 * const task = { due_date: "2026-02-09T00:00:00Z" };
 *
 * matchesDueDateFilter(task.due_date, 'today'); // true if today is 2026-02-09
 * matchesDueDateFilter(task.due_date, 'overdue'); // depends on current date
 * matchesDueDateFilter(null, 'no_due_date'); // true
 * ```
 */
export function matchesDueDateFilter(
  dueDate: string | Date | null | undefined,
  filterType: 'all' | 'overdue' | 'today' | 'this_week' | 'this_month' | 'no_due_date',
  completed: boolean = false
): boolean {
  // Handle special cases
  if (filterType === 'all') {
    return true;
  }

  if (filterType === 'no_due_date') {
    return !dueDate;
  }

  if (!dueDate) {
    return false;
  }

  const dueDateObj = typeof dueDate === 'string' ? new Date(dueDate) : dueDate;

  // Check overdue
  if (filterType === 'overdue') {
    return isOverdue(dueDateObj, completed);
  }

  // Check date ranges
  const [rangeStart, rangeEnd] = formatDateRange(filterType as 'today' | 'this_week' | 'this_month');
  return isDateInRange(dueDateObj, rangeStart, rangeEnd);
}

/**
 * Format a date for display
 *
 * @param date - Date to format
 * @param format - Format type ('short', 'medium', 'long')
 * @returns Formatted date string
 *
 * @example
 * ```typescript
 * const date = new Date('2026-02-09T15:30:00Z');
 *
 * formatDateForDisplay(date, 'short'); // "2/9/26"
 * formatDateForDisplay(date, 'medium'); // "Feb 9, 2026"
 * formatDateForDisplay(date, 'long'); // "February 9, 2026"
 * ```
 */
export function formatDateForDisplay(
  date: string | Date | null | undefined,
  format: 'short' | 'medium' | 'long' = 'medium'
): string {
  if (!date) {
    return 'No due date';
  }

  const dateObj = typeof date === 'string' ? new Date(date) : date;

  switch (format) {
    case 'short':
      return dateObj.toLocaleDateString('en-US', {
        month: 'numeric',
        day: 'numeric',
        year: '2-digit'
      });
    case 'medium':
      return dateObj.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      });
    case 'long':
      return dateObj.toLocaleDateString('en-US', {
        month: 'long',
        day: 'numeric',
        year: 'numeric'
      });
    default:
      return dateObj.toLocaleDateString();
  }
}

/**
 * Get relative time string (e.g., "in 2 days", "2 days ago")
 *
 * @param date - Date to compare
 * @returns Relative time string
 *
 * @example
 * ```typescript
 * const tomorrow = new Date(Date.now() + 24 * 60 * 60 * 1000);
 * getRelativeTimeString(tomorrow); // "in 1 day"
 *
 * const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000);
 * getRelativeTimeString(yesterday); // "1 day ago"
 * ```
 */
export function getRelativeTimeString(date: string | Date | null | undefined): string {
  if (!date) {
    return 'No due date';
  }

  const dateObj = typeof date === 'string' ? new Date(date) : date;
  const now = new Date();
  const deltaMs = dateObj.getTime() - now.getTime();
  const isPast = deltaMs < 0;
  const absDeltaMs = Math.abs(deltaMs);
  const totalSeconds = Math.floor(absDeltaMs / 1000);

  let timeString: string;

  if (totalSeconds < 60) {
    timeString = "less than a minute";
  } else if (totalSeconds < 3600) {
    const minutes = Math.floor(totalSeconds / 60);
    timeString = `${minutes} minute${minutes !== 1 ? 's' : ''}`;
  } else if (totalSeconds < 86400) {
    const hours = Math.floor(totalSeconds / 3600);
    timeString = `${hours} hour${hours !== 1 ? 's' : ''}`;
  } else {
    const days = Math.floor(totalSeconds / 86400);
    timeString = `${days} day${days !== 1 ? 's' : ''}`;
  }

  return isPast ? `${timeString} ago` : `in ${timeString}`;
}

/**
 * Check if a date is today
 *
 * @param date - Date to check
 * @returns True if date is today
 */
export function isToday(date: string | Date | null | undefined): boolean {
  if (!date) return false;

  const dateObj = typeof date === 'string' ? new Date(date) : date;
  const [todayStart, todayEnd] = getTodayRange();

  return isDateInRange(dateObj, todayStart, todayEnd);
}

/**
 * Check if a date is in the past
 *
 * @param date - Date to check
 * @returns True if date is in the past
 */
export function isPast(date: string | Date | null | undefined): boolean {
  if (!date) return false;

  const dateObj = typeof date === 'string' ? new Date(date) : date;
  const now = new Date();

  return dateObj < now;
}

/**
 * Check if a date is in the future
 *
 * @param date - Date to check
 * @returns True if date is in the future
 */
export function isFuture(date: string | Date | null | undefined): boolean {
  if (!date) return false;

  const dateObj = typeof date === 'string' ? new Date(date) : date;
  const now = new Date();

  return dateObj > now;
}

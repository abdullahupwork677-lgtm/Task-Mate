/**
 * DueDateBadge Component
 *
 * Displays a blue badge for upcoming due dates (not overdue).
 */

import React from 'react';
import { formatDueDate, calculateTimeRemaining } from '@/lib/date-utils';

interface DueDateBadgeProps {
  dueDate: string;
  className?: string;
}

export const DueDateBadge: React.FC<DueDateBadgeProps> = ({
  dueDate,
  className = '',
}) => {
  const formattedDate = formatDueDate(dueDate);
  const timeRemaining = calculateTimeRemaining(dueDate);

  return (
    <div
      className={`inline-flex items-center gap-2 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium ${className}`}
      title={`Due: ${formattedDate}`}
    >
      <svg
        className="w-4 h-4"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
        />
      </svg>
      <span>{timeRemaining}</span>
    </div>
  );
};

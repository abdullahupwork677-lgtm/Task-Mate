/**
 * OverdueBadge Component
 *
 * Displays a red badge for overdue tasks with overdue duration.
 */

import React from 'react';
import { formatDueDate, calculateOverdue } from '@/lib/date-utils';

interface OverdueBadgeProps {
  dueDate: string;
  overdueBy?: string | null;
  className?: string;
}

export const OverdueBadge: React.FC<OverdueBadgeProps> = ({
  dueDate,
  overdueBy,
  className = '',
}) => {
  const formattedDate = formatDueDate(dueDate);
  const overdueText = overdueBy || calculateOverdue(dueDate);

  return (
    <div
      className={`inline-flex items-center gap-2 px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm font-medium ${className}`}
      title={`Overdue since: ${formattedDate}`}
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
          d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <span>Overdue {overdueText}</span>
    </div>
  );
};

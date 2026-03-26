'use client';

import React from 'react';
import { Task } from '@/lib/types';
import { Button } from './Button';
import { PriorityBadge } from './PriorityBadge';
import { DueDateBadge } from './DueDateBadge';
import { OverdueBadge } from './OverdueBadge';
import { TagList } from '@/components/TagBadge';
import clsx from 'clsx';

type Props = {
  task: Task;
  onComplete: (task: Task) => void;
  onEdit: (task: Task) => void;
  onDelete: (task: Task) => void;
};

function formatDueDate(dueDateStr: string): string {
  const dueDate = new Date(dueDateStr);
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);
  const dueDay = new Date(dueDate.getFullYear(), dueDate.getMonth(), dueDate.getDate());

  // Format time
  const timeStr = dueDate.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  });

  // Check if today, tomorrow, or specific date
  if (dueDay.getTime() === today.getTime()) {
    return `Today at ${timeStr}`;
  } else if (dueDay.getTime() === tomorrow.getTime()) {
    return `Tomorrow at ${timeStr}`;
  } else {
    const dateStr = dueDate.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: dueDate.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
    });
    return `${dateStr} at ${timeStr}`;
  }
}

export function TaskItem({ task, onComplete, onEdit, onDelete }: Props) {
  return (
    <div className="task-item rounded-2xl border border-theme bg-theme-surface/40 p-4 sm:p-5">
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div className="flex flex-col gap-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-mono font-semibold text-theme-tertiary">
            #{task.id}
          </span>
          <span
            className={clsx(
              'task-title text-base sm:text-lg font-semibold truncate max-w-full',
              task.completed && 'line-through completed'
            )}
          >
            {task.title}
          </span>
          <PriorityBadge priority={task.priority} />
          {task.completed ? (
            <span className="rounded-full bg-green-500/20 px-2 py-0.5 text-xs text-green-200">Done</span>
          ) : null}
          {task.is_recurring && task.recurrence_pattern ? (
            <span className="rounded-full bg-blue-500/20 px-2 py-0.5 text-xs text-blue-200 flex items-center gap-1">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2" />
              </svg>
              {task.recurrence_pattern}
            </span>
          ) : null}
          {/* Due date badges */}
          {task.due_date && !task.completed ? (
            task.is_overdue ? (
              <OverdueBadge dueDate={task.due_date} overdueBy={task.overdue_by} />
            ) : (
              <DueDateBadge dueDate={task.due_date} />
            )
          ) : null}
        </div>

        {/* Task Tags (Phase V - 003-task-tags) */}
        {task.tags && task.tags.length > 0 && (
          <div className="mt-2">
            <TagList tags={task.tags} size="sm" />
          </div>
        )}
        </div>
        {task.description ? (
          <p className="task-description text-sm text-theme-secondary break-words">{task.description}</p>
        ) : null}
        </div>

        <div className="flex flex-wrap gap-2 sm:justify-end">
          <Button variant="secondary" onClick={() => onComplete(task)} className="px-3 py-2">
            {task.completed ? 'Mark Incomplete' : 'Complete'}
          </Button>
          <Button variant="ghost" onClick={() => onEdit(task)} className="px-3 py-2">
            Edit
          </Button>
          <Button
            variant="ghost"
            onClick={() => onDelete(task)}
            className="px-3 py-2 text-red-400 hover:text-red-300"
          >
            Delete
          </Button>
        </div>
      </div>
    </div>
  );
}

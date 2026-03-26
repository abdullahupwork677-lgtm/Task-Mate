/**
 * TaskSort Component
 *
 * Sort dropdown component for task sorting with visual indicators.
 * Provides an accessible interface for sorting tasks by different criteria
 * (due date, priority, created date, title) with ascending/descending direction.
 *
 * Phase: 005-task-sort
 * Task: T009 (US1 - Sort by Due Date)
 *
 * @example
 * ```tsx
 * <TaskSort
 *   sortBy={sortBy}
 *   sortDirection={sortDirection}
 *   onSortChange={handleSortChange}
 * />
 * ```
 */

"use client";

import React from "react";

export type SortField = "due_date" | "priority" | "created_at" | "title";
export type SortDirection = "asc" | "desc";

interface TaskSortProps {
  /** Current sort field */
  sortBy: SortField;

  /** Current sort direction */
  sortDirection: SortDirection;

  /** Callback when sort changes */
  onSortChange: (sortBy: SortField, sortDirection: SortDirection) => void;

  /** Loading state during sort operations */
  isLoading?: boolean;

  /** CSS class name */
  className?: string;
}

/**
 * Task sort component with dropdown and direction toggle.
 *
 * Features:
 * - Sort field dropdown (due_date, priority, created_at, title)
 * - Direction toggle button (↑/↓ arrows)
 * - Visual active sort indicators
 * - Accessible keyboard navigation
 * - Responsive design
 * - Sensible defaults per field
 *
 * Phase: 005-task-sort
 * Tasks: T009 (component), T025 (visual indicators), T026 (direction toggle)
 */
export default function TaskSort({
  sortBy,
  sortDirection,
  onSortChange,
  isLoading = false,
  className = "",
}: TaskSortProps) {
  /**
   * Handle sort field change from dropdown
   */
  const handleSortFieldChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newSortBy = e.target.value as SortField;

    // Use field-specific default direction when changing field
    const defaultDirections: Record<SortField, SortDirection> = {
      created_at: "desc", // Newest first
      due_date: "asc",    // Earliest first
      priority: "asc",    // High → medium → low
      title: "asc",       // A → Z
    };

    const newDirection = defaultDirections[newSortBy];
    onSortChange(newSortBy, newDirection);
  };

  /**
   * Toggle sort direction (asc ↔ desc)
   */
  const handleDirectionToggle = () => {
    const newDirection = sortDirection === "asc" ? "desc" : "asc";
    onSortChange(sortBy, newDirection);
  };

  /**
   * Get human-readable sort field label
   */
  const getSortLabel = (field: SortField): string => {
    const labels: Record<SortField, string> = {
      due_date: "Due Date",
      priority: "Priority",
      created_at: "Created Date",
      title: "Title (A-Z)",
    };
    return labels[field];
  };

  /**
   * Get direction icon (↑ or ↓)
   */
  const getDirectionIcon = (): string => {
    return sortDirection === "asc" ? "↑" : "↓";
  };

  /**
   * Get direction label for accessibility
   */
  const getDirectionLabel = (): string => {
    if (sortBy === "due_date") {
      return sortDirection === "asc" ? "Earliest first" : "Latest first";
    } else if (sortBy === "priority") {
      return sortDirection === "asc" ? "High to low" : "Low to high";
    } else if (sortBy === "created_at") {
      return sortDirection === "asc" ? "Oldest first" : "Newest first";
    } else if (sortBy === "title") {
      return sortDirection === "asc" ? "A to Z" : "Z to A";
    }
    return sortDirection === "asc" ? "Ascending" : "Descending";
  };

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {/* Sort By Label */}
      <label
        htmlFor="task-sort-select"
        className="text-sm font-medium text-gray-700 dark:text-gray-300"
      >
        Sort by:
      </label>

      {/* Sort Field Dropdown */}
      <div className="relative">
        <select
          id="task-sort-select"
          value={sortBy}
          onChange={handleSortFieldChange}
          className="
            appearance-none
            rounded-md
            border
            border-gray-300
            dark:border-gray-600
            bg-white
            dark:bg-gray-800
            px-3
            py-2
            pr-10
            text-sm
            text-gray-900
            dark:text-gray-100
            shadow-sm
            focus:border-blue-500
            focus:outline-none
            focus:ring-2
            focus:ring-blue-500
            focus:ring-offset-0
            cursor-pointer
            hover:bg-gray-50
            dark:hover:bg-gray-700
            transition-colors
          "
          aria-label="Sort tasks by"
        >
          <option value="created_at">Created Date</option>
          <option value="due_date">Due Date</option>
          <option value="priority">Priority</option>
          <option value="title">Title</option>
        </select>

        {/* Dropdown Arrow Icon */}
        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
          <svg
            className="h-5 w-5 text-gray-400"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            aria-hidden="true"
          >
            <path
              fillRule="evenodd"
              d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
              clipRule="evenodd"
            />
          </svg>
        </div>
      </div>

      {/* Direction Toggle Button */}
      <button
        type="button"
        onClick={handleDirectionToggle}
        className="
          flex
          items-center
          gap-1
          rounded-md
          border
          border-gray-300
          dark:border-gray-600
          bg-white
          dark:bg-gray-800
          px-3
          py-2
          text-sm
          text-gray-900
          dark:text-gray-100
          shadow-sm
          hover:bg-gray-50
          dark:hover:bg-gray-700
          focus:outline-none
          focus:ring-2
          focus:ring-blue-500
          focus:ring-offset-0
          transition-colors
          cursor-pointer
        "
        aria-label={`Sort direction: ${getDirectionLabel()}`}
        title={getDirectionLabel()}
      >
        <span className="text-lg font-bold" aria-hidden="true">
          {getDirectionIcon()}
        </span>
        <span className="sr-only">{getDirectionLabel()}</span>
      </button>

      {/* Loading Spinner (T028) */}
      {isLoading && (
        <div className="flex items-center" role="status" aria-live="polite">
          <svg
            className="animate-spin h-4 w-4 text-blue-500"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          <span className="sr-only">Sorting tasks...</span>
        </div>
      )}

      {/* Active Sort Indicator (for screen readers) */}
      <span className="sr-only">
        Currently sorting by {getSortLabel(sortBy)} ({getDirectionLabel()})
      </span>
    </div>
  );
}

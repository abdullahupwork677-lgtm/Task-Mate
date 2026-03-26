/**
 * FilterBar Component
 *
 * Filter bar component for task filtering with dropdowns for status, priority,
 * tags, and due date filters. Provides an accessible interface for applying
 * multiple filters to search results.
 *
 * Phase: 004-search-filter
 * Tasks: T020 (US2), T025 (US3), T029 (US4), T035 (US5)
 *
 * @example
 * ```tsx
 * <FilterBar
 *   statusFilter={filters.statusFilter}
 *   onStatusChange={setStatusFilter}
 *   priorityFilter={filters.priorityFilter}
 *   onPriorityChange={setPriorityFilter}
 *   tagsFilter={filters.tagsFilter}
 *   onTagsChange={setTagsFilter}
 *   dueDateFilter={filters.dueDateFilter}
 *   onDueDateChange={setDueDateFilter}
 *   onClearFilters={resetFilters}
 *   hasActiveFilters={hasFilters}
 * />
 * ```
 */

"use client";

import React from "react";

interface FilterBarProps {
  /** Current status filter */
  statusFilter: "all" | "completed" | "incomplete";

  /** Callback when status filter changes */
  onStatusChange: (status: "all" | "completed" | "incomplete") => void;

  /** Current priority filter */
  priorityFilter?: "all" | "high" | "medium" | "low";

  /** Callback when priority filter changes */
  onPriorityChange?: (priority: "all" | "high" | "medium" | "low") => void;

  /** Current tags filter */
  tagsFilter?: string[];

  /** Callback when tags filter changes */
  onTagsChange?: (tags: string[] | undefined) => void;

  /** Current due date filter */
  dueDateFilter?: "all" | "overdue" | "today" | "this_week" | "this_month" | "no_due_date";

  /** Callback when due date filter changes */
  onDueDateChange?: (filter: "all" | "overdue" | "today" | "this_week" | "this_month" | "no_due_date") => void;

  /** Callback to clear all filters */
  onClearFilters?: () => void;

  /** Whether any filters are active */
  hasActiveFilters?: boolean;

  /** Available tags for autocomplete */
  availableTags?: string[];

  /** CSS class name */
  className?: string;
}

/**
 * Filter bar component for task filtering.
 *
 * Features:
 * - Status filter dropdown (all, completed, incomplete)
 * - Priority filter dropdown (all, high, medium, low)
 * - Tags multi-select dropdown with autocomplete
 * - Due date filter dropdown (overdue, today, this week, etc.)
 * - Clear all filters button
 * - Active filter indicators
 * - Responsive design
 * - Accessible (ARIA labels, keyboard navigation)
 */
export function FilterBar({
  statusFilter,
  onStatusChange,
  priorityFilter,
  onPriorityChange,
  tagsFilter,
  onTagsChange,
  dueDateFilter,
  onDueDateChange,
  onClearFilters,
  hasActiveFilters = false,
  availableTags = [],
  className = ""
}: FilterBarProps) {
  return (
    <div className={`flex flex-wrap items-center gap-3 p-4 bg-gray-50 border border-gray-200 rounded-lg ${className}`}>
      {/* Status Filter */}
      <div className="flex items-center gap-2">
        <label htmlFor="status-filter" className="text-sm font-medium text-gray-700">
          Status:
        </label>
        <select
          id="status-filter"
          value={statusFilter}
          onChange={(e) => onStatusChange(e.target.value as "all" | "completed" | "incomplete")}
          className="px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
          aria-label="Filter by status"
        >
          <option value="all">All</option>
          <option value="incomplete">Incomplete</option>
          <option value="completed">Completed</option>
        </select>
      </div>

      {/* Priority Filter (US3) */}
      {priorityFilter !== undefined && onPriorityChange && (
        <div className="flex items-center gap-2">
          <label htmlFor="priority-filter" className="text-sm font-medium text-gray-700">
            Priority:
          </label>
          <select
            id="priority-filter"
            value={priorityFilter}
            onChange={(e) => onPriorityChange(e.target.value as "all" | "high" | "medium" | "low")}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
            aria-label="Filter by priority"
          >
            <option value="all">All Priorities</option>
            <option value="high">High Priority</option>
            <option value="medium">Medium Priority</option>
            <option value="low">Low Priority</option>
          </select>
        </div>
      )}

      {/* Tags Filter (US4) - Multi-select */}
      {tagsFilter !== undefined && onTagsChange && (
        <div className="flex items-center gap-2">
          <label htmlFor="tags-filter" className="text-sm font-medium text-gray-700">
            Tags:
          </label>
          <div className="relative">
            <select
              id="tags-filter"
              multiple
              value={tagsFilter}
              onChange={(e) => {
                const selected = Array.from(e.target.selectedOptions, option => option.value);
                onTagsChange(selected.length > 0 ? selected : undefined);
              }}
              className="px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
              aria-label="Filter by tags (select multiple with Ctrl/Cmd)"
              size={3}
            >
              {availableTags.map(tag => (
                <option key={tag} value={tag}>
                  {tag}
                </option>
              ))}
            </select>
            {tagsFilter.length > 0 && (
              <span className="absolute -top-2 -right-2 bg-blue-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                {tagsFilter.length}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Due Date Filter (US5) */}
      {dueDateFilter !== undefined && onDueDateChange && (
        <div className="flex items-center gap-2">
          <label htmlFor="due-date-filter" className="text-sm font-medium text-gray-700">
            Due Date:
          </label>
          <select
            id="due-date-filter"
            value={dueDateFilter}
            onChange={(e) => onDueDateChange(e.target.value as any)}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
            aria-label="Filter by due date"
          >
            <option value="all">All Dates</option>
            <option value="overdue">Overdue</option>
            <option value="today">Due Today</option>
            <option value="this_week">This Week</option>
            <option value="this_month">This Month</option>
            <option value="no_due_date">No Due Date</option>
          </select>
        </div>
      )}

      {/* Clear Filters Button */}
      {hasActiveFilters && onClearFilters && (
        <button
          onClick={onClearFilters}
          className="ml-auto px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
          aria-label="Clear all filters"
        >
          <span className="flex items-center gap-1.5">
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
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
            Clear Filters
          </span>
        </button>
      )}

      {/* Active Filters Summary */}
      {hasActiveFilters && (
        <div className="w-full mt-2 pt-2 border-t border-gray-200">
          <p className="text-xs text-gray-600">
            <span className="font-medium">Active filters:</span>
            {statusFilter !== "all" && (
              <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-800 rounded-full text-xs">
                {statusFilter}
              </span>
            )}
            {priorityFilter && priorityFilter !== "all" && (
              <span className="ml-2 px-2 py-0.5 bg-purple-100 text-purple-800 rounded-full text-xs">
                {priorityFilter} priority
              </span>
            )}
            {tagsFilter && tagsFilter.length > 0 && (
              <span className="ml-2 px-2 py-0.5 bg-green-100 text-green-800 rounded-full text-xs">
                {tagsFilter.length} tag{tagsFilter.length > 1 ? "s" : ""}
              </span>
            )}
            {dueDateFilter && dueDateFilter !== "all" && (
              <span className="ml-2 px-2 py-0.5 bg-orange-100 text-orange-800 rounded-full text-xs">
                {dueDateFilter.replace("_", " ")}
              </span>
            )}
          </p>
        </div>
      )}
    </div>
  );
}

/**
 * Example usage with useSearch hook:
 *
 * ```tsx
 * function TaskSearchPage() {
 *   const {
 *     filters,
 *     setStatusFilter,
 *     setPriorityFilter,
 *     setTagsFilter,
 *     setDueDateFilter,
 *     resetFilters,
 *     hasFilters,
 *     results
 *   } = useSearch({ userId: "user-123" });
 *
 *   // Get available tags from results or separate API
 *   const availableTags = results?.tasks
 *     .flatMap(task => task.tags)
 *     .filter((tag, idx, arr) => arr.indexOf(tag) === idx) || [];
 *
 *   return (
 *     <div className="container mx-auto p-4">
 *       <SearchInput
 *         value={filters.keyword || ""}
 *         onChange={setKeyword}
 *       />
 *
 *       <FilterBar
 *         statusFilter={filters.statusFilter}
 *         onStatusChange={setStatusFilter}
 *         priorityFilter={filters.priorityFilter}
 *         onPriorityChange={setPriorityFilter}
 *         tagsFilter={filters.tagsFilter}
 *         onTagsChange={setTagsFilter}
 *         dueDateFilter={filters.dueDateFilter}
 *         onDueDateChange={setDueDateFilter}
 *         onClearFilters={resetFilters}
 *         hasActiveFilters={hasFilters}
 *         availableTags={availableTags}
 *         className="mt-4"
 *       />
 *
 *       {results && (
 *         <div className="mt-6">
 *           <p className="text-sm text-gray-600 mb-4">
 *             {results.appliedFilters.summary}
 *           </p>
 *           <TaskList tasks={results.tasks} />
 *         </div>
 *       )}
 *     </div>
 *   );
 * }
 * ```
 */

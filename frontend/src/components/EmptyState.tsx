/**
 * EmptyState Component
 *
 * Displays a friendly empty state message when no search results are found.
 * Provides guidance on how to adjust search criteria.
 *
 * Phase: 004-search-filter
 * Task: T048 (Phase 9)
 *
 * @example
 * ```tsx
 * <EmptyState
 *   message="No tasks found matching your criteria"
 *   suggestions={["Try adjusting your filters", "Search with different keywords"]}
 * />
 * ```
 */

"use client";

import React from "react";

interface EmptyStateProps {
  /** Main message to display */
  message?: string;

  /** Additional suggestions or tips */
  suggestions?: string[];

  /** Show icon */
  showIcon?: boolean;

  /** CSS class name */
  className?: string;

  /** Action button (optional) */
  action?: {
    label: string;
    onClick: () => void;
  };
}

/**
 * Empty state component for search results.
 *
 * Features:
 * - Clear, friendly message
 * - Helpful suggestions
 * - Optional action button
 * - Accessible
 * - Customizable
 */
export function EmptyState({
  message = "No tasks found matching your criteria",
  suggestions = [
    "Try adjusting your filters",
    "Search with different keywords",
    "Check your spelling",
    "Use broader search terms"
  ],
  showIcon = true,
  className = "",
  action
}: EmptyStateProps) {
  return (
    <div
      className={`flex flex-col items-center justify-center p-12 bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg ${className}`}
      role="status"
      aria-live="polite"
    >
      {/* Icon */}
      {showIcon && (
        <svg
          className="w-16 h-16 text-gray-400 mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
      )}

      {/* Message */}
      <h3 className="text-lg font-medium text-gray-900 mb-2">
        {message}
      </h3>

      {/* Suggestions */}
      {suggestions.length > 0 && (
        <div className="max-w-md text-center">
          <p className="text-sm text-gray-600 mb-3">Try:</p>
          <ul className="text-sm text-gray-600 space-y-1">
            {suggestions.map((suggestion, index) => (
              <li key={index} className="flex items-center justify-center gap-2">
                <svg className="w-4 h-4 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                {suggestion}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Action Button */}
      {action && (
        <button
          onClick={action.onClick}
          className="mt-6 px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}

/**
 * Specialized EmptyState variants
 */

/**
 * Empty state for no tasks at all (new user)
 */
export function EmptyTasksState({ onCreateTask }: { onCreateTask?: () => void }) {
  return (
    <EmptyState
      message="No tasks yet"
      suggestions={["Create your first task to get started", "Tasks help you stay organized"]}
      action={onCreateTask ? { label: "Create Task", onClick: onCreateTask } : undefined}
    />
  );
}

/**
 * Empty state for search with no results
 */
export function NoSearchResultsState({ onClearFilters }: { onClearFilters?: () => void }) {
  return (
    <EmptyState
      message="No tasks found matching your criteria"
      suggestions={[
        "Try adjusting your filters",
        "Search with different keywords",
        "Check your spelling",
        "Use broader search terms"
      ]}
      action={onClearFilters ? { label: "Clear Filters", onClick: onClearFilters } : undefined}
    />
  );
}

/**
 * Example usage with search results:
 *
 * ```tsx
 * function TaskSearchPage() {
 *   const { results, resetFilters } = useSearch({ userId: "user-123" });
 *
 *   return (
 *     <div className="container mx-auto p-4">
 *       <SearchInput ... />
 *       <FilterBar ... />
 *
 *       {results && (
 *         <>
 *           {results.totalCount === 0 ? (
 *             <NoSearchResultsState onClearFilters={resetFilters} />
 *           ) : (
 *             <>
 *               <SearchResultsSummary ... />
 *               <TaskList tasks={results.tasks} />
 *               <Pagination ... />
 *             </>
 *           )}
 *         </>
 *       )}
 *     </div>
 *   );
 * }
 * ```
 */

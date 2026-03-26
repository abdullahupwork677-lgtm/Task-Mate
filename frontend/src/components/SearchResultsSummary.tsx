/**
 * SearchResultsSummary Component
 *
 * Displays search results count with human-readable filter summary.
 * Shows the number of tasks found and which filters are applied.
 *
 * Phase: 004-search-filter
 * Task: T043 (US6)
 *
 * @example
 * ```tsx
 * <SearchResultsSummary
 *   summary="Showing 5 incomplete high priority work tasks"
 *   totalCount={5}
 *   loading={false}
 * />
 * ```
 */

"use client";

import React from "react";

interface SearchResultsSummaryProps {
  /** Human-readable summary from backend */
  summary: string;

  /** Total count of results */
  totalCount: number;

  /** Loading state */
  loading?: boolean;

  /** CSS class name */
  className?: string;
}

/**
 * Search results summary component.
 *
 * Features:
 * - Human-readable filter summary from backend
 * - Result count with proper pluralization
 * - Loading state
 * - Accessible (ARIA live region for screen readers)
 */
export function SearchResultsSummary({
  summary,
  totalCount,
  loading = false,
  className = ""
}: SearchResultsSummaryProps) {
  if (loading) {
    return (
      <div className={`flex items-center gap-2 px-4 py-3 bg-gray-50 border border-gray-200 rounded-md ${className}`}>
        <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full" />
        <span className="text-sm text-gray-600">Loading results...</span>
      </div>
    );
  }

  return (
    <div
      className={`px-4 py-3 bg-gray-50 border border-gray-200 rounded-md ${className}`}
      role="status"
      aria-live="polite"
      aria-atomic="true"
    >
      <p className="text-sm text-gray-700">
        <span className="font-medium">{summary}</span>
      </p>

      {/* Optional: More detailed breakdown */}
      {totalCount === 0 && (
        <p className="text-xs text-gray-500 mt-1">
          Try adjusting your filters or search terms to find more tasks.
        </p>
      )}
    </div>
  );
}

/**
 * Example usage with useSearch hook:
 *
 * ```tsx
 * function TaskSearchPage() {
 *   const { results, isLoading } = useSearch({ userId: "user-123" });
 *
 *   return (
 *     <div className="container mx-auto p-4">
 *       <SearchInput ... />
 *       <FilterBar ... />
 *
 *       {results && (
 *         <>
 *           <SearchResultsSummary
 *             summary={results.appliedFilters.summary}
 *             totalCount={results.totalCount}
 *             loading={isLoading}
 *             className="mt-4 mb-4"
 *           />
 *           <TaskList tasks={results.tasks} />
 *         </>
 *       )}
 *     </div>
 *   );
 * }
 * ```
 */

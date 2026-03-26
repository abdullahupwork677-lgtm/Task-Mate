/**
 * Pagination Component
 *
 * Pagination controls for navigating through search results.
 * Supports page navigation, page size selection, and accessibility.
 *
 * Phase: 004-search-filter
 * Task: T045 (Phase 9)
 *
 * @example
 * ```tsx
 * <Pagination
 *   currentPage={1}
 *   totalPages={5}
 *   onPageChange={setPage}
 *   pageSize={20}
 *   onPageSizeChange={setPageSize}
 * />
 * ```
 */

"use client";

import React from "react";

interface PaginationProps {
  /** Current page number (1-indexed) */
  currentPage: number;

  /** Total number of pages */
  totalPages: number;

  /** Callback when page changes */
  onPageChange: (page: number) => void;

  /** Current page size */
  pageSize?: number;

  /** Callback when page size changes */
  onPageSizeChange?: (size: number) => void;

  /** Available page sizes */
  pageSizes?: number[];

  /** Show page size selector */
  showPageSize?: boolean;

  /** CSS class name */
  className?: string;
}

/**
 * Pagination component with page navigation and size controls.
 *
 * Features:
 * - Previous/Next navigation
 * - Page number display
 * - Jump to first/last page
 * - Page size selector (optional)
 * - Disabled states for boundary pages
 * - Accessible (ARIA labels, keyboard navigation)
 */
export function Pagination({
  currentPage,
  totalPages,
  onPageChange,
  pageSize = 20,
  onPageSizeChange,
  pageSizes = [10, 20, 50, 100],
  showPageSize = true,
  className = ""
}: PaginationProps) {
  const hasPrev = currentPage > 1;
  const hasNext = currentPage < totalPages;

  const handlePrevious = () => {
    if (hasPrev) {
      onPageChange(currentPage - 1);
    }
  };

  const handleNext = () => {
    if (hasNext) {
      onPageChange(currentPage + 1);
    }
  };

  const handleFirst = () => {
    if (currentPage !== 1) {
      onPageChange(1);
    }
  };

  const handleLast = () => {
    if (currentPage !== totalPages) {
      onPageChange(totalPages);
    }
  };

  const handlePageSizeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newSize = parseInt(e.target.value, 10);
    if (onPageSizeChange) {
      onPageSizeChange(newSize);
    }
  };

  // Don't show pagination if only one page
  if (totalPages <= 1) {
    return null;
  }

  return (
    <div className={`flex flex-wrap items-center justify-between gap-4 p-4 bg-gray-50 border border-gray-200 rounded-md ${className}`}>
      {/* Page Size Selector */}
      {showPageSize && onPageSizeChange && (
        <div className="flex items-center gap-2">
          <label htmlFor="page-size" className="text-sm text-gray-700">
            Show:
          </label>
          <select
            id="page-size"
            value={pageSize}
            onChange={handlePageSizeChange}
            className="px-2 py-1 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
            aria-label="Items per page"
          >
            {pageSizes.map(size => (
              <option key={size} value={size}>
                {size} per page
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Page Navigation */}
      <div className="flex items-center gap-2">
        {/* First Page Button */}
        <button
          onClick={handleFirst}
          disabled={currentPage === 1}
          className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
          aria-label="Go to first page"
        >
          <span className="flex items-center gap-1">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
            </svg>
            First
          </span>
        </button>

        {/* Previous Page Button */}
        <button
          onClick={handlePrevious}
          disabled={!hasPrev}
          className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
          aria-label="Go to previous page"
        >
          <span className="flex items-center gap-1">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Previous
          </span>
        </button>

        {/* Page Info */}
        <span className="px-4 py-1.5 text-sm text-gray-700">
          Page <span className="font-medium">{currentPage}</span> of <span className="font-medium">{totalPages}</span>
        </span>

        {/* Next Page Button */}
        <button
          onClick={handleNext}
          disabled={!hasNext}
          className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
          aria-label="Go to next page"
        >
          <span className="flex items-center gap-1">
            Next
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </span>
        </button>

        {/* Last Page Button */}
        <button
          onClick={handleLast}
          disabled={currentPage === totalPages}
          className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
          aria-label="Go to last page"
        >
          <span className="flex items-center gap-1">
            Last
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
            </svg>
          </span>
        </button>
      </div>
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
 *     setPage,
 *     setPageSize,
 *     results,
 *     isLoading
 *   } = useSearch({ userId: "user-123" });
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
 *           />
 *           <TaskList tasks={results.tasks} />
 *           <Pagination
 *             currentPage={results.pagination.page}
 *             totalPages={results.pagination.totalPages}
 *             onPageChange={setPage}
 *             pageSize={filters.pageSize}
 *             onPageSizeChange={setPageSize}
 *             className="mt-4"
 *           />
 *         </>
 *       )}
 *     </div>
 *   );
 * }
 * ```
 */

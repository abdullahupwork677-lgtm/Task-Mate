/**
 * useSearch Hook
 *
 * Manages search state and API integration for task searching and filtering.
 * Handles keyword search, filters, pagination, and API calls with debouncing.
 *
 * Phase: 004-search-filter
 * Task: T016 (US1)
 *
 * @example
 * ```tsx
 * const {
 *   filters,
 *   setKeyword,
 *   setStatusFilter,
 *   results,
 *   isLoading,
 *   error,
 *   searchTasks
 * } = useSearch();
 *
 * // Update keyword
 * setKeyword("grocery");
 *
 * // Apply filters
 * setStatusFilter("incomplete");
 * setPriorityFilter("high");
 *
 * // Search is automatically triggered when filters change
 * ```
 */

import { useState, useEffect, useCallback } from "react";
import { useDebounce } from "./useDebounce";
import {
  SearchFilters,
  SearchResults,
  DEFAULT_SEARCH_FILTERS,
  buildSearchParams,
  hasActiveFilters
} from "../types/search";

interface UseSearchOptions {
  /** Auto-search when filters change (default: true) */
  autoSearch?: boolean;
  /** Debounce delay for keyword in milliseconds (default: 300) */
  debounceDelay?: number;
  /** User ID for task ownership */
  userId: string;
}

interface UseSearchReturn {
  /** Current search filters */
  filters: SearchFilters;

  /** Set keyword filter */
  setKeyword: (keyword: string | undefined) => void;

  /** Set status filter */
  setStatusFilter: (status: "all" | "completed" | "incomplete") => void;

  /** Set priority filter */
  setPriorityFilter: (priority: "all" | "high" | "medium" | "low") => void;

  /** Set tags filter */
  setTagsFilter: (tags: string[] | undefined) => void;

  /** Set due date filter */
  setDueDateFilter: (filter: "all" | "overdue" | "today" | "this_week" | "this_month" | "no_due_date") => void;

  /** Set page number */
  setPage: (page: number) => void;

  /** Set page size */
  setPageSize: (pageSize: number) => void;

  /** Reset all filters to defaults */
  resetFilters: () => void;

  /** Search results */
  results: SearchResults | null;

  /** Loading state */
  isLoading: boolean;

  /** Error state */
  error: string | null;

  /** Manually trigger search */
  searchTasks: () => Promise<void>;

  /** Whether any filters are active */
  hasFilters: boolean;
}

/**
 * Hook for managing task search and filtering.
 *
 * @param options - Configuration options
 * @returns Search state and methods
 */
export function useSearch(options: UseSearchOptions): UseSearchReturn {
  const { autoSearch = true, debounceDelay = 300, userId } = options;

  // Search filters state
  const [filters, setFilters] = useState<SearchFilters>(DEFAULT_SEARCH_FILTERS);

  // Search results state
  const [results, setResults] = useState<SearchResults | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Debounce keyword to avoid excessive API calls
  const debouncedKeyword = useDebounce(filters.keyword, debounceDelay);

  // Update filters with debounced keyword
  const activeFilters: SearchFilters = {
    ...filters,
    keyword: debouncedKeyword
  };

  // Filter update functions
  const setKeyword = useCallback((keyword: string | undefined) => {
    setFilters(prev => ({ ...prev, keyword, page: 1 })); // Reset to page 1 on keyword change
  }, []);

  const setStatusFilter = useCallback((statusFilter: "all" | "completed" | "incomplete") => {
    setFilters(prev => ({ ...prev, statusFilter, page: 1 }));
  }, []);

  const setPriorityFilter = useCallback((priorityFilter: "all" | "high" | "medium" | "low") => {
    setFilters(prev => ({ ...prev, priorityFilter, page: 1 }));
  }, []);

  const setTagsFilter = useCallback((tagsFilter: string[] | undefined) => {
    setFilters(prev => ({ ...prev, tagsFilter, page: 1 }));
  }, []);

  const setDueDateFilter = useCallback((dueDateFilter: "all" | "overdue" | "today" | "this_week" | "this_month" | "no_due_date") => {
    setFilters(prev => ({ ...prev, dueDateFilter, page: 1 }));
  }, []);

  const setPage = useCallback((page: number) => {
    setFilters(prev => ({ ...prev, page }));
  }, []);

  const setPageSize = useCallback((pageSize: number) => {
    setFilters(prev => ({ ...prev, pageSize, page: 1 })); // Reset to page 1 on page size change
  }, []);

  const resetFilters = useCallback(() => {
    setFilters(DEFAULT_SEARCH_FILTERS);
    setResults(null);
    setError(null);
  }, []);

  // Perform search API call
  const searchTasks = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Build query parameters
      const params = buildSearchParams(activeFilters, userId);

      // Call search API endpoint
      const response = await fetch(`/api/search?${params.toString()}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json"
        }
      });

      if (!response.ok) {
        throw new Error(`Search failed: ${response.statusText}`);
      }

      const data: SearchResults = await response.json();
      setResults(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Unknown error occurred";
      setError(errorMessage);
      setResults(null);
    } finally {
      setIsLoading(false);
    }
  }, [activeFilters, userId]);

  // Auto-search when filters change
  useEffect(() => {
    if (autoSearch) {
      searchTasks();
    }
  }, [
    debouncedKeyword, // Use debounced keyword
    activeFilters.statusFilter,
    activeFilters.priorityFilter,
    activeFilters.tagsFilter,
    activeFilters.dueDateFilter,
    activeFilters.page,
    activeFilters.pageSize,
    autoSearch,
    searchTasks
  ]);

  return {
    filters: activeFilters,
    setKeyword,
    setStatusFilter,
    setPriorityFilter,
    setTagsFilter,
    setDueDateFilter,
    setPage,
    setPageSize,
    resetFilters,
    results,
    isLoading,
    error,
    searchTasks,
    hasFilters: hasActiveFilters(activeFilters)
  };
}

/**
 * Example usage:
 *
 * ```tsx
 * function SearchPage() {
 *   const {
 *     filters,
 *     setKeyword,
 *     setStatusFilter,
 *     setPriorityFilter,
 *     results,
 *     isLoading,
 *     error,
 *     hasFilters,
 *     resetFilters
 *   } = useSearch({ userId: "user-123" });
 *
 *   return (
 *     <div>
 *       <SearchInput
 *         value={filters.keyword || ""}
 *         onChange={setKeyword}
 *         placeholder="Search tasks..."
 *       />
 *
 *       <FilterBar
 *         statusFilter={filters.statusFilter}
 *         onStatusChange={setStatusFilter}
 *         priorityFilter={filters.priorityFilter}
 *         onPriorityChange={setPriorityFilter}
 *       />
 *
 *       {hasFilters && (
 *         <button onClick={resetFilters}>Clear all filters</button>
 *       )}
 *
 *       {isLoading && <div>Loading...</div>}
 *       {error && <div>Error: {error}</div>}
 *
 *       {results && (
 *         <div>
 *           <p>{results.appliedFilters.summary}</p>
 *           <TaskList tasks={results.tasks} />
 *           <Pagination
 *             current={results.pagination.page}
 *             total={results.pagination.totalPages}
 *             onChange={setPage}
 *           />
 *         </div>
 *       )}
 *     </div>
 *   );
 * }
 * ```
 */

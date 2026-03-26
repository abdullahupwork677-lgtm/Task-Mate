/**
 * Search and filter types for task searching functionality.
 *
 * Defines TypeScript types for search requests, responses, and pagination,
 * matching the backend SearchRequest and SearchResponse schemas.
 *
 * Phase: 004-search-filter
 * Tasks: T008, T009
 */

/**
 * Search filters for task searching and filtering.
 *
 * All filters use AND logic between types (keyword AND status AND priority...).
 * Tags filter uses OR logic (tasks with ANY of the specified tags).
 */
export interface SearchFilters {
  /** Keyword for case-insensitive partial matching in title and description */
  keyword?: string;

  /** Filter by completion status */
  statusFilter: "all" | "completed" | "incomplete";

  /** Filter by priority level */
  priorityFilter: "all" | "high" | "medium" | "low";

  /** Filter by tags (OR logic - tasks with ANY of these tags) */
  tagsFilter?: string[];

  /** Filter by due date category */
  dueDateFilter: "all" | "overdue" | "today" | "this_week" | "this_month" | "no_due_date";

  /** Page number (1-indexed) */
  page: number;

  /** Number of results per page */
  pageSize: number;
}

/**
 * Pagination metadata for search results.
 */
export interface PaginationInfo {
  /** Current page number (1-indexed) */
  page: number;

  /** Number of results per page */
  pageSize: number;

  /** Total number of pages */
  totalPages: number;

  /** Whether there is a next page */
  hasNext: boolean;

  /** Whether there is a previous page */
  hasPrev: boolean;
}

/**
 * Summary of applied filters.
 */
export interface AppliedFilters {
  /** Keyword search term (if any) */
  keyword?: string;

  /** Status filter applied */
  status: string;

  /** Priority filter applied */
  priority: string;

  /** Tags filter applied (if any) */
  tags?: string[];

  /** Due date filter applied */
  dueDate: string;
}

/**
 * Task object in search results.
 *
 * Matches the task dictionary returned by backend search endpoint.
 */
export interface SearchTask {
  /** Task ID */
  taskId: number;

  /** Task title */
  title: string;

  /** Task description (optional) */
  description?: string;

  /** Whether task is completed */
  completed: boolean;

  /** Priority level */
  priority: "high" | "medium" | "low";

  /** Task tags */
  tags: string[];

  /** Due date (ISO 8601 string, optional) */
  dueDate?: string;

  /** Creation timestamp (ISO 8601 string) */
  createdAt: string;

  /** Last update timestamp (ISO 8601 string) */
  updatedAt: string;
}

/**
 * Search results response.
 *
 * Matches the backend SearchResponse schema.
 */
export interface SearchResults {
  /** List of tasks matching search and filter criteria */
  tasks: SearchTask[];

  /** Total number of tasks matching filters (across all pages) */
  totalCount: number;

  /** Number of tasks in this page */
  filteredCount: number;

  /** Pagination metadata */
  pagination: PaginationInfo;

  /** Summary of filters applied */
  appliedFilters: AppliedFilters;
}

/**
 * Default search filters (no filtering, first page).
 */
export const DEFAULT_SEARCH_FILTERS: SearchFilters = {
  keyword: undefined,
  statusFilter: "all",
  priorityFilter: "all",
  tagsFilter: undefined,
  dueDateFilter: "all",
  page: 1,
  pageSize: 20
};

/**
 * Helper function to build search query parameters for API calls.
 *
 * Converts SearchFilters to URLSearchParams for API requests.
 *
 * @param filters - Search filters
 * @param userId - User ID for task ownership
 * @returns URLSearchParams for API request
 */
export function buildSearchParams(
  filters: SearchFilters,
  userId: string
): URLSearchParams {
  const params = new URLSearchParams();

  params.append("user_id", userId);
  params.append("status_filter", filters.statusFilter);
  params.append("priority_filter", filters.priorityFilter);
  params.append("due_date_filter", filters.dueDateFilter);
  params.append("page", filters.page.toString());
  params.append("page_size", filters.pageSize.toString());

  if (filters.keyword) {
    params.append("keyword", filters.keyword);
  }

  if (filters.tagsFilter && filters.tagsFilter.length > 0) {
    filters.tagsFilter.forEach((tag) => {
      params.append("tags_filter", tag);
    });
  }

  return params;
}

/**
 * Helper function to check if any filters are active.
 *
 * @param filters - Search filters
 * @returns True if any non-default filters are applied
 */
export function hasActiveFilters(filters: SearchFilters): boolean {
  return (
    !!filters.keyword ||
    filters.statusFilter !== "all" ||
    filters.priorityFilter !== "all" ||
    (filters.tagsFilter !== undefined && filters.tagsFilter.length > 0) ||
    filters.dueDateFilter !== "all"
  );
}

/**
 * Helper function to reset filters to defaults.
 *
 * @returns Default search filters
 */
export function resetFilters(): SearchFilters {
  return { ...DEFAULT_SEARCH_FILTERS };
}

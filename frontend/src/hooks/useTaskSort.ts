/**
 * useTaskSort Hook
 *
 * Custom React hook for managing task sorting state with session persistence.
 * Handles sort field and direction state, provides callbacks for updates,
 * and persists preferences in sessionStorage for the duration of the session.
 *
 * Phase: 005-task-sort
 * Task: T010 (US1), T027 (session persistence)
 *
 * @example
 * ```tsx
 * const { sortBy, sortDirection, handleSortChange } = useTaskSort();
 *
 * return (
 *   <TaskSort
 *     sortBy={sortBy}
 *     sortDirection={sortDirection}
 *     onSortChange={handleSortChange}
 *   />
 * );
 * ```
 */

"use client";

import { useState, useEffect, useCallback } from "react";

export type SortField = "due_date" | "priority" | "created_at" | "title";
export type SortDirection = "asc" | "desc";

/**
 * Session storage keys for sort preferences
 */
const STORAGE_KEYS = {
  SORT_BY: "task_sort_by",
  SORT_DIRECTION: "task_sort_direction",
} as const;

/**
 * Default sort configuration
 */
const DEFAULT_SORT: {
  sortBy: SortField;
  sortDirection: SortDirection;
} = {
  sortBy: "created_at",
  sortDirection: "desc", // Newest first
};

/**
 * Return type for useTaskSort hook
 */
export interface UseTaskSortReturn {
  /** Current sort field */
  sortBy: SortField;

  /** Current sort direction */
  sortDirection: SortDirection;

  /** Update sort field and direction */
  handleSortChange: (sortBy: SortField, sortDirection: SortDirection) => void;

  /** Reset sort to default (created_at desc) */
  resetSort: () => void;
}

/**
 * Custom hook for task sorting state management.
 *
 * Features:
 * - Manages sort field and direction state
 * - Persists preferences in sessionStorage (Phase V - 005-task-sort T027)
 * - Restores preferences on page refresh (within same session)
 * - Provides update and reset callbacks
 * - Type-safe sort field and direction
 *
 * Session Persistence:
 * - Stored in sessionStorage (cleared on tab close)
 * - Survives page refresh within same browser tab
 * - Not shared across tabs/windows
 * - Not persisted to database (per spec requirements)
 *
 * Default Sort:
 * - Field: created_at
 * - Direction: desc (newest first)
 *
 * @returns {UseTaskSortReturn} Sort state and callbacks
 *
 * @example
 * ```tsx
 * function TaskList() {
 *   const { sortBy, sortDirection, handleSortChange, resetSort } = useTaskSort();
 *
 *   return (
 *     <div>
 *       <TaskSort
 *         sortBy={sortBy}
 *         sortDirection={sortDirection}
 *         onSortChange={handleSortChange}
 *       />
 *       <button onClick={resetSort}>Reset Sort</button>
 *     </div>
 *   );
 * }
 * ```
 */
export function useTaskSort(): UseTaskSortReturn {
  // Initialize state from sessionStorage or defaults
  const [sortBy, setSortBy] = useState<SortField>(() => {
    // Only access sessionStorage on client-side (Next.js SSR compatibility)
    if (typeof window === "undefined") {
      return DEFAULT_SORT.sortBy;
    }

    try {
      const stored = sessionStorage.getItem(STORAGE_KEYS.SORT_BY);
      if (stored && isValidSortField(stored)) {
        return stored as SortField;
      }
    } catch (error) {
      console.error("Failed to read sort preferences from sessionStorage:", error);
    }

    return DEFAULT_SORT.sortBy;
  });

  const [sortDirection, setSortDirection] = useState<SortDirection>(() => {
    // Only access sessionStorage on client-side (Next.js SSR compatibility)
    if (typeof window === "undefined") {
      return DEFAULT_SORT.sortDirection;
    }

    try {
      const stored = sessionStorage.getItem(STORAGE_KEYS.SORT_DIRECTION);
      if (stored && isValidSortDirection(stored)) {
        return stored as SortDirection;
      }
    } catch (error) {
      console.error("Failed to read sort preferences from sessionStorage:", error);
    }

    return DEFAULT_SORT.sortDirection;
  });

  /**
   * Persist sort preferences to sessionStorage whenever they change
   * (Phase V - 005-task-sort T027: Session persistence)
   */
  useEffect(() => {
    if (typeof window === "undefined") return;

    try {
      sessionStorage.setItem(STORAGE_KEYS.SORT_BY, sortBy);
      sessionStorage.setItem(STORAGE_KEYS.SORT_DIRECTION, sortDirection);
    } catch (error) {
      console.error("Failed to save sort preferences to sessionStorage:", error);
    }
  }, [sortBy, sortDirection]);

  /**
   * Handle sort change (field and direction)
   */
  const handleSortChange = useCallback(
    (newSortBy: SortField, newSortDirection: SortDirection) => {
      setSortBy(newSortBy);
      setSortDirection(newSortDirection);
    },
    []
  );

  /**
   * Reset sort to default (created_at desc)
   */
  const resetSort = useCallback(() => {
    setSortBy(DEFAULT_SORT.sortBy);
    setSortDirection(DEFAULT_SORT.sortDirection);
  }, []);

  return {
    sortBy,
    sortDirection,
    handleSortChange,
    resetSort,
  };
}

/**
 * Type guard to validate sort field
 */
function isValidSortField(value: string): boolean {
  const validFields: SortField[] = ["due_date", "priority", "created_at", "title"];
  return validFields.includes(value as SortField);
}

/**
 * Type guard to validate sort direction
 */
function isValidSortDirection(value: string): boolean {
  const validDirections: SortDirection[] = ["asc", "desc"];
  return validDirections.includes(value as SortDirection);
}

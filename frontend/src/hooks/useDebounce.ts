/**
 * useDebounce Hook
 *
 * Debounces a value by delaying updates until the value has stopped changing
 * for a specified delay period. Useful for optimizing search inputs and reducing
 * API calls.
 *
 * Phase: 004-search-filter
 * Task: T015 (US1)
 *
 * @example
 * ```tsx
 * const [searchTerm, setSearchTerm] = useState("");
 * const debouncedSearchTerm = useDebounce(searchTerm, 300);
 *
 * useEffect(() => {
 *   // This only runs 300ms after user stops typing
 *   if (debouncedSearchTerm) {
 *     performSearch(debouncedSearchTerm);
 *   }
 * }, [debouncedSearchTerm]);
 * ```
 */

import { useState, useEffect } from "react";

/**
 * Debounce a value by the specified delay.
 *
 * @param value - The value to debounce
 * @param delay - Delay in milliseconds (default: 300ms)
 * @returns The debounced value
 *
 * @template T - Type of the value to debounce
 */
export function useDebounce<T>(value: T, delay: number = 300): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    // Set up a timer to update the debounced value after delay
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    // Clean up the timer if value changes before delay expires
    // This prevents the debounced value from updating too frequently
    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]); // Re-run effect when value or delay changes

  return debouncedValue;
}

/**
 * Example usage scenarios:
 *
 * 1. Search input:
 * ```tsx
 * const [query, setQuery] = useState("");
 * const debouncedQuery = useDebounce(query, 300);
 *
 * useEffect(() => {
 *   searchTasks(debouncedQuery);
 * }, [debouncedQuery]);
 * ```
 *
 * 2. Form validation:
 * ```tsx
 * const [email, setEmail] = useState("");
 * const debouncedEmail = useDebounce(email, 500);
 *
 * useEffect(() => {
 *   validateEmail(debouncedEmail);
 * }, [debouncedEmail]);
 * ```
 *
 * 3. Resize handler:
 * ```tsx
 * const [windowWidth, setWindowWidth] = useState(window.innerWidth);
 * const debouncedWidth = useDebounce(windowWidth, 200);
 *
 * useEffect(() => {
 *   recalculateLayout(debouncedWidth);
 * }, [debouncedWidth]);
 * ```
 */

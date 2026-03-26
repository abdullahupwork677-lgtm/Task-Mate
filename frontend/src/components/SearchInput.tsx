/**
 * SearchInput Component
 *
 * Search input component with debounced input handling for task searching.
 * Provides a clean, accessible search interface with keyboard shortcuts
 * and visual feedback.
 *
 * Phase: 004-search-filter
 * Task: T014 (US1)
 *
 * @example
 * ```tsx
 * <SearchInput
 *   value={searchTerm}
 *   onChange={setSearchTerm}
 *   placeholder="Search tasks..."
 *   onClear={() => setSearchTerm("")}
 * />
 * ```
 */

"use client";

import React, { useState, useEffect, useRef } from "react";
import { useDebounce } from "../hooks/useDebounce";

interface SearchInputProps {
  /** Current search value */
  value: string;

  /** Callback when search value changes (debounced) */
  onChange: (value: string) => void;

  /** Placeholder text */
  placeholder?: string;

  /** Callback when search is cleared */
  onClear?: () => void;

  /** Debounce delay in milliseconds */
  debounceDelay?: number;

  /** Whether search is loading */
  isLoading?: boolean;

  /** CSS class name */
  className?: string;

  /** Auto-focus on mount */
  autoFocus?: boolean;
}

/**
 * Search input component with debouncing and keyboard shortcuts.
 *
 * Features:
 * - 300ms debounce delay (configurable)
 * - Clear button when input has value
 * - Loading indicator
 * - Keyboard shortcuts (Cmd/Ctrl+K to focus, Escape to clear)
 * - Accessible (ARIA labels, keyboard navigation)
 */
export function SearchInput({
  value,
  onChange,
  placeholder = "Search tasks...",
  onClear,
  debounceDelay = 300,
  isLoading = false,
  className = "",
  autoFocus = false
}: SearchInputProps) {
  // Local state for immediate UI updates
  const [localValue, setLocalValue] = useState(value);

  // Debounce local value before calling onChange
  const debouncedValue = useDebounce(localValue, debounceDelay);

  // Input ref for focus management
  const inputRef = useRef<HTMLInputElement>(null);

  // Update parent when debounced value changes
  useEffect(() => {
    if (debouncedValue !== value) {
      onChange(debouncedValue);
    }
  }, [debouncedValue, onChange, value]);

  // Sync local value with prop value
  useEffect(() => {
    setLocalValue(value);
  }, [value]);

  // Handle input change
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setLocalValue(e.target.value);
  };

  // Handle clear button
  const handleClear = () => {
    setLocalValue("");
    onChange("");
    onClear?.();
    inputRef.current?.focus();
  };

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd/Ctrl+K to focus search
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        inputRef.current?.focus();
      }

      // Escape to clear search (when focused)
      if (e.key === "Escape" && document.activeElement === inputRef.current) {
        handleClear();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <div className={`relative w-full ${className}`}>
      {/* Search Icon */}
      <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
        <svg
          className="w-5 h-5 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
      </div>

      {/* Input Field */}
      <input
        ref={inputRef}
        type="text"
        value={localValue}
        onChange={handleChange}
        placeholder={placeholder}
        autoFocus={autoFocus}
        className={`
          w-full
          pl-10
          pr-${localValue || isLoading ? "20" : "4"}
          py-2.5
          text-sm
          text-gray-900
          bg-white
          border
          border-gray-300
          rounded-lg
          focus:ring-2
          focus:ring-blue-500
          focus:border-blue-500
          transition-all
          duration-200
          placeholder:text-gray-400
        `}
        aria-label="Search tasks"
        aria-describedby="search-description"
      />

      {/* Screen reader description */}
      <span id="search-description" className="sr-only">
        Search tasks by title or description. Results update as you type with a {debounceDelay}ms delay.
        Press Cmd+K or Ctrl+K to focus, Escape to clear.
      </span>

      {/* Loading Spinner or Clear Button */}
      <div className="absolute inset-y-0 right-0 flex items-center pr-3">
        {isLoading ? (
          <div
            className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full"
            role="status"
            aria-label="Loading search results"
          />
        ) : localValue ? (
          <button
            type="button"
            onClick={handleClear}
            className="text-gray-400 hover:text-gray-600 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
            aria-label="Clear search"
          >
            <svg
              className="w-5 h-5"
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
          </button>
        ) : null}
      </div>

      {/* Keyboard Shortcut Hint (optional, show on hover) */}
      {!localValue && !isLoading && (
        <div className="absolute inset-y-0 right-0 flex items-center pr-12 pointer-events-none">
          <kbd className="hidden sm:inline-flex items-center gap-1 px-2 py-1 text-xs text-gray-500 bg-gray-100 border border-gray-200 rounded">
            <span className="text-xs">⌘K</span>
          </kbd>
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
 *     setKeyword,
 *     results,
 *     isLoading
 *   } = useSearch({ userId: "user-123" });
 *
 *   return (
 *     <div className="container mx-auto p-4">
 *       <SearchInput
 *         value={filters.keyword || ""}
 *         onChange={setKeyword}
 *         isLoading={isLoading}
 *         placeholder="Search tasks by title or description..."
 *         autoFocus
 *       />
 *
 *       {results && (
 *         <div className="mt-4">
 *           <p className="text-sm text-gray-600 mb-2">
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

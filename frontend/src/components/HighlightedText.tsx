/**
 * HighlightedText Component
 *
 * Highlights search keywords within text for better visual feedback.
 * Case-insensitive matching with customizable highlight styles.
 *
 * Phase: 004-search-filter
 * Task: T047 (Phase 9)
 *
 * @example
 * ```tsx
 * <HighlightedText
 *   text="Buy groceries from the store"
 *   keyword="grocery"
 * />
 * // Renders: Buy <mark>groceries</mark> from the store
 * ```
 */

"use client";

import React from "react";

interface HighlightedTextProps {
  /** Text to display */
  text: string;

  /** Keyword to highlight (case-insensitive) */
  keyword?: string | null;

  /** Custom highlight className (default: yellow background) */
  highlightClassName?: string;

  /** CSS class name */
  className?: string;
}

/**
 * Text component with keyword highlighting.
 *
 * Features:
 * - Case-insensitive keyword matching
 * - Multiple keyword occurrences highlighted
 * - Customizable highlight styles
 * - Accessible (uses <mark> semantic element)
 * - No highlighting if keyword is empty
 */
export function HighlightedText({
  text,
  keyword,
  highlightClassName = "bg-yellow-200 font-medium",
  className = ""
}: HighlightedTextProps) {
  // No highlighting if no keyword or empty text
  if (!keyword || !keyword.trim() || !text) {
    return <span className={className}>{text}</span>;
  }

  // Escape special regex characters in keyword
  const escapeRegExp = (str: string): string => {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  };

  try {
    // Create case-insensitive regex pattern
    const escapedKeyword = escapeRegExp(keyword.trim());
    const regex = new RegExp(`(${escapedKeyword})`, 'gi');

    // Split text by keyword matches
    const parts = text.split(regex);

    // Map parts to elements, highlighting matches
    const highlighted = parts.map((part, index) => {
      // Check if this part matches the keyword (case-insensitive)
      if (part.toLowerCase() === keyword.toLowerCase()) {
        return (
          <mark
            key={index}
            className={highlightClassName}
          >
            {part}
          </mark>
        );
      }
      return <span key={index}>{part}</span>;
    });

    return <span className={className}>{highlighted}</span>;
  } catch (error) {
    // If regex fails, return plain text
    console.error('HighlightedText regex error:', error);
    return <span className={className}>{text}</span>;
  }
}

/**
 * Hook for managing highlight state
 *
 * @example
 * ```tsx
 * function TaskItem({ task, keyword }) {
 *   return (
 *     <div>
 *       <h3>
 *         <HighlightedText
 *           text={task.title}
 *           keyword={keyword}
 *         />
 *       </h3>
 *       <p>
 *         <HighlightedText
 *           text={task.description || ""}
 *           keyword={keyword}
 *         />
 *       </p>
 *     </div>
 *   );
 * }
 * ```
 */

/**
 * Example usage in task list:
 *
 * ```tsx
 * function TaskList({ tasks, searchKeyword }) {
 *   return (
 *     <div className="space-y-2">
 *       {tasks.map(task => (
 *         <div key={task.id} className="p-4 border rounded">
 *           <h3 className="font-semibold">
 *             <HighlightedText
 *               text={task.title}
 *               keyword={searchKeyword}
 *             />
 *           </h3>
 *           {task.description && (
 *             <p className="text-sm text-gray-600 mt-1">
 *               <HighlightedText
 *                 text={task.description}
 *                 keyword={searchKeyword}
 *               />
 *             </p>
 *           )}
 *         </div>
 *       ))}
 *     </div>
 *   );
 * }
 * ```
 */

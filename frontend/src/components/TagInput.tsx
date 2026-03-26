'use client';

/**
 * TagInput Component
 *
 * Allows users to enter and manage tags with autocomplete suggestions.
 *
 * Features:
 * - Input field for adding new tags
 * - Autocomplete dropdown with existing tags
 * - Visual tag display with remove capability
 * - Keyboard navigation (Enter to add, Backspace to remove)
 * - Validation (no duplicates, max length)
 *
 * Phase V - Task Tags & Categories (003-task-tags) - Phase 8 Polish
 */

import React, { useState, useRef, useEffect } from 'react';
import { X } from 'lucide-react';
import { TagBadge } from './TagBadge';

export interface TagInputProps {
  /** Current list of tags */
  tags: string[];
  /** Callback when tags change */
  onChange: (tags: string[]) => void;
  /** Suggested tags for autocomplete */
  suggestions?: string[];
  /** Placeholder text */
  placeholder?: string;
  /** Maximum number of tags allowed */
  maxTags?: number;
  /** Input size */
  size?: 'sm' | 'md' | 'lg';
  /** Additional CSS classes */
  className?: string;
  /** Disabled state */
  disabled?: boolean;
}

/**
 * TagInput Component
 *
 * Provides a user-friendly interface for tag management with autocomplete.
 *
 * @example
 * ```tsx
 * <TagInput
 *   tags={['work', 'urgent']}
 *   onChange={(newTags) => setTags(newTags)}
 *   suggestions={['work', 'personal', 'shopping', 'urgent']}
 *   placeholder="Add tags..."
 *   maxTags={10}
 * />
 * ```
 */
export const TagInput: React.FC<TagInputProps> = ({
  tags,
  onChange,
  suggestions = [],
  placeholder = 'Add tags...',
  maxTags = 100,
  size = 'md',
  className = '',
  disabled = false,
}) => {
  const [inputValue, setInputValue] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  // Filter suggestions based on input and exclude already added tags
  const filteredSuggestions = suggestions
    .filter((s) => {
      const normalized = s.toLowerCase().trim();
      const input = inputValue.toLowerCase().trim();
      return (
        normalized.includes(input) &&
        !tags.map((t) => t.toLowerCase()).includes(normalized) &&
        input.length > 0
      );
    })
    .slice(0, 5); // Limit to 5 suggestions

  // Show suggestions when there's input and matches
  useEffect(() => {
    setShowSuggestions(filteredSuggestions.length > 0 && inputValue.length > 0);
    setSelectedSuggestionIndex(0);
  }, [inputValue, filteredSuggestions.length]);

  // Handle adding a tag
  const addTag = (tag: string) => {
    const normalized = tag.toLowerCase().trim();

    // Validation
    if (!normalized) return; // Empty
    if (normalized.length > 50) return; // Too long
    if (tags.map((t) => t.toLowerCase()).includes(normalized)) return; // Duplicate
    if (tags.length >= maxTags) return; // Max tags reached
    if (!/^[a-z0-9_-]+$/.test(normalized)) return; // Invalid characters

    // Add tag
    onChange([...tags, normalized]);
    setInputValue('');
    setShowSuggestions(false);
  };

  // Handle removing a tag
  const removeTag = (index: number) => {
    const newTags = [...tags];
    newTags.splice(index, 1);
    onChange(newTags);
  };

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (showSuggestions && filteredSuggestions.length > 0) {
        // Add selected suggestion
        addTag(filteredSuggestions[selectedSuggestionIndex]);
      } else {
        // Add typed value
        addTag(inputValue);
      }
    } else if (e.key === 'Backspace' && inputValue === '') {
      // Remove last tag on backspace when input is empty
      e.preventDefault();
      if (tags.length > 0) {
        removeTag(tags.length - 1);
      }
    } else if (e.key === 'ArrowDown' && showSuggestions) {
      e.preventDefault();
      setSelectedSuggestionIndex((prev) =>
        prev < filteredSuggestions.length - 1 ? prev + 1 : 0
      );
    } else if (e.key === 'ArrowUp' && showSuggestions) {
      e.preventDefault();
      setSelectedSuggestionIndex((prev) =>
        prev > 0 ? prev - 1 : filteredSuggestions.length - 1
      );
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
      setInputValue('');
    }
  };

  // Handle clicking outside to close suggestions
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(event.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(event.target as Node)
      ) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Size classes
  const sizeClasses = {
    sm: 'text-xs py-1 px-2',
    md: 'text-sm py-2 px-3',
    lg: 'text-base py-2 px-4',
  };

  return (
    <div className={`relative ${className}`}>
      {/* Tag Display */}
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-2">
          {tags.map((tag, index) => (
            <div
              key={`${tag}-${index}`}
              className="flex items-center gap-1 group"
            >
              <TagBadge tag={tag} size={size} />
              {!disabled && (
                <button
                  onClick={() => removeTag(index)}
                  className="opacity-0 group-hover:opacity-100 transition-opacity"
                  aria-label={`Remove ${tag} tag`}
                  type="button"
                >
                  <X className="w-3 h-3 text-gray-500 hover:text-red-600" />
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Input Field */}
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => {
            if (filteredSuggestions.length > 0) {
              setShowSuggestions(true);
            }
          }}
          placeholder={tags.length >= maxTags ? 'Max tags reached' : placeholder}
          disabled={disabled || tags.length >= maxTags}
          className={`
            w-full border border-gray-300 rounded-md
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
            disabled:bg-gray-100 disabled:cursor-not-allowed
            ${sizeClasses[size]}
          `}
        />

        {/* Autocomplete Suggestions */}
        {showSuggestions && filteredSuggestions.length > 0 && (
          <div
            ref={suggestionsRef}
            className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-40 overflow-y-auto"
          >
            {filteredSuggestions.map((suggestion, index) => (
              <button
                key={suggestion}
                type="button"
                onClick={() => addTag(suggestion)}
                className={`
                  w-full text-left px-3 py-2 text-sm
                  hover:bg-blue-50 transition-colors
                  ${index === selectedSuggestionIndex ? 'bg-blue-100' : ''}
                `}
                onMouseEnter={() => setSelectedSuggestionIndex(index)}
              >
                <TagBadge tag={suggestion} size="sm" />
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Helper Text */}
      {!disabled && (
        <p className="mt-1 text-xs text-gray-500">
          {tags.length >= maxTags
            ? `Maximum ${maxTags} tags reached`
            : `${tags.length}/${maxTags} tags • Press Enter to add • Backspace to remove last`}
        </p>
      )}
    </div>
  );
};

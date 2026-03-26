/**
 * useTags Hook
 *
 * Custom React hook for managing tag state and operations.
 *
 * Features:
 * - Add/remove tags with validation
 * - Fetch available tags from API
 * - Tag normalization (lowercase, deduplication)
 * - Autocomplete suggestions
 * - Loading and error states
 *
 * Phase V - Task Tags & Categories (003-task-tags) - Phase 8 Polish
 */

import { useState, useEffect, useCallback } from 'react';

export interface TagInfo {
  name: string;
  color: string;
  count: number;
}

export interface ListTagsResponse {
  tags: TagInfo[];
  total_tags: number;
  total_tasks: number;
}

export interface UseTagsOptions {
  /** Initial tags */
  initialTags?: string[];
  /** Maximum number of tags allowed */
  maxTags?: number;
  /** Automatically fetch available tags for autocomplete */
  fetchAvailableTags?: boolean;
  /** API base URL (defaults to /api) */
  apiBaseUrl?: string;
}

export interface UseTagsReturn {
  /** Current tags */
  tags: string[];
  /** Add a tag */
  addTag: (tag: string) => boolean;
  /** Remove a tag by index */
  removeTag: (index: number) => void;
  /** Set all tags at once */
  setTags: (tags: string[]) => void;
  /** Clear all tags */
  clearTags: () => void;
  /** Check if a tag exists */
  hasTag: (tag: string) => boolean;
  /** Available tags for autocomplete */
  availableTags: string[];
  /** Tag info with counts and colors */
  tagInfo: TagInfo[];
  /** Loading state for fetching tags */
  isLoading: boolean;
  /** Error state */
  error: string | null;
  /** Refresh available tags from API */
  refreshAvailableTags: () => Promise<void>;
  /** Validation error message (if add failed) */
  validationError: string | null;
}

/**
 * Custom hook for managing tags
 *
 * @example
 * ```tsx
 * const {
 *   tags,
 *   addTag,
 *   removeTag,
 *   availableTags,
 *   isLoading
 * } = useTags({
 *   initialTags: ['work', 'urgent'],
 *   fetchAvailableTags: true
 * });
 *
 * // Add a tag
 * const success = addTag('shopping');
 *
 * // Remove a tag
 * removeTag(0);
 *
 * // Use in TagInput component
 * <TagInput
 *   tags={tags}
 *   onChange={setTags}
 *   suggestions={availableTags}
 * />
 * ```
 */
export function useTags(options: UseTagsOptions = {}): UseTagsReturn {
  const {
    initialTags = [],
    maxTags = 100,
    fetchAvailableTags = false,
    apiBaseUrl = '/api',
  } = options;

  // State
  const [tags, setTagsState] = useState<string[]>(initialTags);
  const [availableTags, setAvailableTags] = useState<string[]>([]);
  const [tagInfo, setTagInfo] = useState<TagInfo[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  /**
   * Normalize a tag (lowercase, trim)
   */
  const normalizeTag = useCallback((tag: string): string => {
    return tag.toLowerCase().trim();
  }, []);

  /**
   * Validate a tag
   */
  const validateTag = useCallback(
    (tag: string): { valid: boolean; error?: string } => {
      const normalized = normalizeTag(tag);

      // Empty
      if (!normalized) {
        return { valid: false, error: 'Tag cannot be empty' };
      }

      // Too long
      if (normalized.length > 50) {
        return { valid: false, error: 'Tag must be 50 characters or less' };
      }

      // Invalid characters (only lowercase alphanumeric, hyphens, underscores)
      if (!/^[a-z0-9_-]+$/.test(normalized)) {
        return {
          valid: false,
          error: 'Tag can only contain lowercase letters, numbers, hyphens, and underscores',
        };
      }

      // Duplicate
      if (tags.map((t) => normalizeTag(t)).includes(normalized)) {
        return { valid: false, error: 'Tag already exists' };
      }

      // Max tags
      if (tags.length >= maxTags) {
        return { valid: false, error: `Maximum ${maxTags} tags allowed` };
      }

      return { valid: true };
    },
    [tags, maxTags, normalizeTag]
  );

  /**
   * Add a tag
   */
  const addTag = useCallback(
    (tag: string): boolean => {
      const normalized = normalizeTag(tag);
      const validation = validateTag(normalized);

      if (!validation.valid) {
        setValidationError(validation.error || 'Invalid tag');
        return false;
      }

      setTagsState((prev) => [...prev, normalized]);
      setValidationError(null);
      return true;
    },
    [normalizeTag, validateTag]
  );

  /**
   * Remove a tag by index
   */
  const removeTag = useCallback((index: number) => {
    setTagsState((prev) => {
      const newTags = [...prev];
      newTags.splice(index, 1);
      return newTags;
    });
    setValidationError(null);
  }, []);

  /**
   * Set all tags at once (with normalization and deduplication)
   */
  const setTags = useCallback(
    (newTags: string[]) => {
      const normalized = newTags
        .map((t) => normalizeTag(t))
        .filter((t) => t.length > 0 && t.length <= 50)
        .filter((t) => /^[a-z0-9_-]+$/.test(t));

      // Remove duplicates
      const unique = Array.from(new Set(normalized));

      // Apply max limit
      const limited = unique.slice(0, maxTags);

      setTagsState(limited);
      setValidationError(null);
    },
    [maxTags, normalizeTag]
  );

  /**
   * Clear all tags
   */
  const clearTags = useCallback(() => {
    setTagsState([]);
    setValidationError(null);
  }, []);

  /**
   * Check if a tag exists
   */
  const hasTag = useCallback(
    (tag: string): boolean => {
      const normalized = normalizeTag(tag);
      return tags.map((t) => normalizeTag(t)).includes(normalized);
    },
    [tags, normalizeTag]
  );

  /**
   * Fetch available tags from API
   */
  const refreshAvailableTags = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiBaseUrl}/tags`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Include cookies for authentication
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch tags: ${response.statusText}`);
      }

      const data: ListTagsResponse = await response.json();

      // Extract tag names for autocomplete
      setAvailableTags(data.tags.map((t) => t.name));

      // Store full tag info (with counts and colors)
      setTagInfo(data.tags);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch tags';
      setError(errorMessage);
      console.error('Error fetching tags:', err);
    } finally {
      setIsLoading(false);
    }
  }, [apiBaseUrl]);

  /**
   * Fetch available tags on mount if enabled
   */
  useEffect(() => {
    if (fetchAvailableTags) {
      refreshAvailableTags();
    }
  }, [fetchAvailableTags, refreshAvailableTags]);

  return {
    tags,
    addTag,
    removeTag,
    setTags,
    clearTags,
    hasTag,
    availableTags,
    tagInfo,
    isLoading,
    error,
    refreshAvailableTags,
    validationError,
  };
}

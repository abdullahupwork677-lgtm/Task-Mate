/**
 * TagBadge Component
 *
 * Displays a color-coded badge for a task tag with deterministic color generation.
 * Colors are generated from tag names using MD5 hashing for consistency across the app.
 *
 * Phase V - Task Tags & Categories (003-task-tags)
 */

import React from 'react';
import { generateTagColor } from '@/utils/tagColors';

interface TagBadgeProps {
  /**
   * Tag name to display (should already be normalized lowercase)
   */
  tag: string;

  /**
   * Size variant
   */
  size?: 'sm' | 'md' | 'lg';

  /**
   * Optional className for additional styling
   */
  className?: string;

  /**
   * Optional click handler for interactive tags
   */
  onClick?: (tag: string) => void;
}

/**
 * TagBadge Component
 *
 * Displays a tag with consistent color-coding based on hash algorithm.
 *
 * @example
 * ```tsx
 * <TagBadge tag="work" />
 * <TagBadge tag="urgent" size="lg" onClick={(tag) => filterByTag(tag)} />
 * ```
 */
export const TagBadge: React.FC<TagBadgeProps> = ({
  tag,
  size = 'md',
  className = '',
  onClick
}) => {
  // Generate consistent color from tag name
  const backgroundColor = generateTagColor(tag);

  // Calculate text color based on background brightness
  const textColor = getContrastColor(backgroundColor);

  // Size-based styling
  const sizeClasses = {
    sm: 'px-1.5 py-0.5 text-xs',
    md: 'px-2 py-1 text-sm',
    lg: 'px-3 py-1.5 text-base'
  };

  // Interactive styling if onClick provided
  const interactiveClasses = onClick
    ? 'cursor-pointer hover:opacity-80 transition-opacity duration-150'
    : '';

  return (
    <span
      className={`
        inline-flex items-center rounded-full font-medium
        ${sizeClasses[size]}
        ${interactiveClasses}
        ${className}
      `.trim()}
      style={{
        backgroundColor,
        color: textColor
      }}
      onClick={onClick ? () => onClick(tag) : undefined}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick(tag);
        }
      } : undefined}
      aria-label={onClick ? `Filter by ${tag} tag` : `${tag} tag`}
    >
      {tag}
    </span>
  );
};

/**
 * Calculate contrasting text color (black or white) based on background brightness
 *
 * Uses relative luminance formula to determine if background is light or dark
 */
function getContrastColor(hexColor: string): string {
  // Remove # if present
  const hex = hexColor.replace('#', '');

  // Parse RGB values
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);

  // Calculate relative luminance (0-255)
  // Formula: (299*R + 587*G + 114*B) / 1000
  const brightness = (r * 299 + g * 587 + b * 114) / 1000;

  // Use white text on dark backgrounds, black text on light backgrounds
  return brightness > 128 ? '#000000' : '#FFFFFF';
}

/**
 * TagList Component
 *
 * Displays multiple tags with consistent spacing
 *
 * @example
 * ```tsx
 * <TagList tags={['work', 'urgent', 'shopping']} />
 * ```
 */
interface TagListProps {
  tags: string[];
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  onTagClick?: (tag: string) => void;
}

export const TagList: React.FC<TagListProps> = ({
  tags,
  size = 'md',
  className = '',
  onTagClick
}) => {
  if (!tags || tags.length === 0) {
    return null;
  }

  return (
    <div className={`flex flex-wrap gap-1.5 ${className}`.trim()}>
      {tags.map((tag) => (
        <TagBadge
          key={tag}
          tag={tag}
          size={size}
          onClick={onTagClick}
        />
      ))}
    </div>
  );
};

export default TagBadge;

/**
 * Unit Tests: TagBadge Component
 *
 * Tests the TagBadge and TagList components for:
 * - Rendering with different sizes
 * - Color generation consistency
 * - Interactive behavior (onClick)
 * - Accessibility (ARIA labels, keyboard navigation)
 * - Edge cases (empty tags, special characters)
 *
 * Phase V - Task Tags & Categories (003-task-tags)
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { TagBadge, TagList } from '@/components/TagBadge';
import { generateTagColor } from '@/utils/tagColors';

describe('TagBadge Component', () => {
  describe('Rendering', () => {
    it('renders tag name correctly', () => {
      render(<TagBadge tag="work" />);
      expect(screen.getByText('work')).toBeInTheDocument();
    });

    it('renders with small size', () => {
      const { container } = render(<TagBadge tag="work" size="sm" />);
      const badge = container.firstChild as HTMLElement;
      expect(badge).toHaveClass('text-xs');
    });

    it('renders with medium size (default)', () => {
      const { container } = render(<TagBadge tag="work" size="md" />);
      const badge = container.firstChild as HTMLElement;
      expect(badge).toHaveClass('text-sm');
    });

    it('renders with large size', () => {
      const { container } = render(<TagBadge tag="work" size="lg" />);
      const badge = container.firstChild as HTMLElement;
      expect(badge).toHaveClass('text-base');
    });

    it('applies custom className', () => {
      const { container } = render(<TagBadge tag="work" className="custom-class" />);
      const badge = container.firstChild as HTMLElement;
      expect(badge).toHaveClass('custom-class');
    });
  });

  describe('Color Generation', () => {
    it('applies generated background color', () => {
      const { container } = render(<TagBadge tag="work" />);
      const badge = container.firstChild as HTMLElement;
      const expectedColor = generateTagColor('work');
      expect(badge).toHaveStyle({ backgroundColor: expectedColor });
    });

    it('generates consistent colors for same tag', () => {
      const { container: container1 } = render(<TagBadge tag="urgent" />);
      const { container: container2 } = render(<TagBadge tag="urgent" />);

      const badge1 = container1.firstChild as HTMLElement;
      const badge2 = container2.firstChild as HTMLElement;

      expect(badge1.style.backgroundColor).toBe(badge2.style.backgroundColor);
    });

    it('generates different colors for different tags', () => {
      const { container: container1 } = render(<TagBadge tag="work" />);
      const { container: container2 } = render(<TagBadge tag="urgent" />);

      const badge1 = container1.firstChild as HTMLElement;
      const badge2 = container2.firstChild as HTMLElement;

      expect(badge1.style.backgroundColor).not.toBe(badge2.style.backgroundColor);
    });

    it('applies contrasting text color based on background brightness', () => {
      const { container } = render(<TagBadge tag="work" />);
      const badge = container.firstChild as HTMLElement;

      // Text color should be either black or white for contrast
      const textColor = badge.style.color;
      expect(['#000000', '#FFFFFF', 'rgb(0, 0, 0)', 'rgb(255, 255, 255)']).toContain(textColor);
    });
  });

  describe('Interactive Behavior', () => {
    it('calls onClick handler when clicked', () => {
      const handleClick = jest.fn();
      render(<TagBadge tag="work" onClick={handleClick} />);

      const badge = screen.getByText('work');
      fireEvent.click(badge);

      expect(handleClick).toHaveBeenCalledTimes(1);
      expect(handleClick).toHaveBeenCalledWith('work');
    });

    it('does not have interactive styles without onClick', () => {
      const { container } = render(<TagBadge tag="work" />);
      const badge = container.firstChild as HTMLElement;
      expect(badge).not.toHaveClass('cursor-pointer');
    });

    it('has interactive styles with onClick', () => {
      const handleClick = jest.fn();
      const { container } = render(<TagBadge tag="work" onClick={handleClick} />);
      const badge = container.firstChild as HTMLElement;
      expect(badge).toHaveClass('cursor-pointer');
      expect(badge).toHaveClass('hover:opacity-80');
    });

    it('responds to Enter key when interactive', () => {
      const handleClick = jest.fn();
      render(<TagBadge tag="work" onClick={handleClick} />);

      const badge = screen.getByText('work');
      fireEvent.keyDown(badge, { key: 'Enter' });

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('responds to Space key when interactive', () => {
      const handleClick = jest.fn();
      render(<TagBadge tag="work" onClick={handleClick} />);

      const badge = screen.getByText('work');
      fireEvent.keyDown(badge, { key: ' ' });

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('does not respond to other keys', () => {
      const handleClick = jest.fn();
      render(<TagBadge tag="work" onClick={handleClick} />);

      const badge = screen.getByText('work');
      fireEvent.keyDown(badge, { key: 'a' });

      expect(handleClick).not.toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    it('has button role when interactive', () => {
      const handleClick = jest.fn();
      const { container } = render(<TagBadge tag="work" onClick={handleClick} />);
      const badge = container.firstChild as HTMLElement;
      expect(badge).toHaveAttribute('role', 'button');
    });

    it('does not have button role when non-interactive', () => {
      const { container } = render(<TagBadge tag="work" />);
      const badge = container.firstChild as HTMLElement;
      expect(badge).not.toHaveAttribute('role', 'button');
    });

    it('is keyboard focusable when interactive', () => {
      const handleClick = jest.fn();
      const { container } = render(<TagBadge tag="work" onClick={handleClick} />);
      const badge = container.firstChild as HTMLElement;
      expect(badge).toHaveAttribute('tabIndex', '0');
    });

    it('is not keyboard focusable when non-interactive', () => {
      const { container } = render(<TagBadge tag="work" />);
      const badge = container.firstChild as HTMLElement;
      expect(badge).not.toHaveAttribute('tabIndex');
    });

    it('has appropriate aria-label when interactive', () => {
      const handleClick = jest.fn();
      const { container } = render(<TagBadge tag="work" onClick={handleClick} />);
      const badge = container.firstChild as HTMLElement;
      expect(badge).toHaveAttribute('aria-label', 'Filter by work tag');
    });

    it('has appropriate aria-label when non-interactive', () => {
      const { container } = render(<TagBadge tag="work" />);
      const badge = container.firstChild as HTMLElement;
      expect(badge).toHaveAttribute('aria-label', 'work tag');
    });
  });

  describe('Edge Cases', () => {
    it('handles tags with hyphens', () => {
      render(<TagBadge tag="high-priority" />);
      expect(screen.getByText('high-priority')).toBeInTheDocument();
    });

    it('handles tags with underscores', () => {
      render(<TagBadge tag="work_related" />);
      expect(screen.getByText('work_related')).toBeInTheDocument();
    });

    it('handles tags with numbers', () => {
      render(<TagBadge tag="q1-2026" />);
      expect(screen.getByText('q1-2026')).toBeInTheDocument();
    });

    it('handles very long tag names', () => {
      const longTag = 'a'.repeat(50);
      render(<TagBadge tag={longTag} />);
      expect(screen.getByText(longTag)).toBeInTheDocument();
    });

    it('handles single character tags', () => {
      render(<TagBadge tag="a" />);
      expect(screen.getByText('a')).toBeInTheDocument();
    });
  });
});

describe('TagList Component', () => {
  describe('Rendering', () => {
    it('renders multiple tags', () => {
      render(<TagList tags={['work', 'urgent', 'shopping']} />);
      expect(screen.getByText('work')).toBeInTheDocument();
      expect(screen.getByText('urgent')).toBeInTheDocument();
      expect(screen.getByText('shopping')).toBeInTheDocument();
    });

    it('renders nothing when tags array is empty', () => {
      const { container } = render(<TagList tags={[]} />);
      expect(container.firstChild).toBeNull();
    });

    it('renders nothing when tags is undefined', () => {
      const { container } = render(<TagList tags={undefined as any} />);
      expect(container.firstChild).toBeNull();
    });

    it('renders nothing when tags is null', () => {
      const { container } = render(<TagList tags={null as any} />);
      expect(container.firstChild).toBeNull();
    });

    it('applies size to all tags', () => {
      const { container } = render(<TagList tags={['work', 'urgent']} size="lg" />);
      const badges = container.querySelectorAll('span');
      badges.forEach((badge) => {
        expect(badge).toHaveClass('text-base');
      });
    });

    it('applies custom className', () => {
      const { container } = render(<TagList tags={['work']} className="custom-list" />);
      const wrapper = container.firstChild as HTMLElement;
      expect(wrapper).toHaveClass('custom-list');
    });
  });

  describe('Interactive Behavior', () => {
    it('passes onClick to all tags', () => {
      const handleClick = jest.fn();
      render(<TagList tags={['work', 'urgent']} onTagClick={handleClick} />);

      fireEvent.click(screen.getByText('work'));
      expect(handleClick).toHaveBeenCalledWith('work');

      fireEvent.click(screen.getByText('urgent'));
      expect(handleClick).toHaveBeenCalledWith('urgent');
    });

    it('renders tags in provided order', () => {
      const { container } = render(<TagList tags={['zebra', 'apple', 'banana']} />);
      const badges = container.querySelectorAll('span');
      expect(badges[0]).toHaveTextContent('zebra');
      expect(badges[1]).toHaveTextContent('apple');
      expect(badges[2]).toHaveTextContent('banana');
    });
  });

  describe('Edge Cases', () => {
    it('handles duplicate tags', () => {
      render(<TagList tags={['work', 'work', 'urgent']} />);
      const workTags = screen.getAllByText('work');
      expect(workTags).toHaveLength(2);
    });

    it('handles large number of tags', () => {
      const manyTags = Array.from({ length: 50 }, (_, i) => `tag${i}`);
      render(<TagList tags={manyTags} />);
      expect(screen.getByText('tag0')).toBeInTheDocument();
      expect(screen.getByText('tag49')).toBeInTheDocument();
    });
  });
});

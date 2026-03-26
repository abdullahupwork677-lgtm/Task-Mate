/**
 * DueDateBadge Component Tests
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { DueDateBadge } from '@/components/DueDateBadge';

describe('DueDateBadge', () => {
  it('renders with formatted due date', () => {
    const dueDate = new Date('2026-02-15T14:00:00Z').toISOString();

    render(<DueDateBadge dueDate={dueDate} />);

    // Check that badge is rendered
    const badge = screen.getByTitle(/Due:/i);
    expect(badge).toBeInTheDocument();
  });

  it('displays time remaining', () => {
    // Set due date to 2 days from now
    const now = new Date();
    const dueDate = new Date(now.getTime() + 2 * 24 * 60 * 60 * 1000).toISOString();

    render(<DueDateBadge dueDate={dueDate} />);

    // Check that "in" appears in the text (e.g., "in 2 days")
    expect(screen.getByText(/in/i)).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const dueDate = new Date().toISOString();

    const { container } = render(
      <DueDateBadge dueDate={dueDate} className="custom-class" />
    );

    const badge = container.querySelector('.custom-class');
    expect(badge).toBeInTheDocument();
  });

  it('has blue styling (not overdue)', () => {
    const dueDate = new Date(Date.now() + 86400000).toISOString(); // Tomorrow

    const { container } = render(<DueDateBadge dueDate={dueDate} />);

    const badge = container.querySelector('.bg-blue-100');
    expect(badge).toBeInTheDocument();
  });

  it('shows calendar icon', () => {
    const dueDate = new Date().toISOString();

    const { container } = render(<DueDateBadge dueDate={dueDate} />);

    const icon = container.querySelector('svg');
    expect(icon).toBeInTheDocument();
  });
});

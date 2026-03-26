/**
 * OverdueBadge Component Tests
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { OverdueBadge } from '@/components/OverdueBadge';

describe('OverdueBadge', () => {
  it('renders with overdue date', () => {
    // Set due date to 2 days ago
    const dueDate = new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString();

    render(<OverdueBadge dueDate={dueDate} />);

    // Check that badge is rendered
    const badge = screen.getByTitle(/Overdue since:/i);
    expect(badge).toBeInTheDocument();
  });

  it('displays "Overdue" text', () => {
    const dueDate = new Date(Date.now() - 86400000).toISOString(); // Yesterday

    render(<OverdueBadge dueDate={dueDate} />);

    expect(screen.getByText(/Overdue/i)).toBeInTheDocument();
  });

  it('uses provided overdueBy prop', () => {
    const dueDate = new Date(Date.now() - 86400000).toISOString();
    const overdueBy = '2 days ago';

    render(<OverdueBadge dueDate={dueDate} overdueBy={overdueBy} />);

    expect(screen.getByText(/Overdue 2 days ago/i)).toBeInTheDocument();
  });

  it('calculates overdue duration when overdueBy not provided', () => {
    const dueDate = new Date(Date.now() - 86400000).toISOString(); // Yesterday

    render(<OverdueBadge dueDate={dueDate} />);

    // Check that "ago" appears in the text
    expect(screen.getByText(/ago/i)).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const dueDate = new Date(Date.now() - 86400000).toISOString();

    const { container } = render(
      <OverdueBadge dueDate={dueDate} className="custom-class" />
    );

    const badge = container.querySelector('.custom-class');
    expect(badge).toBeInTheDocument();
  });

  it('has red styling (overdue)', () => {
    const dueDate = new Date(Date.now() - 86400000).toISOString();

    const { container } = render(<OverdueBadge dueDate={dueDate} />);

    const badge = container.querySelector('.bg-red-100');
    expect(badge).toBeInTheDocument();
  });

  it('shows alert icon', () => {
    const dueDate = new Date(Date.now() - 86400000).toISOString();

    const { container } = render(<OverdueBadge dueDate={dueDate} />);

    const icon = container.querySelector('svg');
    expect(icon).toBeInTheDocument();
  });
});

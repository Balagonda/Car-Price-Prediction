import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

describe('UI Components', () => {
  it('renders a standard button correctly', () => {
    render(<button>Click Me</button>);
    const button = screen.getByRole('button', { name: /click me/i });
    expect(button).toBeInTheDocument();
  });

  it('renders a heading properly', () => {
    render(<h1>AutoWorth AI</h1>);
    const heading = screen.getByRole('heading', { level: 1, name: /autoworth ai/i });
    expect(heading).toBeInTheDocument();
  });
});

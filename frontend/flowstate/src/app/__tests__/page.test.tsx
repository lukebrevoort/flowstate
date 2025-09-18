import React from 'react';
import { render, screen } from '@testing-library/react';

// Simple test component for now
function SimpleComponent() {
  return (
    <div>
      <h1>FlowState</h1>
      <p>Welcome to FlowState</p>
    </div>
  );
}

describe('Simple Component Test', () => {
  it('renders correctly', () => {
    render(<SimpleComponent />);
    expect(
      screen.getByRole('heading', { name: /flowstate/i })
    ).toBeInTheDocument();
    expect(screen.getByText(/welcome to flowstate/i)).toBeInTheDocument();
  });
});

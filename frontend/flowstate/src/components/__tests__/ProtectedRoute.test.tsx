import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import ProtectedRoute from '../ProtectedRoute';

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}));

// Mock AuthContext
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(),
}));

const mockPush = jest.fn();
const mockUseRouter = useRouter as jest.MockedFunction<typeof useRouter>;
const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;

const createMockAuthContext = (isAuthenticated: boolean, loading: boolean) => ({
  isAuthenticated,
  loading,
  user: isAuthenticated ? { id: '1', name: 'Test User', email: 'test@example.com' } : null,
  login: jest.fn(),
  logout: jest.fn(),
  signup: jest.fn(),
});

describe('ProtectedRoute Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseRouter.mockReturnValue({
      push: mockPush,
      // Add other router properties as needed
    } as any);
  });

  it('renders children when user is authenticated', () => {
    mockUseAuth.mockReturnValue(createMockAuthContext(true, false));

    render(
      <ProtectedRoute>
        <div>Protected content</div>
      </ProtectedRoute>
    );

    expect(screen.getByText('Protected content')).toBeInTheDocument();
    expect(mockPush).not.toHaveBeenCalled();
  });

  it('shows loading spinner when loading is true', () => {
    mockUseAuth.mockReturnValue(createMockAuthContext(false, true));

    render(
      <ProtectedRoute>
        <div>Protected content</div>
      </ProtectedRoute>
    );

    // Check for loading spinner by class selector
    const loadingSpinner = document.querySelector('.animate-spin');
    expect(loadingSpinner).toBeInTheDocument();
    expect(loadingSpinner).toHaveClass('border-flowstate-accent');
    
    // Protected content should not be visible
    expect(screen.queryByText('Protected content')).not.toBeInTheDocument();
    expect(mockPush).not.toHaveBeenCalled();
  });

  it('redirects to login when user is not authenticated and not loading', async () => {
    mockUseAuth.mockReturnValue(createMockAuthContext(false, false));

    render(
      <ProtectedRoute>
        <div>Protected content</div>
      </ProtectedRoute>
    );

    // Should redirect to login
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/Login');
    });

    // Protected content should not be visible
    expect(screen.queryByText('Protected content')).not.toBeInTheDocument();
  });

  it('returns null when not authenticated and not loading', () => {
    mockUseAuth.mockReturnValue(createMockAuthContext(false, false));

    const { container } = render(
      <ProtectedRoute>
        <div>Protected content</div>
      </ProtectedRoute>
    );

    // Container should be empty (null render)
    expect(container.firstChild).toBeNull();
  });

  it('handles authentication state changes', async () => {
    // Start with loading state
    mockUseAuth.mockReturnValue(createMockAuthContext(false, true));

    const { rerender } = render(
      <ProtectedRoute>
        <div>Protected content</div>
      </ProtectedRoute>
    );

    // Should show loading spinner
    const spinnerElement = document.querySelector('.animate-spin');
    expect(spinnerElement).toBeInTheDocument();

    // Change to authenticated
    mockUseAuth.mockReturnValue(createMockAuthContext(true, false));

    rerender(
      <ProtectedRoute>
        <div>Protected content</div>
      </ProtectedRoute>
    );

    // Should now show protected content
    expect(screen.getByText('Protected content')).toBeInTheDocument();
    expect(document.querySelector('.animate-spin')).not.toBeInTheDocument();
  });

  it('renders multiple children correctly when authenticated', () => {
    mockUseAuth.mockReturnValue(createMockAuthContext(true, false));

    render(
      <ProtectedRoute>
        <div>First child</div>
        <div>Second child</div>
        <span>Third child</span>
      </ProtectedRoute>
    );

    expect(screen.getByText('First child')).toBeInTheDocument();
    expect(screen.getByText('Second child')).toBeInTheDocument();
    expect(screen.getByText('Third child')).toBeInTheDocument();
  });

  it('handles complex React node children', () => {
    mockUseAuth.mockReturnValue(createMockAuthContext(true, false));

    render(
      <ProtectedRoute>
        <div>
          <h1>Dashboard</h1>
          <p>Welcome to the <strong>protected</strong> area!</p>
        </div>
      </ProtectedRoute>
    );

    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Dashboard');
    expect(screen.getByText(/Welcome to the/)).toBeInTheDocument();
    expect(screen.getByText('protected')).toBeInTheDocument();
  });
});
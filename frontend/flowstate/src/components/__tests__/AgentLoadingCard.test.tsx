import React from 'react';
import { render, screen, act, waitFor } from '@testing-library/react';
import AgentLoadingCard, { AgentStep } from '../AgentLoadingCard';

// Mock console.log to prevent test noise
const originalConsoleLog = console.log;
beforeAll(() => {
  console.log = jest.fn();
});

afterAll(() => {
  console.log = originalConsoleLog;
});

// Helper to create mock steps
const createMockStep = (overrides: Partial<AgentStep> = {}): AgentStep => ({
  type: 'action',
  agent: 'Test Agent',
  message: 'Test message',
  ...overrides,
});

// Helper to advance time for timers
const advanceTime = async (ms: number) => {
  await act(async () => {
    jest.advanceTimersByTime(ms);
  });
};

describe('AgentLoadingCard Component', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    jest.clearAllMocks();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  describe('Initial States', () => {
    it('renders initial loading state when no steps provided', () => {
      render(<AgentLoadingCard />);

      expect(
        screen.getByText('Processing Your Request...')
      ).toBeInTheDocument();
      const spinner = document.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });

    it('renders initial loading state with empty steps array', () => {
      render(<AgentLoadingCard steps={[]} />);

      expect(
        screen.getByText('Processing Your Request...')
      ).toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(
        <AgentLoadingCard className='custom-class' />
      );
      expect(container.firstChild).toHaveClass('custom-class');
    });
  });

  describe('Step Rendering', () => {
    it('renders single step correctly', () => {
      const step = createMockStep({
        agent: 'Project Manager',
        message: 'Analyzing your request...',
        type: 'routing',
      });

      render(<AgentLoadingCard steps={[step]} />);

      expect(screen.getByText('Project Manager')).toBeInTheDocument();
      expect(screen.getByText('Analyzing your request...')).toBeInTheDocument();
      expect(screen.getByText('Processing Request')).toBeInTheDocument();
      expect(
        screen.getByText('Student Productivity Agent')
      ).toBeInTheDocument();
    });

    it('renders step with tool information', () => {
      const step = createMockStep({
        message: 'Using calendar integration',
        tool: 'google_calendar_api',
        type: 'tool',
      });

      render(<AgentLoadingCard steps={[step]} />);

      expect(
        screen.getByText('Using calendar integration')
      ).toBeInTheDocument();
      expect(screen.getByText('google_calendar_api')).toBeInTheDocument();
    });

    it('renders correct icons for different step types', () => {
      const steps: AgentStep[] = [
        createMockStep({ type: 'routing' }),
        createMockStep({ type: 'tool' }),
        createMockStep({ type: 'completion' }),
        createMockStep({ type: 'action' }), // default case
      ];

      // Test each step type by rendering individually
      steps.forEach(step => {
        const { unmount } = render(<AgentLoadingCard steps={[step]} />);

        // Icons are rendered as SVG elements within the component structure
        const iconElement = document.querySelector(
          '.text-flowstate-accent svg'
        );
        expect(iconElement).toBeInTheDocument();

        unmount();
      });
    });
  });

  describe('Step Progression', () => {
    it('progresses through multiple steps automatically', async () => {
      const steps = [
        createMockStep({ agent: 'Agent 1', message: 'First step' }),
        createMockStep({ agent: 'Agent 2', message: 'Second step' }),
      ];

      render(<AgentLoadingCard steps={steps} stepDuration={1000} />);

      // Initially shows first step
      expect(screen.getByText('First step')).toBeInTheDocument();
      expect(screen.queryByText('Second step')).not.toBeInTheDocument();

      // After step duration, should progress to second step
      await advanceTime(1000 + 300); // stepDuration + transitionDuration

      expect(screen.getByText('Second step')).toBeInTheDocument();
    });

    it('handles new steps being added dynamically', async () => {
      const initialSteps = [createMockStep({ message: 'Initial step' })];

      const { rerender } = render(
        <AgentLoadingCard steps={initialSteps} stepDuration={1000} />
      );

      expect(screen.getByText('Initial step')).toBeInTheDocument();

      // Add a new step
      const newSteps = [
        ...initialSteps,
        createMockStep({ message: 'New step added' }),
      ];

      rerender(<AgentLoadingCard steps={newSteps} stepDuration={1000} />);

      // Should show the new step (it may take effect immediately or after a delay)
      await waitFor(
        () => {
          expect(screen.getByText('New step added')).toBeInTheDocument();
        },
        { timeout: 2000 }
      );
    });

    it('calls onComplete when all steps are finished', async () => {
      const onComplete = jest.fn();
      const steps = [createMockStep({ message: 'Only step' })];

      render(
        <AgentLoadingCard
          steps={steps}
          stepDuration={1000}
          onComplete={onComplete}
        />
      );

      // Wait for step to complete
      await advanceTime(1000);

      expect(onComplete).toHaveBeenCalledTimes(1);
    });

    it('respects custom step and transition durations', async () => {
      const steps = [
        createMockStep({ message: 'First' }),
        createMockStep({ message: 'Second' }),
      ];

      render(
        <AgentLoadingCard
          steps={steps}
          stepDuration={500}
          transitionDuration={100}
        />
      );

      expect(screen.getByText('First')).toBeInTheDocument();

      // Should transition after custom duration
      await advanceTime(500 + 100);
      expect(screen.getByText('Second')).toBeInTheDocument();
    });
  });

  describe('Completion State', () => {
    it('handles external completion state', () => {
      const steps = [createMockStep({ message: 'Step' })];

      const { rerender } = render(
        <AgentLoadingCard steps={steps} isComplete={false} />
      );

      // Should show normal step
      expect(screen.getByText('Step')).toBeInTheDocument();

      // Mark as complete externally
      rerender(<AgentLoadingCard steps={steps} isComplete={true} />);

      // Component should handle completion state
      expect(screen.getByText('Step')).toBeInTheDocument();
    });

    it('prevents auto-progression when complete', async () => {
      const steps = [
        createMockStep({ message: 'First' }),
        createMockStep({ message: 'Second' }),
      ];

      render(
        <AgentLoadingCard steps={steps} isComplete={true} stepDuration={100} />
      );

      expect(screen.getByText('First')).toBeInTheDocument();

      // Even after waiting, should not progress since complete
      await advanceTime(200);
      expect(screen.getByText('First')).toBeInTheDocument();
      expect(screen.queryByText('Second')).not.toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles undefined currentStepData gracefully', () => {
      const steps = [createMockStep({ message: 'Test' })];

      render(<AgentLoadingCard steps={steps} />);

      // Verify it doesn't crash and shows appropriate fallback
      expect(screen.getByText('Test')).toBeInTheDocument();
    });

    it('handles steps with missing optional fields', () => {
      const step: AgentStep = {
        type: 'action',
        agent: 'Test Agent',
        message: 'Message without optional fields',
        // No tool or timestamp
      };

      render(<AgentLoadingCard steps={[step]} />);

      expect(
        screen.getByText('Message without optional fields')
      ).toBeInTheDocument();
      expect(screen.getByText('Test Agent')).toBeInTheDocument();
      // Should not show tool section
      expect(
        screen.queryByRole('generic', { name: /google_calendar_api/ })
      ).not.toBeInTheDocument();
    });

    it('handles rapid step additions', async () => {
      const { rerender } = render(<AgentLoadingCard steps={[]} />);

      // Add multiple steps rapidly
      const step1 = [createMockStep({ message: 'Step 1' })];
      const step2 = [...step1, createMockStep({ message: 'Step 2' })];
      const step3 = [...step2, createMockStep({ message: 'Step 3' })];

      rerender(<AgentLoadingCard steps={step1} />);
      rerender(<AgentLoadingCard steps={step2} />);
      rerender(<AgentLoadingCard steps={step3} />);

      // Should handle without crashing
      expect(screen.getByText(/Step [1-3]/)).toBeInTheDocument();
    });
  });

  describe('UI Elements', () => {
    it('renders loading animation elements', () => {
      render(<AgentLoadingCard />);

      // Check for spinner in initial state using class selector
      const spinner = document.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });

    it('renders bounce animation dots when showing steps', () => {
      const steps = [createMockStep()];
      render(<AgentLoadingCard steps={steps} />);

      // Should show bouncing dots using class selector
      const dots = document.querySelectorAll('.animate-bounce');
      expect(dots).toHaveLength(3);
    });

    it('shows correct step type styling', () => {
      const step = createMockStep({
        agent: 'Scheduler',
        type: 'tool',
      });

      render(<AgentLoadingCard steps={[step]} />);

      // Should show agent badge
      expect(screen.getByText('Scheduler')).toBeInTheDocument();

      // Should have proper styling classes (component structure)
      const agentBadge = screen.getByText('Scheduler');
      expect(agentBadge).toHaveClass('inline-flex');
    });
  });
});

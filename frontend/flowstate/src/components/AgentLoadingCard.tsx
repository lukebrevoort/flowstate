import React, { useState, useEffect, useMemo } from 'react';
import { Bot, Zap, Clock, CheckCircle, ArrowRight } from 'lucide-react';

// Types
export interface AgentStep {
  type: 'routing' | 'action' | 'tool' | 'completion';
  agent: string;
  message: string;
  tool?: string;
  timestamp?: string;
}

export interface AgentLoadingCardProps {
  steps?: AgentStep[];
  isComplete?: boolean;
  onComplete?: () => void;
  stepDuration?: number; // Duration each step shows in ms
  transitionDuration?: number; // Fade transition duration in ms
  className?: string;
  showDemo?: boolean; // Whether to show demo controls
}

const AgentLoadingCard: React.FC<AgentLoadingCardProps> = ({
  steps = [],
  isComplete = false,
  onComplete,
  stepDuration = 2500,
  transitionDuration = 300,
  className = '',
  showDemo = false
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [showStep, setShowStep] = useState(true);
  const [internalComplete, setInternalComplete] = useState(isComplete);

  // Default steps for demo/testing
  const defaultSteps: AgentStep[] = [
    {
      type: 'routing',
      agent: 'Main Agent',
      message: "Routing request to Project Management Agent...",
      timestamp: new Date().toLocaleTimeString()
    },
    {
      type: 'action',
      agent: 'Project Management Agent',
      message: "Getting current time as reference point...",
      timestamp: new Date().toLocaleTimeString()
    },
    {
      type: 'tool',
      agent: 'Project Management Agent',
      message: "get_current_time",
      tool: 'get_current_time',
      timestamp: new Date().toLocaleTimeString()
    },
    {
      type: 'action',
      agent: 'Project Management Agent',
      message: "Retrieving assignments for the next month...",
      timestamp: new Date().toLocaleTimeString()
    },
    {
      type: 'tool',
      agent: 'Project Management Agent',
      message: "get_assignments_in_date_range",
      tool: 'get_assignments_in_date_range',
      timestamp: new Date().toLocaleTimeString()
    },
    {
      type: 'completion',
      agent: 'Project Management Agent',
      message: "Processing 8 assignments by priority...",
      timestamp: new Date().toLocaleTimeString()
    }
  ];

// Always use the most up-to-date steps - use memo to recalculate when steps change
  const activeSteps = useMemo(() => {
    const result = steps.length > 0 ? steps : defaultSteps;
    console.log('activeSteps recalculated:', result);
    return result;
  }, [steps]);

  // Debug logs to track what's happening
  useEffect(() => {
    console.log('AgentLoadingCard - steps prop:', steps);
    console.log('AgentLoadingCard - activeSteps:', activeSteps);
    console.log('AgentLoadingCard - steps.length:', steps.length);
  }, [steps, activeSteps]);

  // Reset when new steps come in
  useEffect(() => {
    if (steps.length > 0) {
      console.log('New steps received, resetting to step 0');
      setCurrentStep(0);
      setInternalComplete(false);
      setShowStep(true);
    }
  }, [steps]);

  // Handle external completion state changes
  useEffect(() => {
    setInternalComplete(isComplete);
  }, [isComplete]);

  // Handle step progression
  useEffect(() => {
    if (internalComplete) return;
    
    // If we have no steps yet, wait
    if (steps.length === 0) return;
    
    // If we have steps but activeSteps is using defaults, force re-render
    if (steps.length > 0 && activeSteps === defaultSteps) {
      console.log('Forcing re-render with real steps');
      return;
    }

    const interval = setInterval(() => {
      if (currentStep < activeSteps.length - 1) {
        // Fade out current step
        setShowStep(false);
        
        setTimeout(() => {
          setCurrentStep(prev => prev + 1);
          setShowStep(true);
        }, transitionDuration);
      } else {
        setInternalComplete(true);
        if (onComplete) {
          onComplete();
        }
        clearInterval(interval);
      }
    }, stepDuration);

    return () => clearInterval(interval);
  }, [currentStep, activeSteps.length, internalComplete, stepDuration, transitionDuration, onComplete, steps.length, activeSteps, defaultSteps]);

  const getStepIcon = (type: AgentStep['type']) => {
    switch (type) {
      case 'routing':
        return <ArrowRight className="w-4 h-4" />;
      case 'tool':
        return <Zap className="w-4 h-4" />;
      case 'completion':
        return <CheckCircle className="w-4 h-4" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
  };

  const resetDemo = () => {
    setCurrentStep(0);
    setInternalComplete(false);
    setShowStep(true);
  };

  const completeInstantly = () => {
    setCurrentStep(activeSteps.length - 1);
    setInternalComplete(true);
  };

  if (internalComplete) {
    return (
      <div className={`max-w-md mx-auto ${className}`}>
        <div className="bg-flowstate-bg border border-gray-200 rounded-xl shadow-header overflow-hidden">
          <div className="px-6 py-4 bg-flowstate-header">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-full bg-flowstate-accent">
                <CheckCircle className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-flowstate-dark">Task Completed</h3>
                <p className="text-sm text-gray-600">Ready to display results</p>
              </div>
            </div>
          </div>
          <div className="px-6 py-4">
            <button 
              onClick={onComplete}
              className="w-full px-4 py-2 bg-flowstate-accent hover:bg-flowstate-accent text-white text-sm font-medium rounded-lg transition-colors"
            >
              View Results
            </button>
          </div>
        </div>
        
        {showDemo && (
          <div className="mt-4 p-3 bg-gray-100 rounded-lg">
            <button
              onClick={resetDemo}
              className="px-3 py-1 bg-white border border-gray-300 text-sm rounded hover:bg-gray-50"
            >
              Restart Demo
            </button>
          </div>
        )}
      </div>
    );
  }

  if (activeSteps.length === 0) {
    return (
      <div className={`max-w-md mx-auto ${className}`}>
        <div className="bg-flowstate-bg border border-gray-200 rounded-xl shadow-header p-6 text-center">
          <div className="p-2 rounded-full bg-flowstate-accent mx-auto mb-3 w-fit">
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
          </div>
          <p className="text-gray-500">Waiting for agent steps...</p>
        </div>
      </div>
    );
  }

  const currentStepData = activeSteps[currentStep];

  // Safety check - if currentStepData is undefined, don't render
  if (!currentStepData) {
    console.log('currentStepData is undefined, currentStep:', currentStep, 'activeSteps.length:', activeSteps.length);
    return (
      <div className={`max-w-md mx-auto ${className}`}>
        <div className="bg-flowstate-bg border border-gray-200 rounded-xl shadow-header p-6 text-center">
          <p className="text-gray-500">Loading steps...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`max-w-md mx-auto ${className}`}>
      <div className="bg-flowstate-bg border border-gray-200 rounded-xl shadow-header overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 bg-flowstate-header">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-full bg-flowstate-accent">
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            </div>
            <div>
              <h3 className="font-semibold text-flowstate-dark">Processing Request</h3>
              <p className="text-sm text-gray-600">Student Productivity Agent</p>
            </div>
          </div>
        </div>

        {/* Current Step */}
        <div className="px-6 py-6">
          <div 
            className={`transition-all duration-${transitionDuration} ${
              showStep ? 'opacity-100 transform translate-y-0' : 'opacity-0 transform translate-y-2'
            }`}
          >
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0">
                <div className="w-10 h-10 rounded-full bg-flowstate-accent bg-opacity-10 flex items-center justify-center">
                  <div className="text-flowstate-accent">
                    {getStepIcon(currentStepData.type)}
                  </div>
                </div>
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="mb-2">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-flowstate-accent bg-opacity-10 text-flowstate-dark">
                    {currentStepData.agent}
                  </span>
                </div>
                
                <p className="text-flowstate-dark font-medium leading-relaxed">
                  {currentStepData.message}
                </p>
                
                {currentStepData.tool && (
                  <div className="mt-3 inline-flex items-center gap-2 px-3 py-2 bg-flowstate-dark text-flowstate-bg text-sm font-mono rounded-lg">
                    <Zap className="w-3 h-3" />
                    {currentStepData.tool}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Simple loading indicator */}
          <div className="mt-6 flex justify-center">
            <div className="flex gap-1">
              <div className="w-2 h-2 bg-flowstate-accent rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <div className="w-2 h-2 bg-flowstate-accent rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <div className="w-2 h-2 bg-flowstate-accent rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentLoadingCard;

// Usage example:
/*
import AgentLoadingCard, { AgentStep } from './AgentLoadingCard';

// Basic usage with streaming
const [steps, setSteps] = useState<AgentStep[]>([]);
const [isComplete, setIsComplete] = useState(false);

// Add steps as they stream in
const addStep = (step: AgentStep) => {
  setSteps(prev => [...prev, step]);
};

// Mark as complete
const handleComplete = () => {
  setIsComplete(true);
};

<AgentLoadingCard 
  steps={steps}
  isComplete={isComplete}
  onComplete={() => console.log('Task completed!')}
  stepDuration={3000} // 3 seconds per step
  className="my-4"
/>
*/
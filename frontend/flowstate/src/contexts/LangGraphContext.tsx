"use client"
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useAuth } from './AuthContext';
import config from '@/lib/config';
import { AgentStep } from '@/components/AgentLoadingCard';

// Message type definition for LangGraph messages
type LangGraphMessage = {
  type: 'user' | 'assistant' | 'tool' | 'system';
  content: string | object;
  id?: string;
};

interface LangGraphContextType {
  isConnected: boolean;
  loading: boolean;
  error: string | null;
  createThread: () => Promise<string>;
  sendMessage: (threadId: string, content: string) => Promise<string>;
  sendMessageWithStreaming: (threadId: string, content: string, onStep: (step: AgentStep) => void, onComplete: (response: string) => void) => Promise<void>;
  getThreadHistory: (threadId: string) => Promise<LangGraphMessage[]>;
  resetThread: () => Promise<string>;
}

const LangGraphContext = createContext<LangGraphContextType | undefined>(undefined);

export const useLangGraph = () => {
  const context = useContext(LangGraphContext);
  if (context === undefined) {
    throw new Error('useLangGraph must be used within a LangGraphProvider');
  }
  return context;
};

interface LangGraphProviderProps {
  children: ReactNode;
}

export const LangGraphProvider: React.FC<LangGraphProviderProps> = ({ children }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuth();

  useEffect(() => {
    const checkConnection = async () => {
      try {
        // Test connection to your deployed backend
        const response = await fetch(`${config.apiUrl}/`);
        setIsConnected(response.ok);
        setError(null);
      } catch (error) {
        console.error('LangGraph connection failed:', error);
        setIsConnected(false);
        setError('Connection failed');
      } finally {
        setLoading(false);
      }
    };

    checkConnection();
  }, []);

  const createThread = async (): Promise<string> => {
    try {
      // Generate a new session ID - your backend will create the thread when first message is sent
      const newSessionId = `thread_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      return newSessionId;
    } catch (error) {
      console.error('Error creating thread:', error);
      throw error;
    }
  };

  const sendMessage = async (threadId: string, content: string): Promise<string> => {
    try {
      const token = localStorage.getItem('accessToken');
      if (!token) {
        throw new Error('No authentication token found');
      }

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: content,
          session_id: threadId,
          user_id: user?.id || "default_user",
          todo_category: "default"
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to send message');
      }

      const data = await response.json();
      return data.response;
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  };

  const sendMessageWithStreaming = async (
    threadId: string, 
    content: string, 
    onStep: (step: AgentStep) => void, 
    onComplete: (response: string) => void
  ): Promise<void> => {
    try {
      const token = localStorage.getItem('accessToken');
      if (!token) {
        throw new Error('No authentication token found');
      }

      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: content,
          session_id: threadId,
          user_id: user?.id || "default_user",
          todo_category: "default"
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to start streaming');
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No reader available');
      }

      const decoder = new TextDecoder();

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6);
              
              if (data === '[DONE]') {
                // Streaming complete - just call onComplete without final response
                onComplete('');
                return;
              }

              try {
                const stepData = JSON.parse(data);
                
                if (stepData.type === 'error') {
                  throw new Error(stepData.content);
                }

                // Check if this is an agent step for the loading card
                if (stepData.type && ['routing', 'action', 'tool', 'completion'].includes(stepData.type)) {
                  console.log('Received agent step:', stepData); // Debug log
                  onStep({
                    type: stepData.type,
                    agent: stepData.agent,
                    message: stepData.message,
                    tool: stepData.tool,
                    timestamp: stepData.timestamp
                  });
                }
                
              } catch (parseError) {
                console.warn('Failed to parse streaming data:', data);
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }

    } catch (error) {
      console.error('Error in streaming message:', error);
      throw error;
    }
  };

  const getThreadHistory = async (threadId: string): Promise<LangGraphMessage[]> => {
    // For now, return empty array since we're using stateless chat
    // In the future, you could implement message history retrieval from your backend
    return [];
  };

  const resetThread = async (): Promise<string> => {
    return await createThread();
  };

  const value = {
    isConnected,
    loading,
    error,
    createThread,
    sendMessage,
    sendMessageWithStreaming,
    getThreadHistory,
    resetThread,
  };

  return <LangGraphContext.Provider value={value}>{children}</LangGraphContext.Provider>;
};

export default LangGraphProvider;
"use client"
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useAuth } from './AuthContext';
import config from '@/lib/config';
import { error } from 'console';

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
  getThreadHistory: (threadId: string) => Promise<LangGraphMessage[]>;
  resetThread: () => Promise<string>;
  streamResponse?: (threadId: string, handleChunk: (chunk: any) => void) => Promise<void>;
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
  const { user } = useAuth();

  useEffect(() => {
    const checkConnection = async () => {
      try {
        // Test connection to your deployed backend
        const response = await fetch(`${config.apiUrl}/`);
        setIsConnected(response.ok);
      } catch (error) {
        console.error('LangGraph connection failed:', error);
        setIsConnected(false);
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

  const getThreadHistory = async (threadId: string): Promise<LangGraphMessage[]> => {
    // For now, return empty array since we're using stateless chat
    // In the future, you could implement message history retrieval from your backend
    return [];
  };

  const resetThread = async (): Promise<string> => {
    return await createThread();
  };

  // Optional streaming support for future enhancement
  const streamResponse = async (threadId: string, handleChunk: (chunk: any) => void): Promise<void> => {
    // For now, we'll just send the message normally and call handleChunk once
    // In the future, you could implement Server-Sent Events for real streaming
    try {
      const response = await sendMessage(threadId, "");
      handleChunk({ type: 'text', content: response });
    } catch (error) {
      console.error('Error in stream response:', error);
      throw error;
    }
  };

  const value = {
    isConnected,
    loading,
    createThread,
    sendMessage,
    getThreadHistory,
    error: null,
    resetThread,
    streamResponse,
  };

  return <LangGraphContext.Provider value={value}>{children}</LangGraphContext.Provider>;
};

export default LangGraphProvider;
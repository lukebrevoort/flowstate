"use client"
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Client } from '@langchain/langgraph-sdk';
import type { ClientConfig } from '@langchain/langgraph-sdk/client';
import { useAuth } from './AuthContext';
import config from '@/lib/config';

// Configure client to use your deployed backend
const clientConfig: ClientConfig = {
  apiUrl: config.langGraphUrl, // This will now use your Render deployment
};

const client = new Client(clientConfig);

// Message type definition for LangGraph messages
type LangGraphMessage = {
  type: 'user' | 'assistant' | 'tool' | 'system';
  content: string | object;
  id?: string;
};

interface LangGraphContextType {
  isConnected: boolean;
  loading: boolean;
  createThread: () => Promise<string>;
  sendMessage: (threadId: string, content: string) => Promise<void>;
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
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`${config.apiUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: "Start new conversation",
          user_id: user?.id || "default_user"
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to create thread');
      }
      
      const data = await response.json();
      return data.session_id;
    } catch (error) {
      console.error('Error creating thread:', error);
      throw error;
    }
  };

  const sendMessage = async (threadId: string, content: string): Promise<void> => {
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`${config.apiUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: content,
          session_id: threadId,
          user_id: user?.id || "default_user"
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to send message');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  };

  const getThreadHistory = async (threadId: string): Promise<LangGraphMessage[]> => {
    // For now, return empty array since we're using stateless chat
    // In the future, you could implement message history retrieval
    return [];
  };

  const resetThread = async (): Promise<string> => {
    return await createThread();
  };

  const value = {
    isConnected,
    loading,
    createThread,
    sendMessage,
    getThreadHistory,
    resetThread,
  };

  return <LangGraphContext.Provider value={value}>{children}</LangGraphContext.Provider>;
};

export default LangGraphProvider;
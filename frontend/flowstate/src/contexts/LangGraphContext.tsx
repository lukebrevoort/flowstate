"use client"
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Client } from '@langchain/langgraph-sdk';
import type { ClientConfig } from '@langchain/langgraph-sdk/client';
import { useAuth } from './AuthContext';
import config from '@/lib/config';

// Configure client with appropriate base URL for your Docker setup
// Default is localhost:8000 when running locally
const clientConfig: ClientConfig = {
  apiKey: process.env.NEXT_PUBLIC_LANGGRAPH_API_KEY, // Use if your deployment requires auth
  apiUrl: process.env.NEXT_PUBLIC_LANGGRAPH_API_URL || 'http://localhost:9876', // Use your LangGraph API URL
};

const client = new Client(clientConfig);

// Message type definition for LangGraph messages
type LangGraphMessage = {
  type: 'user' | 'assistant' | 'tool' | 'system'; // Corrected role types to match SDK
  content: string | object;
  id?: string;
};

// Context interface definition
interface LangGraphContextType {
  isConnected: boolean;
  loading: boolean;
  error: string | null;
  assistantId: string | null;
  availableAssistants: Array<{ id: string; name: string; }>; // Corrected to use id instead of assistant_id
  createThread: () => Promise<string>;
  sendMessage: (threadId: string, content: string) => Promise<void>;
  streamResponse: (threadId: string, onChunk: (chunk: any) => void) => Promise<void>;
  getThreadHistory: (threadId: string) => Promise<LangGraphMessage[]>;
  resetThread: () => Promise<string>;
}

// Default context values
const defaultContextValues: LangGraphContextType = {
  isConnected: false,
  loading: true,
  error: null,
  assistantId: null,
  availableAssistants: [],
  createThread: async () => { throw new Error('Context not initialized'); },
  sendMessage: async () => { throw new Error('Context not initialized'); },
  streamResponse: async () => { throw new Error('Context not initialized'); },
  getThreadHistory: async () => [],
  resetThread: async () => { throw new Error('Context not initialized'); },
};

// Create context
const LangGraphContext = createContext<LangGraphContextType>(defaultContextValues);

// Provider component
export function LangGraphProvider({ children }: { children: ReactNode }) {
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [assistantId, setAssistantId] = useState<string | null>(null);
  const [availableAssistants, setAvailableAssistants] = useState<Array<{ id: string; name: string; }>>([]);
  const { user } = useAuth();

  // Initialize connection to LangGraph
  useEffect(() => {
    const initLangGraph = async () => {
      if (!user) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        // Fetch available assistants/graphs
        const assistants = await client.assistants.search({ metadata: null, offset: 0, limit: 10 });
        
        if (assistants && assistants.length > 0) {
          setAvailableAssistants(assistants.map(assistant => ({
            id: assistant.assistant_id,
            name: assistant.name || assistant.assistant_id
          })));
          // Use the first assistant by default
          setAssistantId(assistants[0].assistant_id);
          setIsConnected(true);
          setError(null);
        } else {
          throw new Error('No assistants found in LangGraph deployment');
        }
      } catch (err) {
        console.error('Failed to initialize LangGraph connection:', err);
        setError(err instanceof Error ? err.message : 'Failed to connect to LangGraph');
        setIsConnected(false);
      } finally {
        setLoading(false);
      }
    };

    initLangGraph();
  }, [user]);

  // Create a new thread
  const createThread = async (): Promise<string> => {
    try {
      const thread = await client.threads.create();
      return thread.thread_id;
    } catch (err) {
      console.error('Failed to create thread:', err);
      throw new Error(err instanceof Error ? err.message : 'Failed to create thread');
    }
  };

  // Send a message to a thread
  const sendMessage = async (threadId: string, content: string): Promise<void> => {
    if (!assistantId) throw new Error('No assistant is selected');
  
    try {
      // Create a run with the user message as input
      await client.runs.create(threadId, assistantId, {
        input: {
          messages: [{ role: 'user', content }],
        },
      });
    } catch (err) {
      console.error('Failed to send message:', err);
      throw new Error(err instanceof Error ? err.message : 'Failed to send message');
    }
  };
  
  // Stream the response from the assistant
  const streamResponse = async (
    threadId: string,
    onChunk: (chunk: any) => void
  ): Promise<void> => {
    if (!assistantId) throw new Error('No assistant is selected');
  
    try {
      const stream = client.runs.stream(threadId, assistantId, {
        // Optionally pass input if needed to start a run with streaming
      });
  
      for await (const chunk of stream) {
        onChunk(chunk);
      }
    } catch (err) {
      console.error('Failed to stream response:', err);
      throw new Error(err instanceof Error ? err.message : 'Failed to stream response');
    }
  };
  

// Get thread history
const getThreadHistory = async (threadId: string): Promise<LangGraphMessage[]> => {
    try {
      const history = await client.threads.getHistory(threadId);
  
      return history.map((message: any) => ({
        type: message.role === 'user' ? 'user'
             : message.role === 'assistant' ? 'assistant'
             : message.role,
        content: Array.isArray(message.content)
          ? message.content.map((c: any) => c.text || '').join(' ')
          : message.content,
        id: message.message_id || message.id || undefined,
      }));
    } catch (err) {
      console.error('Failed to get thread history:', err);
      return [];
    }
  };

  // Reset thread (creates a new thread)
  const resetThread = async (): Promise<string> => {
    try {
      const newThreadId = await createThread();
      // Clear local storage if you're storing the thread ID there
      localStorage.setItem('flowstate_thread_id', newThreadId);
      return newThreadId;
    } catch (err) {
      console.error('Failed to reset thread:', err);
      throw new Error(err instanceof Error ? err.message : 'Failed to reset thread');
    }
  };

  // Context value
  const contextValue: LangGraphContextType = {
    isConnected,
    loading,
    error,
    assistantId,
    availableAssistants,
    createThread,
    sendMessage,
    streamResponse,
    getThreadHistory,
    resetThread
  };

  return (
    <LangGraphContext.Provider value={contextValue}>
      {children}
    </LangGraphContext.Provider>
  );
}

// Hook to use the LangGraph context
export const useLangGraph = () => useContext(LangGraphContext);


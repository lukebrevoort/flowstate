/**
 * Custom API client for communicating with the FlowState backend
 */

// API base URL from environment variables
const API_BASE_URL = process.env.NEXT_PUBLIC_LANGGRAPH_API_URL || 'http://localhost:9876';

/**
 * Custom API client functions to communicate with backend
 */
export const api = {
  /**
   * Create a new conversation thread
   */
  createThread: async (): Promise<{ thread_id: string }> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/threads`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to create thread: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error creating thread:', error);
      throw error;
    }
  },

  /**
   * Send a message to a conversation thread
   */
  sendMessage: async (
    threadId: string, 
    content: string
  ): Promise<{ message_id: string }> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/threads/${threadId}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content,
          role: 'user',
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to send message: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  },

  /**
   * Get thread history
   */
  getThreadHistory: async (threadId: string): Promise<any[]> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/threads/${threadId}/messages`);
      
      if (!response.ok) {
        throw new Error(`Failed to get thread history: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting thread history:', error);
      return [];
    }
  },

  /**
   * Stream response from the AI
   * Returns an async generator that yields response chunks
   */
  streamResponse: async function* (
    threadId: string,
    messageId: string
  ): AsyncGenerator<any, void, unknown> {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/chat/threads/${threadId}/messages/${messageId}/stream`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to stream response: ${response.status} ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('Failed to get stream reader');
      }

      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        // Parse SSE data
        const lines = chunk.split('\n').filter(line => line.trim() !== '');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const jsonData = JSON.parse(line.slice(6));
              yield jsonData;
            } catch (e) {
              console.warn('Error parsing SSE data:', e);
              yield { type: 'text', content: line.slice(6) };
            }
          }
        }
      }
    } catch (error) {
      console.error('Error streaming response:', error);
      throw error;
    }
  },
};
"use client";

import Image from "next/image";
import { motion } from "framer-motion";
import { useState, FormEvent, useEffect, useRef } from "react";
import { useAuth } from '@/contexts/AuthContext';
import { useLangGraph } from '@/contexts/LangGraphContext';
import ProtectedRoute from '@/components/ProtectedRoute';

// Message type definition
type Message = {
  role: 'user' | 'assistant' | 'system';
  content: string;
  id?: string;
};

// Function to convert LangGraph messages to chat format
const convertLangGraphMessages = (messages: any[]) => {
  return messages.map(msg => ({
    role: msg.type === 'user' ? 'user' : 
          msg.type === 'assistant' ? 'assistant' : 
          msg.type === 'system' ? 'system' : 'assistant',
    content: typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content),
  })) as Message[];
};

function Chat() {
  const [message, setMessage] = useState("");
  const [chatHistory, setChatHistory] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [threadId, setThreadId] = useState<string | null>(null);
  const { user } = useAuth();
  const { 
    createThread, 
    sendMessage, 
    streamResponse, 
    getThreadHistory, 
    resetThread,
    loading: langGraphLoading,
    error: langGraphError,
    isConnected 
  } = useLangGraph();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Effect to scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [chatHistory]);

  // Initialize thread when component mounts
  useEffect(() => {
    const initializeThread = async () => {
      try {
        // Check localStorage for existing threadId
        const savedThreadId = localStorage.getItem('flowstate_thread_id');
        
        if (savedThreadId) {
          setThreadId(savedThreadId);
          
          // Load previous messages if there's an existing threadId
          const messages = await getThreadHistory(savedThreadId);
          
          // Convert LangGraph message format to our app's format
          setChatHistory(convertLangGraphMessages(messages));
        } else {
          // Create new thread if no existing one
          const newThreadId = await createThread();
          setThreadId(newThreadId);
          localStorage.setItem('flowstate_thread_id', newThreadId);
        }
      } catch (error) {
        console.error('Failed to initialize thread:', error);
        setChatHistory([{
          role: 'system',
          content: `Error initializing conversation: ${error instanceof Error ? error.message : 'Connection failed'}`
        }]);
      }
    };

    if (!langGraphLoading && user && isConnected) {
      initializeThread();
    }
  }, [langGraphLoading, user, isConnected, createThread, getThreadHistory]);

  const handleNewConversation = async () => {
    try {
      setIsLoading(true);
      setChatHistory([]);
      const newThreadId = await resetThread();
      setThreadId(newThreadId);
      setIsLoading(false);
    } catch (error) {
      console.error('Failed to create new conversation:', error);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!message.trim() || isLoading || !threadId || !isConnected) return;
    
    const userMessage = message;
    setMessage(""); // Clear input immediately
    setIsLoading(true);
    
    // Add user message to chat
    setChatHistory(prev => [...prev, { role: 'user', content: userMessage }]);
    
    // Define assistantMessageId outside try block to make it accessible in catch block
    const assistantMessageId = Date.now().toString();
    
    try {
      // Add a temporary assistant message that will be updated as we receive chunks
      setChatHistory(prev => [...prev, { 
        role: 'assistant', 
        content: '',
        id: assistantMessageId
      }]);
      
      // Send message to LangGraph backend using the correct format
      await sendMessage(threadId, userMessage);
      
      // Function to handle streaming response updates
      const handleChunk = (chunk: any) => {
        if (chunk.type === 'text') {
          setChatHistory(prev => 
            prev.map(msg => 
              msg.id === assistantMessageId 
                ? { ...msg, content: msg.content + (typeof chunk.content === 'string' ? chunk.content : JSON.stringify(chunk.content)) }
                : msg
            )
          );
        } else if (chunk.type === 'tool_use') {
          // For now, we'll just log tool use events, but in the future
          // we could add special UI components for different tool responses
          console.log('Tool use:', chunk);
        }
      };
      
      // Start streaming the response from the LangGraph backend
      await streamResponse(threadId, handleChunk);
      
    } catch (error) {
      console.error('Chat error:', error);
      setChatHistory(prev => [
        ...prev.filter(msg => msg.id !== assistantMessageId),
        { 
          role: 'system', 
          content: `Error: ${error instanceof Error ? error.message : 'Failed to process your request'}`
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Render chat messages
  const renderChatHistory = () => {
    return chatHistory.map((msg, index) => (
      <div 
        key={index} 
        className={`my-4 p-4 rounded-[35px] ${
          msg.role === 'user' 
            ? 'bg-flowstate-accent text-white ml-auto' 
            : msg.role === 'system' 
              ? 'bg-red-100 text-red-800 mx-auto' 
              : 'bg-flowstate-header'
        } max-w-[80%] ${
          msg.role === 'user' 
            ? 'ml-auto' 
            : msg.role === 'system' 
              ? 'mx-auto' 
              : 'mr-auto'
        }`}
      >
        {msg.content || (msg.role === 'assistant' && isLoading ? '...' : '')}
      </div>
    ));
  };

  // Show connection status or errors
  const renderConnectionStatus = () => {
    if (langGraphLoading) {
      return (
        <div className="absolute top-4 right-4 bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full text-sm">
          Connecting...
        </div>
      );
    }
    
    if (langGraphError) {
      return (
        <div className="absolute top-4 right-4 bg-red-100 text-red-800 px-3 py-1 rounded-full text-sm">
          Connection Error: {langGraphError}
        </div>
      );
    }
    
    if (isConnected) {
      return (
        <div className="absolute top-4 right-4 bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm flex items-center">
          <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
          Connected
        </div>
      );
    }
    
    return (
      <div className="absolute top-4 right-4 bg-gray-100 text-gray-800 px-3 py-1 rounded-full text-sm">
        Disconnected
      </div>
    );
  };

  return (
    <div className="min-h-screen w-full bg-flowstate-bg flex flex-col">
      {/* Header */}
      <header className="w-full h-[89px] bg-flowstate-header shadow-header flex items-center justify-between px-[100px] max-lg:px-10 max-sm:px-5 relative">
        <div className="flex items-center gap-[10px]">
          <a href="/Chat" aria-label="Go to Chat">
            <Image
              src="/flowstate-main-logo.png"
              alt="FlowState Logo"
              width={78}
              height={78}
              className="w-[50px] h-[50px] max-sm:w-[50px] max-sm:h-[50px]"
              priority
            />
          </a>
          <motion.div
            initial={{ opacity: 0, x: -40 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 1.5 }}
          >
            <h1 className="font-alegreya text-[32px] text-black max-lg:text-[30px] max-sm:text-[28px]">
              FlowState
            </h1>
          </motion.div>
        </div>

        {renderConnectionStatus()}

        <div className="flex items-center gap-15">
          {/* New Chat Button */}
          <button
            onClick={handleNewConversation}
            disabled={isLoading || !isConnected}
            className={`mr-4 bg-flowstate-accent text-white px-3 py-1 rounded-full text-sm
              ${isLoading || !isConnected ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:opacity-80'}`}
          >
            New Chat
          </button>

          {/* Mind Map Icon */}
          <a href="/MindMap" aria-label="Go to Mind Map">
            <Image
              src="/Mind Map 1.png"
              alt="Mind Map Icon"
              width={40}
              height={40}
              className="max-sm:hidden cursor-pointer hover:opacity-80 transition-opacity"
            />
          </a>

          {/* Message Circle Icon */}
          <a href="/Chat" aria-label="Go to Chat">
            <svg
              width="40"
              height="40"
              viewBox="0 0 48 48"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              className="max-sm:hidden cursor-pointer hover:opacity-80 transition-opacity"
            >
              <rect width="40" height="40" fill="#F6EEE3" />
              <path
                d="M42 23C42.0069 25.6397 41.3901 28.2438 40.2 30.6C38.7889 33.4235 36.6195 35.7983 33.9349 37.4586C31.2503 39.1188 28.1565 39.9988 25 40C22.3603 40.0069 19.7562 39.3901 17.4 38.2L6 42L9.8 30.6C8.60986 28.2438 7.99312 25.6397 8 23C8.00122 19.8435 8.88122 16.7497 10.5414 14.0651C12.2017 11.3805 14.5765 9.21113 17.4 7.8C19.7562 6.60986 22.3603 5.99311 25 6H26C30.1687 6.22998 34.1061 7.98952 37.0583 10.9417C40.0105 13.8939 41.77 17.8313 42 22V23Z"
                stroke="#1E1E1E"
                strokeWidth="4"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </a>

          {/* User Icon */}
          <a href="/User" aria-label="Go to User Profile">
            <svg
              width="40"
              height="40"
              viewBox="0 0 54 54"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              className="cursor-pointer hover:opacity-80 transition-opacity"
            >
              <circle cx="27" cy="27" r="27" fill="#331C16" />
              <path
                d="M43 42V38C43 35.8783 42.1571 33.8434 40.6569 32.3431C39.1566 30.8429 37.1217 30 35 30H19C16.8783 30 14.8434 30.8429 13.3431 32.3431C11.8429 33.8434 11 35.8783 11 38V42M35 14C35 18.4183 31.4183 22 27 22C22.5817 22 19 18.4183 19 14C19 9.58172 22.5817 6 27 6C31.4183 6 35 9.58172 35 14Z"
                stroke="#F3F3F3"
                strokeWidth="4"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </a>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col items-center justify-between p-6">
        {/* Chat messages */}
        <div className="w-full max-w-[1030px] flex-1 overflow-y-auto mb-6">
          {chatHistory.length === 0 ? (
            <div className="flex justify-center items-center h-full">
              <motion.h2
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8 }}
                className="text-[92px] font-alegreya text-center text-black max-w-[825px] leading-[1.2] mx-auto px-4 max-lg:text-[72px] max-sm:text-[48px] max-sm:px-5"
              >
                Welcome Back{user ? `,` : ''}
                <span className="block mt-2">{user?.name ? user.name : ''}</span>
                <span className="block mt-2">How can I assist you?</span>
              </motion.h2>
            </div>
          ) : (
            <>
              {renderChatHistory()}
              <div ref={messagesEndRef} />
            </>
          )}
          
          {isLoading && !chatHistory.some(msg => msg.role === 'assistant' && msg.id) && (
            <div className="flex justify-center items-center my-4">
              <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-flowstate-accent"></div>
            </div>
          )}
        </div>

        {/* Chat form */}
        <motion.form
          onSubmit={handleSubmit}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="w-full max-w-[1030px] h-[236px] bg-flowstate-header rounded-[35px] p-[25px] relative"
        >
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder={isConnected ? "Ask Anything..." : "Connecting to backend..."}
            className="w-full h-[120px] bg-transparent text-[30px] font-alegreya text-[#665F5D] resize-none focus:outline-none"
            aria-label="Chat message"
            disabled={isLoading || langGraphLoading || !threadId || !isConnected}
          />

          {/* Submit button */}
          <button
            type="submit"
            disabled={isLoading || !message.trim() || langGraphLoading || !threadId || !isConnected}
            className={`absolute right-[25px] bottom-[25px] bg-flowstate-accent text-white p-3 rounded-full
              ${isLoading || !message.trim() || langGraphLoading || !threadId || !isConnected ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            aria-label="Send message"
          >
            {/* Send icon */}
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M22 2L11 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </motion.form>
      </main>
    </div>
  );
}

// Wrap the Chat component with ProtectedRoute
export default function ProtectedChat() {
  return (
    <ProtectedRoute>
      <Chat />
    </ProtectedRoute>
  );
}

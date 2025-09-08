"use client";

import { motion } from "framer-motion";
import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from 'next/navigation';
import Image from "next/image";

export default function OAuth() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  const [loading, setLoading] = useState({
    notion: false,
    google: false,
  });
  
  const [connectionStatus, setConnectionStatus] = useState({
    notion: false,
    google: false,
  });
  
  const [messages, setMessages] = useState({
    success: '',
    error: '',
  });

  // Check for URL parameters on component mount
  useEffect(() => {
    const success = searchParams.get('success');
    const error = searchParams.get('error');
    const workspace = searchParams.get('workspace');
    
    if (success) {
      setMessages(prev => ({ 
        ...prev, 
        success: workspace ? `${success} (${workspace})` : success 
      }));
      // Refresh connection status
      checkNotionStatus();
    }
    
    if (error) {
      setMessages(prev => ({ ...prev, error }));
    }
    
    // Clear messages after 5 seconds
    if (success || error) {
      setTimeout(() => {
        setMessages({ success: '', error: '' });
      }, 5000);
    }
  }, [searchParams]);

  // Check connection status on mount
  useEffect(() => {
    checkNotionStatus();
  }, []);

  const checkNotionStatus = async () => {
    try {
      // Get auth token from localStorage or your auth context
      const token = localStorage.getItem('access_token');
      if (!token) return;

      const response = await fetch('/api/oauth/notion/status', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setConnectionStatus(prev => ({ ...prev, notion: data.connected }));
      }
    } catch (error) {
      console.error('Error checking Notion status:', error);
    }
  };

  const handleNotionAuth = async () => {
    setLoading(prev => ({ ...prev, notion: true }));
    try {
      // Get auth token from localStorage or your auth context
      const token = localStorage.getItem('access_token');
      if (!token) {
        throw new Error('Please log in first');
      }

      const response = await fetch('/api/oauth/notion/authorize', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to initialize Notion OAuth');
      }

      const data = await response.json();
      
      // Redirect to Notion's OAuth page
      window.location.href = data.auth_url;
      
    } catch (error) {
      console.error("Notion auth error:", error);
      setMessages(prev => ({ 
        ...prev, 
        error: error instanceof Error ? error.message : 'Failed to connect to Notion'
      }));
    } finally {
      setLoading(prev => ({ ...prev, notion: false }));
    }
  };

  const handleGoogleAuth = async () => {
    setLoading(prev => ({ ...prev, google: true }));
    try {
      // TODO: Implement actual Google Calendar OAuth flow
      // For now, just simulate a delay
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // This would typically redirect to Google's OAuth URL
      console.log("Google Calendar OAuth would be initiated here");
      
    } catch (error) {
      console.error("Google auth error:", error);
    } finally {
      setLoading(prev => ({ ...prev, google: false }));
    }
  };

  const handleSkip = () => {
    // Redirect to chat page without OAuth setup
    router.push('/Chat');
  };

  const handleContinue = () => {
    // Redirect to chat page after OAuth setup
    router.push('/Chat');
  };

  return (
    <div className="relative min-h-screen flex justify-center items-center p-5 overflow-hidden bg-flowstate-bg">
      {/* Orange blur effect */}
      <div className="absolute top-[-22px] left-[229px] w-[460px] h-[494px]">
        <svg
          width="728"
          height="606"
          viewBox="0 0 728 606"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <g filter="url(#filter0_f_48_36)">
            <ellipse cx="364" cy="225" rx="230" ry="247" fill="#D06224" />
          </g>
          <defs>
            <filter
              id="filter0_f_48_36"
              x="0"
              y="-156"
              width="728"
              height="762"
              filterUnits="userSpaceOnUse"
              colorInterpolationFilters="sRGB"
            >
              <feFlood floodOpacity="0" result="BackgroundImageFix" />
              <feBlend
                mode="normal"
                in="SourceGraphic"
                in2="BackgroundImageFix"
                result="shape"
              />
              <feGaussianBlur
                stdDeviation="67"
                result="effect1_foregroundBlur_48_36"
              />
            </filter>
          </defs>
        </svg>
      </div>

      {/* Green blur effect */}
      <div className="absolute bottom-[-100px] right-0 w-[425px] h-[425px]">
        <svg
          width="833"
          height="567"
          viewBox="0 0 833 567"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <g filter="url(#filter0_f_48_26)">
            <circle cx="416.5" cy="416.5" r="212.5" fill="#9EAB57" />
          </g>
          <defs>
            <filter
              id="filter0_f_48_26"
              x="0"
              y="0"
              width="833"
              height="833"
              filterUnits="userSpaceOnUse"
              colorInterpolationFilters="sRGB"
            >
              <feFlood floodOpacity="0" result="BackgroundImageFix" />
              <feBlend
                mode="normal"
                in="SourceGraphic"
                in2="BackgroundImageFix"
                result="shape"
              />
              <feGaussianBlur
                stdDeviation="102"
                result="effect1_foregroundBlur_48_26"
              />
            </filter>
          </defs>
        </svg>
      </div>

      {/* Form Container */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="bg-flowstate-header rounded-[45px] p-10 w-full max-w-[610px] flex flex-col items-center relative z-10
          max-lg:p-[30px] max-sm:p-5 max-sm:rounded-[25px]"
      >
        <h1 className="font-alegreya text-[48px] text-black mb-5 text-center max-sm:text-[36px]">
          Connect Your Apps
        </h1>
        
        <p className="font-alegreya text-[24px] text-black mb-10 text-center max-w-[500px] max-sm:text-[20px]">
          To get the most out of Flowstate, connect your Notion and Google Calendar for seamless productivity tracking.
        </p>

        <div className="w-full max-w-[400px] space-y-5">
          {/* Success/Error Messages */}
          {messages.success && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-4 bg-green-100 border border-green-400 text-green-700 rounded-lg text-center"
            >
              {messages.success}
            </motion.div>
          )}
          
          {messages.error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg text-center"
            >
              {messages.error}
            </motion.div>
          )}

          {/* Notion Authentication Button */}
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleNotionAuth}
            disabled={loading.notion || loading.google || connectionStatus.notion}
            className={`w-full h-[60px] rounded-[35px] border-[3px] border-black flex items-center justify-center px-6
              font-alegreya text-[24px] cursor-pointer max-sm:h-[50px] max-sm:text-[20px] 
              transition-colors ${
                connectionStatus.notion 
                  ? 'bg-green-100 border-green-500 text-green-700' 
                  : loading.notion 
                    ? 'bg-gray-100 text-gray-500 opacity-70' 
                    : 'bg-white text-black hover:bg-gray-50'
              }`}
          >
            {connectionStatus.notion ? (
              <div className="flex items-center">
                <div className="w-8 h-8 mr-4 rounded overflow-hidden">
                  <Image src="/notion.png" alt="Notion" width={40} height={40} />
                </div>
                <span>✓ Notion Connected</span>
              </div>
            ) : loading.notion ? (
              <span>Connecting to Notion...</span>
            ) : (
              <div className="flex items-center">
                <div className="w-8 h-8 mr-4 rounded overflow-hidden">
                  <Image src="/notion.png" alt="Notion" width={40} height={40} />
                </div>
                <span>Connect Notion</span>
              </div>
            )}
          </motion.button>

          {/* Google Calendar Authentication Button */}
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleGoogleAuth}
            disabled={loading.notion || loading.google}
            className={`w-full h-[60px] rounded-[35px] bg-white border-[3px] border-black flex items-center justify-center px-6
              font-alegreya text-[24px] text-black cursor-pointer max-sm:h-[50px] max-sm:text-[20px]
              transition-colors hover:bg-gray-50 ${loading.google ? 'opacity-70' : ''}`}
          >
            {loading.google ? (
              <span>Connecting to Google Calendar...</span>
            ) : (
              <div className="flex items-center">
                <div className="w-8 h-8 mr-4 rounded overflow-hidden">
                  <svg viewBox="0 0 48 48" className="w-full h-full">
                    <path fill="#4285f4" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
                    <path fill="#34a853" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
                    <path fill="#fbbc05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
                    <path fill="#ea4335" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
                  </svg>
                </div>
                <span>Connect Google Calendar</span>
              </div>
            )}
          </motion.button>

          {/* Action Buttons */}
          <div className="pt-8 space-y-4">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleContinue}
              className="w-full h-[50px] rounded-[35px] bg-flowstate-dark text-white font-alegreya text-[24px] 
                cursor-pointer max-sm:h-[45px] max-sm:text-[20px]"
            >
              Continue to Flowstate
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleSkip}
              className="w-full h-[45px] rounded-[35px] bg-transparent border-[2px] border-gray-400 text-gray-600 
                font-alegreya text-[20px] cursor-pointer hover:border-gray-600 hover:text-gray-800 transition-colors
                max-sm:h-[40px] max-sm:text-[18px]"
            >
              Skip for now
            </motion.button>
          </div>

          {/* Help text */}
          <div className="pt-4 text-center">
            <p className="font-alegreya text-[16px] text-gray-600 max-sm:text-[14px]">
              You can always connect these apps later in your settings.
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}

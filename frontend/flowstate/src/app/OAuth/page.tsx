'use client';

import { motion } from 'framer-motion';
import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Image from 'next/image';

function OAuthContent() {
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
    const email = searchParams.get('email');

    if (success) {
      let successMessage = success;
      if (workspace) {
        successMessage = `${success} (${workspace})`;
      } else if (email) {
        successMessage = `${success} (${email})`;
      }

      setMessages(prev => ({
        ...prev,
        success: successMessage,
      }));

      // Refresh connection status
      checkNotionStatus();
      checkGoogleCalendarStatus();
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
    checkGoogleCalendarStatus();
  }, []);

  const checkNotionStatus = async () => {
    try {
      // Get auth token from localStorage or your auth context
      const token = localStorage.getItem('accessToken');
      if (!token) return;

      const response = await fetch('/api/oauth/notion/status', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setConnectionStatus(prev => ({ ...prev, notion: data.connected }));
      }
    } catch (error) {
      console.error('Error checking Notion status:', error);
    }
  };

  const checkGoogleCalendarStatus = async () => {
    try {
      // Get auth token from localStorage or your auth context
      const token = localStorage.getItem('accessToken');
      if (!token) return;

      const response = await fetch('/api/oauth/google-calendar/status', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setConnectionStatus(prev => ({ ...prev, google: data.connected }));
      }
    } catch (error) {
      console.error('Error checking Google Calendar status:', error);
    }
  };

  const handleNotionAuth = async () => {
    setLoading(prev => ({ ...prev, notion: true }));
    try {
      // Get auth token from localStorage or your auth context
      const token = localStorage.getItem('accessToken');
      if (!token) {
        throw new Error('Please log in first');
      }

      const response = await fetch('/api/oauth/notion/authorize', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to initialize Notion OAuth');
      }

      const data = await response.json();

      // Redirect to Notion's OAuth page
      window.location.href = data.auth_url;
    } catch (error) {
      console.error('Notion auth error:', error);
      setMessages(prev => ({
        ...prev,
        error:
          error instanceof Error
            ? error.message
            : 'Failed to connect to Notion',
      }));
    } finally {
      setLoading(prev => ({ ...prev, notion: false }));
    }
  };

  const handleGoogleAuth = async () => {
    setLoading(prev => ({ ...prev, google: true }));
    try {
      // Get auth token from localStorage or your auth context
      const token = localStorage.getItem('accessToken');
      if (!token) {
        throw new Error('Please log in first');
      }

      const response = await fetch('/api/oauth/google-calendar/authorize', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to initialize Google Calendar OAuth');
      }

      const data = await response.json();

      // Redirect to Google's OAuth page
      window.location.href = data.auth_url;
    } catch (error) {
      console.error('Google Calendar auth error:', error);
      setMessages(prev => ({
        ...prev,
        error:
          error instanceof Error
            ? error.message
            : 'Failed to connect to Google Calendar',
      }));
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
    <div className='relative min-h-screen flex justify-center items-center p-5 overflow-hidden bg-flowstate-bg'>
      {/* Orange blur effect */}
      <div className='absolute top-[-22px] left-[229px] w-[460px] h-[494px]'>
        <svg
          width='728'
          height='606'
          viewBox='0 0 728 606'
          fill='none'
          xmlns='http://www.w3.org/2000/svg'
        >
          <g filter='url(#filter0_f_48_36)'>
            <ellipse cx='364' cy='225' rx='230' ry='247' fill='#D06224' />
          </g>
          <defs>
            <filter
              id='filter0_f_48_36'
              x='0'
              y='-156'
              width='728'
              height='762'
              filterUnits='userSpaceOnUse'
              colorInterpolationFilters='sRGB'
            >
              <feFlood floodOpacity='0' result='BackgroundImageFix' />
              <feBlend
                mode='normal'
                in='SourceGraphic'
                in2='BackgroundImageFix'
                result='shape'
              />
              <feGaussianBlur
                stdDeviation='67'
                result='effect1_foregroundBlur_48_36'
              />
            </filter>
          </defs>
        </svg>
      </div>

      {/* Green blur effect */}
      <div className='absolute bottom-[-100px] right-0 w-[425px] h-[425px]'>
        <svg
          width='833'
          height='567'
          viewBox='0 0 833 567'
          fill='none'
          xmlns='http://www.w3.org/2000/svg'
        >
          <g filter='url(#filter0_f_48_26)'>
            <circle cx='416.5' cy='416.5' r='212.5' fill='#9EAB57' />
          </g>
          <defs>
            <filter
              id='filter0_f_48_26'
              x='0'
              y='0'
              width='833'
              height='833'
              filterUnits='userSpaceOnUse'
              colorInterpolationFilters='sRGB'
            >
              <feFlood floodOpacity='0' result='BackgroundImageFix' />
              <feBlend
                mode='normal'
                in='SourceGraphic'
                in2='BackgroundImageFix'
                result='shape'
              />
              <feGaussianBlur
                stdDeviation='102'
                result='effect1_foregroundBlur_48_26'
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
        className='bg-flowstate-header rounded-[45px] p-10 w-full max-w-[610px] flex flex-col items-center relative z-10
          max-lg:p-[30px] max-sm:p-5 max-sm:rounded-[25px]'
      >
        <h1 className='font-alegreya text-[48px] text-black mb-5 text-center max-sm:text-[36px]'>
          Connect Your Apps
        </h1>

        <p className='font-alegreya text-[24px] text-black mb-10 text-center max-w-[500px] max-sm:text-[20px]'>
          To get the most out of Flowstate, connect your Notion and Google
          Calendar for seamless productivity tracking.
        </p>

        <div className='w-full max-w-[400px] space-y-5'>
          {/* Success/Error Messages */}
          {messages.success && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className='p-4 bg-green-100 border border-green-400 text-green-700 rounded-lg text-center'
            >
              {messages.success}
            </motion.div>
          )}

          {messages.error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className='p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg text-center'
            >
              {messages.error}
            </motion.div>
          )}

          {/* Notion Authentication Button */}
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleNotionAuth}
            disabled={
              loading.notion || loading.google || connectionStatus.notion
            }
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
              <div className='flex items-center'>
                <div className='w-8 h-8 mr-4 rounded overflow-hidden'>
                  <Image
                    src='/notion.png'
                    alt='Notion'
                    width={40}
                    height={40}
                  />
                </div>
                <span>✓ Notion Connected</span>
              </div>
            ) : loading.notion ? (
              <span>Connecting to Notion...</span>
            ) : (
              <div className='flex items-center'>
                <div className='w-8 h-8 mr-4 rounded overflow-hidden'>
                  <Image
                    src='/notion.png'
                    alt='Notion'
                    width={40}
                    height={40}
                  />
                </div>
                <span>Connect Notion</span>
              </div>
            )}
          </motion.button>

          {/* Google Calendar Authentication Button */}
          {/* Google Calendar Authentication Button */}
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleGoogleAuth}
            disabled={
              loading.notion || loading.google || connectionStatus.google
            }
            className={`w-full h-[60px] rounded-[35px] border-[3px] border-black flex items-center justify-center px-6
              font-alegreya text-[24px] cursor-pointer max-sm:h-[50px] max-sm:text-[20px]
              transition-colors ${
                connectionStatus.google
                  ? 'bg-green-100 border-green-500 text-green-700'
                  : loading.google
                    ? 'bg-gray-100 text-gray-500 opacity-70'
                    : 'bg-white text-black hover:bg-gray-50'
              }`}
          >
            {connectionStatus.google ? (
              <div className='flex items-center'>
                <svg
                  className='w-6 h-6 mr-3'
                  fill='currentColor'
                  viewBox='0 0 20 20'
                >
                  <path
                    fillRule='evenodd'
                    d='M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z'
                    clipRule='evenodd'
                  />
                </svg>
                <span>Google Calendar Connected</span>
              </div>
            ) : loading.google ? (
              <span>Connecting to Google Calendar...</span>
            ) : (
              <div className='flex items-center'>
                <svg className='w-6 h-6 mr-3' viewBox='0 0 48 48' fill='none'>
                  <path
                    fill='#FFC107'
                    d='M43.611 20.083H42V20H24v8h11.303c-1.649 4.657-6.08 8-11.303 8-6.627 0-12-5.373-12-12s5.373-12 12-12c3.059 0 5.842 1.154 7.961 3.039l5.657-5.657C34.046 6.053 29.268 4 24 4 12.955 4 4 12.955 4 24s8.955 20 20 20 20-8.955 20-20c0-1.341-.138-2.65-.389-3.917z'
                  />
                  <path
                    fill='#FF3D00'
                    d='m6.306 14.691 6.571 4.819C14.655 15.108 18.961 12 24 12c3.059 0 5.842 1.154 7.961 3.039l5.657-5.657C34.046 6.053 29.268 4 24 4 16.318 4 9.656 8.337 6.306 14.691z'
                  />
                  <path
                    fill='#4CAF50'
                    d='M24 44c5.166 0 9.86-1.977 13.409-5.192l-6.19-5.238A11.91 11.91 0 0 1 24 36c-5.202 0-9.619-3.317-11.283-7.946l-6.522 5.025C9.505 39.556 16.227 44 24 44z'
                  />
                  <path
                    fill='#1976D2'
                    d='M43.611 20.083H42V20H24v8h11.303a12.04 12.04 0 0 1-4.087 5.571l.003-.002 6.19 5.238C36.971 39.205 44 34 44 24c0-1.341-.138-2.65-.389-3.917z'
                  />
                </svg>
                <span>Connect Google Calendar</span>
              </div>
            )}
          </motion.button>

          {/* Action Buttons */}
          <div className='pt-8 space-y-4'>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleContinue}
              className='w-full h-[50px] rounded-[35px] bg-flowstate-dark text-white font-alegreya text-[24px] 
                cursor-pointer max-sm:h-[45px] max-sm:text-[20px]'
            >
              Continue to Flowstate
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleSkip}
              className='w-full h-[45px] rounded-[35px] bg-transparent border-[2px] border-gray-400 text-gray-600 
                font-alegreya text-[20px] cursor-pointer hover:border-gray-600 hover:text-gray-800 transition-colors
                max-sm:h-[40px] max-sm:text-[18px]'
            >
              Skip for now
            </motion.button>
          </div>

          {/* Help text */}
          <div className='pt-4 text-center'>
            <p className='font-alegreya text-[16px] text-gray-600 max-sm:text-[14px]'>
              You can always connect these apps later in your settings.
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}

// Loading component for Suspense fallback
function OAuthLoading() {
  return (
    <div className='relative min-h-screen flex justify-center items-center p-5 overflow-hidden bg-flowstate-bg'>
      {/* Orange blur effect */}
      <div className='absolute top-[-22px] left-[229px] w-[460px] h-[494px]'>
        <svg
          width='728'
          height='606'
          viewBox='0 0 728 606'
          fill='none'
          xmlns='http://www.w3.org/2000/svg'
        >
          <g filter='url(#filter0_f_48_36)'>
            <ellipse cx='364' cy='225' rx='230' ry='247' fill='#D06224' />
          </g>
          <defs>
            <filter
              id='filter0_f_48_36'
              x='0'
              y='-156'
              width='728'
              height='762'
              filterUnits='userSpaceOnUse'
              colorInterpolationFilters='sRGB'
            >
              <feFlood floodOpacity='0' result='BackgroundImageFix' />
              <feBlend
                mode='normal'
                in='SourceGraphic'
                in2='BackgroundImageFix'
                result='shape'
              />
              <feGaussianBlur
                stdDeviation='67'
                result='effect1_foregroundBlur_48_36'
              />
            </filter>
          </defs>
        </svg>
      </div>

      {/* Green blur effect */}
      <div className='absolute bottom-[-100px] right-0 w-[425px] h-[425px]'>
        <svg
          width='833'
          height='567'
          viewBox='0 0 833 567'
          fill='none'
          xmlns='http://www.w3.org/2000/svg'
        >
          <g filter='url(#filter0_f_48_26)'>
            <circle cx='416.5' cy='416.5' r='212.5' fill='#9EAB57' />
          </g>
          <defs>
            <filter
              id='filter0_f_48_26'
              x='0'
              y='0'
              width='833'
              height='833'
              filterUnits='userSpaceOnUse'
              colorInterpolationFilters='sRGB'
            >
              <feFlood floodOpacity='0' result='BackgroundImageFix' />
              <feBlend
                mode='normal'
                in='SourceGraphic'
                in2='BackgroundImageFix'
                result='shape'
              />
              <feGaussianBlur
                stdDeviation='102'
                result='effect1_foregroundBlur_48_26'
              />
            </filter>
          </defs>
        </svg>
      </div>

      {/* Loading Container */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className='bg-flowstate-header rounded-[45px] p-10 w-full max-w-[610px] flex flex-col items-center relative z-10
          max-lg:p-[30px] max-sm:p-5 max-sm:rounded-[25px]'
      >
        <h1 className='font-alegreya text-[48px] text-black mb-5 text-center max-sm:text-[36px]'>
          Connect Your Apps
        </h1>

        <div className='flex items-center justify-center'>
          <div className='animate-spin rounded-full h-8 w-8 border-b-2 border-flowstate-dark'></div>
          <span className='ml-3 font-alegreya text-[20px] text-black'>
            Loading...
          </span>
        </div>
      </motion.div>
    </div>
  );
}

export default function OAuth() {
  return (
    <Suspense fallback={<OAuthLoading />}>
      <OAuthContent />
    </Suspense>
  );
}

'use client';

import Image from 'next/image';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, loading } = useAuth();

  const redirectTo = searchParams.get('redirect') || '/Chat';

  const [formData, setFormData] = useState({
    email: '',
    password: '',
    rememberMe: false,
  });

  const [error, setError] = useState('');

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      // Call login function from AuthContext
      await login(formData.email, formData.password);

      // Redirect to the page they came from, or to chat page
      router.push(redirectTo);
    } catch (err) {
      let message = 'An error occurred during login';
      if (err instanceof Error) {
        if ('code' in err) {
          const errorWithCode = err as Error & { code?: string };
          switch (errorWithCode.code) {
            case 'invalid_credientials':
              message = 'Incorrect email or password.';
              break;
            case 'email_not_confirmed':
              message = 'Your email has not been verified. Please check your inbox.';
              break;
            default:
              message = err.message;
          }
        } else {
          message = err.message;
        }
      }
      setError(message);
    }
  }; return (<div className='relative min-h-screen flex justify-center items-center p-5 bg-flowstate-bg overflow-hidden'> {/* Green blur circle - top */} <div className='absolute top-[-89px] right-[224px] w-[425px] h-[425px]'> <svg width='833' height='540' viewBox='0 0 833 540' fill='none' xmlns='http://www.w3.org/2000/svg' > <g filter='url(#filter0_f_48_20)'> <circle cx='416.5' cy='123.5' r='212.5' fill='#9EAB57' /> </g> <defs> <filter id='filter0_f_48_20' x='0' y='-293' width='833' height='833' filterUnits='userSpaceOnUse' colorInterpolationFilters='sRGB' > <feFlood floodOpacity='0' result='BackgroundImageFix' /> <feBlend mode='normal' in='SourceGraphic' in2='BackgroundImageFix' result='shape' /> <feGaussianBlur stdDeviation='102' result='effect1_foregroundBlur_48_20' /> </filter> </defs> </svg> </div> {/* Orange blur circle - bottom */}
    <div className='absolute bottom-[-89px] left-[124px] w-[460px] h-[494px]'>
      <svg
        width='718'
        height='422'
        viewBox='0 0 718 422'
        fill='none'
        xmlns='http://www.w3.org/2000/svg'
      >
        <g filter='url(#filter0_f_48_38)'>
          <ellipse cx='354' cy='381' rx='230' ry='247' fill='#D06224' />
        </g>
        <defs>
          <filter
            id='filter0_f_48_38'
            x='-10'
            y='0'
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
              result='effect1_foregroundBlur_48_38'
            />
          </filter>
        </defs>
      </svg>
    </div>

    {/* Main container */}
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className='relative w-[610px] mt-[30px] max-lg:w-[90%] max-lg:max-w-[610px] max-sm:w-full px-4'
    >
      <div className='w-full min-h-[800px] rounded-[45px] bg-flowstate-header max-lg:min-h-[750px]'>
        <div className='absolute top-0 left-0 w-full h-full p-10 max-sm:p-5'>
          <h1 className='font-alegreya text-[48px] text-black mb-[30px]'>
            Sign in
          </h1>

          {/* Sign up link */}
          <div className='absolute right-5 top-[65px] text-[20px] max-sm:static max-sm:text-center max-sm:mb-5'>
            <span>Don&apos;t have an account? </span>
            <Link
              href='/Signup'
              className='font-bold cursor-pointer hover:text-flowstate-accent transition-colors'
            >
              Create One
            </Link>
          </div>

          {/* Form */}
          <form
            onSubmit={handleSubmit}
            className='max-w-[427px] mx-auto mt-20 max-sm:mt-10'
          >
            {/* Email field */}
            <div className='mb-10'>
              <label
                htmlFor='email'
                className='font-alegreya text-[32px] text-black mb-2.5 block'
              >
                Email
              </label>
              <input
                type='email'
                id='email'
                name='email'
                placeholder='e.g. student@school.edu'
                value={formData.email}
                onChange={handleInputChange}
                className='w-full h-[40px] rounded-[35px] border-[3px] border-black bg-flowstate-header
                    px-5 font-alegreya text-[24px] text-[#665F5D] max-sm:text-[20px]'
              />
            </div>

            {/* Password field */}
            <div className='mb-10'>
              <label
                htmlFor='password'
                className='font-alegreya text-[32px] text-black mb-2.5 block'
              >
                Password
              </label>
              <input
                type='password'
                id='password'
                name='password'
                placeholder='Password (min 8 characters)'
                value={formData.password}
                onChange={handleInputChange}
                className='w-full h-[40px] rounded-[35px] border-[3px] border-black bg-flowstate-header
                    px-5 font-alegreya text-[24px] text-[#665F5D] max-sm:text-[20px]'
              />
            </div>

            {/* Remember me checkbox */}
            <div className='flex items-center mb-10'>
              <div className='flex items-center gap-2.5'>
                <input
                  type='checkbox'
                  id='rememberMe'
                  name='rememberMe'
                  checked={formData.rememberMe}
                  onChange={handleInputChange}
                  className='w-8 h-8 border-2 border-[#1D1B20] rounded'
                />
                <label
                  htmlFor='rememberMe'
                  className='font-alegreya text-[32px] text-black max-sm:text-[24px]'
                >
                  Remember me
                </label>
              </div>
            </div>

            {/* Buttons */}
            <div className='flex flex-col gap-[25px]'>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                type='submit'
                disabled={loading}
                className='w-full h-[80px] rounded-[35px] bg-flowstate-dark text-white font-alegreya text-[36px]
                    cursor-pointer max-sm:h-[60px] max-sm:text-[28px] max-sm:-mt-[5px]'
              >
                {loading ? 'Signing in...' : 'Sign in'}
              </motion.button>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                type='button'
                className='w-full h-[50px] rounded-[35px] bg-flowstate-bg flex items-center px-5
                    cursor-pointer max-sm:h-[45px] max-lg:px-4'
              >
                <Image
                  src='/google.png'
                  alt='Google'
                  width={32}
                  height={32}
                  className='mr-5 max-lg:mr-3'
                />
                <span className='font-alegreya text-[32px] text-black max-lg:text-[24px] max-sm:text-[17px]'>
                  Sign in with Google
                </span>
              </motion.button>
            </div>

            {/* Error display */}
            {error && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.4, ease: 'easeInOut' }}
                className='mt-5 bg-red-400 border-red-500 border-4 text-red-50 text-center rounded-full font-alegreya text-[20px]'>
                {error}
              </motion.div>
            )}

            {/* Development backdoor info */}
          </form>
        </div>
      </div>
    </motion.div>
  </div>
  );
}

export default function Login() {
  return (
    <Suspense
      fallback={
        <div className='min-h-screen flex items-center justify-center bg-flowstate-bg'>
          <div className='animate-spin rounded-full h-12 w-12 border-b-2 border-flowstate-dark'></div>
        </div>
      }
    >
      <LoginContent />
    </Suspense>
  );
}

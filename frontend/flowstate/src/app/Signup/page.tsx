'use client';

import Image from 'next/image';
import { motion } from 'framer-motion';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

export default function Signup() {
  const router = useRouter();
  const { signup, loading } = useAuth();

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    terms: false,
  });

  const [error, setError] = useState('');
  const [showPasswordRequirements, setShowPasswordRequirements] =
    useState(false);

  // Password validation helper
  const getPasswordValidation = (password: string) => {
    return {
      minLength: password.length >= 8,
      hasLowercase: /[a-z]/.test(password),
      hasUppercase: /[A-Z]/.test(password),
      hasNumber: /\d/.test(password),
      hasSymbol: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password),
    };
  };

  const passwordValidation = getPasswordValidation(formData.password);

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

    // Basic validation
    if (!formData.name || !formData.email || !formData.password) {
      setError('All fields are required');
      return;
    }

    // Password strength validation
    const isPasswordValid = Object.values(passwordValidation).every(Boolean);
    if (!isPasswordValid) {
      setError('Password does not meet the required criteria');
      return;
    }

    if (!formData.terms) {
      setError('You must agree to the Terms & Conditions');
      return;
    }

    try {
      // Call signup function from AuthContext
      await signup(formData.name, formData.email, formData.password);

      // Redirect to OAuth page on successful signup
      router.push('/OAuth');
    } catch (err) {
      let message = 'An error occurred during login';
      if (err instanceof Error) {
        const errorWithCode = err as Error & { code?: string };
        switch (errorWithCode.code) {
          case 'email_address_invalid':
            message = 'Please enter a valid email address.';
          case 'email_exists':
            message =
              'An account with this email already exists, try Logging In!';
          case 'invalid_credentials':
            message = 'invalid credientials provided, try again';
            defualt: message = err.message;
        }
      }
      setError(message);
    }
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
        <h1 className='font-alegreya text-[48px] text-black mb-10 max-sm:text-[36px]'>
          Sign Up
        </h1>

        <form
          onSubmit={handleSubmit}
          className='w-full max-w-[400px] space-y-5'
        >
          {/* Name Input */}
          <div className='w-full'>
            <label
              htmlFor='name'
              className='font-alegreya text-[32px] text-black block mb-2.5 max-sm:text-[24px]'
            >
              Name
            </label>
            <input
              type='text'
              id='name'
              name='name'
              placeholder='e.g. Luke Brevoort'
              value={formData.name}
              onChange={handleInputChange}
              className='w-full h-[40px] rounded-[35px] border-[3px] border-black bg-flowstate-header
                px-5 font-alegreya text-[24px] text-[#665F5D] max-sm:text-[20px]'
            />
          </div>

          {/* Email Input */}
          <div className='w-full'>
            <label
              htmlFor='email'
              className='font-alegreya text-[32px] text-black block mb-2.5 max-sm:text-[24px]'
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

          {/* Password Input */}
          <div className='w-full'>
            <label
              htmlFor='password'
              className='font-alegreya text-[32px] text-black block mb-2.5 max-sm:text-[24px]'
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
              onFocus={() => setShowPasswordRequirements(true)}
              onBlur={() => setShowPasswordRequirements(false)}
              className='w-full h-[40px] rounded-[35px] border-[3px] border-black bg-flowstate-header
                px-5 font-alegreya text-[24px] text-[#665F5D] max-sm:text-[20px]'
            />

            {/* Password Requirements Display */}
            {(showPasswordRequirements || formData.password.length > 0) && (
              <motion.div
                initial={{ opacity: 0, y: -10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -10, scale: 0.95 }}
                transition={{ duration: 0.3, ease: 'easeOut' }}
                className='mt-3 p-3 bg-white rounded-[15px] border-[2px] border-gray-200 shadow-sm'
              >
                <div className='mb-2'>
                  <div className='flex items-center justify-between mb-1'>
                    <h4 className='font-alegreya text-[14px] text-black font-semibold'>
                      Password Requirements
                    </h4>
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ delay: 0.1 }}
                      className='flex items-center gap-1'
                    >
                      <span
                        className={`font-alegreya text-[16px] font-bold ${passwordValidation.minLength ? 'text-green-600' : 'text-gray-500'}`}
                      >
                        8+
                      </span>
                      <span className='font-alegreya text-[12px] text-gray-600'>
                        chars
                      </span>
                      {passwordValidation.minLength && (
                        <motion.span
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          className='text-green-600 text-[14px]'
                        >
                          ✓
                        </motion.span>
                      )}
                    </motion.div>
                  </div>

                  {/* Compact Requirements Grid */}
                  <div className='grid grid-cols-2 gap-2 text-[12px]'>
                    <motion.div
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.1 }}
                      className='flex items-center gap-1'
                    >
                      <motion.span
                        animate={{
                          backgroundColor: passwordValidation.hasLowercase
                            ? '#10b981'
                            : '#d1d5db',
                          scale: passwordValidation.hasLowercase
                            ? [1, 1.2, 1]
                            : 1,
                        }}
                        transition={{ duration: 0.2 }}
                        className='w-3 h-3 rounded-full'
                      ></motion.span>
                      <span
                        className={`font-alegreya ${passwordValidation.hasLowercase ? 'text-green-600' : 'text-gray-500'}`}
                      >
                        Lowercase
                      </span>
                    </motion.div>

                    <motion.div
                      initial={{ opacity: 0, x: 10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.15 }}
                      className='flex items-center gap-1'
                    >
                      <motion.span
                        animate={{
                          backgroundColor: passwordValidation.hasUppercase
                            ? '#10b981'
                            : '#d1d5db',
                          scale: passwordValidation.hasUppercase
                            ? [1, 1.2, 1]
                            : 1,
                        }}
                        transition={{ duration: 0.2 }}
                        className='w-3 h-3 rounded-full'
                      ></motion.span>
                      <span
                        className={`font-alegreya ${passwordValidation.hasUppercase ? 'text-green-600' : 'text-gray-500'}`}
                      >
                        Uppercase
                      </span>
                    </motion.div>

                    <motion.div
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.2 }}
                      className='flex items-center gap-1'
                    >
                      <motion.span
                        animate={{
                          backgroundColor: passwordValidation.hasNumber
                            ? '#10b981'
                            : '#d1d5db',
                          scale: passwordValidation.hasNumber ? [1, 1.2, 1] : 1,
                        }}
                        transition={{ duration: 0.2 }}
                        className='w-3 h-3 rounded-full'
                      ></motion.span>
                      <span
                        className={`font-alegreya ${passwordValidation.hasNumber ? 'text-green-600' : 'text-gray-500'}`}
                      >
                        Number
                      </span>
                    </motion.div>

                    <motion.div
                      initial={{ opacity: 0, x: 10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.25 }}
                      className='flex items-center gap-1'
                    >
                      <motion.span
                        animate={{
                          backgroundColor: passwordValidation.hasSymbol
                            ? '#10b981'
                            : '#d1d5db',
                          scale: passwordValidation.hasSymbol ? [1, 1.2, 1] : 1,
                        }}
                        transition={{ duration: 0.2 }}
                        className='w-3 h-3 rounded-full'
                      ></motion.span>
                      <span
                        className={`font-alegreya ${passwordValidation.hasSymbol ? 'text-green-600' : 'text-gray-500'}`}
                      >
                        Symbol
                      </span>
                    </motion.div>
                  </div>
                </div>

                {/* Progress Bar */}
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: '100%' }}
                  className='w-full bg-gray-200 rounded-full h-1.5 mt-2'
                >
                  <motion.div
                    initial={{ width: '0%' }}
                    animate={{
                      width: `${(Object.values(passwordValidation).filter(Boolean).length / 5) * 100}%`,
                    }}
                    transition={{ duration: 0.3 }}
                    className='bg-gradient-to-r from-red-400 via-yellow-400 to-green-500 h-1.5 rounded-full'
                  ></motion.div>
                </motion.div>
              </motion.div>
            )}
          </div>

          {/* Terms Checkbox */}
          <div className='flex items-center gap-2.5 my-10'>
            <input
              type='checkbox'
              id='terms'
              name='terms'
              checked={formData.terms}
              onChange={handleInputChange}
              className='w-8 h-8 border-2 border-[#1D1B20] rounded'
            />
            <label
              htmlFor='terms'
              className='font-alegreya text-[24px] text-black max-sm:text-[20px]'
            >
              I agree to <span className='font-bold'>Terms and Conditions</span>
            </label>
          </div>

          {/* Sign Up Button */}
          <button
            type='submit'
            disabled={loading}
            className={`w-full h-[50px] rounded-[35px] bg-flowstate-dark text-white font-alegreya text-[24px] 
              ${loading ? 'opacity-70' : ''}`}
          >
            {loading ? 'Creating Account...' : 'Create Account'}
          </button>

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
          <div className='mt-6 p-4 bg-yellow-100 border-2 border-yellow-400 rounded-lg'>
            <div className='text-center text-yellow-800'>
              <p className='font-bold text-sm mb-2'>🔓 DEVELOPMENT MODE</p>
              <p className='text-xs'>
                Use any email with &apos;test&apos; in it to bypass signup
              </p>
              <p className='text-xs font-mono'>Example: yourname@test.com</p>
            </div>
          </div>

          {/* Google Sign Up Button */}
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            type='button'
            className='w-full h-[50px] rounded-[35px] bg-flowstate-bg flex items-center px-6
              font-alegreya text-[32px] text-black cursor-pointer max-sm:h-[45px] max-sm:text-[24px]'
          >
            <Image
              src='/google.png'
              alt='Google'
              width={32}
              height={32}
              className='mr-5'
            />
            <span>Sign up with Google</span>
          </motion.button>
        </form>
      </motion.div>
    </div>
  );
}

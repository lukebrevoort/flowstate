"use client";

import Image from "next/image";
import Link from "next/link";
import { motion } from "framer-motion";
import { useState } from "react";
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

export default function Signup() {
  const router = useRouter();
  const { signup, loading } = useAuth();
  
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    terms: false,
  });
  
  const [error, setError] = useState('');

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
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
    
    if (!formData.terms) {
      setError('You must agree to the Terms & Conditions');
      return;
    }
    
    try {
      // Call signup function from AuthContext
      await signup(formData.name, formData.email, formData.password);
      
      // Redirect to chat page on successful signup
      router.push('/Chat');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred during signup');
    }
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
        <h1 className="font-alegreya text-[48px] text-black mb-10 max-sm:text-[36px]">
          Sign Up
        </h1>

        <form
          onSubmit={handleSubmit}
          className="w-full max-w-[400px] space-y-5"
        >
          {/* Name Input */}
          <div className="w-full">
            <label
              htmlFor="name"
              className="font-alegreya text-[32px] text-black block mb-2.5 max-sm:text-[24px]"
            >
              Name
            </label>
            <input
              type="text"
              id="name"
              name="name"
              placeholder="e.g. Luke Brevoort"
              value={formData.name}
              onChange={handleInputChange}
              className="w-full h-[40px] rounded-[35px] border-[3px] border-black bg-flowstate-header
                px-5 font-alegreya text-[24px] text-[#665F5D] max-sm:text-[20px]"
            />
          </div>

          {/* Email Input */}
          <div className="w-full">
            <label
              htmlFor="email"
              className="font-alegreya text-[32px] text-black block mb-2.5 max-sm:text-[24px]"
            >
              Email
            </label>
            <input
              type="email"
              id="email"
              name="email"
              placeholder="e.g. student@school.edu"
              value={formData.email}
              onChange={handleInputChange}
              className="w-full h-[40px] rounded-[35px] border-[3px] border-black bg-flowstate-header
                px-5 font-alegreya text-[24px] text-[#665F5D] max-sm:text-[20px]"
            />
          </div>

          {/* Password Input */}
          <div className="w-full">
            <label
              htmlFor="password"
              className="font-alegreya text-[32px] text-black block mb-2.5 max-sm:text-[24px]"
            >
              Password
            </label>
            <input
              type="password"
              id="password"
              name="password"
              placeholder="Password (min 8 characters)"
              value={formData.password}
              onChange={handleInputChange}
              className="w-full h-[40px] rounded-[35px] border-[3px] border-black bg-flowstate-header
                px-5 font-alegreya text-[24px] text-[#665F5D] max-sm:text-[20px]"
            />
          </div>

          {/* Terms Checkbox */}
          <div className="flex items-center gap-2.5 my-10">
            <input
              type="checkbox"
              id="terms"
              name="terms"
              checked={formData.terms}
              onChange={handleInputChange}
              className="w-8 h-8 border-2 border-[#1D1B20] rounded"
            />
            <label
              htmlFor="terms"
              className="font-alegreya text-[24px] text-black max-sm:text-[20px]"
            >
              I agree to <span className="font-bold">Terms and Conditions</span>
            </label>
          </div>

          {/* Sign Up Button */}
          <button
            type="submit"
            disabled={loading}
            className={`w-full h-[50px] rounded-[35px] bg-flowstate-dark text-white font-alegreya text-[24px] 
              ${loading ? 'opacity-70' : ''}`}
          >
            {loading ? 'Creating Account...' : 'Create Account'}
          </button>
          
          {/* Error display */}
          {error && (
            <div className="mt-4 text-red-500 text-center">
              {error}
            </div>
          )}

          {/* Google Sign Up Button */}
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            type="button"
            className="w-full h-[50px] rounded-[35px] bg-flowstate-bg flex items-center px-6
              font-alegreya text-[32px] text-black cursor-pointer max-sm:h-[45px] max-sm:text-[24px]"
          >
            <Image
              src="/google.png"
              alt="Google"
              width={32}
              height={32}
              className="mr-5"
            />
            <span>Sign up with Google</span>
          </motion.button>
        </form>
      </motion.div>
    </div>
  );
}

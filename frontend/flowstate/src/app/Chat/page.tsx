"use client";

import Image from "next/image";
import { motion } from "framer-motion";
import { useState, FormEvent } from "react";

export default function Chat() {
  const [message, setMessage] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    console.log("Submitted message:", message);
    // Add your form submission logic here
    setMessage(""); // Clear input after submission
  };

  return (
    <div className="min-h-screen w-full bg-flowstate-bg flex flex-col">
      {/* Header */}
      <header className="w-full h-[89px] bg-flowstate-header shadow-header flex items-center justify-between px-[100px] max-lg:px-10 max-sm:px-5">
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

        <div className="flex items-center gap-15">
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
      <main className="flex-1 flex flex-col items-center justify-center mt-[200px] mb-20 max-lg:mt-[200px] max-sm:mt-[150px]">
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-[92px] font-alegreya text-center text-black max-w-[825px] leading-[1.2] max-lg:text-[72px] max-sm:text-[48px] max-sm:px-5"
        >
          Welcome Back! How can I assist you?
        </motion.h2>

        {/* Chat Input Form */}
        <motion.form
          onSubmit={handleSubmit}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="mt-[134px] w-[1030px] h-[236px] bg-flowstate-header rounded-[35px] p-[25px] relative max-lg:w-[90%] max-sm:w-[95%]"
        >
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Ask Anything..."
            className="w-full h-[120px] bg-transparent text-[30px] font-alegreya text-[#665F5D] resize-none focus:outline-none"
            aria-label="Chat message"
          />

          {/* Attachment Button */}
          <motion.button
            type="button"
            className="absolute bottom-[21px] left-[25px] cursor-pointer bg-flowstate-bg rounded-full p-2 hover:bg-gray-100 transition-all"
            aria-label="Add attachment"
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <motion.svg
              width="40"
              height="40"
              viewBox="0 0 48 48"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              whileHover={{ rotate: 90 }}
              transition={{ type: "spring", stiffness: 260, damping: 20 }}
            >
              <path
                d="M24 16V32M16 24H32M10 6H38C40.2091 6 42 7.79086 42 10V38C42 40.2091 40.2091 42 38 42H10C7.79086 42 6 40.2091 6 38V10C6 7.79086 7.79086 6 10 6Z"
                stroke="#1E1E1E"
                strokeWidth="4"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </motion.svg>
          </motion.button>

          {/* Send Button Area */}
            <div className="absolute bottom-[21px] right-[32px] flex items-center gap-[10px]">
            <motion.div
              animate={{ rotate: message ? 360 : 0 }}
              whileTap={{ rotate: 180 }}
              transition={{ 
              type: "spring", 
              duration: 1.2, 
              bounce: 0.3, 
              }}
            >
              <Image
              src="/flowstate-main-logo.png"
              alt="FlowState Logo"
              width={64}
              height={64}
              className="w-[64px] h-[64px] cursor-pointer"
              />
            </motion.div>
            <motion.button
              type="submit"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="w-[168px] h-[64px] bg-flowstate-accent rounded-[32px] font-alegreya text-[36px] font-bold text-flowstate-bg hover:bg-flowstate-accent-hover transition-colors cursor-pointer"
            >
              Go!
            </motion.button>
            </div>
        </motion.form>
      </main>
    </div>
  );
}

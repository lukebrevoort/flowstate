"use client";

import Image from "next/image";
import { motion } from "framer-motion";

export default function Home() {
  return (
    <div className="relative min-h-screen w-full bg-flowstate-bg overflow-hidden">
      <header className="w-full h-[89px] bg-flowstate-header shadow-header flex items-center justify-between px-[100px] max-lg:px-[50px] max-sm:px-5">
        <div className="flex items-center gap-[10px]">
        <a href="/" aria-label="Go to Chat">
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
        <div className="flex items-center">
            <motion.a 
              href="/Login"
              whileHover={{ 
                scale: 1.05,
                boxShadow: "0px 0px 8px rgba(0, 0, 0, 0.2)"
              }}
              whileTap={{ 
                scale: 0.95,
                boxShadow: "0px 0px 0px rgba(0, 0, 0, 0)"
              }}
              transition={{ type: "spring", stiffness: 400, damping: 17 }}
              onClick={() => console.log('Login clicked')} 
              className="text-white font-alegreya text-[24px] font-medium bg-flowstate-accent hover:bg-flowstate-accent-hover transition-colors duration-200 rounded-[40px] px-[30px] py-[6px] cursor-pointer inline-block text-center"
            >
              Log in
            </motion.a>
        </div>
      </header>

      <main className="flex flex-col items-center justify-center mt-[30px] max-lg:mt-[100px] max-sm:mt-[30px]">
          <video autoPlay muted playsInline className="w-[350px] h-[350px] max-lg:w-[350px] max-lg:h-[350px] max-sm:w-[250px] max-sm:h-[250px]">
            <source src="Large Logo.mp4" type="video/mp4" />
            Your browser does not support the video tag.
          </video>
        <motion.div
        initial={{ opacity: 0, y: -50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1.5 }}

        >
          <h2 className="text-[72px] font-alegreya text-center mt-10 px-5 max-lg:text-[50px] max-sm:text-[48px]">
            Welcome To FlowState
          </h2>
        </motion.div>
      </main>

      <section className="mx-[300px] mt-[80px] max-lg:mx-[150px] max-sm:mx-5">
        <motion.div 
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1.5, delay: 1 }}
          className="bg-flowstate-dark rounded-[50px] flex justify-between items-center px-10 py-10 max-lg:flex-col max-lg:gap-[30px] max-sm:px-5"
            
            >
          <p className="text-flowstate-bg font-alegreya text-[32px] font-bold max-w-[500px] text-center max-lg:text-[36px] max-sm:text-[28px]">
        A brand new way of experiencing productivity
          </p>
          <motion.a
          href="/Signup" 
        whileHover={{ 
          scale: 1.05,
          boxShadow: "0px 0px 15px rgba(255, 255, 255, 0.3)"
        }}
        whileTap={{ 
          scale: 0.95,
          boxShadow: "0px 0px 0px rgba(255, 255, 255, 0)"
        }}
        transition={{ type: "spring", stiffness: 400, damping: 17 }}
        className="text-white font-alegreya text-[24px] font-bold max-lg:text-[22px] max-sm:text-[18px] bg-flowstate-accent hover:bg-flowstate-accent-hover transition-colors duration-200 rounded-[40px] px-[20px] py-[8px] cursor-pointer inline-block text-center"
          >
        Sign Up Today
          </motion.a>
        </motion.div>
      </section>
    </div>
  );
}

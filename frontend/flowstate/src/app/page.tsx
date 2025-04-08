"use client";

import Image from "next/image";
import { motion } from "framer-motion";

export default function Home() {
  return (
    <div className="relative min-h-screen w-full bg-flowstate-bg overflow-hidden">
      <header className="w-full h-[89px] bg-flowstate-header shadow-header flex items-center justify-between px-[100px] max-lg:px-[50px] max-sm:px-5">
        <div className="flex items-center gap-[10px]">
          <Image
            src="/flowstate-main-logo.png"
            alt="FlowState Logo"
            width={78}
            height={78}
            className="w-[50px] h-[50px] max-sm:w-[50px] max-sm:h-[50px]"
            priority
          />
          <h1 className="font-alegreya text-[32px] text-black max-lg:text-[30px] max-sm:text-[28px]">
            FlowState
          </h1>
        </div>
        <div className="flex items-center">
            <motion.button 
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
              className="text-white font-alegreya text-[24px] font-medium bg-flowstate-accent hover:bg-flowstate-accent-hover transition-colors duration-200 rounded-[40px] px-[30px] py-[6px] cursor-pointer"
            >
              Log in
            </motion.button>
        </div>
      </header>

      <main className="flex flex-col items-center justify-center mt-[160px] max-lg:mt-[100px] max-sm:mt-[60px]">
        <Image
          src="/flowstate-main-logo.png"
          alt="FlowState Main Logo"
          width={400}
          height={400}
          className="w-[469px] h-[469px] max-lg:w-[350px] max-lg:h-[350px] max-sm:w-[250px] max-sm:h-[250px]"
          priority
        />
        <h2 className="text-[96px] font-alegreya text-center mt-10 px-5 max-lg:text-[72px] max-sm:text-[48px]">
          Welcome To FlowState
        </h2>
      </main>

      <section className="mx-[100px] mt-[100px] max-lg:mx-[50px] max-sm:mx-5">
        <div className="bg-flowstate-dark rounded-[50px] flex justify-between items-center px-10 py-10 max-lg:flex-col max-lg:gap-[30px] max-sm:px-5">
          <p className="text-flowstate-bg font-alegreya text-[48px] font-bold max-w-[597px] text-center max-lg:text-[36px] max-sm:text-[28px]">
            A brand new way of experiencing productivity
          </p>
          <motion.button 
            whileHover={{ 
              scale: 1.05,
              boxShadow: "0px 0px 15px rgba(255, 255, 255, 0.3)"
            }}
            whileTap={{ 
              scale: 0.95,
              boxShadow: "0px 0px 0px rgba(255, 255, 255, 0)"
            }}
            transition={{ type: "spring", stiffness: 400, damping: 17 }}
            className="text-white font-alegreya text-[40px] font-bold max-lg:text-[32px] max-sm:text-[24px] bg-flowstate-accent hover:bg-flowstate-accent-hover transition-colors duration-200 rounded-[60px] px-[30px] py-[10px] cursor-pointer"
          >
            Sign Up Today
          </motion.button>
        </div>
      </section>
    </div>
  );
}

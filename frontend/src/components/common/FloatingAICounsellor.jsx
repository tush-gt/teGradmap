import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sparkles, Bot } from 'lucide-react';

export const FloatingAICounsellor = () => {
  const location = useLocation();

  // Don't show the floating button if already on the /counsellor page
  if (location.pathname === '/counsellor') {
    return null;
  }

  return (
    <motion.div
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ delay: 0.5, type: 'spring', stiffness: 260, damping: 20 }}
      className="fixed bottom-6 right-6 z-50 group"
    >
      <Link
        to="/counsellor"
        className="flex items-center gap-2.5 bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-500 text-white px-4 py-3 rounded-full shadow-2xl shadow-emerald-500/30 border border-emerald-400/30 hover:scale-105 active:scale-95 transition-all"
      >
        <div className="relative">
          <Bot className="w-5 h-5 text-white" />
          <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-amber-400 rounded-full animate-ping" />
          <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-amber-400 rounded-full" />
        </div>
        <div className="flex flex-col text-left">
          <span className="text-xs font-black tracking-tight flex items-center gap-1">
            AI Counsellor <Sparkles className="w-3 h-3 text-amber-300" />
          </span>
          <span className="text-[10px] text-emerald-100 font-medium">Ask Gemini Anything</span>
        </div>
      </Link>
    </motion.div>
  );
};

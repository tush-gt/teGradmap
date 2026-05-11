import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, X } from 'lucide-react';
import { cn } from '../../utils/cn';

export const TeachTooltip = ({ title = "Smart Tip", children, className }) => {
  const [isVisible, setIsVisible] = useState(true);

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div 
          initial={{ opacity: 0, y: 10, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className={cn(
            "relative p-6 my-6 rounded-3xl bg-violet-500/5 border border-violet-500/20 text-foreground flex items-start gap-4 shadow-xl backdrop-blur-md overflow-hidden group",
            className
          )}
        >
          <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
            <Sparkles className="w-16 h-16 text-violet-400" />
          </div>
          
          <div className="w-10 h-10 rounded-xl bg-violet-600/20 flex items-center justify-center shrink-0">
            <Sparkles className="w-5 h-5 text-violet-400" />
          </div>
          
          <div className="flex-1 relative z-10">
            <h4 className="font-black text-xs uppercase tracking-widest text-violet-400 mb-2">{title}</h4>
            <div className="text-sm font-medium text-muted-foreground leading-relaxed">
              {children}
            </div>
          </div>
          
          <button 
            onClick={() => setIsVisible(false)}
            className="p-2 hover:bg-violet-500/10 rounded-xl transition-all relative z-10"
            aria-label="Dismiss tooltip"
          >
            <X className="w-4 h-4 text-muted-foreground hover:text-foreground" />
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  );
};


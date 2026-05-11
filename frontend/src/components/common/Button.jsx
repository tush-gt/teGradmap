import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../utils/cn';

export const Button = React.forwardRef(({ className, variant = 'primary', size = 'md', children, ...props }, ref) => {
  const baseStyles = 'inline-flex items-center justify-center rounded-xl font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 active:scale-95';
  
  const variants = {
    primary: 'bg-gradient-to-r from-violet-600 to-indigo-600 text-white shadow-lg shadow-violet-500/25 hover:shadow-violet-500/40 hover:-translate-y-0.5',
    secondary: 'bg-secondary/80 backdrop-blur-md text-secondary-foreground shadow-sm hover:bg-secondary hover:-translate-y-0.5 border border-white/10',
    outline: 'border-2 border-border bg-transparent hover:border-brand-base/50 hover:bg-brand-base/5 hover:-translate-y-0.5',
    ghost: 'hover:bg-accent/50 hover:text-accent-foreground',
    destructive: 'bg-red-500/10 text-red-500 border border-red-500/20 hover:bg-red-500 hover:text-white',
    premium: 'bg-gradient-to-r from-violet-600 via-indigo-600 to-cyan-500 text-white shadow-xl shadow-indigo-500/20 hover:shadow-indigo-500/40 hover:-translate-y-1',
  };

  const sizes = {
    sm: 'h-9 px-4 text-xs',
    md: 'h-11 px-6 py-2',
    lg: 'h-14 px-10 text-lg rounded-2xl',
    icon: 'h-10 w-10',
  };

  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      ref={ref}
      className={cn(baseStyles, variants[variant], sizes[size], className)}
      {...props}
    >
      {children}
    </motion.button>
  );
});

Button.displayName = 'Button';


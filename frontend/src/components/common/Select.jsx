import React from 'react';
import { cn } from '../../utils/cn';

export const Select = React.forwardRef(({ className, children, ...props }, ref) => {
  return (
    <select
      className={cn(
        "flex h-12 w-full rounded-xl border border-border bg-background/50 backdrop-blur-sm px-4 py-2 text-sm transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:border-primary/50 focus-visible:bg-background/80 disabled:cursor-not-allowed disabled:opacity-50 appearance-none cursor-pointer",
        className
      )}
      ref={ref}
      {...props}
    >
      {children}
    </select>
  );
});

Select.displayName = "Select";


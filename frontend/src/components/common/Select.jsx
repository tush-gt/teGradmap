import React from 'react';
import { cn } from '../../utils/cn';

export const Select = React.forwardRef(({ className, children, ...props }, ref) => {
  return (
    <select
      className={cn(
        "flex h-12 w-full rounded-xl border border-border bg-zinc-950 text-white px-4 py-2 text-sm transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:border-primary/50 disabled:cursor-not-allowed disabled:opacity-50 appearance-none cursor-pointer [&>option]:bg-zinc-950 [&>option]:text-white",
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


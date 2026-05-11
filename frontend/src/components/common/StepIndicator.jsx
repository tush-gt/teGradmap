import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppStore } from '../../store/useAppStore';
import { cn } from '../../utils/cn';
import { Check } from 'lucide-react';

const stepData = [
  { id: 1, label: 'Welcome' },
  { id: 2, label: 'Profile' },
  { id: 3, label: 'Documents' },
  { id: 4, label: 'Option Form' },
  { id: 5, label: 'Allotment' },
  { id: 6, label: 'Decision' },
  { id: 7, label: 'Round Loop' },
  { id: 8, label: 'Confirmed' },
];

export const StepIndicator = () => {
  const currentStep = useAppStore(state => state.currentStep);
  const setCurrentStep = useAppStore(state => state.setCurrentStep);

  return (
    <div className="w-full">
      {/* Progress bar container */}
      <div className="relative w-full h-2 bg-emerald-500/10 rounded-full mb-8 overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${((currentStep - 1) / (stepData.length - 1)) * 100}%` }}
          transition={{ duration: 0.8, ease: "circOut" }}
          className="absolute left-0 top-0 h-full bg-gradient-to-r from-emerald-600 to-teal-500 rounded-full z-10"
        />
      </div>

      {/* Steps List */}
      <div className="flex items-start justify-between gap-2 overflow-x-auto pb-2 scrollbar-none">
        {stepData.map((step) => {
          const isCompleted = step.id < currentStep;
          const isCurrent = step.id === currentStep;
          
          return (
            <div
              key={step.id}
              className={cn(
                'flex flex-col items-center gap-2 min-w-[70px] transition-all',
                isCompleted ? 'cursor-pointer' : 'cursor-default'
              )}
              onClick={() => isCompleted && setCurrentStep(step.id)}
            >
              <motion.div
                animate={{
                  scale: isCurrent ? 1.1 : 1,
                  backgroundColor: isCompleted ? '#10b981' : (isCurrent ? 'rgba(16, 185, 129, 0.1)' : 'rgba(255, 255, 255, 0.05)'),
                }}
                className={cn(
                  'w-10 h-10 rounded-xl flex items-center justify-center text-xs font-black transition-all border-2',
                  isCompleted ? 'border-emerald-600 text-white' : isCurrent ? 'border-emerald-500 text-emerald-400' : 'border-white/5 text-muted-foreground/30'
                )}
              >
                <AnimatePresence mode="wait">
                  {isCompleted ? (
                    <motion.div key="check" initial={{ scale: 0 }} animate={{ scale: 1 }} exit={{ scale: 0 }}>
                      <Check className="w-4 h-4 stroke-[3px]" />
                    </motion.div>
                  ) : (
                    <motion.span key="number">{step.id}</motion.span>
                  )}
                </AnimatePresence>
              </motion.div>
              <span className={cn('text-[9px] uppercase font-black tracking-tighter text-center', isCurrent ? 'text-emerald-400' : 'text-muted-foreground/40')}>
                {step.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

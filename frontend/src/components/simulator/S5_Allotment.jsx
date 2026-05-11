import React, { useEffect, useState } from 'react';
import { Button } from '../common/Button';
import { TeachTooltip } from '../common/TeachTooltip';
import { useAppStore } from '../../store/useAppStore';
import { api } from '../../services/api';
import { Loader2, PartyPopper, Frown, ChevronRight, MapPin, GitBranch, Star } from 'lucide-react';
import { cn } from '../../utils/cn';

export const S5_Allotment = () => {
  const profile = useAppStore(state => state.profile);
  const optionForm = useAppStore(state => state.optionForm);
  const currentRound = useAppStore(state => state.currentRound);
  const allotmentResult = useAppStore(state => state.allotmentResult);
  const setAllotmentResult = useAppStore(state => state.setAllotmentResult);
  const setCurrentStep = useAppStore(state => state.setCurrentStep);
  const [isLoading, setIsLoading] = useState(!allotmentResult);
  const [dots, setDots] = useState(1);

  useEffect(() => {
    const interval = setInterval(() => setDots(d => (d % 3) + 1), 600);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!allotmentResult && optionForm.length > 0) {
      setIsLoading(true);
      api.simulateRound({ profile, optionForm, currentRound })
        .then(result => {
          setAllotmentResult(result);
          setIsLoading(false);
        });
    }
  }, [allotmentResult, optionForm, profile, currentRound, setAllotmentResult]);

  const handleNext = () => {
    if (allotmentResult?.allotted && allotmentResult.seat.preference_number === 1) {
      setCurrentStep(8);
    } else {
      setCurrentStep(6);
    }
  };

  if (isLoading) {
    return (
      <div className="glass rounded-2xl border-brand-base/10 p-16 flex flex-col items-center text-center">
        <div className="relative mb-8">
          <div className="w-24 h-24 rounded-full bg-brand-base/10 flex items-center justify-center">
            <Loader2 className="w-10 h-10 text-brand-base animate-spin" />
          </div>
          <div className="absolute inset-0 rounded-full bg-brand-base/20 animate-ping" />
        </div>
        <h3 className="text-2xl font-bold mb-2">Running Allotment Algorithm{'.'.repeat(dots)}</h3>
        <p className="text-muted-foreground max-w-sm">
          Checking your {optionForm.length} choices against Round {currentRound} cutoffs for <span className="text-brand-base font-semibold">{profile.category}</span> category.
        </p>
        <div className="mt-8 flex gap-3 flex-wrap justify-center text-sm text-muted-foreground">
          {['Scanning merit list', 'Matching cutoffs', 'Applying reservations', 'Finalising seat'].map((step, i) => (
            <span key={i} className="px-3 py-1 rounded-full bg-brand-base/10 text-brand-base/80 border border-brand-base/20 text-xs">{step}</span>
          ))}
        </div>
      </div>
    );
  }

  const { allotted, seat, message, merit_rank } = allotmentResult || {};
  const isAutoFreeze = allotted && seat.preference_number === 1;

  return (
    <div className="space-y-6">
      <TeachTooltip title="How Allotment Works">
        The computer checks your #1 choice first. If your merit rank qualifies, you get it. Otherwise it checks #2, then #3, and so on. This is deterministic — no randomness.
      </TeachTooltip>

      {/* Result card */}
      <div className={cn(
        "glass rounded-2xl border-2 overflow-hidden transition-all",
        allotted ? "border-brand-base/30" : "border-amber-500/30"
      )}>
        {/* Top accent bar */}
        <div className={cn(
          "h-1.5 w-full",
          allotted ? "bg-gradient-to-r from-brand-base to-teal-400" : "bg-gradient-to-r from-amber-400 to-orange-500"
        )} />

        <div className="p-8 md:p-12 text-center">
          {/* Icon */}
          <div className={cn(
            "w-24 h-24 rounded-full flex items-center justify-center mx-auto mb-6 relative",
            allotted ? "bg-brand-base/15" : "bg-amber-500/15"
          )}>
            {allotted
              ? <PartyPopper className="w-10 h-10 text-brand-base" />
              : <Frown className="w-10 h-10 text-amber-500" />
            }
            <div className={cn(
              "absolute inset-0 rounded-full animate-ping",
              allotted ? "bg-brand-base/10" : "bg-amber-500/10"
            )} />
          </div>

          <div className={cn(
            "text-xs font-bold uppercase tracking-widest mb-2",
            allotted ? "text-brand-base" : "text-amber-500"
          )}>
            Round {currentRound} · {allotted ? 'Allotted' : 'Not Allotted'}
          </div>

          <h2 className="text-3xl md:text-4xl font-extrabold mb-6">
            {allotted ? 'Congratulations! 🎉' : 'No Seat This Round'}
          </h2>

          {allotted ? (
            <div className="max-w-md mx-auto">
              {/* Seat details card */}
              <div className="relative bg-gradient-to-br from-brand-base/10 to-teal-500/5 border border-brand-base/20 rounded-2xl p-6 mb-6 text-left overflow-hidden">
                <div className="absolute top-3 right-3 px-2 py-1 rounded-full bg-brand-base/20 text-brand-base text-xs font-bold">
                  Preference #{seat.preference_number}
                </div>
                {isAutoFreeze && (
                  <div className="mb-3 text-xs font-bold uppercase text-amber-500 tracking-wider flex items-center gap-1">
                    <Star className="w-3 h-3" /> Auto-Freeze (1st Choice)
                  </div>
                )}
                <h3 className="text-xl font-bold pr-20 mb-1">{seat.college_name}</h3>
                <div className="flex items-center gap-2 text-brand-base font-semibold mb-4">
                  <GitBranch className="w-4 h-4" />
                  {seat.branch_name}
                </div>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="bg-background/50 rounded-lg p-3">
                    <div className="text-xs text-muted-foreground mb-1">Category</div>
                    <div className="font-bold">{seat.allotted_category}</div>
                  </div>
                  <div className="bg-background/50 rounded-lg p-3">
                    <div className="text-xs text-muted-foreground mb-1">Simulated Merit Rank</div>
                    <div className="font-bold">{merit_rank?.toLocaleString()}</div>
                  </div>
                </div>
              </div>

              {isAutoFreeze && (
                <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-600 dark:text-amber-400 text-sm font-medium text-left">
                  🔒 Your #1 preference was allotted. Admission is automatically confirmed — no further decisions needed.
                </div>
              )}
            </div>
          ) : (
            <div className="max-w-sm mx-auto bg-muted/20 border border-border/50 rounded-xl p-6 text-muted-foreground">
              <p className="leading-relaxed">{message}</p>
              <div className="mt-4 pt-4 border-t border-border/40">
                <span className="text-sm">Simulated Merit Rank: </span>
                <span className="font-bold text-foreground">{merit_rank?.toLocaleString()}</span>
              </div>
            </div>
          )}

          <div className="mt-10">
            <Button
              size="lg"
              onClick={handleNext}
              className="bg-gradient-to-r from-brand-base to-teal-500 hover:from-brand-dark hover:to-teal-600 border-0 shadow-xl shadow-brand-base/30 px-12 py-5 text-base font-bold gap-2 rounded-xl"
            >
              {isAutoFreeze ? 'View Admission Summary' : 'Proceed to Decision'}
              <ChevronRight className="w-5 h-5" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

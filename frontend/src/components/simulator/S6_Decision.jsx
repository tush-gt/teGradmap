import React from 'react';
import { TeachTooltip } from '../common/TeachTooltip';
import { useAppStore } from '../../store/useAppStore';
import { CheckCircle2, ArrowUpCircle, RefreshCcw, ChevronRight, Trophy } from 'lucide-react';
import { cn } from '../../utils/cn';

const choices = [
  {
    id: 'Freeze',
    icon: CheckCircle2,
    title: 'Freeze',
    tagline: 'I am satisfied.',
    desc: 'Accept this seat permanently. Your admission is confirmed. You will NOT participate in further rounds.',
    gradient: 'from-brand-base/20 to-teal-500/10',
    border: 'border-brand-base/40',
    glow: 'shadow-brand-base/20',
    iconColor: 'text-brand-base',
    iconBg: 'bg-brand-base/15',
    badge: 'bg-brand-base/20 text-brand-base',
    badgeText: 'Recommended',
  },
  {
    id: 'Float',
    icon: ArrowUpCircle,
    title: 'Float',
    tagline: 'Try for better.',
    desc: 'Keep this seat as backup, but try to upgrade to any higher-preference choice (any college/branch) in Round 2.',
    gradient: 'from-blue-500/15 to-cyan-500/10',
    border: 'border-blue-500/30',
    glow: 'shadow-blue-500/20',
    iconColor: 'text-blue-400',
    iconBg: 'bg-blue-500/15',
    badge: 'bg-blue-500/20 text-blue-400',
    badgeText: 'Betterment',
  },
  {
    id: 'Slide',
    icon: RefreshCcw,
    title: 'Slide',
    tagline: 'Same college.',
    desc: 'Keep this seat and try for a higher-preference BRANCH in the SAME college in the next round.',
    gradient: 'from-purple-500/15 to-violet-500/10',
    border: 'border-purple-500/30',
    glow: 'shadow-purple-500/20',
    iconColor: 'text-purple-400',
    iconBg: 'bg-purple-500/15',
    badge: 'bg-purple-500/20 text-purple-400',
    badgeText: 'Same College',
  },
];

export const S6_Decision = () => {
  const allotmentResult = useAppStore(state => state.allotmentResult);
  const currentRound = useAppStore(state => state.currentRound);
  const decision = useAppStore(state => state.decision);
  const setDecision = useAppStore(state => state.setDecision);
  const addToHistory = useAppStore(state => state.addToHistory);
  const setFinalAdmission = useAppStore(state => state.setFinalAdmission);
  const setCurrentStep = useAppStore(state => state.setCurrentStep);

  const { allotted, seat } = allotmentResult || {};

  const handleConfirm = () => {
    if (decision === 'Freeze' || currentRound >= 3) {
      setFinalAdmission(allotted ? seat : null);
      setCurrentStep(8);
    } else {
      addToHistory({ round: currentRound, seat, decision });
      setCurrentStep(4);
    }
  };

  return (
    <div className="space-y-6">
      <TeachTooltip title="Seat Acceptance Decision">
        You must choose within 24 hours of allotment in the real portal, or your seat is cancelled. If not allotted, you automatically proceed to the next round.
      </TeachTooltip>

      {allotted && (
        <div className="glass rounded-2xl border-brand-base/20 overflow-hidden">
          {/* Allotted seat banner */}
          <div className="bg-gradient-to-r from-brand-base/15 to-teal-500/10 px-8 py-6 border-b border-border/40 flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-brand-base/20 flex items-center justify-center">
              <Trophy className="w-6 h-6 text-brand-base" />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-brand-base mb-1">Allotted Seat — Round {currentRound}</p>
              <h3 className="text-xl font-bold">{seat.college_name}</h3>
              <p className="text-brand-base font-medium">{seat.branch_name} · {seat.allotted_category} · Pref #{seat.preference_number}</p>
            </div>
          </div>

          <div className="p-6">
            <p className="text-center text-muted-foreground mb-6 font-medium">Choose what you want to do with this allotment:</p>

            {/* Decision cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
              {choices.map(opt => {
                const Icon = opt.icon;
                const isSelected = decision === opt.id;

                return (
                  <div
                    key={opt.id}
                    onClick={() => setDecision(opt.id)}
                    className={cn(
                      "relative cursor-pointer rounded-2xl border-2 p-6 transition-all duration-200 group overflow-hidden",
                      isSelected
                        ? cn("bg-gradient-to-br", opt.gradient, opt.border, "shadow-xl", opt.glow)
                        : "border-border/50 bg-card hover:border-brand-base/20 hover:bg-muted/20"
                    )}
                  >
                    {/* Selected ring animation */}
                    {isSelected && (
                      <span className="absolute inset-0 rounded-2xl border-2 border-current animate-ping opacity-20 pointer-events-none" />
                    )}

                    <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center mb-4 transition-colors", opt.iconBg)}>
                      <Icon className={cn("w-5 h-5", opt.iconColor)} />
                    </div>

                    <span className={cn("text-xs font-bold px-2 py-0.5 rounded-full", opt.badge, "mb-3 inline-block")}>
                      {opt.badgeText}
                    </span>
                    <h4 className="font-bold text-lg mb-1">{opt.title}</h4>
                    <p className="text-xs text-muted-foreground leading-relaxed font-medium mb-2 italic">{opt.tagline}</p>
                    <p className="text-sm text-muted-foreground leading-relaxed">{opt.desc}</p>
                  </div>
                );
              })}
            </div>

            <div className="flex justify-center">
              <button
                onClick={handleConfirm}
                disabled={!decision}
                className={cn(
                  "flex items-center gap-2 px-10 py-4 rounded-xl font-bold text-white text-base transition-all",
                  decision
                    ? "bg-gradient-to-r from-brand-base to-teal-500 hover:from-brand-dark hover:to-teal-600 shadow-lg shadow-brand-base/30"
                    : "bg-muted text-muted-foreground cursor-not-allowed"
                )}
              >
                {decision === 'Freeze' || currentRound >= 3 ? 'Complete Simulation' : `Confirm ${decision || '—'} & Go to Round ${currentRound + 1}`}
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      )}

      {!allotted && (
        <div className="glass rounded-2xl border-amber-500/20 overflow-hidden text-center p-12">
          <h2 className="text-2xl font-bold mb-4">No Seat in Round {currentRound}</h2>
          <p className="text-muted-foreground mb-8 max-w-md mx-auto">You were not allotted a seat. You automatically proceed to Round {currentRound + 1}.</p>
          <button
            onClick={handleConfirm}
            className="px-10 py-4 rounded-xl font-bold text-white bg-gradient-to-r from-brand-base to-teal-500 hover:from-brand-dark hover:to-teal-600 shadow-lg shadow-brand-base/30 inline-flex items-center gap-2"
          >
            Go to Round {currentRound + 1} <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      )}
    </div>
  );
};

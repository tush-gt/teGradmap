import React from 'react';
import { Button } from '../common/Button';
import { TeachTooltip } from '../common/TeachTooltip';
import { useAppStore } from '../../store/useAppStore';
import { Zap, BookOpen, CheckCircle2, Trophy, ChevronRight } from 'lucide-react';

const steps = [
  { icon: BookOpen, text: 'Set up your candidate profile and documents' },
  { icon: CheckCircle2, text: 'Build and lock your ranked option form' },
  { icon: Trophy, text: 'Run the allotment and choose Freeze, Float or Slide' },
];

export const S1_Welcome = () => {
  const setCurrentStep = useAppStore(state => state.setCurrentStep);

  return (
    <div className="space-y-6">
      <TeachTooltip title="Safe Practice Environment">
        This mirrors the real CET Cell portal — choices here don't affect your real admission. Everything resets when you restart.
      </TeachTooltip>

      {/* Hero card */}
      <div className="relative rounded-3xl overflow-hidden border border-brand-base/20 shadow-2xl shadow-brand-base/10">
        {/* Animated gradient background */}
        <div className="absolute inset-0 bg-gradient-to-br from-brand-base/20 via-teal-500/10 to-cyan-500/20" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(16,185,129,0.15),transparent_60%)]" />
        <div className="absolute -top-24 -right-24 w-64 h-64 bg-cyan-400/20 rounded-full blur-3xl" />
        <div className="absolute -bottom-16 -left-16 w-48 h-48 bg-brand-base/20 rounded-full blur-3xl" />

        <div className="relative z-10 p-10 md:p-14">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-brand-base/20 border border-brand-base/30 text-brand-base text-sm font-medium mb-8">
            <Zap className="w-3.5 h-3.5" /> 8-Step Interactive Simulation
          </div>

          <h2 className="text-3xl md:text-5xl font-extrabold text-white mb-5 leading-tight tracking-tight">
            Practice the full CAP<br className="hidden md:block" /> process — without risk
          </h2>

          <p className="text-lg text-white/70 max-w-xl mb-10 leading-relaxed">
            Experience every step of Maharashtra's Centralised Admission Process. Make decisions, run allotments, and understand the system before the real thing.
          </p>

          {/* Steps preview */}
          <div className="flex flex-col sm:flex-row gap-4 mb-12">
            {steps.map(({ icon: Icon, text }, i) => (
              <div key={i} className="flex items-center gap-3 flex-1 bg-white/5 border border-white/10 rounded-xl p-4 backdrop-blur-sm">
                <div className="w-9 h-9 rounded-lg bg-brand-base/30 flex items-center justify-center shrink-0">
                  <Icon className="w-4 h-4 text-brand-base" />
                </div>
                <p className="text-sm text-white/80 leading-snug">{text}</p>
              </div>
            ))}
          </div>

          <Button
            size="lg"
            onClick={() => setCurrentStep(2)}
            className="bg-gradient-to-r from-brand-base to-teal-500 hover:from-brand-dark hover:to-teal-600 border-0 shadow-xl shadow-brand-base/30 text-white font-bold px-10 py-6 text-lg rounded-2xl gap-3 group"
          >
            Start Simulation
            <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </Button>
        </div>
      </div>

      {/* Info cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { label: 'Realistic', desc: 'Uses real historical cutoffs from 2022-2024', color: 'text-brand-base', bg: 'bg-brand-base/10' },
          { label: 'Category-Aware', desc: 'Strict seat filtering by your category', color: 'text-cyan-400', bg: 'bg-cyan-500/10' },
          { label: 'Zero Risk', desc: 'Practice freely — nothing is submitted', color: 'text-teal-400', bg: 'bg-teal-500/10' },
        ].map((c, i) => (
          <div key={i} className={`glass rounded-xl p-5 border-brand-base/10`}>
            <span className={`text-xs font-bold uppercase tracking-wider ${c.color} ${c.bg} px-2 py-0.5 rounded-full`}>{c.label}</span>
            <p className="text-muted-foreground text-sm mt-3 leading-relaxed">{c.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

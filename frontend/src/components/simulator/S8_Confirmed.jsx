import React from 'react';
import { Button } from '../common/Button';
import { useAppStore } from '../../store/useAppStore';
import { GraduationCap, TrendingUp, RotateCcw, GitBranch, Star, ChevronRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const S8_Confirmed = () => {
  const finalAdmission = useAppStore(state => state.finalAdmission);
  const currentRound = useAppStore(state => state.currentRound);
  const resetSimulator = useAppStore(state => state.resetSimulator);
  const navigate = useNavigate();

  return (
    <div className="space-y-6">
      {/* Hero result card */}
      <div className="relative rounded-3xl overflow-hidden border border-brand-base/20 shadow-2xl shadow-brand-base/10">
        {/* Animated BG */}
        <div className="absolute inset-0 bg-gradient-to-br from-brand-base/20 via-teal-500/10 to-cyan-500/20" />
        <div className="absolute -top-24 -right-24 w-72 h-72 bg-cyan-400/20 rounded-full blur-3xl" />
        <div className="absolute -bottom-16 -left-16 w-56 h-56 bg-brand-base/20 rounded-full blur-3xl" />

        <div className="relative z-10 p-10 md:p-14 text-center">
          {/* Icon */}
          <div className="w-28 h-28 rounded-full bg-brand-base/20 border-2 border-brand-base/30 flex items-center justify-center mx-auto mb-6 shadow-xl shadow-brand-base/20">
            <GraduationCap className="w-14 h-14 text-brand-base" />
          </div>

          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-base/20 border border-brand-base/30 text-brand-base text-sm font-semibold mb-4">
            <Star className="w-3.5 h-3.5" /> Simulation Complete
          </div>

          <h2 className="text-4xl md:text-5xl font-extrabold text-white mb-3 tracking-tight">
            {finalAdmission ? 'Admission Confirmed! 🎓' : 'Simulation Ended'}
          </h2>
          <p className="text-white/60 text-lg mb-10">
            {finalAdmission
              ? `You secured a seat after ${currentRound} round(s) of the CAP process.`
              : 'No seat was allotted across all rounds based on your choices and rank.'}
          </p>

          {finalAdmission ? (
            <div className="max-w-md mx-auto bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-8 text-left mb-10">
              <p className="text-xs font-bold uppercase tracking-widest text-brand-base mb-4">Your Allotted Seat</p>
              <h3 className="text-2xl font-bold text-white mb-1">{finalAdmission.college_name}</h3>
              <div className="flex items-center gap-2 text-brand-base font-semibold text-lg mb-5">
                <GitBranch className="w-4 h-4" /> {finalAdmission.branch_name}
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm">
                {[
                  { label: 'Category', value: finalAdmission.allotted_category },
                  { label: 'Confirmed in Round', value: `Round ${finalAdmission.round}` },
                  { label: 'Preference No.', value: `#${finalAdmission.preference_number}` },
                  { label: 'Allotment Type', value: finalAdmission.preference_number === 1 ? 'Auto-Freeze' : 'Accepted' },
                ].map((item, i) => (
                  <div key={i} className="bg-white/5 border border-white/10 rounded-xl p-3">
                    <div className="text-white/50 text-xs mb-1">{item.label}</div>
                    <div className="text-white font-bold">{item.value}</div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="max-w-sm mx-auto bg-white/5 border border-white/10 rounded-2xl p-6 mb-10 text-white/70">
              <p className="leading-relaxed">Consider increasing your option form coverage, adjusting your percentile target, or applying through spot rounds and institutional quota in the real process.</p>
            </div>
          )}

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              onClick={() => navigate('/predictor')}
              className="gap-2 bg-gradient-to-r from-brand-base to-teal-500 hover:from-brand-dark hover:to-teal-600 border-0 shadow-xl shadow-brand-base/30 px-8 py-5 text-base font-bold rounded-xl"
            >
              <TrendingUp className="w-5 h-5" /> View Cutoff Trends
            </Button>
            <Button
              variant="outline"
              onClick={() => { resetSimulator(); }}
              className="gap-2 border-white/20 bg-white/5 hover:bg-white/10 text-white px-8 py-5 text-base font-bold rounded-xl"
            >
              <RotateCcw className="w-5 h-5" /> Restart Simulator
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppStore } from '../../store/useAppStore';
import { StepIndicator } from '../common/StepIndicator';
import { S1_Welcome } from './S1_Welcome';
import { S2_Profile } from './S2_Profile';
import { S3_Documents } from './S3_Documents';
import { S4_OptionForm } from './S4_OptionForm';
import { S5_Allotment } from './S5_Allotment';
import { S6_Decision } from './S6_Decision';
import { S8_Confirmed } from './S8_Confirmed';
import { Link } from 'react-router-dom';
import { GraduationCap, ArrowLeft, ShieldCheck, Sparkles } from 'lucide-react';

export const SimulatorLayout = () => {
  const currentStep = useAppStore(state => state.currentStep);

  const renderStep = () => {
    switch (currentStep) {
      case 1: return <S1_Welcome />;
      case 2: return <S2_Profile />;
      case 3: return <S3_Documents />;
      case 4: return <S4_OptionForm />;
      case 5: return <S5_Allotment />;
      case 6: return <S6_Decision />;
      case 7: return <S5_Allotment />;
      case 8: return <S8_Confirmed />;
      default: return <S1_Welcome />;
    }
  };

  const stepTitles = {
    1: { title: 'CAP Simulator', sub: 'Practice the full admission cycle safely.' },
    2: { title: 'Candidate Profile', sub: 'Personalize your admission data.' },
    3: { title: 'Document Vault', sub: 'Verify your eligibility markers.' },
    4: { title: 'Option Form', sub: 'Strategize your preference list.' },
    5: { title: 'Allotment Result', sub: 'Round-wise institutional seating.' },
    6: { title: 'Your Decision', sub: 'Freeze, Float, or Slide?' },
    7: { title: 'Next Iteration', sub: 'Refining choices for better seats.' },
    8: { title: 'Outcome Reached', sub: 'Your final admission trajectory.' },
  };

  const { title, sub } = stepTitles[currentStep] || stepTitles[1];

  return (
    <div className="min-h-screen bg-background bg-mesh relative overflow-hidden">
      
      {/* Top Nav Bar */}
      <nav className="border-b border-white/5 bg-background/40 backdrop-blur-2xl sticky top-0 z-50 px-6 py-4">
        <div className="max-w-5xl mx-auto flex justify-between items-center">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-9 h-9 bg-gradient-to-br from-emerald-600 to-teal-600 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/20 group-hover:scale-110 transition-transform">
              <GraduationCap className="text-white w-5 h-5" />
            </div>
            <span className="font-black text-xl text-gradient">GradMap</span>
          </Link>
          <Link to="/predictor">
            <button className="flex items-center gap-2 text-xs font-black uppercase tracking-widest text-muted-foreground hover:text-emerald-400 transition-all">
              <ArrowLeft className="w-4 h-4" /> Predictor
            </button>
          </Link>
        </div>
      </nav>

      <div className="max-w-5xl mx-auto px-6 pt-12 pb-24 relative z-10">
        
        {/* Page header */}
        <motion.div 
          key={currentStep}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12 text-center"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-black uppercase tracking-wider mb-6">
            <ShieldCheck className="w-3 h-3" />
            Secure Environment
          </div>
          <h1 className="text-5xl md:text-6xl font-black tracking-tight text-foreground mb-4">
            {title}
          </h1>
          <p className="text-muted-foreground text-lg font-medium">{sub}</p>
        </motion.div>

        {/* Step indicator card */}
        <div className="glass-morphism rounded-[2.5rem] p-8 mb-12 border-white/5 shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4 opacity-10">
            <Sparkles className="w-12 h-12 text-emerald-400" />
          </div>
          <StepIndicator />
        </div>

        {/* Step content */}
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.4, ease: "circOut" }}
          >
            {renderStep()}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
};

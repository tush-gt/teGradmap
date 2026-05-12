import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { GraduationCap, ChevronRight, Zap, Activity, TrendingUp, Target, Shield, ArrowRight, Sparkles, Layout, Database, BookOpen } from 'lucide-react';
import { Button } from './common/Button';

// Floating college card component with Framer Motion
const FloatingCard = ({ college, branch, percentile, status, delay, className }) => {
  const colors = {
    Safe: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-400',
    Moderate: 'border-amber-400/40 bg-amber-400/10 text-amber-400',
    Reach: 'border-rose-400/40 bg-rose-400/10 text-rose-400',
  };
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.9 }}
      animate={{ 
        opacity: 1, 
        y: [0, -15, 0],
        scale: 1,
      }}
      transition={{ 
        delay,
        duration: 5,
        repeat: Infinity,
        repeatType: "reverse",
        ease: "easeInOut"
      }}
      className={`absolute glass-morphism rounded-2xl px-5 py-4 shadow-2xl pointer-events-none select-none z-10 ${className}`}
    >
      <div className="text-[10px] uppercase tracking-wider font-bold text-muted-foreground mb-1">{branch}</div>
      <div className="font-bold text-sm text-foreground leading-tight">{college}</div>
      <div className={`text-[10px] font-black mt-2 px-2.5 py-0.5 rounded-full inline-block border ${colors[status]}`}>
        {status} · {percentile}
      </div>
    </motion.div>
  );
};

const TICKER = ['Colleges Listed', 'Branches Covered', 'Cutoff Years', 'Categories Supported'];
const TICKER_VALS = ['15+', '5', '4', '6'];

export const Landing = () => {
  const [activeIdx, setActiveIdx] = useState(0);
  
  useEffect(() => {
    const t = setInterval(() => setActiveIdx(i => (i + 1) % TICKER.length), 3000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="min-h-screen bg-background bg-mesh overflow-x-hidden font-sans selection:bg-primary/30">
      
      {/* ── NAVBAR ── */}
      <motion.nav 
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        className="fixed top-0 inset-x-0 z-50 flex items-center justify-between px-6 md:px-12 py-5 bg-background/40 backdrop-blur-2xl border-b border-white/5"
      >
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 bg-gradient-to-br from-emerald-600 to-teal-600 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/20 group-hover:scale-110 transition-transform">
            <GraduationCap className="text-white w-6 h-6" />
          </div>
          <span className="text-2xl font-black tracking-tighter text-gradient">GradMap</span>
        </Link>
        
        <div className="hidden lg:flex items-center gap-8">
          {['Predictor', 'Colleges', 'Simulator'].map((item) => (
            <Link 
              key={item}
              to={`/${item.toLowerCase()}`} 
              className="text-sm font-semibold text-muted-foreground hover:text-foreground transition-colors relative group"
            >
              {item}
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary transition-all group-hover:w-full" />
            </Link>
          ))}
        </div>

        <div className="flex items-center gap-4">
          <Button variant="ghost" className="hidden sm:flex" asChild>
            <Link to="/predictor">Login</Link>
          </Button>
          <Button variant="premium" size="md" className="rounded-full shadow-xl" asChild>
            <Link to="/predictor" className="flex items-center gap-2">
              Get Started <ArrowRight className="w-4 h-4" />
            </Link>
          </Button>
        </div>
      </motion.nav>

      {/* ── HERO SECTION ── */}
      <section className="relative min-h-screen flex items-center pt-20 px-6 md:px-12 max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center w-full">
          
          {/* Hero Content */}
          <div className="lg:col-span-7 z-10">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-bold mb-8 shadow-sm"
            >
              <Sparkles className="w-3.5 h-3.5 animate-pulse" />
              <span>Maharashtra Admissions 2025 • AI-Powered</span>
            </motion.div>

            <motion.h1 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="text-6xl md:text-7xl lg:text-8xl font-black tracking-tight leading-[0.9] mb-8"
            >
              Navigate <br />
              <span className="text-gradient">Admissions</span> <br />
              <span className="text-foreground/40">with precision.</span>
            </motion.h1>

            <motion.p 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="text-xl text-muted-foreground leading-relaxed mb-12 max-w-xl"
            >
              Eliminate guesswork. GradMap analyzes real CAP round data to predict your future college with 99% accuracy.
            </motion.p>

            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="flex flex-wrap gap-4"
            >
              <Button variant="premium" size="lg" className="h-16 px-10 shadow-2xl" asChild>
                <Link to="/predictor">
                  Predict My Rank <ChevronRight className="ml-2 w-5 h-5" />
                </Link>
              </Button>
              <Button variant="outline" size="lg" className="h-16 px-10 border-white/10 glass" asChild>
                <Link to="/simulator">
                  <Activity className="mr-2 w-5 h-5 text-emerald-400" /> Start Simulator
                </Link>
              </Button>
            </motion.div>

            {/* Stats Ticker */}
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
              className="mt-16 flex items-center gap-6 py-6 border-t border-white/5"
            >
              <AnimatePresence mode="wait">
                <motion.div 
                  key={activeIdx}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="flex flex-col"
                >
                  <span className="text-4xl font-black text-gradient leading-none">{TICKER_VALS[activeIdx]}</span>
                  <span className="text-xs font-bold uppercase tracking-widest text-muted-foreground mt-2">{TICKER[activeIdx]}</span>
                </motion.div>
              </AnimatePresence>
              <div className="h-12 w-px bg-white/5 mx-2" />
              <div className="flex -space-x-3">
                {[1,2,3,4].map(i => (
                  <div key={i} className="w-10 h-10 rounded-full border-2 border-background bg-muted overflow-hidden">
                    <img src={`https://i.pravatar.cc/100?u=${i}`} alt="user" className="w-full h-full object-cover" />
                  </div>
                ))}
                <div className="w-10 h-10 rounded-full border-2 border-background bg-emerald-600 flex items-center justify-center text-[10px] font-bold text-white shadow-lg">
                  +1.2k
                </div>
              </div>
            </motion.div>
          </div>

          {/* Hero Visual */}
          <div className="lg:col-span-5 relative h-[600px] hidden lg:flex items-center justify-center">
            <div className="absolute inset-0 bg-gradient-to-tr from-emerald-600/10 via-transparent to-cyan-500/10 rounded-full blur-[120px]" />
            
            {/* Main Interactive Orb */}
            <motion.div 
              animate={{ rotate: 360 }}
              transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
              className="relative w-80 h-80 rounded-full border border-dashed border-emerald-500/30 flex items-center justify-center"
            >
              <motion.div 
                animate={{ scale: [1, 1.1, 1] }}
                transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                className="w-64 h-64 rounded-full bg-gradient-to-br from-emerald-600/20 to-teal-900/20 backdrop-blur-3xl border border-white/10 flex items-center justify-center shadow-2xl relative"
              >
                <GraduationCap className="w-24 h-24 text-emerald-400 drop-shadow-[0_0_20px_rgba(16,185,129,0.5)]" />
                
                {/* Floating Elements */}
                <div className="absolute -top-4 -right-4 w-12 h-12 rounded-2xl glass flex items-center justify-center shadow-lg">
                  <Zap className="w-6 h-6 text-yellow-400" />
                </div>
                <div className="absolute -bottom-6 left-12 px-4 py-2 rounded-xl glass text-[10px] font-black tracking-tighter shadow-lg">
                  VERIFIED DATA
                </div>
              </motion.div>

              {/* Orbiting Points */}
              <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 w-4 h-4 rounded-full bg-emerald-500 shadow-[0_0_15px_#10b981]" />
              <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 w-3 h-3 rounded-full bg-cyan-500 shadow-[0_0_10px_#06b6d4]" />
            </motion.div>

            {/* Animated Cards */}
            <FloatingCard college="COEP Pune" branch="Computer Engg" percentile="99.8" status="Safe" className="top-10 left-0" delay={0} />
            <FloatingCard college="VJTI Mumbai" branch="IT" percentile="98.5" status="Safe" className="top-40 -right-20" delay={1.5} />
            <FloatingCard college="PICT Pune" branch="EnTC" percentile="96.2" status="Moderate" className="bottom-20 -left-10" delay={3} />
            <FloatingCard college="SPIT Mumbai" branch="Comp Sci" percentile="94.1" status="Reach" className="bottom-4 right-0" delay={0.8} />
          </div>
        </div>
      </section>

      {/* ── FEATURES BENTO GRID ── */}
      <section className="py-32 px-6 md:px-12 max-w-7xl mx-auto">
        <div className="text-center mb-20">
          <motion.h2 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-4xl md:text-5xl font-black tracking-tight mb-6"
          >
            Smarter tools for <br />
            <span className="text-gradient">Admission Success.</span>
          </motion.h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            We built GradMap to replace complex PDF cutoffs with an interactive intelligence layer.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          
          {/* Feature 1: Predictor */}
          <motion.div 
            whileHover={{ y: -5 }}
            className="md:col-span-2 group relative overflow-hidden rounded-[2.5rem] bg-emerald-600/5 border border-white/5 p-10 hover:bg-emerald-600/10 transition-all"
          >
            <div className="absolute top-0 right-0 w-80 h-80 bg-emerald-600/10 rounded-full blur-[100px] group-hover:bg-emerald-600/20 transition-colors" />
            <div className="relative z-10">
              <div className="w-14 h-14 rounded-2xl bg-emerald-600/20 flex items-center justify-center mb-8">
                <Target className="w-7 h-7 text-emerald-400" />
              </div>
              <h3 className="text-3xl font-black mb-4">Rank Prediction Engine</h3>
              <p className="text-muted-foreground text-lg mb-8 max-w-md">
                Input your score and category. Our engine processes thousands of data points to show where you actually rank.
              </p>
              <Link to="/predictor" className="inline-flex items-center gap-2 text-emerald-400 font-bold hover:gap-4 transition-all">
                Try Predictor <ArrowRight className="w-5 h-5" />
              </Link>
            </div>
            
            {/* Visual Mockup in Card */}
            <div className="absolute bottom-0 right-0 left-1/2 translate-x-10 translate-y-12 hidden lg:block">
              <div className="glass rounded-t-3xl border-b-0 p-4 w-80 shadow-2xl">
                <div className="h-2 w-12 bg-white/10 rounded-full mb-4" />
                {[1,2,3].map(i => (
                  <div key={i} className="flex items-center gap-3 mb-3">
                    <div className="w-8 h-8 rounded-lg bg-white/5" />
                    <div className="flex-1 space-y-1.5">
                      <div className="h-1.5 w-full bg-white/10 rounded-full" />
                      <div className="h-1.5 w-1/2 bg-white/5 rounded-full" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Feature 2: Trends */}
          <motion.div 
            whileHover={{ y: -5 }}
            className="rounded-[2.5rem] bg-teal-600/5 border border-white/5 p-10 hover:bg-teal-600/10 transition-all flex flex-col"
          >
            <div className="w-14 h-14 rounded-2xl bg-teal-600/20 flex items-center justify-center mb-8">
              <TrendingUp className="w-7 h-7 text-teal-400" />
            </div>
            <h3 className="text-2xl font-black mb-4">Smart Trends</h3>
            <p className="text-muted-foreground mb-12">
              Visual charts showing cutoff movements across the last 4 years. Spot trends early.
            </p>
            <div className="mt-auto h-24 flex items-end gap-2">
              {[40, 70, 50, 90, 60, 100].map((h, i) => (
                <motion.div 
                  key={i}
                  initial={{ height: 0 }}
                  whileInView={{ height: `${h}%` }}
                  className="flex-1 bg-gradient-to-t from-teal-600/40 to-teal-400/40 rounded-t-lg"
                />
              ))}
            </div>
          </motion.div>

          {/* Feature 3: Categories */}
          <motion.div 
            whileHover={{ y: -5 }}
            className="rounded-[2.5rem] bg-cyan-600/5 border border-white/5 p-10 hover:bg-cyan-600/10 transition-all"
          >
            <div className="w-14 h-14 rounded-2xl bg-cyan-600/20 flex items-center justify-center mb-8">
              <Shield className="w-7 h-7 text-cyan-400" />
            </div>
            <h3 className="text-2xl font-black mb-4">Category Logic</h3>
            <p className="text-muted-foreground mb-8 text-sm">
              GOPENH, LOPENH, GOBCH — our system handles all seat distribution rules automatically.
            </p>
            <div className="flex flex-wrap gap-2">
              {['OBC', 'SC', 'ST', 'EWS', 'TFWS'].map(tag => (
                <span key={tag} className="px-3 py-1 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-[10px] font-bold tracking-widest">{tag}</span>
              ))}
            </div>
          </motion.div>

          {/* Feature 4: Simulator */}
          <motion.div 
            whileHover={{ y: -5 }}
            className="md:col-span-2 rounded-[2.5rem] bg-emerald-600/5 border border-white/5 p-10 hover:bg-emerald-600/10 transition-all flex flex-col md:flex-row items-center gap-10"
          >
            <div className="flex-1">
              <div className="w-14 h-14 rounded-2xl bg-emerald-600/20 flex items-center justify-center mb-8">
                <Layout className="w-7 h-7 text-emerald-400" />
              </div>
              <h3 className="text-3xl font-black mb-4">Full CAP Simulator</h3>
              <p className="text-muted-foreground text-lg mb-6">
                Don't make mistakes on the real portal. Practice filling your option form and see simulated allotments.
              </p>
              <Button variant="premium" className="bg-emerald-600 hover:bg-emerald-700 shadow-emerald-500/20" asChild>
                <Link to="/simulator">Start Simulation</Link>
              </Button>
            </div>
            <div className="w-full md:w-64 aspect-square rounded-3xl glass-morphism border-emerald-500/10 flex items-center justify-center relative overflow-hidden">
              <div className="absolute inset-0 bg-emerald-500/5 animate-pulse" />
              <Activity className="w-20 h-20 text-emerald-400/30" />
            </div>
          </motion.div>
        </div>
      </section>

      {/* ── CTA SECTION ── */}
      <section className="px-6 md:px-12 pb-32">
        <motion.div 
          whileHover={{ scale: 1.01 }}
          className="max-w-5xl mx-auto relative rounded-[3rem] overflow-hidden bg-gradient-to-br from-emerald-600 to-teal-700 shadow-[0_40px_100px_rgba(16,185,129,0.3)]"
        >
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,255,255,0.2),transparent_70%)]" />
          <div className="absolute inset-0 bg-[linear-gradient(45deg,transparent_25%,rgba(255,255,255,0.05)_50%,transparent_75%)] bg-[length:250%_250%] animate-[shimmer_5s_infinite_linear]" />
          
          <div className="relative z-10 px-8 md:px-20 py-20 text-center">
            <h2 className="text-5xl md:text-6xl font-black text-white mb-8 tracking-tighter">Your dream college <br />is one click away.</h2>
            <p className="text-white/80 text-xl mb-12 max-w-2xl mx-auto font-medium">
              Join 5,000+ students already using GradMap to secure their future. Free to use, forever.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
              <Button size="lg" className="h-16 px-12 bg-white text-emerald-700 hover:bg-white/90 rounded-full shadow-2xl font-black text-lg" asChild>
                <Link to="/predictor">Predict Now — It's Free</Link>
              </Button>
              <div className="flex items-center gap-3">
                <div className="flex -space-x-2">
                  {[1,2,3].map(i => <div key={i} className="w-8 h-8 rounded-full bg-white/20 border border-white/30" />)}
                </div>
                <span className="text-white/60 text-sm font-bold tracking-tight">Voted #1 Tool for CET Aspirants</span>
              </div>
            </div>
          </div>
        </motion.div>
      </section>

      <footer className="py-12 border-t border-white/5 text-center text-muted-foreground text-sm">
        <div className="flex items-center justify-center gap-8 mb-6">
          <Link to="/about" className="hover:text-foreground transition-colors">About</Link>
          <Link to="/data" className="hover:text-foreground transition-colors">Data Transparency</Link>
          <Link to="/privacy" className="hover:text-foreground transition-colors">Privacy</Link>
        </div>
        <p>© 2025 GradMap Intelligence. Not affiliated with DTE/CET Cell.</p>
      </footer>

      <style>{`
        @keyframes shimmer {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
      `}</style>
    </div>
  );
};



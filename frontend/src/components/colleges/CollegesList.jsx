import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '../../services/api';
import { GraduationCap, Search, MapPin, Building2, ChevronRight, ArrowLeft, Filter, Sparkles } from 'lucide-react';
import { Button } from '../common/Button';
import { Input } from '../common/Input';

const TYPE_COLORS = {
  'Government Autonomous': 'bg-emerald-500/15 text-emerald-400 border-emerald-500/20',
  'Government': 'bg-emerald-500/15 text-emerald-400 border-emerald-400/20',
  'Government Aided': 'bg-teal-500/15 text-teal-400 border-teal-400/20',
  'Un-Aided Autonomous': 'bg-cyan-500/15 text-cyan-400 border-cyan-400/20',
  'Un-Aided': 'bg-amber-500/15 text-amber-400 border-amber-400/20',
};

const DISTRICTS = ['All', 'Mumbai', 'Pune', 'Nashik', 'Nagpur', 'Aurangabad', 'Amravati', 'Satara', 'Jalgaon', 'Buldhana'];

export const CollegesList = () => {
  const [colleges, setColleges] = useState([]);
  const [search, setSearch] = useState('');
  const [district, setDistrict] = useState('All');
  const navigate = useNavigate();

  useEffect(() => {
    api.getColleges().then(setColleges);
  }, []);

  const filtered = colleges.filter(c => {
    const matchSearch = c.name.toLowerCase().includes(search.toLowerCase());
    const matchDistrict = district === 'All' || c.district === district;
    return matchSearch && matchDistrict;
  });

  return (
    <div className="min-h-screen bg-background bg-mesh relative overflow-hidden selection:bg-emerald-500/30">
      
      {/* Navbar */}
      <motion.nav 
        initial={{ y: -50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="border-b border-white/5 bg-background/40 backdrop-blur-2xl sticky top-0 z-50 px-6 py-4"
      >
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-9 h-9 bg-gradient-to-br from-emerald-600 to-teal-600 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/20 group-hover:scale-110 transition-transform">
              <GraduationCap className="text-white w-5 h-5" />
            </div>
            <span className="font-black text-xl text-gradient">GradMap</span>
          </Link>
          <div className="flex items-center gap-6">
            <Link to="/predictor" className="text-xs font-black uppercase tracking-widest text-muted-foreground hover:text-emerald-400 transition-colors">Predictor</Link>
            <Link to="/simulator" className="text-xs font-black uppercase tracking-widest text-muted-foreground hover:text-emerald-400 transition-colors">Simulator</Link>
          </div>
        </div>
      </motion.nav>

      <div className="max-w-7xl mx-auto px-6 pt-12 pb-24 relative z-10">
        
        {/* Header */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12"
        >
          <Link to="/" className="inline-flex items-center gap-2 text-xs font-black uppercase tracking-widest text-muted-foreground hover:text-emerald-400 mb-8 transition-colors">
            <ArrowLeft className="w-4 h-4" /> Back
          </Link>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-black uppercase tracking-wider mb-6">
            <Building2 className="w-3.5 h-3.5" />
            {colleges.length} MH Engineering Colleges
          </div>
          <h1 className="text-5xl md:text-6xl font-black tracking-tight mb-4 text-foreground">
            College <span className="text-gradient">Explorer</span>
          </h1>
          <p className="text-muted-foreground text-lg max-w-2xl font-medium">
            Browse through Maharashtra's premier engineering institutions. Click any card to dive deep into historical trends.
          </p>
        </motion.div>

        {/* Search + Filter bar */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-morphism rounded-[2.5rem] border-white/5 p-6 mb-12 flex flex-col lg:flex-row gap-6 shadow-2xl"
        >
          <div className="relative flex-1">
            <Search className="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground/50" />
            <Input
              type="text"
              placeholder="Search by institution name..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="pl-14 h-14 bg-background/40 border-white/10 font-bold"
            />
          </div>
          <div className="flex gap-2 flex-wrap items-center">
            <div className="flex items-center gap-2 text-muted-foreground mr-2">
              <Filter className="w-4 h-4" />
              <span className="text-[10px] font-black uppercase tracking-widest">Regions:</span>
            </div>
            {DISTRICTS.map(d => (
              <button
                key={d}
                onClick={() => setDistrict(d)}
                className={`px-5 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all border ${
                  district === d
                    ? 'bg-emerald-600 text-white border-emerald-600 shadow-xl shadow-emerald-500/20'
                    : 'border-white/5 bg-white/5 text-muted-foreground hover:bg-white/10 hover:border-white/20'
                }`}
              >
                {d}
              </button>
            ))}
          </div>
        </motion.div>

        {/* College grid */}
        <AnimatePresence mode="popLayout">
          {filtered.length === 0 ? (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="glass-morphism rounded-[3rem] p-24 text-center border-white/5"
            >
              <Building2 className="w-20 h-20 mx-auto mb-6 opacity-10 text-emerald-400" />
              <h3 className="text-2xl font-black mb-2 uppercase tracking-tight">No institutions found</h3>
              <p className="text-muted-foreground font-medium">Try adjusting your filters or search query.</p>
            </motion.div>
          ) : (
            <motion.div 
              layout
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8"
            >
              {filtered.map((college, idx) => (
                <motion.div
                  layout
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: idx * 0.02 }}
                  key={college.code}
                  onClick={() => navigate(`/colleges/${college.code}`)}
                  className="group glass-morphism rounded-[2.5rem] border-white/5 p-8 cursor-pointer hover:border-emerald-500/30 hover:-translate-y-2 transition-all duration-500 relative overflow-hidden shadow-xl"
                >
                  <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-opacity">
                    <Sparkles className="w-16 h-16 text-emerald-400" />
                  </div>

                  {/* Header Badge */}
                  <div className="flex justify-between items-start mb-8">
                    <div className="px-3 py-1 rounded-lg bg-white/5 border border-white/10 text-[10px] font-black tracking-widest text-muted-foreground/60 uppercase">
                      Code: {college.code}
                    </div>
                    <div className={`px-3 py-1 rounded-full text-[9px] font-black uppercase tracking-widest border ${TYPE_COLORS[college.type] || 'bg-white/5 text-muted-foreground border-white/10'}`}>
                      {college.type.split(' ')[0]}
                    </div>
                  </div>

                  {/* Body Content */}
                  <div className="flex items-start gap-5 mb-8">
                    <div className="w-16 h-16 rounded-[1.25rem] bg-emerald-600/10 flex items-center justify-center shrink-0 group-hover:bg-emerald-600/20 transition-all duration-500 group-hover:scale-110">
                      <GraduationCap className="w-8 h-8 text-emerald-400" />
                    </div>
                    <div>
                      <h3 className="font-black text-lg leading-[1.2] text-foreground group-hover:text-emerald-400 transition-colors mb-2">
                        {college.name}
                      </h3>
                      <div className="flex items-center gap-2 text-muted-foreground text-xs font-bold uppercase tracking-tight">
                        <MapPin className="w-3.5 h-3.5 text-emerald-500/60" />
                        {college.district}
                      </div>
                    </div>
                  </div>

                  {/* Footer Info */}
                  <div className="flex items-center justify-between pt-6 border-t border-white/5">
                    <div className="text-[10px] font-black text-muted-foreground uppercase tracking-widest">
                      2022 — 2025 Trends
                    </div>
                    <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-emerald-400 group-hover:gap-4 transition-all">
                      Details <ChevronRight className="w-4 h-4" />
                    </div>
                  </div>
                </motion.div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};



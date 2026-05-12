import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { TrendChartModal } from './TrendChartModal';
import { api, CATEGORIES, BRANCHES } from '../../services/api';
import { Link, useNavigate } from 'react-router-dom';
import { GraduationCap, Loader2, ChevronRight, Target, TrendingUp, Activity, Search, Sparkles, Filter, Info, MapPin } from 'lucide-react';
import { cn } from '../../utils/cn';
import { Button } from '../common/Button';
import { Input } from '../common/Input';

const DISTRICTS = ['Mumbai', 'Pune', 'Nashik', 'Nagpur', 'Aurangabad', 'Amravati', 'Satara', 'Jalgaon', 'Buldhana'];

export const PredictorLayout = () => {
  const navigate = useNavigate();
  const [percentile, setPercentile] = useState('');
  const [category, setCategory] = useState('GOPENH');
  const [district, setDistrict] = useState('');
  const [branch, setBranch] = useState('');
  const [results, setResults] = useState([]);
  const [isPredicting, setIsPredicting] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [trendModal, setTrendModal] = useState({ isOpen: false });

  const handlePredict = async () => {
    if (!percentile) return;
    setIsPredicting(true);
    setHasSearched(true);
    try {
      const res = await api.predict({
        percentile: parseFloat(percentile),
        category,
        districts: district ? [district] : [],
        branches: branch ? [branch] : [],
      });
      setResults(res);
    } finally {
      setIsPredicting(false);
    }
  };

  const safe = results.filter(r => r.status === 'Safe');
  const moderate = results.filter(r => r.status === 'Moderate');
  const reach = results.filter(r => r.status === 'Reach');

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
          <div className="flex items-center gap-4">
            <Link to="/simulator">
              <Button variant="ghost" size="sm" className="hidden sm:flex gap-2">
                CAP Simulator <ChevronRight className="w-4 h-4" />
              </Button>
            </Link>
          </div>
        </div>
      </motion.nav>

      <div className="max-w-7xl mx-auto px-6 pt-12 pb-24 relative z-10">
        
        {/* Header Section */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-black uppercase tracking-wider mb-6">
            <Sparkles className="w-3 h-3" />
            Predictor Engine v2.0
          </div>
          <h1 className="text-5xl md:text-6xl font-black tracking-tight mb-4 text-foreground">
            Smart <span className="text-gradient">Predictor</span>
          </h1>
          <p className="text-muted-foreground text-lg max-w-2xl font-medium">
            Discover your admission path with AI-driven insights based on real round-by-round historical data.
          </p>
        </motion.div>

        {/* Search Panel Card */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="glass-morphism rounded-[2.5rem] border-white/5 p-8 md:p-10 mb-12 shadow-2xl relative overflow-hidden group"
        >
          <div className="absolute -top-24 -right-24 w-64 h-64 bg-emerald-600/10 rounded-full blur-[100px] group-hover:bg-emerald-600/20 transition-all duration-500" />
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10 relative z-10">
            {/* Percentile Input */}
            <div>
              <label className="text-[10px] font-black text-muted-foreground uppercase tracking-widest block mb-3 ml-1">Percentile Score</label>
              <Input
                type="number"
                step="0.01"
                min="0"
                max="100"
                value={percentile}
                onChange={e => setPercentile(e.target.value)}
                placeholder="00.00"
                className="text-2xl font-black h-14 bg-background/40 border-white/10"
              />
            </div>

            {/* Category Select */}
            <div>
              <label className="text-[10px] font-black text-muted-foreground uppercase tracking-widest block mb-3 ml-1">Admission Category</label>
              <div className="relative">
                <select
                  value={category}
                  onChange={e => setCategory(e.target.value)}
                  className="w-full h-14 px-5 rounded-xl border border-white/10 bg-background/40 text-sm font-bold focus:outline-none focus:ring-2 focus:ring-emerald-500 appearance-none transition-all cursor-pointer hover:border-emerald-500/50"
                >
                  {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
                <Filter className="absolute right-5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
              </div>
            </div>

            {/* District Select */}
            <div>
              <label className="text-[10px] font-black text-muted-foreground uppercase tracking-widest block mb-3 ml-1">Target District</label>
              <div className="relative">
                <select
                  value={district}
                  onChange={e => setDistrict(e.target.value)}
                  className="w-full h-14 px-5 rounded-xl border border-white/10 bg-background/40 text-sm font-bold focus:outline-none focus:ring-2 focus:ring-emerald-500 appearance-none transition-all cursor-pointer hover:border-emerald-500/50"
                >
                  <option value="">Maharashtra (All)</option>
                  {DISTRICTS.map(d => <option key={d} value={d}>{d}</option>)}
                </select>
                <MapPin className="absolute right-5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
              </div>
            </div>

            {/* Branch Select */}
            <div>
              <label className="text-[10px] font-black text-muted-foreground uppercase tracking-widest block mb-3 ml-1">Study Branch</label>
              <div className="relative">
                <select
                  value={branch}
                  onChange={e => setBranch(e.target.value)}
                  className="w-full h-14 px-5 rounded-xl border border-white/10 bg-background/40 text-sm font-bold focus:outline-none focus:ring-2 focus:ring-emerald-500 appearance-none transition-all cursor-pointer hover:border-emerald-500/50"
                >
                  <option value="">Any Engineering Branch</option>
                  {BRANCHES.map(b => <option key={b} value={b}>{b}</option>)}
                </select>
                <ChevronRight className="absolute right-5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground rotate-90 pointer-events-none" />
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between flex-wrap gap-6 pt-6 border-t border-white/5">
            <div className="flex items-center gap-3 text-muted-foreground bg-white/5 px-4 py-2 rounded-full border border-white/5">
              <Info className="w-4 h-4 text-emerald-400" />
              <p className="text-[11px] font-bold">
                Showing <span className="text-emerald-400">{category}</span> seats only
              </p>
            </div>
            <Button
              onClick={handlePredict}
              disabled={!percentile || isPredicting}
              variant="premium"
              size="lg"
              className="min-w-[240px] h-14"
            >
              {isPredicting ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : <Search className="w-5 h-5 mr-2" />}
              {isPredicting ? 'Analyzing Data...' : 'Run Prediction'}
            </Button>
          </div>
        </motion.div>

        {/* Results Sections */}
        <AnimatePresence mode="wait">
          {hasSearched && !isPredicting ? (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-10"
            >
              {/* Stat Overview */}
              {results.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {[
                    { label: 'Safe', count: safe.length, color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', icon: Target },
                    { label: 'Moderate', count: moderate.length, color: 'text-amber-400', bg: 'bg-amber-400/10', border: 'border-amber-400/20', icon: Activity },
                    { label: 'Reach', count: reach.length, color: 'text-rose-400', bg: 'bg-rose-500/10', border: 'border-rose-500/20', icon: TrendingUp },
                  ].map(s => (
                    <motion.div 
                      key={s.label} 
                      whileHover={{ y: -5 }}
                      className={`glass-morphism rounded-3xl p-6 border ${s.border} flex items-center gap-6 shadow-xl`}
                    >
                      <div className={`w-14 h-14 rounded-2xl ${s.bg} flex items-center justify-center`}>
                        <s.icon className={`w-7 h-7 ${s.color}`} />
                      </div>
                      <div>
                        <div className={`text-3xl font-black ${s.color}`}>{s.count}</div>
                        <div className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">{s.label} Options</div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}

              {/* Table Result */}
              <div className="glass-morphism rounded-[2.5rem] border-white/5 overflow-hidden shadow-2xl">
                <div className="px-8 py-6 border-b border-white/5 bg-white/5 flex justify-between items-center">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-xl bg-emerald-600/20 flex items-center justify-center">
                      <GraduationCap className="w-5 h-5 text-emerald-400" />
                    </div>
                    <div>
                      <h3 className="font-black text-sm">Prediction Results</h3>
                      <p className="text-[10px] text-muted-foreground uppercase font-black tracking-tighter">Analysis based on {results.length} institutional mappings</p>
                    </div>
                  </div>
                  <div className="px-4 py-1.5 rounded-full bg-emerald-600/20 text-emerald-400 text-[10px] font-black uppercase tracking-widest border border-emerald-600/30">
                    2024 Context
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="bg-white/3 border-b border-white/5">
                        <th className="text-left px-8 py-5 text-[10px] font-black text-muted-foreground uppercase tracking-widest">Institution & Course</th>
                        <th className="text-left px-6 py-5 text-[10px] font-black text-muted-foreground uppercase tracking-widest hidden md:table-cell">Region</th>
                        <th className="text-left px-6 py-5 text-[10px] font-black text-muted-foreground uppercase tracking-widest">Cutoff Delta</th>
                        <th className="text-left px-6 py-5 text-[10px] font-black text-muted-foreground uppercase tracking-widest">Status</th>
                        <th className="text-right px-8 py-5 text-[10px] font-black text-muted-foreground uppercase tracking-widest">Insight</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                      {results.map((item, idx) => (
                        <motion.tr 
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: idx * 0.05 }}
                          key={idx} 
                          className="hover:bg-white/5 transition-colors group cursor-pointer"
                          onClick={() => navigate(`/colleges/${item.college_code}`)}
                        >
                          <td className="px-8 py-6">
                            <div className="font-black text-foreground group-hover:text-emerald-400 transition-colors">{item.college_name}</div>
                            <div className="text-xs text-muted-foreground font-medium mt-1 uppercase tracking-tight">{item.branch_name}</div>
                          </td>
                          <td className="px-6 py-6 hidden md:table-cell">
                            <div className="flex items-center gap-2 text-muted-foreground text-xs font-bold">
                              <MapPin className="w-3 h-3" /> {item.district}
                            </div>
                          </td>
                          <td className="px-6 py-6">
                            <div className="font-black text-lg">{item.cutoff}</div>
                            <div className={cn("text-[10px] font-black uppercase tracking-tighter mt-1",
                              item.status === 'Safe' ? "text-emerald-400" : item.status === 'Moderate' ? "text-amber-400" : "text-rose-400"
                            )}>
                              {item.delta > 0 ? 'Surplus ' : 'Shortfall '}{Math.abs(item.delta)}
                            </div>
                          </td>
                          <td className="px-6 py-6">
                            <span className={cn(
                              "px-3 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-widest border",
                              item.status === 'Safe' ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400" :
                                item.status === 'Moderate' ? "bg-amber-500/10 border-amber-500/20 text-amber-400" :
                                  "bg-rose-500/10 border-rose-500/20 text-rose-400"
                            )}>
                              {item.status}
                            </span>
                          </td>
                          <td className="px-8 py-6 text-right">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                setTrendModal({ isOpen: true, instituteCode: item.college_code, branchName: item.branch_name, category: item.category });
                              }}
                              className="text-emerald-400 hover:bg-emerald-400/10 group/btn"
                            >
                              <TrendingUp className="w-4 h-4 mr-2 group-hover/btn:scale-110 transition-transform" />
                              Trends
                            </Button>
                          </td>
                        </motion.tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </motion.div>
          ) : !hasSearched ? (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-12"
            >
              {[
                { icon: Target, title: 'Safe Zone', desc: 'Predicting colleges where you exceed cutoffs comfortably.', color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
                { icon: Activity, title: 'Edge Case', desc: 'Analyzing border-line options with highest volatility.', color: 'text-amber-400', bg: 'bg-amber-400/10' },
                { icon: TrendingUp, title: 'Dream Target', desc: 'Identifying reach institutions for spot rounds.', color: 'text-rose-400', bg: 'bg-rose-500/10' },
              ].map((c, i) => (
                <motion.div 
                  key={i} 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 + (i * 0.1) }}
                  className="glass-morphism rounded-[2rem] p-10 border-white/5 text-center flex flex-col items-center group hover:border-emerald-500/30 transition-all duration-500 shadow-xl"
                >
                  <div className={`w-16 h-16 ${c.bg} rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-500`}>
                    <c.icon className={`w-8 h-8 ${c.color}`} />
                  </div>
                  <h3 className="font-black text-xl mb-3">{c.title}</h3>
                  <p className="text-muted-foreground text-sm font-medium leading-relaxed">{c.desc}</p>
                </motion.div>
              ))}
            </motion.div>
          ) : null}
        </AnimatePresence>
      </div>

      <TrendChartModal
        {...trendModal}
        onClose={() => setTrendModal(prev => ({ ...prev, isOpen: false }))}
      />
    </div>
  );
};



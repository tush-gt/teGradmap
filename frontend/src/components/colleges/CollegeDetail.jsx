import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '../../services/api';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, AreaChart, Area
} from 'recharts';
import { GraduationCap, MapPin, ArrowLeft, TrendingUp, BarChart2, PieChart as PieIcon, Loader2, Sparkles, Building2, Calendar, Users, Award, Filter } from 'lucide-react';
import { cn } from '../../utils/cn';
import { Button } from '../common/Button';

const BRANCHES = [
  'Computer Engineering',
  'Information Technology',
  'Electronics and Telecommunication',
  'Mechanical Engineering',
  'Civil Engineering',
];
const CATEGORIES = ['GOPENH', 'LOPENH', 'GOBCH', 'GOSC'];
const CHART_TABS = ['Trends', 'Distribution', 'Comparison'];

const COLORS = ['#10b981', '#059669', '#06b6d4', '#34d399', '#f59e0b'];
const ROUND_COLORS = { round1: '#10b981', round2: '#059669', round3: '#06b6d4' };

const mockCollegeDetails = {
  '3012': { established: 1887, affiliation: 'Mumbai University', intake: 960, naac: 'A++', location: 'Matunga, Mumbai' },
  '6006': { established: 1854, affiliation: 'Pune University', intake: 840, naac: 'A++', location: 'Shivajinagar, Pune' },
  '3009': { established: 1933, affiliation: 'Mumbai University', intake: 480, naac: 'A', location: 'Matunga, Mumbai' },
  '3014': { established: 1957, affiliation: 'Mumbai University', intake: 540, naac: 'A', location: 'Andheri, Mumbai' },
  '6271': { established: 1983, affiliation: 'Pune University', intake: 720, naac: 'A', location: 'Dhankawadi, Pune' },
};
const defaultDetails = { established: 1980, affiliation: 'Regional University', intake: 480, naac: 'B+', location: 'Maharashtra' };

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="glass-morphism rounded-2xl px-5 py-4 shadow-2xl border border-white/10 backdrop-blur-2xl">
        <p className="font-black text-[10px] uppercase tracking-widest text-emerald-400 mb-3">{label} Analysis</p>
        <div className="space-y-2">
          {payload.map((entry, i) => (
            <div key={i} className="flex items-center justify-between gap-6">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full" style={{ background: entry.color }} />
                <span className="text-[11px] font-bold text-muted-foreground">{entry.name}:</span>
              </div>
              <span className="font-black text-sm text-foreground">{entry.value?.toFixed(2)}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }
  return null;
};

export const CollegeDetail = () => {
  const { code } = useParams();
  const [college, setCollege] = useState(null);
  const [selectedBranch, setSelectedBranch] = useState(BRANCHES[0]);
  const [selectedCategory, setSelectedCategory] = useState('GOPENH');
  const [trendData, setTrendData] = useState([]);
  const [branchCompareData, setBranchCompareData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeChart, setActiveChart] = useState('Trends');

  useEffect(() => {
    api.getColleges().then(data => {
      const found = data.find(c => c.code === code);
      setCollege(found || null);
    });
  }, [code]);

  useEffect(() => {
    if (!code || !selectedBranch || !selectedCategory) return;
    setLoading(true);
    api.getTrends({ institute_code: code, branch_name: selectedBranch, category: selectedCategory })
      .then(data => {
        setTrendData(data);
        setLoading(false);
      });
  }, [code, selectedBranch, selectedCategory]);

  useEffect(() => {
    if (!code) return;
    Promise.all(
      BRANCHES.map(b =>
        api.getTrends({ institute_code: code, branch_name: b, category: selectedCategory })
          .then(data => {
            const yr2024 = data.find(d => d.year === '2024');
            return { branch: b.replace('Electronics and Telecommunication', 'ENTC').replace('Computer Engineering', 'CS').replace('Information Technology', 'IT').replace('Mechanical Engineering', 'Mech').replace('Civil Engineering', 'Civil'), cutoff: yr2024?.round1 || 0 };
          })
      )
    ).then(setBranchCompareData);
  }, [code, selectedCategory]);

  const details = mockCollegeDetails[code] || defaultDetails;

  const pieData = trendData.map(d => ({
    name: d.year,
    value: d.round1 || 0,
  })).filter(d => d.value > 0);

  if (!college && !loading) {
    return (
      <div className="min-h-screen bg-background bg-mesh flex items-center justify-center p-6">
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center glass-morphism p-12 rounded-[3rem] border-white/5"
        >
          <Building2 className="w-20 h-20 mx-auto mb-6 opacity-10 text-emerald-400" />
          <h2 className="text-3xl font-black mb-6">Institution Not Found</h2>
          <Link to="/colleges">
            <Button variant="premium">Return to Explorer</Button>
          </Link>
        </motion.div>
      </div>
    );
  }

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
          <Link to="/colleges">
            <Button variant="ghost" size="sm" className="gap-2">
              <ArrowLeft className="w-4 h-4" /> Explorer
            </Button>
          </Link>
        </div>
      </motion.nav>

      <div className="max-w-7xl mx-auto px-6 pt-12 pb-24 relative z-10">

        {/* Hero Section */}
        {college && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="relative rounded-[3rem] overflow-hidden border border-white/5 shadow-2xl mb-12 group"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-emerald-600/20 via-teal-600/10 to-cyan-500/10" />
            <div className="absolute -top-24 -right-24 w-96 h-96 bg-emerald-600/10 rounded-full blur-[120px] group-hover:bg-emerald-600/20 transition-all duration-700" />
            
            <div className="relative z-10 p-10 md:p-14">
              <div className="flex flex-col md:flex-row gap-10 items-start">
                <motion.div 
                  whileHover={{ scale: 1.05 }}
                  className="w-28 h-28 rounded-[2rem] bg-emerald-600/20 border border-emerald-500/30 flex items-center justify-center shrink-0 shadow-2xl"
                >
                  <GraduationCap className="w-12 h-12 text-emerald-400" />
                </motion.div>
                
                <div className="flex-1">
                  <div className="flex flex-wrap gap-3 mb-6">
                    <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground bg-white/5 px-3 py-1 rounded-lg border border-white/10">ID: {college.code}</span>
                    <span className="text-[10px] font-black uppercase tracking-widest px-3 py-1 rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">{college.type}</span>
                  </div>
                  
                  <h1 className="text-4xl md:text-5xl font-black text-foreground mb-4 tracking-tight leading-[1.1]">{college.name}</h1>
                  
                  <div className="flex items-center gap-2 text-muted-foreground font-bold text-sm mb-10">
                    <MapPin className="w-4 h-4 text-emerald-500" /> {details.location}
                  </div>

                  {/* Stats Grid */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {[
                      { label: 'Established', value: details.established, icon: Calendar },
                      { label: 'Annual Intake', value: details.intake, icon: Users },
                      { label: 'NAAC Rating', value: details.naac, icon: Award },
                      { label: 'University', value: details.affiliation.split(' ')[0], icon: Building2 },
                    ].map((s, i) => (
                      <div key={i} className="glass-morphism bg-white/5 border border-white/5 rounded-2xl p-4 flex items-center gap-4">
                        <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center">
                          <s.icon className="w-5 h-5 text-emerald-400/70" />
                        </div>
                        <div>
                          <div className="text-[9px] font-black uppercase tracking-widest text-muted-foreground mb-1">{s.label}</div>
                          <div className="font-black text-sm text-foreground">{s.value}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Data Controls */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-12">
          {/* Branch Picker */}
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="lg:col-span-2 glass-morphism rounded-[2.5rem] border-white/5 p-8"
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="w-8 h-8 rounded-lg bg-emerald-600/20 flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-emerald-400" />
              </div>
              <h3 className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Select Department</h3>
            </div>
            <div className="flex flex-wrap gap-2">
              {BRANCHES.map(b => (
                <button
                  key={b}
                  onClick={() => setSelectedBranch(b)}
                  className={cn(
                    "px-4 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all border",
                    selectedBranch === b
                      ? "bg-emerald-600 text-white border-emerald-600 shadow-xl shadow-emerald-500/20 scale-105"
                      : "border-white/5 bg-white/5 text-muted-foreground hover:bg-white/10 hover:border-white/20"
                  )}
                >
                  {b.replace('Engineering', '').replace('and Telecommunication', '')}
                </button>
              ))}
            </div>
          </motion.div>

          {/* Category Picker */}
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="glass-morphism rounded-[2.5rem] border-white/5 p-8"
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="w-8 h-8 rounded-lg bg-teal-600/20 flex items-center justify-center">
                <Filter className="w-4 h-4 text-teal-400" />
              </div>
              <h3 className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Admission Group</h3>
            </div>
            <div className="flex flex-wrap gap-2">
              {CATEGORIES.map(c => (
                <button
                  key={c}
                  onClick={() => setSelectedCategory(c)}
                  className={cn(
                    "px-4 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all border",
                    selectedCategory === c
                      ? "bg-teal-600 text-white border-teal-600 shadow-xl shadow-teal-500/20"
                      : "border-white/5 bg-white/5 text-muted-foreground hover:bg-white/10 hover:border-white/20"
                  )}
                >
                  {c}
                </button>
              ))}
            </div>
          </motion.div>
        </div>

        {/* Charts Section */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass-morphism rounded-[3rem] border-white/5 p-10 md:p-14 shadow-2xl relative overflow-hidden"
        >
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-8 mb-12">
            <div>
              <h2 className="text-3xl font-black mb-3">
                {activeChart === 'Comparison' ? 'Branch Volatility' : 'Cutoff Intelligence'}
              </h2>
              <p className="text-muted-foreground font-medium max-w-xl">
                {activeChart === 'Comparison' 
                  ? 'Competitive analysis across departments for the 2024 cycle.' 
                  : `Visualizing admission thresholds for ${selectedBranch.split(' ')[0]} department.`}
              </p>
            </div>
            
            <div className="flex gap-2 p-1.5 rounded-2xl bg-white/5 border border-white/5">
              {CHART_TABS.map(tab => {
                const icons = { Trends: BarChart2, Distribution: PieIcon, Comparison: TrendingUp };
                const Icon = icons[tab];
                return (
                  <button
                    key={tab}
                    onClick={() => setActiveChart(tab)}
                    className={cn(
                      "flex items-center gap-2 px-4 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all",
                      activeChart === tab
                        ? "bg-emerald-600 text-white shadow-lg"
                        : "text-muted-foreground hover:text-foreground"
                    )}
                  >
                    <Icon className="w-3.5 h-3.5" /> {tab}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="h-[400px] w-full">
            {loading ? (
              <div className="h-full flex flex-col items-center justify-center gap-6">
                <Loader2 className="w-12 h-12 animate-spin text-emerald-500" />
                <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Parsing historical data...</p>
              </div>
            ) : (
              <AnimatePresence mode="wait">
                <motion.div
                  key={activeChart}
                  initial={{ opacity: 0, scale: 0.98 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.98 }}
                  transition={{ duration: 0.3 }}
                  className="h-full"
                >
                  {activeChart === 'Trends' && (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={trendData} margin={{ top: 20, right: 0, left: -20, bottom: 0 }}>
                        <defs>
                          <linearGradient id="colorR1" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor={ROUND_COLORS.round1} stopOpacity={0.8}/>
                            <stop offset="95%" stopColor={ROUND_COLORS.round1} stopOpacity={0.1}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
                        <XAxis 
                          dataKey="year" 
                          axisLine={false} 
                          tickLine={false} 
                          tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11, fontWeight: 900 }} 
                        />
                        <YAxis 
                          domain={['dataMin - 1', 'dataMax + 0.5']} 
                          axisLine={false} 
                          tickLine={false} 
                          tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11, fontWeight: 900 }} 
                        />
                        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
                        <Legend iconType="circle" wrapperStyle={{ paddingTop: 30, fontSize: 10, fontWeight: 900, textTransform: 'uppercase', letterSpacing: 1 }} />
                        <Bar dataKey="round1" name="Round 01" fill="url(#colorR1)" radius={[10, 10, 0, 0]} />
                        <Bar dataKey="round2" name="Round 02" fill={ROUND_COLORS.round2} radius={[10, 10, 0, 0]} opacity={0.4} />
                        <Bar dataKey="round3" name="Round 03" fill={ROUND_COLORS.round3} radius={[10, 10, 0, 0]} opacity={0.2} />
                      </BarChart>
                    </ResponsiveContainer>
                  )}

                  {activeChart === 'Distribution' && (
                    <div className="flex flex-col md:flex-row items-center h-full gap-12">
                      <div className="flex-1 w-full h-full">
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie
                              data={pieData}
                              cx="50%"
                              cy="50%"
                              outerRadius="90%"
                              innerRadius="65%"
                              paddingAngle={8}
                              dataKey="value"
                              stroke="transparent"
                            >
                              {pieData.map((_, i) => (
                                <Cell key={i} fill={COLORS[i % COLORS.length]} />
                              ))}
                            </Pie>
                            <Tooltip content={<CustomTooltip />} />
                          </PieChart>
                        </ResponsiveContainer>
                      </div>
                      <div className="flex flex-col gap-6 min-w-[240px] glass-morphism p-8 rounded-3xl border-white/5">
                        <h4 className="text-[10px] font-black uppercase tracking-widest text-emerald-400">Cyclical Analysis</h4>
                        {pieData.map((d, i) => (
                          <div key={i} className="flex items-center justify-between group">
                            <div className="flex items-center gap-3">
                              <span className="w-2.5 h-2.5 rounded-full" style={{ background: COLORS[i % COLORS.length] }} />
                              <span className="text-xs font-black text-muted-foreground uppercase">{d.name} Peak</span>
                            </div>
                            <span className="font-black text-sm">{d.value?.toFixed(2)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {activeChart === 'Comparison' && (
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={branchCompareData} margin={{ top: 20, right: 0, left: -20, bottom: 0 }}>
                        <defs>
                          <linearGradient id="colorCutoff" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor={COLORS[0]} stopOpacity={0.3}/>
                            <stop offset="95%" stopColor={COLORS[0]} stopOpacity={0}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
                        <XAxis 
                          dataKey="branch" 
                          axisLine={false} 
                          tickLine={false} 
                          tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10, fontWeight: 900 }} 
                        />
                        <YAxis 
                          domain={['dataMin - 5', 'dataMax + 1']} 
                          axisLine={false} 
                          tickLine={false} 
                          tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10, fontWeight: 900 }} 
                        />
                        <Tooltip content={<CustomTooltip />} />
                        <Area 
                          type="monotone" 
                          dataKey="cutoff" 
                          name="2024 Threshold" 
                          stroke={COLORS[0]} 
                          strokeWidth={4} 
                          fill="url(#colorCutoff)" 
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  )}
                </motion.div>
              </AnimatePresence>
            )}
          </div>
        </motion.div>

        {/* Action Bar */}
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="mt-12 flex justify-center"
        >
          <Link to="/predictor">
            <Button variant="premium" size="lg" className="px-12 h-16 text-lg">
              Check Admission Eligibility
            </Button>
          </Link>
        </motion.div>
      </div>
    </div>
  );
};

import React, { useEffect, useState, useMemo, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine, Label } from 'recharts';
import { X, Loader2, TrendingUp, Calendar, Target, Activity, AlertCircle } from 'lucide-react';
import { api } from '../../services/api';
import { cn } from '../../utils/cn';

/**
 * TrendChartModal Component
 * 
 * FINAL ARCHITECTURAL FIX FOR RECHARTS IN MODALS:
 * 
 * 1. DIMENSION TRACKING: Instead of relying on ResponsiveContainer's internal measurement
 *    (which is prone to -1/0 errors in animated flex parents), we use a manual ResizeObserver.
 * 2. ABSOLUTE INJECTION: We pass measured width/height directly to the LineChart.
 * 3. RENDER GATING: The chart is physically withheld from the DOM until width > 0.
 */
export const TrendChartModal = ({ isOpen, onClose, instituteCode, branchName, category, userPercentile, status, collegeName }) => {
  const [data, setData] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isStable, setIsStable] = useState(false);
  
  const containerRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  // 1. Fetch data
  useEffect(() => {
    if (isOpen && instituteCode && branchName && category) {
      setLoading(true);
      api.getTrends({ institute_code: instituteCode, branch_name: branchName, category })
        .then(res => {
          // res is now { trends: [...], summary: {...} }
          setData(res.trends || []);
          setSummary(res.summary || null);
          setLoading(false);
        })
        .catch(err => {
          console.error("Trends Fetch Error:", err);
          setLoading(false);
        });
    }
  }, [isOpen, instituteCode, branchName, category]);

  // 2. Track dimensions manually
  useEffect(() => {
    if (!isStable || !containerRef.current) return;

    const observer = new ResizeObserver((entries) => {
      if (entries[0]) {
        const { width, height } = entries[0].contentRect;
        // Only update if we have meaningful dimensions to avoid flicker
        if (width > 0 && height > 0) {
          setDimensions({ width, height });
        }
      }
    });

    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, [isStable]);

  // 3. Reset state on close
  useEffect(() => {
    if (!isOpen) {
      setIsStable(false);
      setDimensions({ width: 0, height: 0 });
    }
  }, [isOpen]);

  const handleAnimationComplete = () => {
    // Wait for the modal to be visually and structurally stable
    setTimeout(() => setIsStable(true), 150);
  };

  // 4. Guaranteed Render Logic
  const chartContent = useMemo(() => {
    if (!isStable || loading || data.length === 0 || dimensions.width === 0) return null;

    return (
      <LineChart 
        width={dimensions.width} 
        height={dimensions.height} 
        data={data} 
        margin={{ top: 20, right: 30, left: -20, bottom: 0 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
        <XAxis 
          dataKey="year" 
          axisLine={false}
          tickLine={false}
          tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11, fontWeight: 900 }} 
        />
        <YAxis 
          domain={['auto', 'auto']} 
          axisLine={false}
          tickLine={false}
          tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11, fontWeight: 900 }}
        />
        <Tooltip 
          contentStyle={{ 
            backgroundColor: 'rgba(15, 12, 25, 0.95)',
            backdropFilter: 'blur(16px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '24px',
            padding: '16px',
            boxShadow: '0 10px 40px rgba(0,0,0,0.5)'
          }}
          itemStyle={{ fontSize: '11px', fontWeight: 900, textTransform: 'uppercase' }}
          labelStyle={{ marginBottom: '8px', color: '#34d399', fontWeight: 900 }}
        />
        <Legend iconType="circle" wrapperStyle={{ paddingTop: 30, fontSize: 10, fontWeight: 900, textTransform: 'uppercase', letterSpacing: 1 }} />
        
        {userPercentile && (
          <ReferenceLine y={userPercentile} stroke="#10b981" strokeDasharray="5 5" strokeWidth={2}>
            <Label value={`Your Score: ${userPercentile}`} position="insideBottomRight" fill="#10b981" fontSize={10} fontWeight={900} offset={10} />
          </ReferenceLine>
        )}

        <Line type="monotone" dataKey="round1" name="Round 1" stroke="#10b981" strokeWidth={4} dot={{ r: 6, strokeWidth: 0 }} activeDot={{ r: 10 }} isAnimationActive={false} />
        <Line type="monotone" dataKey="round2" name="Round 2" stroke="#059669" strokeWidth={3} dot={{ r: 4, strokeWidth: 0 }} opacity={0.6} isAnimationActive={false} />
        <Line type="monotone" dataKey="round3" name="Round 3" stroke="#06b6d4" strokeWidth={3} dot={{ r: 4, strokeWidth: 0 }} opacity={0.4} isAnimationActive={false} />
      </LineChart>
    );
  }, [isStable, loading, data, userPercentile, dimensions]);

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-background/80 backdrop-blur-md"
          />
          
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            onAnimationComplete={handleAnimationComplete}
            className="glass-morphism w-full max-w-6xl rounded-[2.5rem] shadow-2xl border border-white/5 overflow-hidden relative z-10"
          >
            <div className="flex items-center justify-between p-8 md:p-10 border-b border-white/5 bg-white/5">
              <div className="flex items-center gap-5">
                <div className="w-12 h-12 rounded-2xl bg-emerald-600/20 flex items-center justify-center shadow-lg shadow-emerald-500/10">
                  <TrendingUp className="w-6 h-6 text-emerald-400" />
                </div>
                <div>
                  <h3 className="text-xl font-black text-white max-w-md truncate">{collegeName || 'Cutoff Intelligence'}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-[10px] font-black uppercase tracking-widest px-2 py-0.5 bg-emerald-500/20 text-emerald-400 rounded-md border border-emerald-500/30">{category}</span>
                    <span className="text-[11px] font-bold text-muted-foreground truncate">{branchName}</span>
                  </div>
                </div>
              </div>

              {summary && (
                <div className="flex gap-4">
                   <div className="hidden md:flex flex-col items-end">
                    <span className="text-[9px] font-black uppercase tracking-tighter text-muted-foreground/60 mb-1">Volatility Index</span>
                    <div className={cn(
                      "px-3 py-1 rounded-full text-[10px] font-black border",
                      summary.volatility > 1.0 ? "bg-rose-500/10 text-rose-400 border-rose-500/20" : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                    )}>
                      σ {summary.volatility}
                    </div>
                  </div>
                  <div className="flex flex-col items-end">
                    <span className="text-[9px] font-black uppercase tracking-tighter text-muted-foreground/60 mb-1">Market Trend</span>
                    <div className={cn(
                      "px-3 py-1 rounded-full text-[10px] font-black border flex items-center gap-1",
                      summary.trend_direction === 'RISING' ? "bg-rose-500/10 text-rose-400 border-rose-500/20" : 
                      summary.trend_direction === 'FALLING' ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" :
                      "bg-blue-500/10 text-blue-400 border-blue-500/20"
                    )}>
                      {summary.trend_direction === 'RISING' ? <TrendingUp className="w-3 h-3" /> : <Activity className="w-3 h-3" />}
                      {summary.trend_direction}
                    </div>
                  </div>
                </div>
              )}
              <button onClick={onClose} className="p-3 hover:bg-white/5 rounded-2xl transition-all group">
                <X className="w-6 h-6 text-muted-foreground group-hover:text-white group-hover:rotate-90 transition-all duration-300" />
              </button>
            </div>
            
            <div className="p-8 md:p-10">
              {/* This container's dimensions are tracked by ResizeObserver */}
              <div ref={containerRef} className="h-[400px] w-full relative flex items-center justify-center bg-white/[0.02] rounded-[2rem] border border-white/5">
                {loading && (
                  <div className="flex flex-col items-center justify-center gap-6">
                    <Loader2 className="w-12 h-12 animate-spin text-emerald-500" />
                    <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Synthesizing Historical Records...</p>
                  </div>
                )}

                {!loading && data.length > 0 && chartContent}

                {!loading && data.length > 0 && dimensions.width === 0 && (
                  <div className="flex flex-col items-center gap-3">
                    <Loader2 className="w-8 h-8 animate-spin text-emerald-500/30" />
                    <span className="text-[9px] font-black uppercase tracking-widest text-muted-foreground/40">Calibrating Viewport...</span>
                  </div>
                )}

                {!loading && data.length === 0 && (
                  <div className="text-center p-12">
                    <Calendar className="w-16 h-16 text-white/5 mx-auto mb-4" />
                    <p className="text-muted-foreground font-black text-sm uppercase tracking-tight">No historical trends available for this selection.</p>
                  </div>
                )}
              </div>
            </div>
            
            {!loading && data.length > 0 && status && (
              <div className="px-10 pb-10">
                <div className={cn(
                  "rounded-3xl p-6 border flex flex-col md:flex-row items-start md:items-center gap-6",
                  status === 'Safe' ? 'bg-emerald-500/5 border-emerald-500/20' :
                  status === 'Moderate' ? 'bg-amber-500/5 border-amber-500/20' :
                  'bg-rose-500/5 border-rose-500/20'
                )}>
                  <div className={cn(
                    "w-12 h-12 rounded-2xl flex items-center justify-center shrink-0",
                    status === 'Safe' ? 'bg-emerald-500/20 text-emerald-400' :
                    status === 'Moderate' ? 'bg-amber-500/20 text-amber-400' :
                    'bg-rose-500/20 text-rose-400'
                  )}>
                    {status === 'Safe' ? <Target className="w-6 h-6" /> : status === 'Moderate' ? <Activity className="w-6 h-6" /> : <AlertCircle className="w-6 h-6" />}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Recommendation:</span>
                      <span className={cn(
                        "text-[10px] font-black uppercase tracking-widest",
                        status === 'Safe' ? 'text-emerald-400' : status === 'Moderate' ? 'text-amber-400' : 'text-rose-400'
                      )}>{status} Option</span>
                    </div>
                    <p className="text-sm font-bold text-foreground leading-relaxed">
                      {status === 'Safe' && `Your percentile (${userPercentile}) is safely above the historical trend. This institution is a high-probability safety option for your rank.`}
                      {status === 'Moderate' && `Your percentile (${userPercentile}) is very close to the historical cutoffs. This is a competitive target where admission depends on this year's volatility.`}
                      {status === 'Reach' && `Your percentile (${userPercentile}) is below the historical cutoffs. This is an ambitious dream college; consider it for CAP Round 3 or Spot Rounds.`}
                    </p>
                  </div>
                </div>
              </div>
            )}
            
            <div className="px-10 py-6 bg-white/3 border-t border-white/5 flex items-center justify-between text-[10px] font-black uppercase tracking-widest text-muted-foreground/40">
              <span>Predictive Analysis Alpha v2.0</span>
              <span className="text-emerald-400/50">Historical Reference Only</span>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};



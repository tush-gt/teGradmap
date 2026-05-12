import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { X, Loader2, TrendingUp, Calendar } from 'lucide-react';
import { api } from '../../services/api';
import { cn } from '../../utils/cn';

export const TrendChartModal = ({ isOpen, onClose, instituteCode, branchName, category }) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && instituteCode && branchName && category) {
      setLoading(true);
      api.getTrends({ institute_code: instituteCode, branch_name: branchName, category })
        .then(res => {
          setData(res);
          setLoading(false);
        });
    }
  }, [isOpen, instituteCode, branchName, category]);

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
            className="glass-morphism w-full max-w-4xl rounded-[2.5rem] shadow-2xl border border-white/5 overflow-hidden relative z-10"
          >
            <div className="flex items-center justify-between p-8 md:p-10 border-b border-white/5 bg-white/5">
              <div className="flex items-center gap-5">
                <div className="w-12 h-12 rounded-2xl bg-emerald-600/20 flex items-center justify-center">
                  <TrendingUp className="w-6 h-6 text-emerald-400" />
                </div>
                <div>
                  <h3 className="text-2xl font-black text-foreground">Cutoff Intelligence</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-[10px] font-black uppercase tracking-widest px-2 py-0.5 bg-emerald-500/20 text-emerald-400 rounded-md border border-emerald-500/30">{category}</span>
                    <span className="text-[11px] font-bold text-muted-foreground">{branchName}</span>
                  </div>
                </div>
              </div>
              <button 
                onClick={onClose}
                className="p-3 hover:bg-white/5 rounded-2xl transition-all group"
              >
                <X className="w-6 h-6 text-muted-foreground group-hover:text-foreground group-hover:rotate-90 transition-all duration-300" />
              </button>
            </div>
            
            <div className="p-8 md:p-10 h-[450px]">
              {loading ? (
                <div className="h-full flex flex-col items-center justify-center gap-6">
                  <Loader2 className="w-12 h-12 animate-spin text-emerald-500" />
                  <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Synthesizing 2022-2024 Records...</p>
                </div>
              ) : data.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={data} margin={{ top: 20, right: 30, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
                    <XAxis 
                      dataKey="year" 
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11, fontWeight: 900 }} 
                    />
                    <YAxis 
                      domain={['dataMin - 1', 'dataMax + 1']} 
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11, fontWeight: 900 }}
                    />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: 'rgba(15, 12, 25, 0.9)',
                        backdropFilter: 'blur(16px)',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                        borderRadius: '24px',
                        padding: '16px'
                      }}
                      itemStyle={{ fontSize: '11px', fontWeight: 900, textTransform: 'uppercase' }}
                      labelStyle={{ marginBottom: '8px', color: '#34d399', fontWeight: 900 }}
                    />
                    <Legend iconType="circle" wrapperStyle={{ paddingTop: 30, fontSize: 10, fontWeight: 900, textTransform: 'uppercase', letterSpacing: 1 }} />
                    <Line type="monotone" dataKey="round1" name="Round 1" stroke="#10b981" strokeWidth={4} dot={{ r: 6, strokeWidth: 0 }} activeDot={{ r: 10 }} />
                    <Line type="monotone" dataKey="round2" name="Round 2" stroke="#059669" strokeWidth={3} dot={{ r: 4, strokeWidth: 0 }} opacity={0.6} />
                    <Line type="monotone" dataKey="round3" name="Round 3" stroke="#06b6d4" strokeWidth={3} dot={{ r: 4, strokeWidth: 0 }} opacity={0.4} />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-center">
                  <Calendar className="w-16 h-16 text-white/5 mb-4" />
                  <p className="text-muted-foreground font-bold">No historical trend data exists for this parameters.</p>
                </div>
              )}
            </div>
            
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



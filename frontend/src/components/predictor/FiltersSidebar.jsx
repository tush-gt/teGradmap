import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../common/Card';
import { Select } from '../common/Select';
import { Button } from '../common/Button';
import { Filter, RotateCcw } from 'lucide-react';

export const FiltersSidebar = ({ filters, onFilterChange, onReset }) => {
  return (
    <Card className="w-full glass sticky top-6 border-white/5 shadow-2xl overflow-hidden group">
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-500 to-teal-500" />
      
      <CardHeader className="pb-4">
        <CardTitle className="text-sm font-black uppercase tracking-[0.2em] flex justify-between items-center text-foreground/80">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-emerald-400" />
            Control Panel
          </div>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={onReset}
            className="h-8 px-2 text-[10px] font-black uppercase tracking-widest text-emerald-400 hover:bg-emerald-500/10"
          >
            <RotateCcw className="w-3 h-3 mr-1" /> Reset
          </Button>
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-8">
        {/* College Type */}
        <div>
          <label className="block text-[10px] font-black uppercase tracking-widest mb-4 text-muted-foreground/60">Institution Type</label>
          <div className="space-y-3">
            {['Government', 'Un-Aided'].map(type => (
              <label key={type} className="flex items-center gap-3 text-xs font-bold cursor-pointer group/label">
                <div className="relative flex items-center justify-center">
                  <input 
                    type="checkbox" 
                    checked={filters.types?.includes(type)}
                    onChange={(e) => {
                      const next = e.target.checked 
                        ? [...(filters.types || []), type]
                        : (filters.types || []).filter(t => t !== type);
                      onFilterChange('types', next);
                    }}
                    className="peer appearance-none w-5 h-5 rounded-md border-2 border-white/10 bg-white/5 checked:bg-emerald-500 checked:border-emerald-500 transition-all cursor-pointer" 
                  />
                  <div className="absolute opacity-0 peer-checked:opacity-100 transition-opacity pointer-events-none">
                    <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="4">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                </div>
                <span className="text-muted-foreground group-hover/label:text-foreground transition-colors">{type}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Admission Round */}
        <div>
          <label className="block text-[10px] font-black uppercase tracking-widest mb-3 text-muted-foreground/60">CAP Round</label>
          <Select 
            value={filters.round} 
            onChange={(e) => onFilterChange('round', parseInt(e.target.value))}
            className="h-11 bg-background/40 border-white/10 text-xs font-bold focus:ring-emerald-500/40"
          >
            <option value="1">Round 1 (Initial)</option>
            <option value="2">Round 2 (Intermediate)</option>
            <option value="3">Round 3 (Final)</option>
          </Select>
        </div>

        {/* Cutoff Year */}
        <div>
          <label className="block text-[10px] font-black uppercase tracking-widest mb-3 text-muted-foreground/60">Data Baseline</label>
          <Select 
            value={filters.year} 
            onChange={(e) => onFilterChange('year', e.target.value)}
            className="h-11 bg-background/40 border-white/10 text-xs font-bold focus:ring-emerald-500/40"
          >
            <option value="2024">2024 (Latest)</option>
            <option value="2023">2023</option>
            <option value="2022">2022</option>
          </Select>
          <p className="mt-3 text-[9px] font-medium text-muted-foreground/50 leading-relaxed italic">
            * Older data may not reflect current branch demand surges.
          </p>
        </div>
      </CardContent>
    </Card>
  );
};


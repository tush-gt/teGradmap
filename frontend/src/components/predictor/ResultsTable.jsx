import React, { useState } from 'react';
import { Card, CardContent } from '../common/Card';
import { cn } from '../../utils/cn';
import { LineChart, Line, ResponsiveContainer } from 'recharts';
import { Activity, Building2 } from 'lucide-react';

export const ResultsTable = ({ results, onOpenTrend }) => {
  if (!results || results.length === 0) {
    return (
      <Card className="flex flex-col items-center justify-center p-12 text-center text-muted-foreground glass">
        <Building2 className="w-16 h-16 mb-4 opacity-20" />
        <p className="text-lg">No colleges found matching your criteria.</p>
        <p className="text-sm mt-2">Try adjusting your filters or percentile.</p>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden border-border glass">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-muted/50 border-b border-border">
            <tr>
              <th className="px-6 py-4 font-medium text-muted-foreground whitespace-nowrap">College & Branch</th>
              <th className="px-6 py-4 font-medium text-muted-foreground whitespace-nowrap">District</th>
              <th className="px-6 py-4 font-medium text-muted-foreground whitespace-nowrap">Cutoff ('24)</th>
              <th className="px-6 py-4 font-medium text-muted-foreground whitespace-nowrap">Status</th>
              <th className="px-6 py-4 font-medium text-muted-foreground whitespace-nowrap">Trend</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {results.map((item, idx) => {
              const isSafe = item.status === 'Safe';
              const isMod = item.status === 'Moderate';
              
              // Dummy mini-sparkline data
              const sparkData = [
                { val: item.cutoff - 1.2 },
                { val: item.cutoff - 0.5 },
                { val: item.cutoff + 0.3 },
                { val: item.cutoff }
              ];

              return (
                <tr key={`${item.college_code}-${item.branch_name}-${idx}`} className="hover:bg-muted/20 transition-colors">
                  <td className="px-6 py-4">
                    <div className="font-semibold text-foreground">{item.college_name}</div>
                    <div className="text-muted-foreground mt-1">{item.branch_name}</div>
                  </td>
                  <td className="px-6 py-4 text-muted-foreground">{item.district}</td>
                  <td className="px-6 py-4">
                    <div className="font-medium">{item.cutoff}%</div>
                    <div className={cn(
                      "text-xs mt-1 font-medium",
                      isSafe ? "text-green-500" : isMod ? "text-amber-500" : "text-red-500"
                    )}>
                      {item.delta > 0 ? '+' : ''}{item.delta}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={cn(
                      "inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold",
                      isSafe ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400" : 
                      isMod ? "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400" : 
                      "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400"
                    )}>
                      {item.status} ({Math.round(item.probability)}%)
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <button 
                      onClick={() => onOpenTrend(item.college_code, item.branch_name, item.category)}
                      className="group flex items-center gap-2 hover:bg-muted p-2 rounded-md transition-colors w-[100px] h-[40px]"
                      title="View full trend"
                    >
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={sparkData}>
                          <Line 
                            type="monotone" 
                            dataKey="val" 
                            stroke={isSafe ? "#10b981" : isMod ? "#f59e0b" : "#ef4444"} 
                            strokeWidth={2} 
                            dot={false} 
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
};

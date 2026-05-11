import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '../common/Card';
import { Input } from '../common/Input';
import { Select } from '../common/Select';
import { Button } from '../common/Button';
import { useAppStore } from '../../store/useAppStore';
import { api } from '../../services/api';
import { Loader2 } from 'lucide-react';

export const InputPanel = ({ onResults, isPredicting, setIsPredicting }) => {
  const profile = useAppStore(state => state.profile);
  const updateProfile = useAppStore(state => state.updateProfile);

  const [localPercentile, setLocalPercentile] = useState(profile.percentile);
  const [category, setCategory] = useState(profile.category);
  const [districts, setDistricts] = useState([]);
  const [branches, setBranches] = useState([]);
  const [colleges, setColleges] = useState([]);

  useEffect(() => {
    // Load options once
    api.getColleges().then(data => setColleges(data));
  }, []);

  const uniqueDistricts = [...new Set(colleges.map(c => c.district))].sort();
  const mockBranches = ['Computer Engineering', 'Information Technology', 'Electronics and Telecommunication', 'Mechanical Engineering', 'Civil Engineering'];

  const handlePredict = async () => {
    if (!localPercentile || localPercentile < 0 || localPercentile > 100) return;
    
    setIsPredicting(true);
    // Sync profile state
    updateProfile({ percentile: localPercentile, category });

    try {
      const results = await api.predict({
        percentile: localPercentile,
        category,
        districts,
        branches
      });
      onResults(results);
    } catch (error) {
      console.error(error);
    } finally {
      setIsPredicting(false);
    }
  };

  return (
    <Card className="mb-6 border-brand-light/20 bg-gradient-to-br from-background to-brand-50/10">
      <CardContent className="p-6">
        <div className="flex flex-wrap gap-4 items-end">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium mb-1.5 text-muted-foreground">MHT-CET Percentile</label>
            <Input 
              type="number" 
              step="0.01" 
              placeholder="e.g. 94.50" 
              value={localPercentile}
              onChange={(e) => setLocalPercentile(parseFloat(e.target.value) || '')}
              className="text-lg font-medium"
            />
          </div>
          <div className="flex-1 min-w-[150px]">
            <label className="block text-sm font-medium mb-1.5 text-muted-foreground">Category</label>
            <Select value={category} onChange={e => setCategory(e.target.value)}>
              <option value="GOPENH">GOPENH (Open General)</option>
              <option value="LOPENH">LOPENH (Open Ladies)</option>
              <option value="GOBCH">GOBCH (OBC General)</option>
              <option value="LOBCH">LOBCH (OBC Ladies)</option>
              <option value="GOSC">GOSC (SC General)</option>
              <option value="LOSC">LOSC (SC Ladies)</option>
            </Select>
          </div>
          <div className="flex-1 min-w-[150px]">
            <label className="block text-sm font-medium mb-1.5 text-muted-foreground">Preferred District</label>
            <Select 
              value={districts[0] || ''} 
              onChange={e => setDistricts(e.target.value ? [e.target.value] : [])}
            >
              <option value="">Any District</option>
              {uniqueDistricts.map(d => (
                <option key={d} value={d}>{d}</option>
              ))}
            </Select>
          </div>
          <div className="flex-1 min-w-[180px]">
            <label className="block text-sm font-medium mb-1.5 text-muted-foreground">Preferred Branch</label>
            <Select 
              value={branches[0] || ''} 
              onChange={e => setBranches(e.target.value ? [e.target.value] : [])}
            >
              <option value="">Any Branch</option>
              {mockBranches.map(b => (
                <option key={b} value={b}>{b}</option>
              ))}
            </Select>
          </div>
          <div className="w-full md:w-auto mt-4 md:mt-0">
            <Button 
              size="lg" 
              onClick={handlePredict} 
              disabled={!localPercentile || isPredicting}
              className="w-full md:w-auto shadow-brand-base/20"
            >
              {isPredicting ? <Loader2 className="w-5 h-5 mr-2 animate-spin" /> : null}
              Predict Colleges
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

import React, { useState } from 'react';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { Select } from '../common/Select';
import { TeachTooltip } from '../common/TeachTooltip';
import { useAppStore } from '../../store/useAppStore';
import { CATEGORIES } from '../../services/api';
import { getCategoryMetadata } from '../../utils/normalization';
import { User, ChevronRight, ChevronLeft } from 'lucide-react';

const Field = ({ label, hint, children }) => (
  <div>
    <label className="block text-sm font-semibold mb-1 text-foreground/80">{label}</label>
    {hint && <p className="text-xs text-muted-foreground mb-2">{hint}</p>}
    {children}
  </div>
);

export const S2_Profile = () => {
  const profile = useAppStore(state => state.profile);
  const updateProfile = useAppStore(state => state.updateProfile);
  const setCurrentStep = useAppStore(state => state.setCurrentStep);
  const [local, setLocal] = useState(profile);

  const handleChange = (e) => setLocal(prev => ({ ...prev, [e.target.name]: e.target.value }));

  const handleNext = () => {
    updateProfile(local);
    setCurrentStep(3);
  };

  // Filter categories based on gender
  const filteredCategories = CATEGORIES.filter(cat => {
    const meta = getCategoryMetadata(cat);
    if (local.gender === 'Female') return true; // Females can take General (All) or Female seats
    return meta.gender === 'All'; // Males can only take General (All) seats
  });

  return (
    <div className="space-y-6">
      <TeachTooltip title="Category determines your seats">
        Your category determines which quota seats you can access. Ladies quota seats are only available to female candidates.
      </TeachTooltip>

      <div className="glass rounded-2xl border-brand-base/10 overflow-hidden">
        {/* Card header */}
        <div className="bg-gradient-to-r from-brand-base/10 to-teal-500/5 px-8 py-6 border-b border-border/40 flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-brand-base/20 flex items-center justify-center">
            <User className="w-6 h-6 text-brand-base" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-foreground">Candidate Profile</h2>
            <p className="text-sm text-muted-foreground">This will personalise seat eligibility and allotment.</p>
          </div>
        </div>

        <div className="p-8 grid grid-cols-1 sm:grid-cols-2 gap-6">
          <Field label="MHT-CET Percentile" hint="Enter your exact percentile up to 2 decimal places.">
            <Input
              type="number"
              step="0.01"
              min="0"
              max="100"
              name="percentile"
              value={local.percentile}
              onChange={handleChange}
              placeholder="e.g. 94.52"
              className="text-lg font-semibold h-12 border-brand-base/20 focus-visible:ring-brand-base/40"
            />
          </Field>

          <Field label="Gender">
            <Select name="gender" value={local.gender} onChange={handleChange} className="h-12 border-brand-base/20 focus-visible:ring-brand-base/40">
              <option value="Male">Male</option>
              <option value="Female">Female (eligible for Ladies quota)</option>
            </Select>
          </Field>

          <Field label="Category" hint="Only categories matching your gender are shown.">
            <Select name="category" value={local.category} onChange={handleChange} className="h-12 border-brand-base/20 focus-visible:ring-brand-base/40">
              {filteredCategories.map(cat => (
                <option key={cat} value={cat}>{cat} — {getCategoryMetadata(cat).seat_pool}</option>
              ))}
            </Select>
          </Field>

          <Field label="Home University">
            <Select name="home_university" value={local.home_university} onChange={handleChange} className="h-12 border-brand-base/20 focus-visible:ring-brand-base/40">
              <option value="Pune">Savitribai Phule Pune University</option>
              <option value="Mumbai">University of Mumbai</option>
              <option value="Aurangabad">Dr. B.A.M. University, Aurangabad</option>
              <option value="Nagpur">RTMN University, Nagpur</option>
            </Select>
          </Field>

          <Field label="Domicile Status">
            <Select name="domicile" value={local.domicile} onChange={handleChange} className="h-12 border-brand-base/20 focus-visible:ring-brand-base/40">
              <option value="Maharashtra">Maharashtra Domicile</option>
              <option value="Outside">Outside Maharashtra</option>
            </Select>
          </Field>
        </div>

        {/* Footer */}
        <div className="px-8 py-5 border-t border-border/40 bg-muted/10 flex justify-between items-center">
          <Button variant="ghost" onClick={() => setCurrentStep(1)} className="gap-2">
            <ChevronLeft className="w-4 h-4" /> Back
          </Button>
          <Button
            onClick={handleNext}
            disabled={!local.percentile}
            className="bg-gradient-to-r from-brand-base to-teal-500 hover:from-brand-dark hover:to-teal-600 border-0 shadow-lg shadow-brand-base/20 gap-2 px-8"
          >
            Save & Continue <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};


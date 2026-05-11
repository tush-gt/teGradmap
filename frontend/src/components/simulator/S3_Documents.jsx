import React from 'react';
import { Button } from '../common/Button';
import { TeachTooltip } from '../common/TeachTooltip';
import { useAppStore } from '../../store/useAppStore';
import { Check, AlertCircle, FileCheck, ChevronLeft, ChevronRight, ShieldCheck } from 'lucide-react';
import { cn } from '../../utils/cn';

export const S3_Documents = () => {
  const profile = useAppStore(state => state.profile);
  const documentsChecked = useAppStore(state => state.documentsChecked);
  const setDocumentChecked = useAppStore(state => state.setDocumentChecked);
  const setCurrentStep = useAppStore(state => state.setCurrentStep);

  const docs = [
    { id: 'ssc', label: 'SSC (Std. X) Mark sheet', desc: 'Original + 2 attested photocopies', mandatory: true },
    { id: 'hsc', label: 'HSC (Std. XII) Mark sheet', desc: 'Original + 2 attested photocopies', mandatory: true },
    { id: 'mhtcet', label: 'MHT-CET Score Card', desc: 'Printout from official MHT-CET portal', mandatory: true },
    { id: 'domicile', label: 'Domicile Certificate', desc: 'Issued by competent authority', mandatory: true },
  ];

  if (profile.category.includes('OBC') || profile.category.includes('SC')) {
    docs.push({ id: 'caste_cert', label: 'Caste Certificate', desc: 'Issued by competent authority', mandatory: true });
    docs.push({ id: 'caste_validity', label: 'Caste Validity Certificate', desc: 'Issued by Caste Scrutiny Committee', mandatory: true });
  }
  if (profile.category.includes('OBC')) {
    docs.push({ id: 'ncl', label: 'Non-Creamy Layer (NCL) Certificate', desc: 'Valid up to 31st March of the admission year', mandatory: true });
  }

  const checkedCount = docs.filter(d => documentsChecked[d.id]).length;
  const allMandatoryChecked = docs.every(d => !d.mandatory || documentsChecked[d.id]);
  const progress = Math.round((checkedCount / docs.length) * 100);

  return (
    <div className="space-y-6">
      <TeachTooltip title="Document Scrutiny">
        In the real portal, documents are verified before seat acceptance. If a category document is invalid, your category reverts to OPEN.
      </TeachTooltip>

      <div className="glass rounded-2xl border-brand-base/10 overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-brand-base/10 to-teal-500/5 px-8 py-6 border-b border-border/40">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-brand-base/20 flex items-center justify-center">
                <FileCheck className="w-6 h-6 text-brand-base" />
              </div>
              <div>
                <h2 className="text-xl font-bold">Document Checklist</h2>
                <p className="text-sm text-muted-foreground">Select all documents you currently possess</p>
              </div>
            </div>
            {/* Progress ring */}
            <div className="text-right">
              <div className={cn(
                "text-3xl font-black tabular-nums",
                progress === 100 ? "text-brand-base" : "text-foreground"
              )}>{progress}%</div>
              <div className="text-xs text-muted-foreground">{checkedCount}/{docs.length} checked</div>
            </div>
          </div>

          {/* Progress bar */}
          <div className="mt-5 h-2 bg-muted/50 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-brand-base to-teal-400 rounded-full transition-all duration-700"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Doc list */}
        <div className="p-6 space-y-3">
          {docs.map(doc => {
            const isChecked = !!documentsChecked[doc.id];
            return (
              <label
                key={doc.id}
                className={cn(
                  "flex items-center gap-4 p-4 rounded-xl border cursor-pointer transition-all duration-200 group",
                  isChecked
                    ? "bg-brand-base/5 border-brand-base/30 shadow-sm shadow-brand-base/10"
                    : "bg-card hover:bg-muted/30 border-border hover:border-brand-base/20"
                )}
              >
                {/* Checkbox */}
                <div className={cn(
                  "w-6 h-6 rounded-md border-2 flex items-center justify-center shrink-0 transition-all duration-200",
                  isChecked ? "bg-brand-base border-brand-base" : "border-border group-hover:border-brand-base/50"
                )}>
                  {isChecked && <Check className="w-3.5 h-3.5 text-white" strokeWidth={3} />}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-sm text-foreground">{doc.label}</div>
                  <div className="text-xs text-muted-foreground mt-0.5">{doc.desc}</div>
                </div>

                {doc.mandatory && (
                  <span className="shrink-0 text-xs font-semibold px-2 py-0.5 rounded-full bg-red-500/10 text-red-500 border border-red-500/20">
                    Required
                  </span>
                )}

                <input
                  type="checkbox"
                  className="hidden"
                  checked={isChecked}
                  onChange={e => setDocumentChecked(doc.id, e.target.checked)}
                />
              </label>
            );
          })}
        </div>

        {/* All checked banner */}
        {allMandatoryChecked && (
          <div className="mx-6 mb-4 p-3 rounded-xl bg-brand-base/10 border border-brand-base/20 flex items-center gap-3 text-brand-base text-sm font-medium">
            <ShieldCheck className="w-5 h-5 shrink-0" />
            All required documents verified! You may proceed.
          </div>
        )}

        {!allMandatoryChecked && (
          <div className="mx-6 mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center gap-3 text-red-500 text-sm">
            <AlertCircle className="w-5 h-5 shrink-0" />
            Check all mandatory documents before proceeding.
          </div>
        )}

        {/* Footer */}
        <div className="px-8 py-5 border-t border-border/40 bg-muted/10 flex justify-between">
          <Button variant="ghost" onClick={() => setCurrentStep(2)} className="gap-2">
            <ChevronLeft className="w-4 h-4" /> Back
          </Button>
          <Button
            onClick={() => setCurrentStep(4)}
            disabled={!allMandatoryChecked}
            className="bg-gradient-to-r from-brand-base to-teal-500 hover:from-brand-dark hover:to-teal-600 border-0 shadow-lg shadow-brand-base/20 gap-2 px-8"
          >
            Confirm Documents <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};

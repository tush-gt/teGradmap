import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '../common/Card';
import { Button } from '../common/Button';
import { TeachTooltip } from '../common/TeachTooltip';
import { useAppStore } from '../../store/useAppStore';
import { api } from '../../services/api';
import { DndContext, closestCenter, KeyboardSensor, PointerSensor, useSensor, useSensors } from '@dnd-kit/core';
import { arrayMove, SortableContext, sortableKeyboardCoordinates, verticalListSortingStrategy, useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { GripVertical, X, ArrowUp, ArrowDown, Lock, AlertCircle, Search as SearchIcon } from 'lucide-react';

const SortableItem = ({ id, option, index, onRemove, onMoveUp, onMoveDown, isFirst, isLast }) => {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div ref={setNodeRef} style={style} className="flex items-center gap-3 p-3 bg-card border rounded-lg mb-2 shadow-sm group">
      <div {...attributes} {...listeners} className="cursor-grab touch-none p-1 text-muted-foreground hover:text-foreground">
        <GripVertical className="w-5 h-5" />
      </div>
      <div className="w-8 h-8 rounded-full bg-brand-light/20 text-brand-base flex items-center justify-center font-bold text-sm shrink-0">
        {index + 1}
      </div>
      <div className="flex-1 min-w-0">
        <h4 className="font-semibold text-sm truncate">{option.college_name}</h4>
        <p className="text-xs text-muted-foreground truncate">{option.branch_name}</p>
      </div>
      
      {/* Mobile touch fallbacks */}
      <div className="flex md:hidden flex-col gap-1">
        <button disabled={isFirst} onClick={() => onMoveUp(index)} className="p-1 disabled:opacity-30"><ArrowUp className="w-4 h-4"/></button>
        <button disabled={isLast} onClick={() => onMoveDown(index)} className="p-1 disabled:opacity-30"><ArrowDown className="w-4 h-4"/></button>
      </div>

      <button onClick={() => onRemove(index)} className="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-md transition-colors opacity-0 group-hover:opacity-100 focus:opacity-100">
        <X className="w-4 h-4" />
      </button>
    </div>
  );
};

export const S4_OptionForm = () => {
  const profile = useAppStore(state => state.profile);
  const optionForm = useAppStore(state => state.optionForm);
  const setOptionForm = useAppStore(state => state.setOptionForm);
  const setCurrentStep = useAppStore(state => state.setCurrentStep);

  const [availableOptions, setAvailableOptions] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  useEffect(() => {
    setIsLoading(true);
    // Fetch real available colleges for this category using a very high percentile to see many options
    api.predict({ percentile: 100, category: profile.category }).then(data => {
      setAvailableOptions(data);
      setIsLoading(false);
    });
  }, [profile.category]);

  const handleDragEnd = (event) => {
    const { active, over } = event;
    if (active.id !== over.id) {
      const oldIndex = optionForm.findIndex(item => item.id === active.id);
      const newIndex = optionForm.findIndex(item => item.id === over.id);
      setOptionForm(arrayMove(optionForm, oldIndex, newIndex));
    }
  };

  const handleAdd = (option) => {
    if (optionForm.length >= 300) return;
    const newOption = { ...option, id: `${option.college_code}-${option.branch_name}-${Date.now()}` };
    setOptionForm([...optionForm, newOption]);
  };

  const handleRemove = (index) => {
    const newForm = [...optionForm];
    newForm.splice(index, 1);
    setOptionForm(newForm);
  };

  const moveItem = (index, direction) => {
    if ((direction === -1 && index === 0) || (direction === 1 && index === optionForm.length - 1)) return;
    const newForm = arrayMove(optionForm, index, index + direction);
    setOptionForm(newForm);
  };

  const handleLock = () => {
    setShowConfirmModal(false);
    setCurrentStep(5);
  };

  const filteredAvailable = availableOptions.filter(opt => 
    opt.college_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    opt.branch_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">
      <TeachTooltip title="The Option Form">
        This is the most critical step. You can add up to 300 choices. Order matters immensely! The algorithm checks your choices from top to bottom. 
        <br/><br/><strong className="text-red-600 dark:text-red-400">Golden Rule:</strong> If you are allotted your Preference #1, it is AUTO-FROZEN. You MUST take admission and cannot participate in further rounds.
      </TeachTooltip>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Available Options Selection */}
        <Card className="glass h-[600px] flex flex-col">
          <div className="p-4 border-b border-border bg-muted/30">
            <h3 className="font-semibold text-lg">Available Choices</h3>
            <p className="text-sm text-muted-foreground mb-4">Filtered for {profile.category}</p>
            
            <div className="relative">
              <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search college or branch..."
                className="w-full pl-9 pr-4 py-2 bg-background/50 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-base/40"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
          <div className="p-4 overflow-y-auto flex-1 space-y-2">
            {isLoading ? (
              <div className="h-full flex items-center justify-center text-muted-foreground">
                Loading options...
              </div>
            ) : filteredAvailable.length === 0 ? (
              <div className="h-full flex items-center justify-center text-muted-foreground">
                No matching options found.
              </div>
            ) : (
              filteredAvailable.map((opt, idx) => (
                <div key={idx} className="flex justify-between items-center p-3 border rounded-lg bg-card hover:border-brand-base transition-colors group">
                  <div className="min-w-0 pr-2">
                    <h4 className="font-medium text-sm truncate" title={opt.college_name}>{opt.college_name}</h4>
                    <p className="text-xs text-muted-foreground truncate">{opt.branch_name}</p>
                  </div>
                  <Button size="sm" variant="secondary" onClick={() => handleAdd(opt)} className="shrink-0 group-hover:bg-brand-base group-hover:text-white">Add</Button>
                </div>
              ))
            )}
          </div>
        </Card>

        {/* Selected Options (Sortable) */}
        <Card className="glass h-[600px] flex flex-col border-brand-base/30">
          <div className="p-4 border-b border-border bg-brand-light/5 flex justify-between items-center">
            <div>
              <h3 className="font-semibold text-lg">Your Option Form</h3>
              <p className="text-sm text-muted-foreground">{optionForm.length} / 300 choices added</p>
            </div>
            {optionForm.length > 0 && <span className="text-xs font-semibold px-2 py-1 bg-red-100 text-red-700 rounded">#1 Auto-Freezes</span>}
          </div>
          <div className="p-4 overflow-y-auto flex-1 bg-muted/10">
            {optionForm.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-muted-foreground opacity-60">
                <GripVertical className="w-12 h-12 mb-4" />
                <p>No options added yet.</p>
                <p className="text-sm">Add options from the left panel.</p>
              </div>
            ) : (
              <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
                <SortableContext items={optionForm.map(i => i.id)} strategy={verticalListSortingStrategy}>
                  {optionForm.map((opt, idx) => (
                    <SortableItem 
                      key={opt.id} 
                      id={opt.id} 
                      option={opt} 
                      index={idx} 
                      onRemove={handleRemove}
                      onMoveUp={(i) => moveItem(i, -1)}
                      onMoveDown={(i) => moveItem(i, 1)}
                      isFirst={idx === 0}
                      isLast={idx === optionForm.length - 1}
                    />
                  ))}
                </SortableContext>
              </DndContext>
            )}
          </div>
          <div className="p-4 border-t border-border bg-card flex gap-3">
            <Button variant="outline" className="flex-1" onClick={() => setCurrentStep(3)}>Back</Button>
            <Button 
              className="flex-1 gap-2 bg-brand-base hover:bg-brand-dark border-0 text-white" 
              onClick={() => setShowConfirmModal(true)}
              disabled={optionForm.length === 0}
            >
              <Lock className="w-4 h-4" /> Lock Options
            </Button>
          </div>
        </Card>
      </div>

      {showConfirmModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in">
          <Card className="w-full max-w-md shadow-2xl">
            <CardContent className="p-6">
              <div className="w-12 h-12 rounded-full bg-amber-100 text-amber-600 flex items-center justify-center mb-4">
                <AlertCircle className="w-6 h-6" />
              </div>
              <h2 className="text-xl font-bold mb-2">Are you absolutely sure?</h2>
              <p className="text-muted-foreground mb-6">
                Once locked, your choices <strong className="text-foreground">cannot be changed</strong> for this round. Make sure you have ordered them strictly by preference.
              </p>
              <div className="flex gap-3">
                <Button variant="outline" className="flex-1" onClick={() => setShowConfirmModal(false)}>Cancel, let me edit</Button>
                <Button variant="destructive" className="flex-1" onClick={handleLock}>Yes, Lock it</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};


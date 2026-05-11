import { create } from 'zustand';

export const useAppStore = create((set) => ({
  // User Profile
  profile: {
    percentile: '',
    category: 'GOPENH',
    gender: 'Male',
    domicile: 'Maharashtra',
    home_university: 'Pune'
  },
  updateProfile: (updates) => set((state) => ({ 
    profile: { ...state.profile, ...updates } 
  })),

  // Simulator State
  currentStep: 1,
  setCurrentStep: (step) => set({ currentStep: step }),
  
  documentsChecked: {},
  setDocumentChecked: (docId, checked) => set((state) => ({
    documentsChecked: { ...state.documentsChecked, [docId]: checked }
  })),
  
  optionForm: [], // Array of { college_code, college_name, branch_name }
  setOptionForm: (options) => set({ optionForm: options }),
  addOption: (option) => set((state) => ({
    optionForm: [...state.optionForm, option]
  })),
  removeOption: (index) => set((state) => {
    const newOptions = [...state.optionForm];
    newOptions.splice(index, 1);
    return { optionForm: newOptions };
  }),
  
  currentRound: 1,
  allotmentResult: null, // { allotted: boolean, seat: {...}, merit_rank: number, message: string }
  setAllotmentResult: (result) => set({ allotmentResult: result }),
  
  decision: null, // 'Freeze', 'Float', 'Slide'
  setDecision: (decision) => set({ decision }),
  
  roundHistory: [], // Track previous rounds
  addToHistory: (roundData) => set((state) => ({
    roundHistory: [...state.roundHistory, roundData],
    currentRound: state.currentRound + 1,
    decision: null,
    allotmentResult: null
  })),

  finalAdmission: null,
  setFinalAdmission: (admission) => set({ finalAdmission: admission }),

  resetSimulator: () => set({
    currentStep: 1,
    documentsChecked: {},
    optionForm: [],
    currentRound: 1,
    allotmentResult: null,
    decision: null,
    roundHistory: [],
    finalAdmission: null
  })
}));

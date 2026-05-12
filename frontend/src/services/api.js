import categoryMap from '../assets/category_map.json';
import branchMap from '../assets/branch_map.json';
import collegeMap from '../assets/college_name_map.json';
import { normalizeBranch, getCategoryMetadata } from '../utils/normalization';

// Extract lists from assets
export const COLLEGES = Object.keys(collegeMap['College Name -> Variations']).map((name, index) => ({
  code: (1000 + index).toString(),
  name: name,
  district: name.split(',').pop().trim(), // Heuristic district extraction
  type: name.includes('Government') ? 'Government' : 'Un-Aided'
})).slice(0, 100); // Take first 100 for performance

export const CATEGORIES = Object.keys(categoryMap.categories);
export const BRANCHES = Object.keys(branchMap.branches);

// Generate consistent semi-real mock data on load
const generateMockData = () => {
  const data = [];
  // For performance, we only generate a subset of the full matrix
  const topColleges = COLLEGES.slice(0, 50);
  const coreBranches = BRANCHES.slice(0, 10);
  const coreCategories = CATEGORIES.slice(0, 20);

  topColleges.forEach(college => {
    coreBranches.forEach(branch => {
      let baseCutoff = 80 + (Math.random() * 15); // Random baseline
      
      // Prestige modifiers
      if (college.name.includes('COEP') || college.name.includes('VJTI')) baseCutoff = 98;
      if (college.name.includes('Institute of Computer Technology')) baseCutoff = 96;
      
      // Branch modifiers
      if (branch.includes('Computer')) baseCutoff += 2;
      if (branch.includes('Information Technology')) baseCutoff += 1.5;
      if (branch.includes('Mechanical')) baseCutoff -= 4;
      if (branch.includes('Civil')) baseCutoff -= 6;

      coreCategories.forEach(category => {
        const meta = getCategoryMetadata(category);
        let catMod = 0;
        if (meta.caste_group === 'OBC') catMod = -1.5;
        if (meta.caste_group === 'SC') catMod = -5;
        if (meta.caste_group === 'ST') catMod = -12;
        if (meta.gender === 'Female') catMod -= 0.5;

        ['2022', '2023', '2024'].forEach(year => {
          let yearMod = (parseInt(year) - 2024) * 0.3;
          
          [1, 2, 3].forEach(round => {
            let roundMod = (round - 1) * -0.8;
            
            let finalCutoff = baseCutoff + catMod + yearMod + roundMod + (Math.random() * 0.4 - 0.2);
            finalCutoff = Math.min(Math.max(finalCutoff, 30), 99.99);

            data.push({
              college_code: college.code,
              college_name: college.name,
              district: college.district,
              type: college.type,
              branch_name: branch,
              category: category,
              year: year,
              round: round,
              cutoff: parseFloat(finalCutoff.toFixed(2))
            });
          });
        });
      });
    });
  });
  return data;
};

const mockDatabase = generateMockData();

const delay = (ms = 500) => new Promise(resolve => setTimeout(resolve, ms));

export const api = {
  // GET /predict
  async predict({ percentile, category, year = '2024', round = 3, districts = [], branches = [] }) {
    await delay(800);
    
    let results = mockDatabase.filter(d => d.year === year.toString() && d.round === round);
    
    // STRICT RULE: Category must match exactly
    results = results.filter(d => d.category === category);
    
    if (districts.length > 0) {
      results = results.filter(d => districts.some(dist => d.district.includes(dist)));
    }
    if (branches.length > 0) {
      results = results.filter(d => branches.includes(d.branch_name));
    }

    const ranked = results.map(d => {
      const delta = parseFloat((percentile - d.cutoff).toFixed(2));
      let status = 'Reach';
      if (delta >= 3.0) status = 'Safe';
      else if (delta >= -1.0) status = 'Moderate';

      return {
        ...d,
        delta,
        status,
        probability: Math.min(99, Math.max(1, 50 + (delta * 12)))
      };
    });

    return ranked.sort((a, b) => b.cutoff - a.cutoff);
  },

  // GET /trends
  async getTrends({ institute_code, branch_name, category }) {
    await delay(400);
    const trends = mockDatabase.filter(d => 
      d.college_code === institute_code && 
      d.branch_name === branch_name && 
      d.category === category
    );
    
    return ['2022', '2023', '2024'].map(year => {
      const yearData = trends.filter(t => t.year === year);
      return {
        year,
        round1: yearData.find(t => t.round === 1)?.cutoff || null,
        round2: yearData.find(t => t.round === 2)?.cutoff || null,
        round3: yearData.find(t => t.round === 3)?.cutoff || null,
      };
    });
  },

  // GET /colleges
  async getColleges() {
    await delay(300);
    return COLLEGES;
  },

  // POST /simulate
  async simulateRound({ profile, optionForm, currentRound }) {
    await delay(1500);
    
    let allottedSeat = null;
    let rank = null;

    for (let i = 0; i < optionForm.length; i++) {
      const choice = optionForm[i];
      const cutoffData = mockDatabase.find(d => 
        d.college_code === choice.college_code && 
        d.branch_name === choice.branch_name && 
        d.category === profile.category &&
        d.year === '2024' &&
        d.round === currentRound
      );

      const requiredCutoff = cutoffData ? cutoffData.cutoff : 99; // Assume very high if missing

      if (profile.percentile >= requiredCutoff) {
        allottedSeat = {
          ...choice,
          allotted_category: profile.category,
          round: currentRound,
          preference_number: i + 1,
        };
        rank = Math.floor(120000 - (profile.percentile * 1200));
        break;
      }
    }

    return {
      allotted: allottedSeat !== null,
      seat: allottedSeat,
      merit_rank: rank,
      message: allottedSeat 
        ? (allottedSeat.preference_number === 1 ? 'Auto-Freeze triggered.' : 'Seat Allotted!')
        : `No seat allotted in Round ${currentRound}.`
    };
  }
};


import categoryMap from '../assets/category_map.json';
import branchMap from '../assets/branch_map.json';

const API_BASE_URL = 'http://localhost:8000';

export const CATEGORIES = Object.keys(categoryMap.categories);
export const BRANCHES = Object.keys(branchMap.branches);

const fetchAPI = async (endpoint, options = {}) => {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'API request failed');
  }
  
  return response.json();
};

export const api = {
  // POST /recommend
  async predict({ percentile, category, districts = [], branches = [], topN = 100 }) {
    // Note: Backend expects 'branch_family' and 'preferred_tiers'
    // We map frontend params to backend schema
    const body = {
      percentile: parseFloat(percentile),
      category: category,
      branch_family: branches.length > 0 ? branches[0] : null,
      preferred_tiers: null, // Default to all tiers
      top_n: topN
    };

    const data = await fetchAPI('/recommend', {
      method: 'POST',
      body: JSON.stringify(body)
    });

    // Flatten data for frontend components that expect a single list
    // but preserving bucket information in the item
    const flattened = [];
    ['SAFE', 'TARGET', 'AMBITIOUS'].forEach(bucket => {
      if (data[bucket]) {
        data[bucket].forEach(item => {
          flattened.push({
            ...item,
            status: bucket === 'SAFE' ? 'Safe' : bucket === 'TARGET' ? 'Moderate' : 'Reach',
            college_code: item.institute_code
          });
        });
      }
    });

    return flattened;
  },

  // GET /trends
  async getTrends({ institute_code, branch_name, category }) {
    const params = new URLSearchParams({
      institute_code,
      branch_name,
      category
    });
    const data = await fetchAPI(`/trends?${params.toString()}`);
    return data.trends;
  },

  // GET /colleges
  async getColleges() {
    return fetchAPI('/colleges');
  },

  // GET /analytics/college
  async getCollegeAnalytics(instituteCode, category) {
    const params = new URLSearchParams({
      institute_code: instituteCode,
      category
    });
    return fetchAPI(`/analytics/college?${params.toString()}`);
  },

  // POST /simulate
  async simulateRound({ profile, optionForm, currentRound }) {
    const body = {
      profile: {
        percentile: parseFloat(profile.percentile),
        category: profile.category,
        district: profile.district,
        merit_rank: null // Calculated by backend
      },
      optionForm: optionForm.map(opt => ({
        college_code: opt.college_code || opt.code,
        college_name: opt.college_name || opt.name,
        branch_name: opt.branch_name,
        institute_tier: opt.institute_tier || 3
      })),
      currentRound: parseInt(currentRound)
    };

    return fetchAPI('/simulate', {
      method: 'POST',
      body: JSON.stringify(body)
    });
  }
};



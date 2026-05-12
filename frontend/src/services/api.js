// src/services/api.js

// ─────────────────────────────────────────────────────────────────────────────
// REAL BACKEND — GradMap FastAPI
// ─────────────────────────────────────────────────────────────────────────────
const BASE_URL = 'http://localhost:8000';

/**
 * Branch family display labels shown in the UI selector.
 * These map to the engine's internal branch_family strings.
 */
export const BRANCH_FAMILIES = [
  { value: null,               label: 'All Branches' },
  { value: 'CS_FAMILY',        label: 'Computer & IT' },
  { value: 'CIRCUITS_FAMILY',  label: 'Electronics & Electrical' },
  { value: 'CORE_MECHANICAL',  label: 'Mechanical & Robotics' },
  { value: 'CIVIL_FAMILY',     label: 'Civil & Structural' },
  { value: 'CHEMICAL_FAMILY',  label: 'Chemical & Polymer' },
];

/**
 * Maps the engine's bucket names to the UI's status strings.
 */
const BUCKET_TO_STATUS = {
  SAFE:      'Safe',
  TARGET:    'Moderate',
  AMBITIOUS: 'Reach',
};

/**
 * Common fetch helper with error handling
 */
async function fetchAPI(endpoint, options = {}) {
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    method: options.method || 'GET',
    headers: { 'Content-Type': 'application/json', ...options.headers },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(
      typeof err.detail === 'string'
        ? err.detail
        : JSON.stringify(err.detail)
    );
  }
  return await response.json();
}

/**
 * Call POST /recommend on the GradMap backend and return a flat
 * array of recommendation objects compatible with the UI table.
 */
export async function fetchRecommendations({ percentile, category, branchFamily = null, preferredTiers = null, topN = 20 }) {
  const payload = {
    percentile,
    category,
    branch_family: branchFamily || undefined,
    preferred_tiers: preferredTiers || undefined,
    top_n: topN,
  };

  const data = await fetchAPI('/recommend', { method: 'POST', body: payload });
  
  // Flatten into a single array matching the table's field names.
  const flat = [];
  for (const bucket of ['SAFE', 'TARGET', 'AMBITIOUS']) {
    for (const rec of data[bucket] ?? []) {
      flat.push({
        ...rec,
        college_code: rec.institute_code || rec.college_code,
        cutoff: rec.percentile_cutoff,
        delta: parseFloat((percentile - rec.percentile_cutoff).toFixed(2)),
        status: BUCKET_TO_STATUS[rec.recommendation_bucket] ?? rec.recommendation_bucket,
        district: rec.college_name?.split(',').slice(-1)[0]?.trim() ?? '—',
      });
    }
  }
  return flat;
}

export const api = {
  /**
   * Call POST /recommend on the GradMap backend
   */
  async predict(params) {
    return fetchRecommendations(params);
  },

  /**
   * GET /trends
   */
  async getTrends({ institute_code, branch_name, category }) {
    const params = new URLSearchParams({ institute_code, branch_name, category });
    try {
      return await fetchAPI(`/trends?${params}`);
    } catch (e) {
      console.error("Trends fetch failed:", e);
      return [];
    }
  },

  /**
   * GET /analytics/college
   */
  async getCollegeAnalytics({ institute_code, category }) {
    const params = new URLSearchParams({ institute_code, category });
    try {
      return await fetchAPI(`/analytics/college?${params}`);
    } catch (e) {
      console.error("Analytics fetch failed:", e);
      return null;
    }
  },

  /**
   * GET /colleges
   */
  async getColleges() {
    try {
      return await fetchAPI('/colleges');
    } catch (e) {
      console.error("Colleges fetch failed:", e);
      return [];
    }
  },

  /**
   * REAL Deterministic Simulation
   * POST /simulate
   */
  async simulateRound({ profile, optionForm, currentRound }) {
    // Map optionForm to backend schema (OptionItem)
    const backendForm = optionForm.map(opt => ({
      college_code: opt.college_code || opt.code,
      college_name: opt.college_name || opt.name,
      branch_name: opt.branch_name
    }));

    const payload = {
      profile: {
        percentile: parseFloat(profile.percentile),
        category: profile.category
      },
      optionForm: backendForm,
      currentRound: currentRound
    };

    try {
      const result = await fetchAPI('/simulate', { method: 'POST', body: payload });
      
      // Map back to frontend expected structure if necessary
      // (The backend response matches exactly the success/failure shapes requested)
      return {
        ...result,
        message: result.message
      };
    } catch (e) {
      console.error("Simulation failed:", e);
      return {
        allotted: false,
        seat: null,
        merit_rank: 0,
        message: "Simulation failed. Please check your connection."
      };
    }
  }
};

/**
 * Category list for UI selectors
 */
export const CATEGORIES = [
  'GOPENH', 'LOPENH', 'GOBCH', 'LOBCH', 'GSCH', 'LSCH', 'GSTH', 'LSTH',
  'GOPENO', 'LOPENO', 'GOBCO', 'LOBCO', 'GSCO', 'LSCO', 'GSTO', 'LSTO',
  'TFWS', 'EWS'
];



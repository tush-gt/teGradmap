import branchMap from '../assets/branch_map.json';
import categoryMap from '../assets/category_map.json';
import collegeMap from '../assets/college_name_map.json';

/**
 * Normalizes a branch name using the branch_map.json
 * @param {string} rawName 
 * @returns {string} Canonical branch name
 */
export const normalizeBranch = (rawName) => {
  if (!rawName) return 'Unknown Branch';
  const searchName = rawName.toLowerCase().trim();
  
  for (const [canonical, data] of Object.entries(branchMap.branches)) {
    if (data.variants.map(v => v.toLowerCase()).includes(searchName) || canonical.toLowerCase() === searchName) {
      return canonical;
    }
  }
  return rawName; // Fallback to raw if no match
};

/**
 * Normalizes a category and retrieves its metadata
 * @param {string} code e.g., 'GOPENH'
 * @returns {Object} Category metadata
 */
export const getCategoryMetadata = (code) => {
  return categoryMap.categories[code] || {
    caste_group: 'Unknown',
    gender: 'All',
    home_university_type: 'Unknown',
    seat_pool: 'Unknown'
  };
};

/**
 * Normalizes a college name using the college_name_map.json
 * @param {string} rawName 
 * @returns {string} Canonical college name
 */
export const normalizeCollege = (rawName) => {
  if (!rawName) return 'Unknown College';
  const searchName = rawName.trim();

  for (const [canonical, variants] of Object.entries(collegeMap)) {
    if (variants.includes(searchName) || canonical === searchName) {
      return canonical;
    }
  }
  return rawName;
};

/**
 * Validates if a category is allowed based on gender
 * @param {string} category 
 * @param {string} gender 
 * @returns {boolean}
 */
export const isCategoryAllowedForGender = (category, gender) => {
  const meta = getCategoryMetadata(category);
  if (meta.gender === 'All') return true;
  return meta.gender === gender;
};

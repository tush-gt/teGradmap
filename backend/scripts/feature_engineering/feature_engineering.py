"""
GradMap — Feature Engineering Pipeline
======================================
Generates derived features for counselling intelligence, simulation,
and recommendation.

Input  : clean/clean_recommendation_dataset.csv
Output : features/featured_master_dataset.csv
         features/feature_metadata.json

Key Features:
  1. admission_difficulty   : Categorical (VERY_HARD to VERY_EASY)
  2. percentile_band        : 1% buckets (e.g., 95-96)
  3. branch_family         : Functional grouping (CS_FAMILY, CIRCUITS, etc.)
  4. institute_tier        : Heuristic tiering (Tier 1-3)
  5. recommendation_score   : Explainable score for counselling
  6. seat_competitiveness  : Numeric (100 - percentile)
  7. round_type            : Temporal grouping (EARLY, MID, LATE)

Author  : GradMap Pipeline
Version : 1.0.0
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd
import numpy as np

# ──────────────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CLEAN_DIR = BASE_DIR / "clean"
FEATURES_DIR = BASE_DIR / "features"
CONFIGS_DIR = BASE_DIR / "configs"

INPUT_FILE = CLEAN_DIR / "clean_recommendation_dataset.csv"
OUTPUT_FILE = FEATURES_DIR / "featured_master_dataset.csv"
METADATA_FILE = FEATURES_DIR / "feature_metadata.json"

# ──────────────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("feature_engineering")


# ======================================================================
#  FEATURE HELPER FUNCTIONS
# ======================================================================

def get_admission_difficulty(p: float) -> str:
    """Categorize difficulty based on percentile."""
    if p >= 99: return "VERY_HARD"
    if p >= 97: return "HARD"
    if p >= 90: return "MEDIUM"
    if p >= 75: return "EASY"
    return "VERY_EASY"


def get_percentile_band(p: float) -> str:
    # """Create 1% percentile bands."""
    # low = int(np.floor(p))
    # return f"{low}-{low+1}"
    if p>= 99:
        low = np.floor(p*10) / 10
        high = low + 0.1
        return f"{low:.1f}-{high:.1f}"
    elif p >= 95:
        low = np.floor(p * 2) / 2
        high = low + 0.5
        return f"{low:.1f}-{high:.1f}"
    else:
        low = int(np.floor(p))
        return f"{low}-{low+1}"


def get_branch_family(branch: str) -> str:
    """Group branches into functional families."""
    b = str(branch).upper()
    
    cs_keywords = ["COMPUTER", "INFORMATION TECHNOLOGY", "DATA SCIENCE", "ARTIFICIAL INTELLIGENCE", "MACHINE LEARNING", "IT", "SOFTWARE", "CYBER"]
    circuits_keywords = ["ELECTRONICS", "ELECTRICAL", "EXTC", "TELECOMMUNICATION", "INSTRUMENTATION"]
    mechanical_keywords = ["MECHANICAL", "PRODUCTION", "AUTOMOBILE", "AERONAUTICAL", "MECHATRONICS", "ROBOTICS"]
    civil_keywords = ["CIVIL", "STRUCTURAL", "CONSTRUCTION"]
    chemical_keywords = ["CHEMICAL", "POLYMER", "TEXTILE", "PHARMACY", "BIO"]

    if any(k in b for k in cs_keywords): return "CS_FAMILY"
    if any(k in b for k in circuits_keywords): return "CIRCUITS_FAMILY"
    if any(k in b for k in mechanical_keywords): return "CORE_MECHANICAL"
    if any(k in b for k in civil_keywords): return "CIVIL_FAMILY"
    if any(k in b for k in chemical_keywords): return "CHEMICAL_FAMILY"
    
    return "OTHER"


# ──────────────────────────────────────────────────────────────────────
# INSTITUTE TIER MAPPING
# Strict curated lists — fragment matched against lowercased college name.
#
# RULES FOR ADDING ENTRIES:
#   1. Each fragment must be UNIQUE enough to NOT match unintended colleges.
#   2. Do NOT use: 'pune', 'mumbai', 'technology', 'engineering', 'institute'
#      as standalone fragments — they are far too broad.
#   3. Use the most specific distinguishing part of the canonical name.
#   4. Test by checking what else the fragment would match.
# ──────────────────────────────────────────────────────────────────────

# Tier 1 — Genuinely elite Maharashtra engineering institutes only.
# Intentionally SMALL. High cutoffs + national/state-level recognition.
_TIER_1_FRAGMENTS = [
    "coep technological university",            # COEP (new name)
    "college of engineering, shivajinagar",     # COEP (older maps)
    "veermata jijabai technological institute", # VJTI (full unique name)
    "bhartiya vidya bhavan's sardar patel institute of technology",  # SPIT (fully qualified, unique)
    "pune institute of computer technology",    # PICT — unique enough
    "institute of chemical technology, matunga",  # ICT Mumbai — qualified
    "walchand college of engineering, sangli",  # Walchand Sangli — qualified
    "cummins college of engineering for women", # Cummins — unique enough
    "mksss's cummins college of engineering",   # Cummins alternate form
]

# Tier 2 — Established, reputed private/autonomous institutes.
# Decent cutoffs, recognisable brand, strong placement.
_TIER_2_FRAGMENTS = [
    "dwarkadas j. sanghvi college of engineering",               # DJSCE
    "shri vile parle kelvani mandal's dwarkadas j. sanghvi",     # DJSCE alternate
    "pimpri chinchwad college of engineering and research",       # PCCOE Ravet
    "pimpri chinchwad college of engineering, pune",              # PCCOE main
    "pimpri chinchwad education trust, pimpri chinchwad college", # PCCOE trust form
    "vishwakarma institute of technology, bibwewadi",             # VIT Bibwewadi (qualified)
    "b.r.a.c.t's vishwakarma institute of technology",           # VIIT/VIT exact form
    "vishwakarma institute of information technology",            # VIIT Kondhwa
    "b.r.a.c.t's vishwakarma institute of information technology",
    "k j somaiya institute of technology",
    "thadomal shahani engineering college",
    "fr. conceicao rodrigues college of engineering",             # Fr. Agnel
    "lokmanya tilak college of engineering, kopar khairane",      # qualified
    "shri ramdeobaba college of engineering and management",
    "sardar patel college of engineering, andheri",               # NOT SPIT
    "k. e. society's rajarambapu institute of technology",
    "army institute of technology",
    "sies graduate school of technology",
    "d.y. patil college of engineering, akurdi",
    "pune vidyarthi griha's college of engineering and technology",
    "maharashtra institute of technology, pune",
    "indira college of engineering and management",
    "k j somaiya college of engineering",
]



def get_institute_tier(college: str) -> int:
    """
    Assign heuristic prestige tier (1=Elite, 2=Good, 3=Default).

    Uses strict curated canonical name fragment matching on lowercased
    college name. This prevents false positives from generic keywords.
    DO NOT use broad keywords (e.g. 'pune', 'technology', 'institute').
    """
    c = str(college).strip().lower()

    for fragment in _TIER_1_FRAGMENTS:
        if fragment in c:
            return 1

    for fragment in _TIER_2_FRAGMENTS:
        if fragment in c:
            return 2

    return 3

def get_tier_weight(tier: int) -> int:
    """
    Convert tier into weighted score.
    """
    weights = {
        1: 35,
        2: 20,
        3: 5
    }

    return weights.get(tier, 0)

def get_round_type(r: int) -> str:
    """Group rounds into early, mid, and late stages."""
    if r == 1: return "EARLY_ROUND"
    if r == 2: return "MID_ROUND"
    return "LATE_ROUND"


# ======================================================================
#  CORE PIPELINE
# ======================================================================

def run_feature_engineering():
    log.info("═" * 56)
    log.info("GradMap — Feature Engineering Stage")
    log.info("═" * 56)

    if not INPUT_FILE.exists():
        log.error("Input file not found: %s", INPUT_FILE)
        return

    # 1. Load Clean Dataset
    log.info("Loading clean recommendation dataset...")
    df = pd.read_csv(INPUT_FILE, dtype={"choice_code": str, "institute_code": str})
    log.info("Total rows to process: %d", len(df))

    # 2. Implement Features
    log.info("Generating features...")
    
    # Simple direct features
    df["seat_competitiveness"] = 100 - df["percentile_cutoff"]
    df["admission_difficulty"] = df["percentile_cutoff"].apply(get_admission_difficulty)
    df["percentile_band"] = df["percentile_cutoff"].apply(get_percentile_band)
    df["branch_family"] = df["branch_name"].apply(get_branch_family)
    df["institute_tier"] = df["college_name"].apply(get_institute_tier)
    df["round_type"] = df["round"].apply(get_round_type)

    # 3. recommendation_score    
    # Normalize percentile to 0–50
    percentile_component = (df["percentile_cutoff"] / 100) * 50

    tier_weights = {
        1: 35,
        2: 20,
        3: 5
    }

    family_weights = {
        "CS_FAMILY": 15,
        "CIRCUITS_FAMILY": 10,
        "CORE_MECHANICAL": 7,
        "CIVIL_FAMILY": 5,
        "CHEMICAL_FAMILY": 5,
        "OTHER": 2
    }

    df["percentile_zscore"] = (
        (df["percentile_cutoff"] - df["percentile_cutoff"].mean())
        / df["percentile_cutoff"].std()
    )

    df["recommendation_score"] = (
        percentile_component
        + df["institute_tier"].apply(get_tier_weight)
        + df["branch_family"].map(family_weights)
    )

    # 4. Final Cleanup
    # Sort for consistency
    df = df.sort_values(
        by=["recommendation_score", "percentile_cutoff"],
        ascending=[False, False]
    )

    df["choice_code"] = (
        df["choice_code"]
        .astype(str)
        .str.replace(".0", "", regex=False)
    )

    # 5. Export Featured Dataset
    FEATURES_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
    log.info("Exported featured dataset: %s", OUTPUT_FILE)

    # 6. Export Metadata
    metadata = {
        "features": [
            {
                "name": "admission_difficulty",
                "type": "categorical",
                "description": "Heuristic difficulty level based on percentile cutoff.",
                "relevance": "Helps users understand their chances at a glance."
            },
            {
                "name": "percentile_band",
                "type": "categorical",
                "description": "Adaptive percentile buckets with finer granularity at high percentiles.",
                "relevance": "User-friendly grouping for analytics."
            },
            {
                "name": "branch_family",
                "type": "categorical",
                "description": "Functional grouping of related engineering branches.",
                "relevance": "Allows users to explore related disciplines (e.g., IT vs CS)."
            },
            {
                "name": "institute_tier",
                "type": "ordinal",
                "description": "Heuristic prestige tier (1=Top, 3=Other).",
                "relevance": "Critical for ranking and weightage in recommendation."
            },
            {
                "name": "percentile_zscore",
                "type": "numerical",
                "description": "Standardized percentile feature using z-score normalization.",
                "relevance": "Useful for future ML models, ranking systems, and anomaly analysis."
            },
            {
                "name": "recommendation_score",
                "type": "numerical",
                "description": "Explainable score combining percentile, tier, and branch popularity.",
                "relevance": "Primary sorting key for the recommendation engine."
            },
            {
                "name": "seat_competitiveness",
                "type": "numerical",
                "description": "Inverted percentile (100 - p). Lower is more competitive.",
                "relevance": "Used for ranking scarcity."
            },
            {
                "name": "round_type",
                "type": "categorical",
                "description": "Grouping of admission rounds into Early, Mid, and Late stages.",
                "relevance": "Essential for simulation strategy (when to wait vs when to freeze)."
            }
        ],
        "engineering_details": {
            "tier_1_keywords": ["COEP", "VJTI", "SPIT", "PICT", "ICT"],
            "score_formula": "((percentile_cutoff / 100) * 50) + tier_weight + branch_family_weight",
            "total_rows": len(df)
        }
    }

    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    log.info("Exported feature metadata: %s", METADATA_FILE)

    log.info("═" * 56)
    log.info("FEATURE ENGINEERING COMPLETE")
    log.info("═" * 56)

if __name__ == "__main__":
    run_feature_engineering()

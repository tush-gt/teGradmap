"""
GradMap — Recommendation Engine Configuration
===============================================
Central config for all engine parameters.

All tunable constants live here so the engine behaviour can be
adjusted without touching logic code.

Author  : GradMap Pipeline
Version : 1.0.0
"""

from __future__ import annotations
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent
FEATURES_DIR = BASE_DIR / "features"
DATASET_PATH = FEATURES_DIR / "featured_master_dataset.csv"

# ──────────────────────────────────────────────────────────────────────
# Bucket Thresholds
# ──────────────────────────────────────────────────────────────────────
# percentile_gap = user_percentile - cutoff_percentile
#   SAFE       : gap >= SAFE_THRESHOLD        (user comfortably above cutoff)
#   TARGET     : AMBITIOUS_THRESHOLD <= gap < SAFE_THRESHOLD
#   AMBITIOUS  : gap < AMBITIOUS_THRESHOLD    (user below cutoff — stretch goal)
SAFE_THRESHOLD: float = 2.0
AMBITIOUS_THRESHOLD: float = -1.0

# ──────────────────────────────────────────────────────────────────────
# Recommendation Split
# ──────────────────────────────────────────────────────────────────────
# How many recommendations per bucket when returning top_n results.
# The engine will try to fill these counts, but may return fewer
# if insufficient data exists for a bucket.
DEFAULT_TOP_N: int = 20
BUCKET_SPLIT: dict[str, int] = {
    "SAFE": 5,
    "TARGET": 10,
    "AMBITIOUS": 5,
}

# ──────────────────────────────────────────────────────────────────────
# Tier Weights (used in recommendation_score)
# ──────────────────────────────────────────────────────────────────────
TIER_WEIGHTS: dict[int, int] = {
    1: 35,
    2: 20,
    3: 5,
}

# ──────────────────────────────────────────────────────────────────────
# Branch Family Weights (used in recommendation_score)
# ──────────────────────────────────────────────────────────────────────
BRANCH_FAMILY_WEIGHTS: dict[str, int] = {
    "CS_FAMILY": 15,
    "CIRCUITS_FAMILY": 10,
    "CORE_MECHANICAL": 7,
    "CIVIL_FAMILY": 5,
    "CHEMICAL_FAMILY": 5,
    "OTHER": 2,
}

# ──────────────────────────────────────────────────────────────────────
# Year Recency Bonus
# ──────────────────────────────────────────────────────────────────────
# More recent data is slightly more relevant. This bonus is added to
# recommendation_score so 2025 data edges out older identical entries.
YEAR_RECENCY_BONUS: dict[int, float] = {
    2025: 2.0,
    2024: 1.0,
    2023: 0.5,
    2022: 0.0,
}
DEFAULT_YEAR_BONUS: float = 0.0

# ──────────────────────────────────────────────────────────────────────
# Deduplication
# ──────────────────────────────────────────────────────────────────────
# When the same college+branch appears across multiple rounds/years,
# keep only the highest-ranked entry to avoid recommendation spam.
DEDUP_KEY_COLUMNS: list[str] = ["college_name", "branch_name"]

# ──────────────────────────────────────────────────────────────────────
# Output Columns
# ──────────────────────────────────────────────────────────────────────
# Fields returned in each recommendation object.
RECOMMENDATION_COLUMNS: list[str] = [
    "college_name",
    "branch_name",
    "category",
    "percentile_cutoff",
    "percentile_gap",
    "recommendation_bucket",
    "recommendation_score",
    "institute_tier",
    "admission_difficulty",
    "round",
    "year",
    "choice_code",
    "institute_code",
    "ml_probability",
    "probability_bucket",
    "confidence_label",
    "probability_percent",
]

# ──────────────────────────────────────────────────────────────────────
# Bucket Display Priority (higher = shown first in mixed listings)
# ──────────────────────────────────────────────────────────────────────
BUCKET_PRIORITY: dict[str, int] = {
    "SAFE": 3,
    "TARGET": 2,
    "AMBITIOUS": 1,
}

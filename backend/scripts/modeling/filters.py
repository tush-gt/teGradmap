"""
GradMap — Recommendation Engine Filters
=========================================
Modular filtering functions that narrow the full dataset down to
rows relevant for a specific user's admission profile.

Each filter accepts a DataFrame and returns a filtered copy.
Filters are composable and order-independent.

Author  : GradMap Pipeline
Version : 1.0.0
"""

from __future__ import annotations

import logging
from typing import Optional

import pandas as pd

log = logging.getLogger("gradmap.engine")


def filter_by_category(
    df: pd.DataFrame,
    user_category: str,
) -> pd.DataFrame:
    """
    Keep only rows whose `category` column matches the user's 
    category family (e.g. GOPENS matches GOPENS, GOPENH, GOPENO).

    This uses a family-based root extraction to ensure students see 
    all relevant seats they are eligible for.
    """
    # Extract root family (e.g., GOPEN, GOBC, etc.)
    cat_root = user_category
    families = ("GOPEN", "LOPEN", "GOBC", "LOBC", "GSC", "LSC", "GST", "LST", "GNT", "LNT", "GVJ", "LVJ")
    for fam in families:
        if user_category.startswith(fam):
            cat_root = fam
            break

    mask = df["category"].str.contains(cat_root, na=False, case=False)
    result = df[mask].copy()
    log.info("Category filter (root: %s): %d → %d rows",
             cat_root, len(df), len(result))
    return result


def filter_by_branch_family(
    df: pd.DataFrame,
    preferred_branch_family: Optional[str],
) -> pd.DataFrame:
    """
    Keep only rows matching the preferred branch family.

    If preferred_branch_family is None, no filtering is applied
    (user is open to all branches).
    """
    if preferred_branch_family is None:
        log.info("Branch family filter: skipped (no preference)")
        return df

    mask = df["branch_family"] == preferred_branch_family
    result = df[mask].copy()
    log.info("Branch family filter (%s): %d → %d rows",
             preferred_branch_family, len(df), len(result))
    return result


def filter_by_tier(
    df: pd.DataFrame,
    preferred_tiers: Optional[list[int]],
) -> pd.DataFrame:
    """
    Keep only rows matching the preferred institute tiers.

    If preferred_tiers is None, no filtering is applied
    (user is open to all tiers).
    """
    if preferred_tiers is None:
        log.info("Tier filter: skipped (no preference)")
        return df

    mask = df["institute_tier"].isin(preferred_tiers)
    result = df[mask].copy()
    log.info("Tier filter (%s): %d → %d rows",
             preferred_tiers, len(df), len(result))
    return result


def filter_by_percentile_window(
    df: pd.DataFrame,
    user_percentile: float,
    lower_margin: float = 10.0,
    upper_margin: float = 5.0,
) -> pd.DataFrame:
    """
    Pre-filter to a reasonable percentile window around the user's score.

    This prevents the engine from processing 230k rows when only a
    narrow band is relevant. The window is intentionally wider on the
    lower side (user could aim below) and tighter on the upper side
    (very high cutoffs are truly unreachable).

    Default window: [user - 10, user + 5]
    """
    lo = max(0.0, user_percentile - lower_margin)
    hi = min(100.0, user_percentile + upper_margin)

    mask = (df["percentile_cutoff"] >= lo) & (df["percentile_cutoff"] <= hi)
    result = df[mask].copy()
    log.info("Percentile window [%.1f – %.1f]: %d → %d rows",
             lo, hi, len(df), len(result))
    return result

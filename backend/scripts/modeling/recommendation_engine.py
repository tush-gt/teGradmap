"""
GradMap — Recommendation Engine (Orchestrator)
===============================================
Top-level entry point that wires together all engine modules.

Pipeline:
  1. Load dataset       (utils)
  2. Validate input     (utils)
  3. Filter by category (filters)
  4. Filter by branch   (filters)
  5. Filter by tier     (filters)
  6. Percentile window  (filters)
  7. Compute gap        (bucket_logic)
  8. Assign buckets     (bucket_logic)
  9. Apply scoring      (scoring)
  10. Deduplicate       (ranking)
  11. Rank & split      (ranking)
  12. Format output     (ranking)

Usage (CLI):
    python -m scripts.modeling.recommendation_engine

Usage (import):
    from scripts.modeling.recommendation_engine import recommend
    results = recommend({
        "user_percentile": 97.2,
        "user_category": "GOPEN",
        "preferred_branch_family": "CS_FAMILY",
        "top_n": 20,
    })

Author  : GradMap Pipeline
Version : 1.0.0
"""

from __future__ import annotations

import json
import logging
from typing import Any

import pandas as pd

from . import config
from .utils import load_dataset, validate_user_input, assert_columns, setup_logging
from .filters import (
    filter_by_category,
    filter_by_branch_family,
    filter_by_tier,
    filter_by_percentile_window,
)
from .bucket_logic import compute_percentile_gap, assign_buckets
from .scoring import apply_year_recency
from .ranking import (
    deduplicate_recommendations,
    rank_within_buckets,
    split_by_bucket,
    format_recommendations,
)

log = logging.getLogger("gradmap.engine")


# ======================================================================
#  CORE RECOMMEND FUNCTION
# ======================================================================

def recommend(
    user_input: dict[str, Any],
    df: pd.DataFrame | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """
    Run the full recommendation pipeline.

    Args:
        user_input: Raw user request dict (see utils.validate_user_input).
        df: Optional pre-loaded dataset. If None, loads from disk.

    Returns:
        {
            "SAFE":      [list of recommendation dicts],
            "TARGET":    [list of recommendation dicts],
            "AMBITIOUS": [list of recommendation dicts],
        }
    """
    log.info("═" * 60)
    log.info("GradMap Recommendation Engine")
    log.info("═" * 60)

    # 1. Validate user input
    params = validate_user_input(user_input)

    # 2. Load dataset
    if df is None:
        df = load_dataset()
    assert_columns(df)

    # 3. Apply filters (pipeline of composable narrowing)
    df = filter_by_category(df, params["user_category"])
    df = filter_by_branch_family(df, params["preferred_branch_family"])
    df = filter_by_tier(df, params["preferred_tier"])
    df = filter_by_percentile_window(df, params["user_percentile"])

    if df.empty:
        log.warning("No candidates after filtering. Returning empty results.")
        return {"SAFE": [], "TARGET": [], "AMBITIOUS": []}

    # 4. Compute percentile gap and assign buckets
    df = compute_percentile_gap(df, params["user_percentile"])
    df = assign_buckets(df)

    # 5. Apply scoring (year recency)
    df = apply_year_recency(df)

    # 6. Deduplicate for diversity
    df = deduplicate_recommendations(df)

    # 7. Rank within buckets
    df = rank_within_buckets(df)

    # 8. Split into groups and fill allocations
    groups = split_by_bucket(df, params["top_n"])

    # 9. Format for frontend
    result = format_recommendations(groups)

    total = sum(len(v) for v in result.values())
    log.info("─" * 60)
    log.info("Total recommendations returned: %d", total)
    log.info("═" * 60)

    return result


# ======================================================================
#  PRETTY PRINTER (CLI only)
# ======================================================================

def print_recommendations(result: dict[str, list[dict[str, Any]]]) -> None:
    """Human-readable CLI output for quick testing."""
    for bucket in ("SAFE", "TARGET", "AMBITIOUS"):
        recs = result.get(bucket, [])
        print(f"\n{'-' * 80}")
        print(f"  {bucket}  ({len(recs)} recommendations)")
        print(f"{'-' * 80}")

        if not recs:
            print("  (none)")
            continue

        for i, rec in enumerate(recs, 1):
            print(
                f"  {i:>2}. {rec.get('college_name', '???')}\n"
                f"      Branch: {rec.get('branch_name', '???')}  |  "
                f"Tier {rec.get('institute_tier', '?')}  |  "
                f"Cutoff: {rec.get('percentile_cutoff', 0):.2f}  |  "
                f"Gap: {rec.get('percentile_gap', 0):+.2f}  |  "
                f"Score: {rec.get('recommendation_score', 0):.1f}  |  "
                f"Round {rec.get('round', '?')} ({rec.get('year', '?')})"
            )


# ======================================================================
#  CLI ENTRY POINT
# ======================================================================

if __name__ == "__main__":
    setup_logging()

    # Example request — edit these values for testing
    test_input = {
        "user_percentile": 97.2,
        "user_category": "GOPEN",
        "preferred_branch_family": "CS_FAMILY",
        "preferred_tier": None,       # None = all tiers
        "top_n": 20,
    }

    results = recommend(test_input)
    print_recommendations(results)

"""
GradMap — Recommendation Scoring
=================================
Applies the explainable recommendation score with year-recency bonus.

Current formula (deterministic, no ML):

    final_score = recommendation_score + year_recency_bonus

Where recommendation_score was computed in feature engineering as:
    (percentile_cutoff / 100) * 50
    + tier_weight
    + branch_family_weight

This module adds the year-recency bonus so 2025 data edges out
identical older entries, reflecting the fact that recent cutoffs
are more predictive of upcoming rounds.

Author  : GradMap Pipeline
Version : 1.0.0
"""

from __future__ import annotations

import logging

import pandas as pd

from . import config

log = logging.getLogger("gradmap.engine")


def apply_year_recency(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add `year_bonus` and compute `final_score`.

    final_score = recommendation_score + year_bonus

    The bonus is small (0–2 points) to avoid swamping the main score
    but large enough to break ties in favour of more recent data.
    """
    df["year_bonus"] = df["year"].map(config.YEAR_RECENCY_BONUS).fillna(
        config.DEFAULT_YEAR_BONUS
    )
    df["final_score"] = df["recommendation_score"] + df["year_bonus"]

    log.info("Year recency applied. Score range: %.2f – %.2f",
             df["final_score"].min(), df["final_score"].max())
    return df

"""
GradMap — Bucket Classification Logic
=======================================
Assigns every candidate row to a SAFE / TARGET / AMBITIOUS bucket
based on how the user's percentile compares to the row's cutoff.

This is the psychological backbone of the recommender:
  SAFE       → "You will almost certainly get this."
  TARGET     → "Realistic, but competitive."
  AMBITIOUS  → "Dream college — reach for it."

Author  : GradMap Pipeline
Version : 1.0.0
"""

from __future__ import annotations

import logging

import pandas as pd

from . import config

log = logging.getLogger("gradmap.engine")


def compute_percentile_gap(
    df: pd.DataFrame,
    user_percentile: float,
) -> pd.DataFrame:
    """
    Add `percentile_gap` column.

    Formula:
        gap = user_percentile - percentile_cutoff

    Positive gap  → user is above the cutoff (safer)
    Negative gap  → user is below the cutoff (ambitious)
    """
    df["percentile_gap"] = user_percentile - df["percentile_cutoff"]
    return df


def classify_bucket(gap: float) -> str:
    """
    Classify a single percentile_gap value into a recommendation bucket.

    Thresholds (from config):
        gap >= SAFE_THRESHOLD       → SAFE
        AMBITIOUS_THRESHOLD <= gap  → TARGET
        gap < AMBITIOUS_THRESHOLD   → AMBITIOUS
    """
    if gap >= config.SAFE_THRESHOLD:
        return "SAFE"
    elif gap >= config.AMBITIOUS_THRESHOLD:
        return "TARGET"
    else:
        return "AMBITIOUS"


def assign_buckets(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add `recommendation_bucket` and `bucket_priority` columns.

    Requires `percentile_gap` to already exist (call compute_percentile_gap first).
    """
    df["recommendation_bucket"] = df["percentile_gap"].apply(classify_bucket)
    df["bucket_priority"] = df["recommendation_bucket"].map(config.BUCKET_PRIORITY)

    # Log distribution
    counts = df["recommendation_bucket"].value_counts()
    log.info("Bucket distribution: %s",
             {b: int(counts.get(b, 0)) for b in ("SAFE", "TARGET", "AMBITIOUS")})

    return df

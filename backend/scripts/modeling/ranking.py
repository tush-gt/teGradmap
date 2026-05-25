"""
GradMap — Ranking & Diversity
==============================
Takes scored + bucketed candidate rows and produces the final
ranked recommendation list with diversity guarantees.

Key responsibilities:
  1. Deduplicate (same college + branch across rounds → keep best)
  2. Rank within each bucket by final_score
  3. Fill the SAFE / TARGET / AMBITIOUS split from config
  4. Return a structured grouped result

Author  : GradMap Pipeline
Version : 1.0.0
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from . import config

log = logging.getLogger("gradmap.engine")


def deduplicate_recommendations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove duplicate college+branch entries, keeping only the
    highest-scoring row.

    This prevents the output from being flooded with the same
    college appearing 12 times across different rounds and years.
    """
    before = len(df)

    df = (
        df.sort_values("final_score", ascending=False)
        .drop_duplicates(subset=config.DEDUP_KEY_COLUMNS, keep="first")
    )

    removed = before - len(df)
    if removed > 0:
        log.info("Diversity dedup: removed %d duplicate college+branch combos "
                 "(%d → %d)", removed, before, len(df))
    return df


def _compute_city_priority(college_name: str) -> int:
    """
    Return a numeric priority based on whether the college name
    contains a known city fragment. Lower = better.
    Mumbai = 1, Pune = 2, etc.  Unknown = 999.
    """
    name_lower = college_name.lower()
    for idx, city in enumerate(config.CITY_FRAGMENTS_PRIORITY, start=1):
        if city in name_lower:
            return idx
    return 999


def rank_within_buckets(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sort candidates with a deterministic multi-key ordering:
      1. bucket_priority  ↓  (SAFE first)
      2. institute_tier   ↑  (Tier 1 first)
      3. city_priority    ↑  (Mumbai > Pune > others)
      4. branch_sort_pri  ↑  (CS > Circuits > Mech > ...)
      5. final_score      ↓  (highest score first)
    """
    # Compute sort helpers (cheap, runs on already-filtered ~300 rows)
    df = df.copy()
    df["city_priority"] = df["college_name"].apply(_compute_city_priority)
    df["branch_sort_priority"] = df["branch_family"].map(
        config.BRANCH_FAMILY_SORT_PRIORITY
    ).fillna(999)

    df = df.sort_values(
        by=[
            "bucket_priority",
            "institute_tier",
            "city_priority",
            "branch_sort_priority",
            "final_score",
        ],
        ascending=[False, True, True, True, False],
    )

    # Drop helper columns — they're not needed in the output
    df = df.drop(columns=["city_priority", "branch_sort_priority"])
    return df


def split_by_bucket(
    df: pd.DataFrame,
    top_n: int,
) -> dict[str, pd.DataFrame]:
    """
    Split recommendations into SAFE / TARGET / AMBITIOUS groups,
    respecting the configured split ratios.

    If a bucket has fewer candidates than its allocation, the surplus
    is redistributed to TARGET first, then SAFE.

    Returns:
        {"SAFE": DataFrame, "TARGET": DataFrame, "AMBITIOUS": DataFrame}
    """
    split = config.BUCKET_SPLIT.copy()

    # Scale split to match requested top_n
    total_split = sum(split.values())
    if total_split != top_n:
        ratio = top_n / total_split
        split = {k: max(1, int(v * ratio)) for k, v in split.items()}
        # Adjust rounding to hit exact top_n
        diff = top_n - sum(split.values())
        split["TARGET"] += diff

    groups: dict[str, pd.DataFrame] = {}
    surplus = 0

    for bucket in ("AMBITIOUS", "SAFE", "TARGET"):
        bucket_df = df[df["recommendation_bucket"] == bucket].copy()
        requested = split[bucket] + surplus
        actual = min(len(bucket_df), requested)
        groups[bucket] = bucket_df.head(actual)
        surplus = requested - actual

    # If there's still surplus after all buckets, try to fill from TARGET
    if surplus > 0:
        target_remaining = df[
            (df["recommendation_bucket"] == "TARGET")
            & (~df.index.isin(groups["TARGET"].index))
        ]
        extra = target_remaining.head(surplus)
        groups["TARGET"] = pd.concat([groups["TARGET"], extra])

    for bucket, gdf in groups.items():
        log.info("  %-10s : %d recommendations", bucket, len(gdf))

    return groups


def format_recommendations(
    groups: dict[str, pd.DataFrame],
) -> dict[str, list[dict[str, Any]]]:
    """
    Convert grouped DataFrames into a frontend-friendly dict of lists.

    Each recommendation is a plain dict with the columns defined in
    config.RECOMMENDATION_COLUMNS.
    """
    output_cols = config.RECOMMENDATION_COLUMNS
    result: dict[str, list[dict[str, Any]]] = {}

    for bucket in ("SAFE", "TARGET", "AMBITIOUS"):
        gdf = groups.get(bucket, pd.DataFrame())
        # Only include columns that exist
        cols = [c for c in output_cols if c in gdf.columns]
        result[bucket] = gdf[cols].to_dict(orient="records")

    return result

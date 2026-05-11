"""
GradMap — Recommendation Engine Utilities
==========================================
Shared helpers for dataset loading, validation, and logging setup.

Author  : GradMap Pipeline
Version : 1.0.0
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from . import config

log = logging.getLogger("gradmap.engine")


# ======================================================================
#  DATASET LOADING
# ======================================================================

def load_dataset(path: Path | None = None) -> pd.DataFrame:
    """
    Load the featured master dataset with consistent dtypes.

    Returns a fresh copy every call so callers can mutate freely.
    """
    dataset_path = path or config.DATASET_PATH

    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Featured dataset not found at {dataset_path}. "
            "Run the feature engineering pipeline first."
        )

    df = pd.read_csv(
        dataset_path,
        dtype={"choice_code": str, "institute_code": str},
        low_memory=False,
    )
    log.info("Loaded dataset: %d rows from %s", len(df), dataset_path.name)
    return df


# ======================================================================
#  INPUT VALIDATION
# ======================================================================

_VALID_BRANCH_FAMILIES = {
    "CS_FAMILY", "CIRCUITS_FAMILY", "CORE_MECHANICAL",
    "CIVIL_FAMILY", "CHEMICAL_FAMILY", "OTHER",
}


def validate_user_input(user_input: dict[str, Any]) -> dict[str, Any]:
    """
    Validate and normalise raw user input into a clean request dict.

    Required keys:
        user_percentile     : float  (0–100)
        user_category       : str    (e.g. "GOPEN", "GOBC")
        preferred_branch_family : str | None

    Optional keys:
        preferred_tier      : list[int] | None
        top_n               : int (default from config)
        preferred_location  : str | None  (future placeholder)

    Raises ValueError for invalid inputs.
    """
    # --- required ---
    p = user_input.get("user_percentile")
    if p is None:
        raise ValueError("user_percentile is required.")
    p = float(p)
    if not (0 <= p <= 100):
        raise ValueError(f"user_percentile must be 0–100, got {p}")

    category = user_input.get("user_category")
    if not category or not isinstance(category, str):
        raise ValueError("user_category is required (e.g. 'GOPEN').")
    category = category.strip().upper()

    # --- optional ---
    branch_family = user_input.get("preferred_branch_family")
    if branch_family:
        branch_family = branch_family.strip().upper()
        if branch_family not in _VALID_BRANCH_FAMILIES:
            raise ValueError(
                f"Unknown branch_family '{branch_family}'. "
                f"Valid: {_VALID_BRANCH_FAMILIES}"
            )

    preferred_tier = user_input.get("preferred_tier")
    if preferred_tier is not None:
        if not isinstance(preferred_tier, list):
            preferred_tier = [preferred_tier]
        preferred_tier = [int(t) for t in preferred_tier]
        if not all(t in (1, 2, 3) for t in preferred_tier):
            raise ValueError("preferred_tier values must be 1, 2, or 3.")

    top_n = int(user_input.get("top_n", config.DEFAULT_TOP_N))
    if top_n < 1:
        raise ValueError("top_n must be >= 1.")

    preferred_location = user_input.get("preferred_location")  # future placeholder

    validated = {
        "user_percentile": p,
        "user_category": category,
        "preferred_branch_family": branch_family,
        "preferred_tier": preferred_tier,
        "top_n": top_n,
        "preferred_location": preferred_location,
    }

    log.info("Validated user input: percentile=%.2f, category=%s, branch=%s, tiers=%s, top_n=%d",
             p, category, branch_family, preferred_tier, top_n)
    return validated


# ======================================================================
#  COLUMN CHECKS
# ======================================================================

_REQUIRED_COLUMNS = {
    "college_name", "branch_name", "category", "percentile_cutoff",
    "recommendation_score", "branch_family", "institute_tier",
    "admission_difficulty", "round", "year", "choice_code",
}


def assert_columns(df: pd.DataFrame) -> None:
    """Raise if the dataset is missing expected columns."""
    missing = _REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise RuntimeError(
            f"Dataset is missing columns: {missing}. "
            "Re-run the feature engineering pipeline."
        )


# ======================================================================
#  LOGGING SETUP
# ======================================================================

def setup_logging(level: int = logging.INFO) -> None:
    """Configure the shared logger for the engine package."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

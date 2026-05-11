"""
GradMap — AI Quota Merge Pipeline
===================================
Merges all normalized AI quota CSVs into a single master dataset.

Reads from  : normalized/ai/*.csv
Writes to   : merged/ai/master_ai_dataset.csv

Pipeline:
  1. Discover & load all normalized CSVs
  2. Concatenate into single DataFrame
  3. Add dataset_type column ("AI")
  4. Deduplicate on composite key
  5. Sort (year ↑, round ↑, percentile ↓)
  6. Validate
  7. Export

Author  : GradMap Pipeline
Version : 1.0.0
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

# ──────────────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "normalized" / "ai"
OUTPUT_DIR = BASE_DIR / "merged" / "ai"
OUTPUT_FILE = OUTPUT_DIR / "master_ai_dataset.csv"

DATASET_TYPE = "AI"

DEDUP_COLS = ["year", "round", "choice_code", "category", "percentile_cutoff"]

# ──────────────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("merge_ai")


# ======================================================================
#  LOAD
# ======================================================================

def load_all_csvs(input_dir: Path) -> pd.DataFrame:
    """Discover and concatenate all normalized CSVs."""
    csv_files = sorted(input_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {input_dir}")

    frames: list[pd.DataFrame] = []
    for f in csv_files:
        df = pd.read_csv(f, dtype={"choice_code": str, "institute_code": str})
        log.info("  Loaded %-45s  %6d rows", f.name, len(df))
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    log.info("Total rows loaded: %d  (from %d files)", len(combined), len(csv_files))
    return combined


# ======================================================================
#  DEDUPLICATION
# ======================================================================

def deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicates on the composite key."""
    before = len(df)
    df = df.drop_duplicates(subset=DEDUP_COLS, keep="first")
    removed = before - len(df)
    log.info("Deduplication: removed %d duplicates (%d → %d)", removed, before, len(df))
    return df


# ======================================================================
#  SORTING
# ======================================================================

def sort_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Sort by year ↑, round ↑, percentile_cutoff ↓."""
    df = df.sort_values(
        by=["year", "round", "percentile_cutoff"],
        ascending=[True, True, False],
    ).reset_index(drop=True)
    log.info("Sorted dataset: year ↑, round ↑, percentile ↓")
    return df


# ======================================================================
#  VALIDATION
# ======================================================================

def validate(df: pd.DataFrame) -> pd.DataFrame:
    """Validate rows and log summary statistics."""
    initial = len(df)

    # Filter invalid rows
    df = df[
        df["institute_code"].notna()
        & df["college_name"].notna()
        & (df["college_name"] != "")
        & df["branch_name"].notna()
        & (df["branch_name"] != "")
        & (df["percentile_cutoff"] >= 0)
        & (df["percentile_cutoff"] <= 100)
    ]

    removed = initial - len(df)
    if removed > 0:
        log.warning("Validation: removed %d invalid rows", removed)

    # Summary stats
    log.info("─" * 50)
    log.info("DATASET SUMMARY")
    log.info("  Total rows       : %d", len(df))
    log.info("  Year range       : %d – %d", df["year"].min(), df["year"].max())
    log.info("  Rounds           : %s", sorted(df["round"].unique()))
    log.info("  Unique colleges  : %d", df["college_name"].nunique())
    log.info("  Unique branches  : %d", df["branch_name"].nunique())
    log.info("  Unique categories: %d", df["category"].nunique())
    log.info("  UNKNOWN branches : %d", (df["branch_name"] == "UNKNOWN").sum())
    log.info("─" * 50)

    return df


# ======================================================================
#  EXPORT
# ======================================================================

def export(df: pd.DataFrame, output_path: Path) -> None:
    """Write final merged CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    size_mb = output_path.stat().st_size / (1024 * 1024)
    log.info("Exported: %s  (%.2f MB)", output_path.name, size_mb)


# ======================================================================
#  MAIN
# ======================================================================

def main() -> None:
    log.info("═" * 50)
    log.info("GradMap — AI Quota Merge Pipeline")
    log.info("═" * 50)

    # 1. Load
    df = load_all_csvs(INPUT_DIR)

    # 2. Add dataset_type
    df["dataset_type"] = DATASET_TYPE

    # 3. Deduplicate
    df = deduplicate(df)

    # 4. Sort
    df = sort_dataset(df)

    # 5. Validate
    df = validate(df)

    # 6. Export
    export(df, OUTPUT_FILE)

    log.info("═" * 50)
    log.info("MERGE COMPLETE")
    log.info("═" * 50)


if __name__ == "__main__":
    main()

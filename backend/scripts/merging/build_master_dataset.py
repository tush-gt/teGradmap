"""
GradMap — Final Dataset Consolidation
======================================
Combines the AI and MH master datasets into a single canonical dataset.

Reads from  : merged/ai/master_ai_dataset.csv
              merged/mh/master_mh_dataset.csv
Writes to   : merged/master_combined_dataset.csv
              analytics/dataset_summary.json
              analytics/dataset_summary.txt

Pipeline:
  1. Load AI and MH master datasets
  2. Concatenate into single DataFrame
  3. Generate stable deterministic row_id (UUID5 over composite key)
  4. Deduplicate on composite key
  5. Sort (year ↑, round ↑, percentile ↓)
  6. Validate
  7. Export combined CSV + analytics metadata

Author  : GradMap Pipeline
Version : 1.0.0
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

# ──────────────────────────────────────────────────────────────────────
# Paths (all relative to project root — never hardcoded absolute paths)
# ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
MERGED_DIR = BASE_DIR / "merged"
ANALYTICS_DIR = BASE_DIR / "analytics"

AI_INPUT = MERGED_DIR / "ai" / "master_ai_dataset.csv"
MH_INPUT = MERGED_DIR / "mh" / "master_mh_dataset.csv"
COMBINED_OUTPUT = MERGED_DIR / "master_combined_dataset.csv"
SUMMARY_JSON = ANALYTICS_DIR / "dataset_summary.json"
SUMMARY_TXT = ANALYTICS_DIR / "dataset_summary.txt"

# Composite key used for deduplication AND row_id generation
DEDUP_COLS = ["year", "round", "choice_code", "category", "percentile_cutoff"]

# Final column order (row_id prepended to canonical schema)
OUTPUT_COLUMNS = [
    "row_id",
    "year",
    "round",
    "quota_type",
    "choice_code",
    "exam_type",
    "institute_code",
    "college_name",
    "branch_code",
    "branch_name",
    "category",
    "percentile_cutoff",
    "rank_cutoff",
    "source_file",
    "dataset_type",
]

# ──────────────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("build_master")


# ======================================================================
#  LOAD
# ======================================================================

def load_dataset(path: Path, label: str) -> pd.DataFrame:
    """Load a single master CSV with consistent dtypes."""
    df = pd.read_csv(path, dtype={"choice_code": str, "institute_code": str})
    log.info("Loaded %-6s  %7d rows  ←  %s", label, len(df), path.name)
    return df


def load_both() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load AI and MH master datasets and return as separate DataFrames."""
    ai_df = load_dataset(AI_INPUT, "AI")
    mh_df = load_dataset(MH_INPUT, "MH")
    return ai_df, mh_df


# ======================================================================
#  ROW ID GENERATION
# ======================================================================

def _make_row_id(row: pd.Series) -> str:
    """
    Generate a deterministic, stable row_id using SHA-256 over the
    composite key: [year, round, choice_code, category, percentile_cutoff].

    Using SHA-256 (truncated to 16 hex chars) instead of random UUIDs
    so the same logical row always gets the same ID across runs.
    This supports frontend linking, debugging, and bookmarking.
    """
    key = "|".join([
        str(row["year"]),
        str(row["round"]),
        str(row["choice_code"]),
        str(row["category"]),
        str(row["percentile_cutoff"]),
    ])
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def add_row_ids(df: pd.DataFrame) -> pd.DataFrame:
    """Vectorised row_id generation over the full DataFrame."""
    # Build key series once — faster than apply on individual rows
    key_series = (
        df["year"].astype(str) + "|"
        + df["round"].astype(str) + "|"
        + df["choice_code"].astype(str) + "|"
        + df["category"].astype(str) + "|"
        + df["percentile_cutoff"].astype(str)
    )
    df["row_id"] = key_series.apply(
        lambda k: hashlib.sha256(k.encode()).hexdigest()[:16]
    )
    log.info("Generated %d row_ids (deterministic SHA-256)", len(df))
    return df


# ======================================================================
#  DEDUPLICATION
# ======================================================================

def deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove semantic duplicates using the composite key.
    Keeps the first occurrence (AI rows load first → AI wins ties).
    Also checks row_id uniqueness after dedup.
    """
    before = len(df)
    df = df.drop_duplicates(subset=DEDUP_COLS, keep="first")
    removed = before - len(df)
    log.info("Deduplication: removed %d semantic duplicates (%d → %d)",
             removed, before, len(df))

    # Verify row_id uniqueness
    dup_ids = df["row_id"].duplicated().sum()
    if dup_ids > 0:
        log.warning("  %d duplicate row_ids detected — investigate composite key collisions", dup_ids)
    else:
        log.info("  row_id uniqueness check: PASSED")

    return df


# ======================================================================
#  SORTING
# ======================================================================

def sort_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Sort: year ↑, round ↑, percentile_cutoff ↓."""
    df = df.sort_values(
        by=["year", "round", "percentile_cutoff"],
        ascending=[True, True, False],
    ).reset_index(drop=True)
    log.info("Sorted: year ↑, round ↑, percentile ↓")
    return df


# ======================================================================
#  VALIDATION
# ======================================================================

def validate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate all rows and remove those failing schema constraints.
    Logs a full summary including unique counts per dimension.
    """
    initial = len(df)

    # Drop rows violating schema constraints
    df = df[
        df["institute_code"].notna()
        & df["college_name"].notna()
        & (df["college_name"].str.strip() != "")
        & df["branch_name"].notna()
        & (df["branch_name"].str.strip() != "")
        & (df["percentile_cutoff"] >= 0)
        & (df["percentile_cutoff"] <= 100)
    ]

    removed = initial - len(df)
    if removed > 0:
        log.warning("Validation: removed %d invalid rows", removed)

    log.info("─" * 50)
    log.info("COMBINED DATASET SUMMARY")
    log.info("  Total rows       : %d", len(df))
    log.info("  AI rows          : %d", (df["dataset_type"] == "AI").sum())
    log.info("  MH rows          : %d", (df["dataset_type"] == "MH").sum())
    log.info("  Year range       : %d – %d", df["year"].min(), df["year"].max())
    log.info("  Years covered    : %s", sorted(df["year"].unique().tolist()))
    log.info("  Rounds           : %s", sorted(df["round"].unique().tolist()))
    log.info("  Unique colleges  : %d", df["college_name"].nunique())
    log.info("  Unique branches  : %d", df["branch_name"].nunique())
    log.info("  Unique categories: %d", df["category"].nunique())
    log.info("  Percentile range : %.4f – %.4f",
             df["percentile_cutoff"].min(), df["percentile_cutoff"].max())
    log.info("  UNKNOWN branches : %d", (df["branch_name"] == "UNKNOWN").sum())
    log.info("─" * 50)

    return df


# ======================================================================
#  EXPORT DATASET
# ======================================================================

def export_dataset(df: pd.DataFrame) -> None:
    """Write final combined CSV, preserving column order."""
    COMBINED_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    # Ensure output_columns that exist are written in order; add any
    # extras at the end so future schema additions don't break the export
    present = [c for c in OUTPUT_COLUMNS if c in df.columns]
    extras = [c for c in df.columns if c not in OUTPUT_COLUMNS]
    final_cols = present + extras

    df[final_cols].to_csv(COMBINED_OUTPUT, index=False)
    size_mb = COMBINED_OUTPUT.stat().st_size / (1024 * 1024)
    log.info("Exported: %s  (%.2f MB)", COMBINED_OUTPUT.name, size_mb)


# ======================================================================
#  ANALYTICS METADATA EXPORT
# ======================================================================

def build_summary(df: pd.DataFrame) -> dict[str, Any]:
    """Build the analytics summary dictionary."""
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total_rows": int(len(df)),
        "ai_rows": int((df["dataset_type"] == "AI").sum()),
        "mh_rows": int((df["dataset_type"] == "MH").sum()),
        "unique_colleges": int(df["college_name"].nunique()),
        "unique_branches": int(df["branch_name"].nunique()),
        "unique_categories": int(df["category"].nunique()),
        "unique_choice_codes": int(df["choice_code"].nunique()),
        "years_covered": sorted(df["year"].unique().tolist()),
        "rounds_covered": sorted(df["round"].unique().tolist()),
        "min_percentile": round(float(df["percentile_cutoff"].min()), 6),
        "max_percentile": round(float(df["percentile_cutoff"].max()), 6),
        "unknown_branches": int((df["branch_name"] == "UNKNOWN").sum()),
        "source_files": sorted(df["source_file"].dropna().unique().tolist()),
    }


def export_summary_json(summary: dict[str, Any]) -> None:
    """Write analytics/dataset_summary.json."""
    ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)
    with open(SUMMARY_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    log.info("Exported: %s", SUMMARY_JSON.name)


def export_summary_txt(summary: dict[str, Any]) -> None:
    """
    Write analytics/dataset_summary.txt — human-readable version
    intended for PPTs, demos, interviews, and documentation.
    """
    ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)

    lines = [
        "=" * 56,
        "  GradMap — Dataset Summary",
        "=" * 56,
        f"  Generated at       : {summary['generated_at']}",
        "",
        "  SCALE",
        f"  Total rows         : {summary['total_rows']:,}",
        f"  AI quota rows      : {summary['ai_rows']:,}",
        f"  MH quota rows      : {summary['mh_rows']:,}",
        "",
        "  COVERAGE",
        f"  Years covered      : {summary['years_covered']}",
        f"  Rounds covered     : {summary['rounds_covered']}",
        "",
        "  DIMENSIONALITY",
        f"  Unique colleges    : {summary['unique_colleges']:,}",
        f"  Unique branches    : {summary['unique_branches']:,}",
        f"  Unique categories  : {summary['unique_categories']:,}",
        f"  Unique choice codes: {summary['unique_choice_codes']:,}",
        "",
        "  CUTOFF RANGE",
        f"  Min percentile     : {summary['min_percentile']}",
        f"  Max percentile     : {summary['max_percentile']}",
        "",
        "  DATA QUALITY",
        f"  UNKNOWN branches   : {summary['unknown_branches']:,}",
        "=" * 56,
    ]

    with open(SUMMARY_TXT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log.info("Exported: %s", SUMMARY_TXT.name)


# ======================================================================
#  MAIN
# ======================================================================

def main() -> None:
    log.info("═" * 56)
    log.info("GradMap — Final Dataset Consolidation")
    log.info("═" * 56)

    # 1. Load
    ai_df, mh_df = load_both()
    ai_count = len(ai_df)
    mh_count = len(mh_df)

    # 2. Concatenate (AI first → wins ties in dedup)
    df = pd.concat([ai_df, mh_df], ignore_index=True)
    log.info("Combined: %d rows (AI=%d, MH=%d)", len(df), ai_count, mh_count)

    # 3. Generate stable row_ids BEFORE dedup
    #    (so IDs reflect the composite key, not insertion order)
    df = add_row_ids(df)

    # 4. Deduplicate (and verify row_id uniqueness)
    df = deduplicate(df)

    # 5. Sort
    df = sort_dataset(df)

    # 6. Validate + log summary
    df = validate(df)

    # 7. Export combined CSV
    export_dataset(df)

    # 8. Build and export analytics metadata
    summary = build_summary(df)
    export_summary_json(summary)
    export_summary_txt(summary)

    log.info("═" * 56)
    log.info("CONSOLIDATION COMPLETE")
    log.info("  Output : %s", COMBINED_OUTPUT)
    log.info("  JSON   : %s", SUMMARY_JSON)
    log.info("  TXT    : %s", SUMMARY_TXT)
    log.info("═" * 56)


if __name__ == "__main__":
    main()

"""
GradMap — Quality Filtering & Dataset Quarantine
================================================
Filters the master combined dataset into clean, unknown-branch, and corrupted segments.

Architecture:
master_combined_dataset.csv
        ↓
quality_filter.py
        ↓
clean_recommendation_dataset.csv  (Validated rows for the engine)
potential_corrupted.csv          (Suspicious or invalid rows)
unknown_branch.csv               (Rows with missing branch info)

Metrics:
analytics/final_metrics.json
analytics/final_metrics.txt

Author  : GradMap Pipeline
Version : 1.0.0
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

# ──────────────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
MERGED_DIR = BASE_DIR / "merged"
ANALYTICS_DIR = BASE_DIR / "analytics"

INPUT_FILE = MERGED_DIR / "master_combined_dataset.csv"

# Output files
CLEAN_OUTPUT = ANALYTICS_DIR / "clean_recommendation_dataset.csv"
CORRUPTED_OUTPUT = ANALYTICS_DIR / "potential_corrupted.csv"
UNKNOWN_OUTPUT = ANALYTICS_DIR / "unknown_branch.csv"
METRICS_JSON = ANALYTICS_DIR / "final_metrics.json"
METRICS_TXT = ANALYTICS_DIR / "final_metrics.txt"

# ──────────────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("quality_filter")


def main() -> None:
    log.info("═" * 56)
    log.info("GradMap — Quality Filtering Stage")
    log.info("═" * 56)

    if not INPUT_FILE.exists():
        log.error("Input file not found: %s", INPUT_FILE)
        return

    # 1. Load Master Dataset
    log.info("Loading master combined dataset...")
    df = pd.read_csv(INPUT_FILE, dtype={"choice_code": str, "institute_code": str})
    total_input = len(df)
    log.info("Total rows loaded: %d", total_input)

    # 2. Define Filters
    # Corruption Filters
    invalid_p_mask = (df["percentile_cutoff"] <= 0) | (df["percentile_cutoff"] >= 100)
    contamination_mask = df["college_name"].str.contains("JEE\(Main\)", na=False, case=False)
    
    corrupted_mask = invalid_p_mask | contamination_mask
    
    # Unknown Branch Filter (exclude already corrupted rows to keep sets clean)
    unknown_branch_mask = df["branch_name"].str.contains("UNKNOWN", na=False, case=False) & ~corrupted_mask

    # 3. Create Corrupted Segment
    df_corrupted = df[corrupted_mask].copy()
    
    def get_reason(row):
        reasons = []
        if (row["percentile_cutoff"] <= 0) or (row["percentile_cutoff"] >= 100):
            reasons.append("INVALID_PERCENTILE")
        if "JEE(Main)" in str(row["college_name"]):
            reasons.append("POSSIBLE_ROW_CONTAMINATION")
        return " | ".join(reasons)

    if len(df_corrupted) > 0:
        df_corrupted["corruption_reason"] = df_corrupted.apply(get_reason, axis=1)
    else:
        df_corrupted["corruption_reason"] = None

    # 4. Create Unknown Branch Segment
    df_unknown = df[unknown_branch_mask].copy()
    df_unknown["possible_branch_match"] = ""
    df_unknown["recovery_status"] = "NOT_RECOVERED"

    # 5. Create Clean Segment
    df_clean = df[~(corrupted_mask | unknown_branch_mask)].copy()

    # 6. Validation of Counts
    total_output = len(df_clean) + len(df_corrupted) + len(df_unknown)
    if total_input != total_output:
        log.warning("Count mismatch! Input: %d, Sum of segments: %d", total_input, total_output)

    # 7. Export Datasets
    ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)
    
    df_clean.to_csv(CLEAN_OUTPUT, index=False)
    df_corrupted.to_csv(CORRUPTED_OUTPUT, index=False)
    df_unknown.to_csv(UNKNOWN_OUTPUT, index=False)
    
    log.info("Exported segments to %s", ANALYTICS_DIR)

    # 8. Build Metrics
    metrics = {
        "potential_corrupted_rows": int(len(df_corrupted)),
        "unknown_branch_rows": int(len(df_unknown)),
        "clean_recommendation_rows": int(len(df_clean)),
        "total_rows": int(total_input),
        "corruption_breakdown": {
            "invalid_percentile": int(invalid_p_mask.sum()),
            "row_contamination": int(contamination_mask.sum())
        }
    }

    # Export Metrics
    with open(METRICS_JSON, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    
    with open(METRICS_TXT, "w", encoding="utf-8") as f:
        f.write("=" * 40 + "\n")
        f.write("     GradMap Final Metrics\n")
        f.write("=" * 40 + "\n")
        f.write(f"Potential corrupted rows  : {metrics['potential_corrupted_rows']:,}\n")
        f.write(f"UNKNOWN branch rows       : {metrics['unknown_branch_rows']:,}\n")
        f.write(f"Clean recommendation rows : {metrics['clean_recommendation_rows']:,}\n")
        f.write("-" * 40 + "\n")
        f.write(f"Total rows processed      : {metrics['total_rows']:,}\n")
        f.write("=" * 40 + "\n")

    log.info("═" * 56)
    log.info("QUALITY FILTERING COMPLETE")
    log.info("  Clean rows    : %d", len(df_clean))
    log.info("  Corrupted     : %d", len(df_corrupted))
    log.info("  Unknown Br    : %d", len(df_unknown))
    log.info("═" * 56)


if __name__ == "__main__":
    main()

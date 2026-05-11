"""
GradMap — AI Quota Normalization Pipeline
==========================================
Normalizes extracted AI quota CSVs into a clean, consistent format.

This script is **normalization only** — it does NOT do extraction.
It reads from  : extracted/ai/*.csv
It writes to   : normalized/ai/*.csv
It loads maps  : configs/college_name_map.json
                 configs/branch_name_map.json

Pipeline stages (in order):
  1. Load extracted CSVs
  2. Clean whitespace & standardize text
  3. Normalize college names  (college_name_map.json)
  4. Normalize branch names   (branch_name_map.json)
  5. Recover UNKNOWN branches (choice_code majority mapping)
  6. Validate rows
  7. Deduplicate
  8. Export normalized CSVs

Author  : GradMap Pipeline
Version : 1.0.0
"""

from __future__ import annotations

import json
import logging
import argparse
from pathlib import Path
from collections import Counter
from typing import Optional

import pandas as pd

# ──────────────────────────────────────────────────────────────────────
# Project paths (all relative to project root)
# ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIGS_DIR = BASE_DIR / "configs"
COLLEGE_MAP_PATH = CONFIGS_DIR / "college_name_map.json"
BRANCH_MAP_PATH = CONFIGS_DIR / "branch_name_map.json"
DEFAULT_INPUT_DIR = BASE_DIR / "extracted" / "ai"
DEFAULT_OUTPUT_DIR = BASE_DIR / "normalized" / "ai"

# ──────────────────────────────────────────────────────────────────────
# Canonical schema — output columns in exact order
# ──────────────────────────────────────────────────────────────────────
OUTPUT_COLUMNS = [
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
]

# ──────────────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("normalize_ai")


# ======================================================================
#  MAP LOADERS
# ======================================================================

def load_college_map(path: Path) -> dict[str, str]:
    """
    Load college_name_map.json and build a reverse lookup:
      variation (lowercased, stripped) → canonical name

    Structure of college_name_map.json:
      { "College Name -> Variations": {
            "Canonical Name": ["variation1", "variation2", ...]
        }
      }
    """
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    inner = raw.get("College Name -> Variations", {})
    lookup: dict[str, str] = {}

    for canonical, variations in inner.items():
        # Also index the canonical name itself (lowered)
        lookup[canonical.strip().lower()] = canonical
        for var in variations:
            key = var.strip().lower()
            if key in lookup and lookup[key] != canonical:
                log.debug(
                    "College map collision: '%s' mapped to both '%s' and '%s' — keeping first",
                    key, lookup[key], canonical,
                )
                continue
            lookup[key] = canonical

    log.info("Loaded college map: %d variations → %d canonical names",
             len(lookup), len(inner))
    return lookup


def load_branch_map(path: Path) -> dict[str, str]:
    """
    Load branch_name_map.json and build a reverse lookup:
      variant (lowercased, stripped) → canonical name

    Structure of branch_name_map.json:
      { "_meta": { ... },
        "Canonical Branch": ["variant1", "variant2", ...],
        ...
      }
    """
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    lookup: dict[str, str] = {}
    canonical_count = 0

    for canonical, variants in raw.items():
        if canonical == "_meta":
            continue
        canonical_count += 1

        # Also index the canonical name itself
        lookup[canonical.strip().lower()] = canonical
        for var in variants:
            key = var.strip().lower()
            if key in lookup and lookup[key] != canonical:
                log.debug(
                    "Branch map collision: '%s' mapped to both '%s' and '%s' — keeping first",
                    key, lookup[key], canonical,
                )
                continue
            lookup[key] = canonical

    log.info("Loaded branch map: %d variants → %d canonical branches",
             len(lookup), canonical_count)
    return lookup


# ======================================================================
#  TEXT CLEANING
# ======================================================================

def clean_text(val: object) -> Optional[str]:
    """Strip whitespace, collapse newlines, normalize spacing."""
    if pd.isna(val):
        return None
    s = str(val)
    # Replace literal newlines and carriage returns
    s = s.replace("\n", " ").replace("\r", " ")
    # Collapse multiple spaces
    s = " ".join(s.split())
    return s.strip()


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Stage 1: Basic text cleaning on all string columns.
    - Strip whitespace from every string cell
    - Collapse embedded newlines
    - Standardize institute_code to string (zero-padded is fine)
    """
    text_cols = ["college_name", "branch_name", "category",
                 "exam_type", "quota_type", "source_file", "choice_code"]

    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].apply(clean_text)

    # Ensure institute_code is string for consistent handling
    df["institute_code"] = df["institute_code"].apply(
        lambda x: str(int(x)) if pd.notna(x) else None
    )

    return df


# ======================================================================
#  COLLEGE NAME NORMALIZATION
# ======================================================================

def normalize_college_names(
    df: pd.DataFrame,
    college_lookup: dict[str, str],
) -> pd.DataFrame:
    """
    Stage 2: Map every college_name to its canonical form using the
    college_name_map.json lookup.

    Matching strategy:
      1. Exact match (case-insensitive, stripped)
      2. If no match → keep original (log warning)
    """
    unmapped: Counter = Counter()
    mapped_count = 0

    def _normalize(name: Optional[str]) -> Optional[str]:
        nonlocal mapped_count
        if name is None:
            return None
        key = name.strip().lower()
        canonical = college_lookup.get(key)
        if canonical is not None:
            mapped_count += 1
            return canonical
        # No match — keep original, track for reporting
        unmapped[name] += 1
        return name

    df["college_name"] = df["college_name"].apply(_normalize)

    total = len(df)
    log.info("College normalization: %d/%d mapped (%.1f%%)",
             mapped_count, total, 100.0 * mapped_count / max(total, 1))

    if unmapped:
        log.warning("  %d unique unmapped college names (%d rows total)",
                     len(unmapped), sum(unmapped.values()))
        # Show top 10 unmapped for debugging
        for name, count in unmapped.most_common(10):
            log.warning("    [%d rows] %s", count, name)

    return df


# ======================================================================
#  BRANCH NAME NORMALIZATION
# ======================================================================

def normalize_branch_names(
    df: pd.DataFrame,
    branch_lookup: dict[str, str],
) -> pd.DataFrame:
    """
    Stage 3: Map every branch_name to its canonical form using the
    branch_name_map.json lookup.

    Matching strategy:
      1. Exact match on lowered+stripped text
      2. If branch is UNKNOWN → leave as-is (will be recovered later)
      3. If no match → keep original, log warning
    """
    unmapped: Counter = Counter()
    mapped_count = 0
    unknown_count = 0

    def _normalize(name: Optional[str]) -> Optional[str]:
        nonlocal mapped_count, unknown_count
        if name is None:
            return None
        if name == "UNKNOWN":
            unknown_count += 1
            return "UNKNOWN"

        key = name.strip().lower()
        canonical = branch_lookup.get(key)
        if canonical is not None:
            mapped_count += 1
            return canonical
        # No match
        unmapped[name] += 1
        return name

    df["branch_name"] = df["branch_name"].apply(_normalize)

    total = len(df)
    log.info("Branch normalization: %d/%d mapped, %d UNKNOWN (%.1f%% hit rate)",
             mapped_count, total - unknown_count,
             unknown_count,
             100.0 * mapped_count / max(total - unknown_count, 1))

    if unmapped:
        log.warning("  %d unique unmapped branch names (%d rows total)",
                     len(unmapped), sum(unmapped.values()))
        for name, count in unmapped.most_common(10):
            log.warning("    [%d rows] %s", count, name)

    return df


# ======================================================================
#  UNKNOWN BRANCH RECOVERY
# ======================================================================

def recover_unknown_branches(df: pd.DataFrame) -> pd.DataFrame:
    """
    Stage 4: Use choice_code → branch_name majority mapping to
    recover rows where branch_name == 'UNKNOWN'.

    Logic:
      1. Build a mapping from choice_code → branch_name using only
         rows where branch_name is NOT 'UNKNOWN'.
      2. For each choice_code, pick the most common branch_name
         (majority vote).
      3. Apply the mapping to all UNKNOWN rows.
      4. Any remaining UNKNOWN rows (no known mapping exists) stay
         as 'UNKNOWN' and are logged.
    """
    known = df[df["branch_name"] != "UNKNOWN"]
    unknown_mask = df["branch_name"] == "UNKNOWN"
    unknown_count_before = unknown_mask.sum()

    if unknown_count_before == 0:
        log.info("UNKNOWN branch recovery: no UNKNOWN rows — skipped")
        return df

    # Build choice_code → branch_name majority mapping
    # Group known rows by choice_code, pick most frequent branch_name
    code_branch_map: dict[str, str] = {}
    grouped = known.groupby("choice_code")["branch_name"]

    for code, branch_series in grouped:
        counts = branch_series.value_counts()
        if len(counts) > 0:
            code_branch_map[code] = counts.index[0]

    # Apply recovery
    recovered = 0
    still_unknown = 0

    def _recover(row: pd.Series) -> str:
        nonlocal recovered, still_unknown
        if row["branch_name"] != "UNKNOWN":
            return row["branch_name"]
        mapped = code_branch_map.get(row["choice_code"])
        if mapped is not None:
            recovered += 1
            return mapped
        still_unknown += 1
        return "UNKNOWN"

    df["branch_name"] = df.apply(_recover, axis=1)

    log.info("UNKNOWN branch recovery: %d/%d recovered, %d still UNKNOWN",
             recovered, unknown_count_before, still_unknown)

    # Log remaining UNKNOWN rows for manual inspection
    remaining = df[df["branch_name"] == "UNKNOWN"]
    if not remaining.empty:
        for _, row in remaining.iterrows():
            log.warning("  Still UNKNOWN: choice_code=%s, college=%s",
                         row["choice_code"], row["college_name"])

    return df


# ======================================================================
#  VALIDATION
# ======================================================================

def validate_dataframe(df: pd.DataFrame, filename: str) -> pd.DataFrame:
    """
    Stage 5: Validate each row and log anomalies.
    Returns a cleaned DataFrame with invalid rows removed.

    Checks:
      1. percentile_cutoff must be between 0 and 100
      2. institute_code must not be null
      3. college_name must not be empty
      4. branch_name must not be empty
      5. Count remaining UNKNOWN branches
    """
    initial_count = len(df)
    issues: list[str] = []

    # 1. Percentile range check
    bad_perc = df[
        (df["percentile_cutoff"] < 0) | (df["percentile_cutoff"] > 100)
    ]
    if not bad_perc.empty:
        issues.append(f"percentile out of [0,100]: {len(bad_perc)} rows")
        df = df[
            (df["percentile_cutoff"] >= 0) & (df["percentile_cutoff"] <= 100)
        ]

    # 2. Null institute_code
    null_inst = df["institute_code"].isna()
    if null_inst.any():
        issues.append(f"null institute_code: {null_inst.sum()} rows")
        df = df[~null_inst]

    # 3. Empty college_name
    empty_college = df["college_name"].isna() | (df["college_name"] == "")
    if empty_college.any():
        issues.append(f"empty college_name: {empty_college.sum()} rows")
        df = df[~empty_college]

    # 4. Empty branch_name
    empty_branch = df["branch_name"].isna() | (df["branch_name"] == "")
    if empty_branch.any():
        issues.append(f"empty branch_name: {empty_branch.sum()} rows")
        df = df[~empty_branch]

    # 5. Count remaining UNKNOWN branches
    unknown_branches = (df["branch_name"] == "UNKNOWN").sum()
    if unknown_branches > 0:
        issues.append(f"UNKNOWN branch_name: {unknown_branches} rows")

    removed = initial_count - len(df)
    if issues:
        log.warning("Validation [%s]: %s (removed %d rows)",
                     filename, "; ".join(issues), removed)
    else:
        log.info("Validation [%s]: all %d rows passed", filename, len(df))

    return df


# ======================================================================
#  DEDUPLICATION
# ======================================================================

def deduplicate(df: pd.DataFrame, filename: str) -> pd.DataFrame:
    """
    Stage 6: Remove duplicate rows based on the composite key:
      [year, round, choice_code, category, percentile_cutoff]

    This is a semantic dedup — two rows with the same institute+branch+
    category+round at the same cutoff are truly duplicates, even if
    other fields differ slightly (e.g. whitespace in college_name).
    """
    dedup_cols = ["year", "round", "choice_code", "category", "percentile_cutoff"]
    before = len(df)
    df = df.drop_duplicates(subset=dedup_cols, keep="first")
    after = len(df)
    removed = before - after

    if removed > 0:
        log.info("Deduplication [%s]: removed %d dupes (%d → %d)",
                 filename, removed, before, after)
    else:
        log.info("Deduplication [%s]: no duplicates found (%d rows)",
                 filename, after)

    return df


# ======================================================================
#  SINGLE-FILE PIPELINE
# ======================================================================

def normalize_file(
    csv_path: Path,
    output_dir: Path,
    college_lookup: dict[str, str],
    branch_lookup: dict[str, str],
) -> dict:
    """
    Run the full normalization pipeline on a single extracted CSV.
    Returns a stats dict for batch reporting.
    """
    filename = csv_path.name
    log.info("── Normalizing: %s", filename)

    # Load
    df = pd.read_csv(csv_path)
    initial_count = len(df)
    log.info("   Loaded %d rows", initial_count)

    # Stage 1: Clean text
    df = clean_dataframe(df)

    # Stage 2: Normalize college names
    df = normalize_college_names(df, college_lookup)

    # Stage 3: Normalize branch names
    df = normalize_branch_names(df, branch_lookup)

    # Stage 4: Recover UNKNOWN branches via choice_code mapping
    df = recover_unknown_branches(df)

    # Stage 5: Validate
    df = validate_dataframe(df, filename)

    # Stage 6: Deduplicate
    df = deduplicate(df, filename)

    # Stage 7: Export
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename

    # Ensure column order matches schema exactly
    df = df[OUTPUT_COLUMNS]
    df.to_csv(output_path, index=False)

    final_count = len(df)
    unknown_remaining = (df["branch_name"] == "UNKNOWN").sum()

    log.info("   Output: %s (%d rows)", output_path.name, final_count)

    return {
        "file": filename,
        "input_rows": initial_count,
        "output_rows": final_count,
        "removed": initial_count - final_count,
        "unknown_branches": unknown_remaining,
    }


# ======================================================================
#  GLOBAL CROSS-FILE UNKNOWN RECOVERY
# ======================================================================

def global_unknown_recovery(output_dir: Path) -> int:
    """
    After all files have been individually normalized, run a second
    pass using the COMBINED choice_code→branch_name knowledge from
    ALL normalized files.

    This recovers UNKNOWNs in 2022/2023 PDFs where branch names were
    lost during extraction, but the same choice_code appears with a
    known branch in other years (e.g. 2024/2025).

    Returns the number of rows recovered.
    """
    csv_files = sorted(output_dir.glob("*.csv"))
    if not csv_files:
        return 0

    # Load all normalized files into memory
    file_dfs: dict[str, pd.DataFrame] = {}
    for f in csv_files:
        file_dfs[f.name] = pd.read_csv(f, dtype={"choice_code": str})

    combined = pd.concat(file_dfs.values(), ignore_index=True)
    total_unknown_before = (combined["branch_name"] == "UNKNOWN").sum()

    if total_unknown_before == 0:
        log.info("Global recovery: no UNKNOWN rows across all files — skipped")
        return 0

    # Build global choice_code → branch_name map from ALL known rows
    known = combined[combined["branch_name"] != "UNKNOWN"]
    global_map: dict[str, str] = {}
    for code, branch_series in known.groupby("choice_code")["branch_name"]:
        counts = branch_series.value_counts()
        if len(counts) > 0:
            global_map[str(code)] = counts.index[0]

    log.info("Global recovery: built mapping with %d choice_codes from %d known rows",
             len(global_map), len(known))

    # Apply global recovery to each file individually and re-save
    total_recovered = 0
    for filename, df in file_dfs.items():
        unknown_mask = df["branch_name"] == "UNKNOWN"
        file_unknown = unknown_mask.sum()
        if file_unknown == 0:
            continue

        recovered_in_file = 0
        for idx in df.index[unknown_mask]:
            code = str(df.at[idx, "choice_code"])
            mapped = global_map.get(code)
            if mapped is not None:
                df.at[idx, "branch_name"] = mapped
                recovered_in_file += 1

        if recovered_in_file > 0:
            # Re-save the file
            output_path = output_dir / filename
            df.to_csv(output_path, index=False)
            total_recovered += recovered_in_file
            still_unknown = (df["branch_name"] == "UNKNOWN").sum()
            log.info("  %s: recovered %d/%d UNKNOWN (%d remaining)",
                     filename, recovered_in_file, file_unknown, still_unknown)

    total_unknown_after = total_unknown_before - total_recovered
    log.info("Global recovery complete: %d/%d recovered, %d still UNKNOWN",
             total_recovered, total_unknown_before, total_unknown_after)

    return total_recovered


# ======================================================================
#  BATCH RUNNER
# ======================================================================

def run_batch(input_dir: Path, output_dir: Path) -> None:
    """
    Discover all extracted AI CSVs, load config maps once,
    then normalize each file through the pipeline.
    After all files are processed, run a global cross-file
    UNKNOWN branch recovery pass.
    """
    # Load normalization maps (once for the whole batch)
    if not COLLEGE_MAP_PATH.exists():
        log.error("College map not found at %s", COLLEGE_MAP_PATH)
        return
    if not BRANCH_MAP_PATH.exists():
        log.error("Branch map not found at %s", BRANCH_MAP_PATH)
        return

    college_lookup = load_college_map(COLLEGE_MAP_PATH)
    branch_lookup = load_branch_map(BRANCH_MAP_PATH)

    # Discover input files
    if input_dir.is_file():
        csv_files = [input_dir]
    elif input_dir.is_dir():
        csv_files = sorted(input_dir.glob("*.csv"))
    else:
        log.error("Input path does not exist: %s", input_dir)
        return

    if not csv_files:
        log.error("No CSV files found in %s", input_dir)
        return

    log.info("Found %d extracted AI CSV(s) in %s", len(csv_files), input_dir)
    log.info("Output directory: %s", output_dir)
    log.info("═" * 50)

    # ── Pass 1: Per-file normalization ──
    all_stats: list[dict] = []
    for csv_path in csv_files:
        stats = normalize_file(csv_path, output_dir, college_lookup, branch_lookup)
        all_stats.append(stats)
        log.info("")  # blank line between files

    total_in = sum(s["input_rows"] for s in all_stats)
    total_out = sum(s["output_rows"] for s in all_stats)
    total_removed = sum(s["removed"] for s in all_stats)
    total_unknown = sum(s["unknown_branches"] for s in all_stats)

    log.info("═" * 50)
    log.info("PASS 1 COMPLETE — Per-file normalization")
    log.info("Files processed   : %d", len(all_stats))
    log.info("Total input rows  : %d", total_in)
    log.info("Total output rows : %d", total_out)
    log.info("Rows removed      : %d", total_removed)
    log.info("UNKNOWN branches  : %d", total_unknown)
    log.info("═" * 50)

    # ── Pass 2: Global cross-file UNKNOWN recovery ──
    if total_unknown > 0:
        log.info("")
        log.info("═" * 50)
        log.info("PASS 2 — Global cross-file UNKNOWN recovery")
        log.info("═" * 50)
        global_recovered = global_unknown_recovery(output_dir)
        total_unknown -= global_recovered

    # ── Final summary ──
    log.info("")
    log.info("═" * 50)
    log.info("NORMALIZATION COMPLETE")
    log.info("Files processed      : %d", len(all_stats))
    log.info("Total input rows     : %d", total_in)
    log.info("Total output rows    : %d", total_out)
    log.info("Rows removed         : %d", total_removed)
    log.info("UNKNOWN branches     : %d", total_unknown)
    log.info("═" * 50)

    if total_unknown > 0:
        log.warning(
            "REMINDER: %d rows still have UNKNOWN branch_name. "
            "Review and update configs/branch_name_map.json if patterns emerge.",
            total_unknown,
        )


# ======================================================================
#  CLI ENTRY POINT
# ======================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="GradMap — Normalize extracted AI quota CSVs",
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help="Path to extracted AI CSVs (directory or single file)",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory for normalized CSVs",
    )
    args = parser.parse_args()

    run_batch(args.input, args.output)

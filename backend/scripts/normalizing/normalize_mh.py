"""
GradMap — MH Quota Normalization Pipeline
==========================================
Normalizes extracted MH quota CSVs into a clean, consistent format.

This script is **normalization only** — it does NOT do extraction.
It reads from  : extracted/mh/*.csv
It writes to   : normalized/mh/*.csv
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
DEFAULT_INPUT_DIR = BASE_DIR / "extracted" / "mh"
DEFAULT_OUTPUT_DIR = BASE_DIR / "normalized" / "mh"

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
log = logging.getLogger("normalize_mh")


# ======================================================================
#  MAP LOADERS
# ======================================================================

def load_college_map(path: Path) -> dict[str, str]:
    """
    Load college_name_map.json and build a reverse lookup:
      variation (lowercased, stripped) → canonical name
    """
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    inner = raw.get("College Name -> Variations", {})
    lookup: dict[str, str] = {}

    for canonical, variations in inner.items():
        lookup[canonical.strip().lower()] = canonical
        for var in variations:
            key = var.strip().lower()
            if key in lookup and lookup[key] != canonical:
                continue
            lookup[key] = canonical

    log.info("Loaded college map: %d variations → %d canonical names",
             len(lookup), len(inner))
    return lookup


def load_branch_map(path: Path) -> dict[str, str]:
    """
    Load branch_name_map.json and build a reverse lookup:
      variant (lowercased, stripped) → canonical name
    """
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    lookup: dict[str, str] = {}
    canonical_count = 0

    for canonical, variants in raw.items():
        if canonical == "_meta":
            continue
        canonical_count += 1
        lookup[canonical.strip().lower()] = canonical
        for var in variants:
            key = var.strip().lower()
            if key in lookup and lookup[key] != canonical:
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
    s = s.replace("\n", " ").replace("\r", " ")
    s = " ".join(s.split())
    return s.strip()


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Stage 1: Basic text cleaning on all string columns."""
    text_cols = ["college_name", "branch_name", "category",
                 "exam_type", "quota_type", "source_file", "choice_code"]

    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].apply(clean_text)

    if "institute_code" in df.columns:
        df["institute_code"] = df["institute_code"].apply(
            lambda x: str(int(float(x))) if pd.notna(x) else None
        )

    return df


# ======================================================================
#  COLLEGE NAME NORMALIZATION
# ======================================================================

def normalize_college_names(
    df: pd.DataFrame,
    college_lookup: dict[str, str],
) -> pd.DataFrame:
    """Stage 2: Map college_name to its canonical form."""
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
        unmapped[name] += 1
        return name

    df["college_name"] = df["college_name"].apply(_normalize)

    total = len(df)
    log.info("College normalization: %d/%d mapped (%.1f%%)",
             mapped_count, total, 100.0 * mapped_count / max(total, 1))

    if unmapped:
        log.warning("  %d unique unmapped college names (%d rows total)",
                     len(unmapped), sum(unmapped.values()))
        for name, count in unmapped.most_common(5):
            log.warning("    [%d rows] %s", count, name)

    return df


# ======================================================================
#  BRANCH NAME NORMALIZATION
# ======================================================================

def normalize_branch_names(
    df: pd.DataFrame,
    branch_lookup: dict[str, str],
) -> pd.DataFrame:
    """Stage 3: Map branch_name to its canonical form."""
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
        unmapped[name] += 1
        return name

    df["branch_name"] = df["branch_name"].apply(_normalize)

    total = len(df)
    log.info("Branch normalization: %d/%d mapped, %d UNKNOWN",
             mapped_count, total - unknown_count, unknown_count)

    if unmapped:
        log.warning("  %d unique unmapped branch names (%d rows total)",
                     len(unmapped), sum(unmapped.values()))
        for name, count in unmapped.most_common(5):
            log.warning("    [%d rows] %s", count, name)

    return df


# ======================================================================
#  UNKNOWN BRANCH RECOVERY
# ======================================================================

def recover_unknown_branches(df: pd.DataFrame) -> pd.DataFrame:
    """Stage 4: Use choice_code majority mapping to recover UNKNOWN branches."""
    known = df[df["branch_name"] != "UNKNOWN"]
    unknown_mask = df["branch_name"] == "UNKNOWN"
    unknown_count_before = unknown_mask.sum()

    if unknown_count_before == 0:
        return df

    code_branch_map: dict[str, str] = {}
    grouped = known.groupby("choice_code")["branch_name"]

    for code, branch_series in grouped:
        counts = branch_series.value_counts()
        if len(counts) > 0:
            code_branch_map[str(code)] = counts.index[0]

    recovered = 0
    def _recover(row: pd.Series) -> str:
        nonlocal recovered
        if row["branch_name"] != "UNKNOWN":
            return row["branch_name"]
        mapped = code_branch_map.get(str(row["choice_code"]))
        if mapped is not None:
            recovered += 1
            return mapped
        return "UNKNOWN"

    df["branch_name"] = df.apply(_recover, axis=1)
    log.info("UNKNOWN branch recovery: %d/%d recovered", recovered, unknown_count_before)
    return df


# ======================================================================
#  VALIDATION & DEDUPLICATION
# ======================================================================

def validate_dataframe(df: pd.DataFrame, filename: str) -> pd.DataFrame:
    """Stage 5: Validate each row."""
    initial_count = len(df)
    # Basic filters
    df = df[(df["percentile_cutoff"] >= 0) & (df["percentile_cutoff"] <= 100)]
    df = df.dropna(subset=["institute_code", "college_name", "branch_name"])
    
    removed = initial_count - len(df)
    if removed > 0:
        log.warning("Validation [%s]: removed %d invalid rows", filename, removed)
    return df


def deduplicate(df: pd.DataFrame, filename: str) -> pd.DataFrame:
    """Stage 6: Remove duplicates."""
    dedup_cols = ["year", "round", "choice_code", "category", "percentile_cutoff"]
    before = len(df)
    df = df.drop_duplicates(subset=dedup_cols, keep="first")
    removed = before - len(df)
    if removed > 0:
        log.info("Deduplication [%s]: removed %d dupes", filename, removed)
    return df


# ======================================================================
#  GLOBAL CROSS-FILE UNKNOWN RECOVERY
# ======================================================================

def global_unknown_recovery(output_dir: Path) -> int:
    """Pass 2: Global cross-file UNKNOWN recovery pass."""
    csv_files = sorted(output_dir.glob("*.csv"))
    if not csv_files: return 0

    file_dfs: dict[str, pd.DataFrame] = {f.name: pd.read_csv(f, dtype={"choice_code": str}) for f in csv_files}
    combined = pd.concat(file_dfs.values(), ignore_index=True)
    
    known = combined[combined["branch_name"] != "UNKNOWN"]
    global_map: dict[str, str] = {}
    for code, branch_series in known.groupby("choice_code")["branch_name"]:
        global_map[str(code)] = branch_series.value_counts().index[0]

    total_recovered = 0
    for filename, df in file_dfs.items():
        unknown_mask = df["branch_name"] == "UNKNOWN"
        if not unknown_mask.any(): continue
        
        start_unknown = unknown_mask.sum()
        df.loc[unknown_mask, "branch_name"] = df.loc[unknown_mask, "choice_code"].map(global_map).fillna("UNKNOWN")
        recovered = start_unknown - (df["branch_name"] == "UNKNOWN").sum()
        
        if recovered > 0:
            df.to_csv(output_dir / filename, index=False)
            total_recovered += recovered
            log.info("  %s: globally recovered %d rows", filename, recovered)

    return total_recovered


# ======================================================================
#  BATCH RUNNER
# ======================================================================

def normalize_file(csv_path: Path, output_dir: Path, college_lookup, branch_lookup):
    filename = csv_path.name
    df = pd.read_csv(csv_path)
    df = clean_dataframe(df)
    df = normalize_college_names(df, college_lookup)
    df = normalize_branch_names(df, branch_lookup)
    df = recover_unknown_branches(df)
    df = validate_dataframe(df, filename)
    df = deduplicate(df, filename)

    output_dir.mkdir(parents=True, exist_ok=True)
    df[OUTPUT_COLUMNS].to_csv(output_dir / filename, index=False)
    return {"file": filename, "in": len(df), "unknown": (df["branch_name"] == "UNKNOWN").sum()}

def run_batch(input_dir: Path, output_dir: Path):
    college_lookup = load_college_map(COLLEGE_MAP_PATH)
    branch_lookup = load_branch_map(BRANCH_MAP_PATH)
    
    csv_files = sorted(input_dir.glob("*.csv"))
    log.info("Found %d MH CSVs", len(csv_files))
    
    all_stats = []
    for csv_path in csv_files:
        log.info("── Normalizing: %s", csv_path.name)
        stats = normalize_file(csv_path, output_dir, college_lookup, branch_lookup)
        all_stats.append(stats)

    total_unknown = sum(s["unknown"] for s in all_stats)
    if total_unknown > 0:
        log.info("Running global recovery pass...")
        recovered = global_unknown_recovery(output_dir)
        total_unknown -= recovered

    log.info("═" * 50)
    log.info("MH NORMALIZATION COMPLETE")
    log.info("Total files: %d", len(all_stats))
    log.info("Remaining UNKNOWN: %d", total_unknown)
    log.info("═" * 50)

if __name__ == "__main__":
    run_batch(DEFAULT_INPUT_DIR, DEFAULT_OUTPUT_DIR)

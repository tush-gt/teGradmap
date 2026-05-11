"""
GradMap — MH Quota CSV Extractor
=================================
Extracts cutoff data from Maharashtra State (MH) quota CSVs (2025 onwards).

Filename pattern : 2025ENGG_CAP1_CutOff_MH.csv
Quota type       : MH (Maharashtra State)
Output           : extracted/mh/<filename>.csv

CSV Column Structure (source files):
  college code | college name | branch code | branch name | Stage | category | rank | percentile

Author  : GradMap Pipeline
Version : 1.0.0
"""

import re
import csv
import logging
import argparse
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent

# ──────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("extract_mh_csv")

# ──────────────────────────────────────────────
# Schema column order (must match schema.json)
# ──────────────────────────────────────────────
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

# ──────────────────────────────────────────────
# Filename parser
# ──────────────────────────────────────────────
FILENAME_PATTERN = re.compile(
    r"^(\d{4})ENGG_CAP(\d+)_CutOff_MH",
    re.IGNORECASE,
)

def parse_filename(filename: str) -> dict:
    m = FILENAME_PATTERN.match(filename)
    if not m:
        raise ValueError(
            f"Filename '{filename}' does not match expected MH pattern: "
            "YYYYENGG_CAPN_CutOff_MH.csv"
        )
    return {
        "year": int(m.group(1)),
        "round": int(m.group(2)),
        "quota_type": "MH",
    }

def clean_text(val):
    if pd.isna(val):
        return val
    return str(val).replace("\n", " ").replace("\r", " ").strip()

# ──────────────────────────────────────────────
# Main per-file extraction
# ──────────────────────────────────────────────

def extract_csv(csv_path: Path, output_dir: Path) -> dict:
    filename = csv_path.name
    log.info("── Processing: %s", filename)

    try:
        meta = parse_filename(filename)
    except ValueError as e:
        log.error("Skipping file — %s", e)
        return {}

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / (csv_path.stem + ".csv")

    stats = {
        "total_rows": 0,
        "corrupt_rows": 0,
        "output_path": str(output_path),
    }

    try:
        df = pd.read_csv(csv_path, dtype=str)
    except Exception as e:
        log.error("Failed to read CSV: %s — %s", csv_path, e)
        return {}

    # Strip whitespace from column names
    df.columns = df.columns.str.strip()

    # Column Mapping:
    # college code -> institute_code
    # college name -> college_name
    # branch code  -> choice_code
    # branch name  -> branch_name
    # rank         -> rank_cutoff
    # percentile   -> percentile_cutoff
    # category     -> category
    
    mapping = {
        "college code": "institute_code",
        "college name": "college_name",
        "branch code": "choice_code",
        "branch name": "branch_name",
        "rank": "rank_cutoff",
        "percentile": "percentile_cutoff",
        "category": "category"
    }
    
    # Check if all required columns exist
    missing = [c for c in mapping.keys() if c not in df.columns]
    if missing:
        log.error("Missing columns in CSV: %s", missing)
        return {}

    # Clean text fields
    for col in ["college name", "branch name", "category"]:
        df[col] = df[col].apply(clean_text)

    # Process and write
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()

        for _, row in df.iterrows():
            stats["total_rows"] += 1
            
            try:
                rank_val = row["rank"]
                perc_val = row["percentile"]
                
                # Basic validation
                if pd.isna(perc_val) or str(perc_val).strip() == "":
                    stats["corrupt_rows"] += 1
                    continue
                
                writer.writerow({
                    "year": meta["year"],
                    "round": meta["round"],
                    "quota_type": meta["quota_type"],
                    "choice_code": row["branch code"],
                    "exam_type": "MHT-CET", # Default for MH quota
                    "institute_code": row["college code"],
                    "college_name": row["college name"],
                    "branch_code": None, # MH CSVs don't separate branch code from choice code usually
                    "branch_name": row["branch name"],
                    "category": row["category"],
                    "percentile_cutoff": float(perc_val),
                    "rank_cutoff": int(float(rank_val)) if pd.notna(rank_val) else None,
                    "source_file": filename,
                })
            except Exception as e:
                log.warning("Row failed: %s", e)
                stats["corrupt_rows"] += 1

    log.info("   Done — %d rows written, %d corrupt", stats["total_rows"] - stats["corrupt_rows"], stats["corrupt_rows"])
    return stats

def run_batch(input_path: Path, output_dir: Path):
    if input_path.is_file():
        csvs = [input_path]
    elif input_path.is_dir():
        csvs = sorted(input_path.glob("*_MH.csv"))
    else:
        log.error("Input path does not exist: %s", input_path)
        return

    for csv_path in csvs:
        extract_csv(csv_path, output_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GradMap MH CSV Extractor")
    parser.add_argument("--input", "-i", type=Path, required=True)
    parser.add_argument("--output", "-o", type=Path, default=BASE_DIR / "extracted" / "mh")
    args = parser.parse_args()
    run_batch(args.input, args.output)

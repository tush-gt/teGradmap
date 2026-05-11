"""
GradMap — AI Quota CSV Extractor
=================================
Extracts cutoff data from All India (AI) quota CSVs (2025 onwards).

Filename pattern : 2025ENGG_CAP1_AI_CutOff.csv
Quota type       : AI (All India)
Output           : extracted/ai/<filename>.csv

CSV Column Structure (source files):
  Sr No | All India Merit | Choice Code | Institute Name | Course Name | Merit Exam | Type | Seat Type

Key differences from PDF pipeline (extract_ai.py):
  - Source data is already tabular (CSV), no pdfplumber needed.
  - "All India Merit" = "rank (percentile)" → split into rank_cutoff + percentile_cutoff
  - "Institute Name"  = "CODE - Name" → split into institute_code + college_name
  - "Course Name"     = raw branch name (normalize later)
  - "Merit Exam"      = JEE / MHT-CET / JEE(Main)-2025 / NEET-2025 etc. → exam_type
  - "Type" + "Seat Type" together determine category:
        • "AI to AI"  / seat="AI"     → category = "AI"
        • "MI to AI"  / seat="MI"     → category = "MI"
        • "MH to AI"  / seat=<code>   → category = <code>   (GOPENH, LSTH, etc.)
  - Shifted rows: When Type = "AI to AI AI" (or similar double-token),
    columns shift right — Course Name is null, and the branch name is
    appended to Institute Name.  These rows must be repaired.
  - Newlines (\n) may appear inside quoted fields — must be stripped.
  - branch_code = None (not present in AI CSVs)

Usage:
  python extract_ai_csv.py --input raw/2025/ai/2025ENGG_CAP1_AI_CutOff.csv --output extracted/ai/
  python extract_ai_csv.py --input raw/2025/ai/ --output extracted/ai/   # batch mode

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
log = logging.getLogger("extract_ai_csv")

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
    r"^(\d{4})ENGG_CAP(\d+)_AI_CutOff",
    re.IGNORECASE,
)


def parse_filename(filename: str) -> dict:
    """
    Extract year, round, quota_type from filename.

    Examples:
      2025ENGG_CAP1_AI_CutOff.csv → year=2025, round=1, quota_type=AI
      2025ENGG_CAP3_AI_CutOff.csv → year=2025, round=3, quota_type=AI
    """
    m = FILENAME_PATTERN.match(filename)
    if not m:
        raise ValueError(
            f"Filename '{filename}' does not match expected AI pattern: "
            "YYYYENGG_CAPN_AI_CutOff.csv"
        )
    return {
        "year": int(m.group(1)),
        "round": int(m.group(2)),
        "quota_type": "AI",
    }


# ──────────────────────────────────────────────
# Field parsers
# ──────────────────────────────────────────────
MERIT_PATTERN = re.compile(r"^(\d+)\s*\(([\d.]+)\)$")


def parse_merit(raw: str) -> tuple:
    """
    Parse "15312 (86.6844102)" → rank_cutoff=15312, percentile_cutoff=86.6844102

    Returns (rank_cutoff, percentile_cutoff) as (int, float).
    Returns (None, None) if the string is malformed — caller must log this.
    """
    if not raw or (isinstance(raw, float) and pd.isna(raw)):
        return None, None
    raw = str(raw).strip()
    m = MERIT_PATTERN.match(raw)
    if not m:
        return None, None
    return int(m.group(1)), float(m.group(2))


INSTITUTE_PATTERN = re.compile(r"^(\d+)\s*-\s*(.+)$", re.DOTALL)


def parse_institute(raw: str) -> tuple:
    """
    Parse "01101 - Shri Sant Gajanan Maharaj College of Engineering,Shegaon"
        → ("01101", "Shri Sant Gajanan Maharaj College of Engineering,Shegaon")

    Returns (institute_code, college_name).
    Returns (None, raw) if pattern doesn't match — keeps raw name for debugging.
    """
    if not raw or (isinstance(raw, float) and pd.isna(raw)):
        return None, None
    raw = str(raw).strip()
    m = INSTITUTE_PATTERN.match(raw)
    if not m:
        log.warning("Institute name did not match expected pattern: '%s'", raw)
        return None, raw
    return m.group(1).strip(), m.group(2).strip()


def parse_exam_type(raw: str) -> str:
    """
    Normalize exam type from the Merit Exam column.

    Known values in 2025 CSVs:
      "JEE"            → "JEE(Main)"
      "JEE(Main)-2025" → "JEE(Main)"
      "MHT-CET"        → "MHT-CET"
      "MHT-CET-PCB 2025" → "MHT-CET"
      "MHT-CET-PCM 2025" → "MHT-CET"
      "NEET-2025"      → "NEET"    (pharmacy/medical branches in ENGG file)

    Returns normalized string or None if unrecognized.
    """
    if not raw or (isinstance(raw, float) and pd.isna(raw)):
        return None
    raw = str(raw).strip().upper()
    if "JEE" in raw:
        return "JEE(Main)"
    if "MHT" in raw or "CET" in raw:
        return "MHT-CET"
    if "NEET" in raw:
        return "NEET"
    log.warning("Unrecognized exam type: '%s'", raw)
    return None


def parse_category(type_col: str, seat_type_col: str) -> str:
    """
    Derive the category field from the CSV's Type and Seat Type columns.

    Logic:
      - Type "AI to AI"  + Seat Type "AI"     → "AI"
      - Type "MI to AI"  + Seat Type "MI"     → "MI"
      - Type "MH to AI"  + Seat Type <code>   → <code>  (e.g. GOPENH, LSTH)
      - Type "AI to AI AI" (shifted row, already repaired) → "AI"
      - Type contains embedded category (e.g. "MH to AI LNT2H") → extract it

    Falls back to "AI" if unable to determine.
    """
    type_str = str(type_col).strip() if pd.notna(type_col) else ""
    seat_str = str(seat_type_col).strip() if pd.notna(seat_type_col) else ""

    # Simple cases: seat type is present and meaningful
    if seat_str and seat_str not in ("", "nan"):
        if seat_str == "AI":
            return "AI"
        if seat_str == "MI":
            return "MI"
        # For MH to AI rows, seat type IS the category code
        return seat_str

    # Shifted/repaired rows where seat type was null — derive from Type column
    if "MI to AI" in type_str:
        # Check if there's an embedded category in the Type column
        # e.g. "MI to AI MI" → the trailing part after standard prefix
        return "MI"

    if "MH to AI" in type_str:
        # e.g. "MH to AI LNT2H" → extract "LNT2H"
        parts = type_str.split("MH to AI")
        if len(parts) > 1 and parts[1].strip():
            return parts[1].strip()
        return "AI"  # fallback

    if "AI to AI" in type_str:
        return "AI"

    # Fallback
    log.warning("Could not determine category from Type='%s', Seat Type='%s'", type_str, seat_str)
    return "AI"


# ──────────────────────────────────────────────
# Known branch patterns for shifted-row repair
# (used to split branch name out of Institute Name
#  when columns have shifted)
#
# SORTED LONGEST-FIRST so that more specific
# patterns match before shorter substrings.
# ──────────────────────────────────────────────
BRANCH_PATTERNS = sorted([
    # ── Computer / IT ──
    "Computer Science and Engineering(Data Science)",
    "Computer Science and Engineering (Data Science)",
    "Computer Science and Engineering (IoT)",
    "Computer Science and Engineering (Internet of",
    "Computer Science and Engineering (Artificial",
    "Computer Science and Engineering(Artificial",
    "Computer Science and Engineering (Cyber",
    "Computer Science and Engineering(Cyber",
    "Computer Science and Engineering",
    "Computer Science and Business Systems",
    "Computer Science and Information Technology",
    "Computer Science and Design",
    "Computer Science Engineering",
    "Computer Science",
    "Computer Engineering (Regional Language)",
    "Computer Engineering (Software Engineering)",
    "Computer Engineering",
    "Computer Technology",
    "Information Technology",
    "Cyber Security",
    "Data Science",
    "Data Engineering",
    "Internet of Things (IoT)",
    "Internet of Things",
    "Industrial IoT",
    "VLSI Design and Technology",
    "VLSI",
    "5G",

    # ── AI / ML ──
    "Artificial Intelligence (AI) and Data Science",
    "Artificial Intelligence and Data Science",
    "Artificial Intelligence and Machine Learning",
    "Artificial Intelligence",
    "Robotics and Artificial Intelligence",

    # ── Electronics ──
    "Electronics and Telecommunication Engineering",
    "Electronics and Telecommunication Engg",
    "Electronics & Telecommunication",
    "Electronics and Communication(Advanced",
    "Electronics and Communication",
    "ELECTRONICS AND COMMUNICATION",
    "Electronics and Computer Engineering",
    "Electronics and Computer Science",
    "Electronics and Biomedical Engineering",
    "Electronics Engineering ( VLSI Design and",
    "Electronics Engineering",

    # ── Electrical ──
    "Electrical Engg[Electronics and Power]",
    "Electrical and Computer Engineering",
    "Electrical and Electronics Engineering",
    "Electrical, Electronics and Power",
    "Electrical Engineering",
    "Electrical Engg",

    # ── Mechanical ──
    "Mechanical and Automation Engineering",
    "Mechanical and Mechatronics Engineering",
    "Mechanical & Automation Engineering",
    "Mechanical Engineering[Sandwich]",
    "Mechanical Engineering",
    "MECHANICAL AND RAIL ENGINEERING",
    "Mechatronics Engineering",

    # ── Civil ──
    "Civil Engineering (Structural Engineering)",
    "Civil Engineering and Planning",
    "Civil Engineering with Computer Application",
    "Civil and Environmental Engineering",
    "Civil and infrastructure Engineering",
    "Civil Engineering",

    # ── Chemical / Polymer / Petro ──
    "Chemical Engineering",
    "Petro Chemical Engineering",
    "Polymer Engineering and Technology",
    "Plastic and Polymer Engineering",

    # ── Instrumentation ──
    "Instrumentation and Control Engineering",
    "Instrumentation Engineering",

    # ── Production / Manufacturing ──
    "Manufacturing Science and Engineering",
    "Production Engineering",

    # ── Automation / Robotics ──
    "Automation and Robotics",
    "Robotics and Automation",

    # ── Automobile / Aero ──
    "Automobile Engineering",
    "Aeronautical Engineering",
    "Aerospace Engineering",

    # ── Bio / Pharma / Food ──
    "Bio Medical Engineering",
    "Bio Technology",
    "Biomedical Engineering",
    "Food Engineering and Technology",
    "Food Engineering",
    "Food Technology",
    "Pharmaceuticals Chemistry and Technology",
    "Agricultural Engineering",

    # ── Textile / Printing ──
    "Textile Engineering / Technology",
    "Textile Engineering",
    "Textile Technology",
    "Textile Chemistry",
    "Technical Textiles",
    "Fibres and Textile Processing Technology",
    "Man Made Textile Technology",
    "Printing and Packing Technology",
    "Printing Technology",
    "Fashion Technology",

    # ── Mining / Metallurgy ──
    "Mining Engineering",
    "Metallurgy and Material Technology",

    # ── Other ──
    "Structural Engineering",
    "Oil,Oleochemicals and Surfactants Technology",
    "Oil Technology",
    "Surface Coating Technology",
    "Dyestuff Technology",
    "Paper and Pulp Technology",
], key=len, reverse=True)  # longest-first for greedy matching


def clean_newlines(val):
    """Strip embedded newlines from CSV fields."""
    if pd.isna(val):
        return val
    return str(val).replace("\n", " ").replace("\r", " ").strip()


# Pre-compiled regex: institute code at the start of the combined string
_INST_CODE_RE = re.compile(r"^(\d{5})\s*-\s*")


def repair_shifted_row(institute_name: str) -> tuple:
    """
    For shifted rows, the Institute Name column contains both the
    institute info AND the branch name appended at the end.

    Example:
      "01107 - P. R. Pote Patil College of Engineering & Management, Amravati Electrical Engineering"
      → institute_part = "01107 - P. R. Pote Patil College of Engineering & Management, Amravati"
      → branch_name = "Electrical Engineering"

    Strategy:
      1. Try exact suffix match against BRANCH_PATTERNS (longest-first).
      2. Try rfind match (branch embedded near end).
      3. Fallback: regex split at the last known city/location boundary.

    Returns (institute_part, branch_name) or (original, None) if no branch found.
    """
    if not institute_name or pd.isna(institute_name):
        return institute_name, None

    inst_clean = clean_newlines(institute_name)

    # Strategy 1 & 2: Try exact branch pattern matching
    for branch in BRANCH_PATTERNS:
        idx = inst_clean.rfind(branch)
        if idx > 0:
            # Check that nothing meaningful follows after the branch match
            after_branch = inst_clean[idx + len(branch):].strip()
            if not after_branch:
                institute_part = inst_clean[:idx].strip()
                return institute_part, branch

    # Strategy 3: Regex-based heuristic for truncated branch names
    # e.g. "06267 - Kolhapur Institute of Technology's College of Mechanical Engineering Engineering"
    # Look for the LAST occurrence of a known keyword that likely starts a branch name
    branch_start_keywords = [
        "Computer Science and",
        "Computer Engineering",
        "Information Technology",
        "Artificial Intelligence",
        "Electronics and",
        "Electronics Engineering",
        "Electrical Eng",
        "Electrical Engg",
        "Electrical and",
        "Electrical,",
        "Mechanical Eng",
        "Mechanical and",
        "Civil Eng",
        "Civil and",
        "Chemical Eng",
        "Instrumentation",
        "Bio Technology",
        "Bio Medical",
        "Biomedical",
        "Food Technology",
        "Food Eng",
        "Textile",
        "Printing",
        "Mining Eng",
        "Metallurgy",
        "Aeronautical",
        "Aerospace",
        "Automobile",
        "Automation and Robotics",
        "Robotics and",
        "Mechatronics",
        "Cyber Security",
        "Data Science",
        "Data Eng",
        "Internet of Things",
        "Industrial IoT",
        "Structural Eng",
        "VLSI",
        "Manufacturing",
        "Production Eng",
        "Petro Chemical",
        "Polymer",
        "Plastic",
        "Agricultural",
        "Fashion",
        "MECHANICAL AND",
        "ELECTRONICS AND",
    ]

    best_idx = -1
    best_kw = None
    for kw in branch_start_keywords:
        # Use rfind to find the LAST occurrence (closest to the end)
        idx = inst_clean.rfind(kw)
        if idx > 0 and idx > best_idx:
            # Ensure this is not part of the institute name itself
            # Heuristic: branch should be within the last ~50% of the string
            if idx > len(inst_clean) * 0.3:
                best_idx = idx
                best_kw = kw

    if best_idx > 0:
        branch_name = inst_clean[best_idx:].strip()
        institute_part = inst_clean[:best_idx].strip()
        return institute_part, branch_name

    log.debug("Could not repair shifted row: '%s'", inst_clean[:80])
    return inst_clean, None


# ──────────────────────────────────────────────
# Main per-file extraction
# ──────────────────────────────────────────────

def extract_csv(csv_path: Path, output_dir: Path) -> dict:
    """
    Extract one AI CSV → one cleaned CSV in output_dir.

    Returns a stats dict:
      {total_rows, corrupt_rows, missing_institute_code, shifted_rows,
       repaired_rows, output_path}
    """
    filename = csv_path.name
    log.info("── Processing: %s", filename)

    # Parse metadata from filename
    try:
        meta = parse_filename(filename)
    except ValueError as e:
        log.error("Skipping file — %s", e)
        return {}

    log.info(
        "   Year=%d  Round=%d  Quota=%s",
        meta["year"], meta["round"], meta["quota_type"],
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / (csv_path.stem + ".csv")

    stats = {
        "total_rows": 0,
        "corrupt_rows": 0,
        "missing_institute_code": 0,
        "shifted_rows": 0,
        "repaired_rows": 0,
        "output_path": str(output_path),
    }

    # ── Read source CSV ────────────────────────────────────────
    try:
        df = pd.read_csv(csv_path, dtype=str)
    except Exception as e:
        log.error("Failed to read CSV: %s — %s", csv_path, e)
        return {}

    # Strip whitespace from column names
    df.columns = df.columns.str.strip()

    log.info("   Total source rows: %d", len(df))

    # ── Clean newlines in all text fields ──────────────────────
    for col in df.columns:
        df[col] = df[col].apply(clean_newlines)

    # ── Open output and process row by row ─────────────────────
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()

        for idx, row in df.iterrows():
            stats["total_rows"] += 1
            try:
                # ─────────────────────────────────────────
                # Detect and repair shifted rows
                # ─────────────────────────────────────────
                course_name = row.get("Course Name", "")
                institute_raw = row.get("Institute Name", "")
                is_shifted = pd.isna(course_name) or str(course_name).strip() in ("", "nan")

                if is_shifted:
                    stats["shifted_rows"] += 1
                    # Repair: split branch name out of Institute Name
                    institute_raw_repaired, branch_name = repair_shifted_row(institute_raw)
                    if branch_name:
                        stats["repaired_rows"] += 1
                        institute_raw = institute_raw_repaired
                    else:
                        branch_name = "UNKNOWN"
                        log.warning(
                            "   Row %d: shifted row could not be repaired — "
                            "Institute Name: '%s'",
                            idx, institute_raw[:80],
                        )
                else:
                    branch_name = str(course_name).strip()

                # ─────────────────────────────────────────
                # MERIT + PERCENTILE
                # ─────────────────────────────────────────
                merit_raw = row.get("All India Merit", "")
                rank_cutoff, percentile_cutoff = parse_merit(merit_raw)

                # ─────────────────────────────────────────
                # CHOICE CODE
                # ─────────────────────────────────────────
                choice_code = row.get("Choice Code", "")
                if pd.isna(choice_code) or str(choice_code).strip() in ("", "nan"):
                    choice_code = None
                else:
                    choice_code = str(choice_code).strip()

                # ─────────────────────────────────────────
                # INSTITUTE CODE + COLLEGE NAME
                # ─────────────────────────────────────────
                institute_code, college_name = parse_institute(institute_raw)

                # ─────────────────────────────────────────
                # EXAM TYPE
                # ─────────────────────────────────────────
                exam_type = parse_exam_type(row.get("Merit Exam", ""))

                # ─────────────────────────────────────────
                # CATEGORY
                # ─────────────────────────────────────────
                category = parse_category(
                    row.get("Type", ""),
                    row.get("Seat Type", ""),
                )

                # ─────────────────────────────────────────
                # Corruption checks
                # ─────────────────────────────────────────
                corrupt = False

                if percentile_cutoff is None:
                    log.warning(
                        "   Row %d: could not parse merit '%s' — row skipped",
                        idx, merit_raw,
                    )
                    stats["corrupt_rows"] += 1
                    corrupt = True

                if percentile_cutoff is not None and not (0.0 <= percentile_cutoff <= 100.0):
                    log.warning(
                        "   Row %d: percentile out of range: %s — row flagged",
                        idx, percentile_cutoff,
                    )
                    stats["corrupt_rows"] += 1
                    corrupt = True

                if not institute_code:
                    log.warning(
                        "   Row %d: missing institute_code for '%s'",
                        idx, str(institute_raw)[:60],
                    )
                    stats["missing_institute_code"] += 1

                if not branch_name or branch_name == "UNKNOWN":
                    log.warning("   Row %d: empty/unknown branch_name", idx)
                    branch_name = "UNKNOWN"

                if exam_type is None:
                    log.warning("   Row %d: could not parse exam type", idx)
                    stats["corrupt_rows"] += 1
                    corrupt = True

                if corrupt:
                    continue

                # ─────────────────────────────────────────
                # Write row
                # ─────────────────────────────────────────
                writer.writerow({
                    "year":              meta["year"],
                    "round":             meta["round"],
                    "quota_type":        meta["quota_type"],
                    "choice_code":       choice_code,
                    "exam_type":         exam_type,
                    "institute_code":    institute_code,
                    "college_name":      college_name,
                    "branch_code":       None,          # not in AI CSVs
                    "branch_name":       branch_name,
                    "category":          category,
                    "percentile_cutoff": percentile_cutoff,
                    "rank_cutoff":       rank_cutoff,
                    "source_file":       filename,
                })

            except Exception as e:
                log.error("   Row %d FAILED: %s", idx, e)
                stats["corrupt_rows"] += 1
                continue

    log.info(
        "   Done — %d rows written, %d corrupt, %d missing institute_code",
        stats["total_rows"] - stats["corrupt_rows"],
        stats["corrupt_rows"],
        stats["missing_institute_code"],
    )
    log.info(
        "   Shifted rows: %d total, %d repaired",
        stats["shifted_rows"],
        stats["repaired_rows"],
    )
    log.info("   Output: %s", output_path)
    return stats


# ──────────────────────────────────────────────
# Batch runner
# ──────────────────────────────────────────────

def run_batch(input_path: Path, output_dir: Path):
    """
    If input_path is a file: extract that one CSV.
    If input_path is a directory: extract all AI CSVs in it.
    """
    if input_path.is_file():
        csvs = [input_path]
    elif input_path.is_dir():
        # Only grab AI CSVs — files with _AI_ in their name
        csvs = sorted(input_path.glob("*_AI_*.csv"))
        log.info("Found %d AI CSV(s) in %s", len(csvs), input_path)
    else:
        log.error("Input path does not exist: %s", input_path)
        return

    if not csvs:
        log.warning("No AI CSVs found. Check your input path and filename pattern.")
        return

    all_stats = []
    for csv_path in csvs:
        stats = extract_csv(csv_path, output_dir)
        if stats:
            all_stats.append(stats)

    # ── Summary report ────────────────────────────────────────────
    log.info("══════════════════════════════════════")
    log.info("BATCH COMPLETE")
    log.info("Files processed : %d", len(all_stats))
    log.info(
        "Total rows      : %d",
        sum(s["total_rows"] for s in all_stats),
    )
    log.info(
        "Corrupt rows    : %d",
        sum(s["corrupt_rows"] for s in all_stats),
    )
    log.info(
        "Missing inst.   : %d",
        sum(s["missing_institute_code"] for s in all_stats),
    )
    log.info(
        "Shifted rows    : %d (repaired: %d)",
        sum(s["shifted_rows"] for s in all_stats),
        sum(s["repaired_rows"] for s in all_stats),
    )
    log.info("══════════════════════════════════════")

    # ── MANUAL INSPECTION REMINDER ────────────────────────────────
    log.warning(
        "REMINDER: Manually inspect at least 20 rows from each output CSV. "
        "Do NOT trust extraction just because it completed without errors."
    )


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="GradMap AI CSV Extractor — extracts AI quota cutoff data from CET CSVs"
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        required=True,
        help="Path to a single AI CSV or a directory containing AI CSVs",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=BASE_DIR / "extracted" / "ai",
        help="Output directory for extracted CSVs (default: extracted/ai/)",
    )
    args = parser.parse_args()

    run_batch(args.input, args.output)
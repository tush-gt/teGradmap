"""
GradMap — AI Quota PDF Extractor
=================================
Extracts cutoff data from All India (AI) quota PDFs.

Filename pattern : 2022ENGG_CAP1_AI_CutOff.pdf
Quota type       : AI (All India)
Output           : extracted/ai/<filename>.csv

PDF Column Structure (as seen in actual PDFs):
  Sr. No | All India Merit | Choice Code | Institute Name | Course Name | Exam(JEE/MHT-CET) | Type | Seat Type

Key parsing decisions:
  - "All India Merit" = "rank (percentile)" → split into rank_cutoff + percentile_cutoff
  - "Institute Name"  = "CODE - Name" → split into institute_code + college_name
  - "Course Name"     = raw branch name (normalize later)
  - "Exam" column     = JEE(Main) or MHT-CET → exam_type
  - category          = always "AI" for AI quota PDFs (no caste breakdown in this doc)
  - branch_code       = None (not present in AI PDFs)

Usage:
  python extract_ai.py --input raw/2022ENGG_CAP1_AI_CutOff.pdf --output extracted/ai/
  python extract_ai.py --input raw/ --output extracted/ai/     # batch mode

Author  : GradMap Pipeline
Version : 1.0.0
"""

import re
import csv
import logging
import argparse
from pathlib import Path

import pdfplumber
BASE_DIR = Path(__file__).resolve().parent.parent
# ──────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("extract_ai")

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
      2022ENGG_CAP1_AI_CutOff.pdf → year=2022, round=1, quota_type=AI
      2024ENGG_CAP3_AI_CutOff.pdf → year=2024, round=3, quota_type=AI
    """
    m = FILENAME_PATTERN.match(filename)
    if not m:
        raise ValueError(
            f"Filename '{filename}' does not match expected AI pattern: "
            "YYYYENGG_CAPN_AI_CutOff.pdf"
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
    Parse "86 (99.5054906)" → rank_cutoff=86, percentile_cutoff=99.5054906

    Returns (rank_cutoff, percentile_cutoff) as (int, float).
    Returns (None, None) if the string is malformed — caller must log this.
    """
    if not raw:
        return None, None
    raw = raw.strip()
    m = MERIT_PATTERN.match(raw)
    if not m:
        return None, None
    return int(m.group(1)), float(m.group(2))


INSTITUTE_PATTERN = re.compile(r"^(\d+)\s*-\s*(.+)$")

def parse_institute(raw: str) -> tuple:
    """
    Parse "6006 - COEP Technological University" → ("6006", "COEP Technological University")

    Returns (institute_code, college_name).
    Returns (None, raw) if pattern doesn't match — keeps raw name for debugging.
    """
    if not raw:
        return None, None
    raw = raw.strip()
    m = INSTITUTE_PATTERN.match(raw)
    if not m:
        log.warning("Institute name did not match expected pattern: '%s'", raw)
        return None, raw
    return m.group(1).strip(), m.group(2).strip()


def parse_exam_type(raw: str) -> str:
    """
    Parse "JEE(Main)" or "MHT-CET" from Exam column.

    Returns normalized string or None if unrecognized.
    """
    if not raw:
        return None
    raw = raw.strip()
    if "JEE" in raw.upper():
        return "JEE(Main)"
    if "MHT" in raw.upper() or "CET" in raw.upper():
        return "MHT-CET"
    log.warning("Unrecognized exam type: '%s'", raw)
    return None


# ──────────────────────────────────────────────
# PDF table extraction
# ──────────────────────────────────────────────

# pdfplumber table settings tuned for CET PDFs
TABLE_SETTINGS = {
    "vertical_strategy": "lines",
    "horizontal_strategy": "lines",
    "snap_tolerance": 5,
    "join_tolerance": 3,
    "edge_min_length": 10,
    "min_words_vertical": 3,
    "min_words_horizontal": 1,
}

# Column header keywords to identify the correct table on each page.
# CET AI PDFs always have these headers.
EXPECTED_HEADERS = {"sr", "merit", "choice", "institute", "course", "exam", "type", "seat"}
branch_patterns = [
                    "Computer Science and Engineering",
                    "Computer Science Engineering",
                    "Computer Engineering",
                    "Information Technology",

                    "Artificial Intelligence and Data Science",
                    "Artificial Intelligence and Machine Learning",
                    "Artificial Intelligence",
                    "Data Science",

                    "Electronics and Telecommunication Engineering",
                    "Electronics and Telecommunication Engg",
                    "Electronics Engineering",
                    "Electronics and Computer Engineering",

                    "Electrical Engineering",
                    "Electrical and Electronics Engineering",

                    "Mechanical Engineering",
                    "Mechanical and Automation Engineering",

                    "Civil Engineering",
                    "Civil and Environmental Engineering",

                    "Chemical Engineering",
                    "Polymer Engineering",

                    "Instrumentation Engineering",
                    "Instrumentation and Control Engineering",

                    "Production Engineering",
                    "Manufacturing Engineering",

                    "Mechatronics Engineering",
                    "Automation and Robotics",

                    "Robotics and Automation",

                    "Automobile Engineering",
                    "Automotive Engineering",

                    "Bio Technology",
                    "Bio Medical Engineering",
                    "Biomedical Engineering",

                    "Food Technology",
                    "Textile Engineering",
                    "Textile Technology",

                    "Mining Engineering",
                    "Metallurgy Engineering",

                    "Aeronautical Engineering",
                    "Aerospace Engineering",

                    "Computer Science and Business Systems",

                    "VLSI Design and Technology",

                    "Internet of Things",

                    "Cyber Security",

                    "Structural Engineering",
                    "Computer Science and Engineering (Data Science)",
                    "Computer Science and Engineering(Data Science)",
                    "Computer Science and Information Technology",
                    "Artificial Intelligence and Data Science",
                    "Artificial Intelligence and Machine Learning",
                    "Data Engineering",
                ]


def is_header_row(row: list) -> bool:
    """Return True if this row looks like the table header."""
    if not row:
        return False
    joined = " ".join(str(c).lower() for c in row if c)
    return sum(1 for h in EXPECTED_HEADERS if h in joined) >= 4


def is_data_row(row: list) -> bool:
    """
    Return True if this row looks like a real data row.
    A data row must have a numeric Sr. No in the first non-empty cell.
    """
    for cell in row:
        if cell and str(cell).strip():
            return re.match(r"^\d+", str(cell).strip())
    return False


import re

def extract_table_from_page(page):
    text = page.extract_text()

    if not text:
        return []

    lines = text.split("\n")
    rows = []
    current_row = ""

    for line in lines:
        line = line.strip()
        # Detect NEW row starting with serial number
        if re.match(r"^\d+\s+\d+\s+\(", line):
            # save previous row
            if current_row:
                rows.append(current_row)
            current_row = line

        else:
            # continuation of previous row
            if current_row:
                current_row += " " + line

    # append last row
    if current_row:
        rows.append(current_row)

    return rows

# ──────────────────────────────────────────────
# Column name resolver
# (handles pdfplumber outputting slightly
#  different header text across PDF years)
# ──────────────────────────────────────────────

def resolve_column(raw_headers: dict, candidates: list):
    """
    Given a dict of {col_index: header_text}, find the index
    of the first header that contains any of the candidate keywords.
    Returns the matching header key or None.
    """
    for key, header in raw_headers.items():
        for c in candidates:
            if c in header.lower():
                return key
    return None


# ──────────────────────────────────────────────
# Main per-file extraction
# ──────────────────────────────────────────────

def extract_pdf(pdf_path: Path, output_dir: Path) -> dict:
    """
    Extract one AI PDF → one CSV in output_dir.

    Returns a stats dict:
      {total_rows, corrupt_rows, missing_institute_code, output_path}
    """
    filename = pdf_path.name
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
    output_path = output_dir / (pdf_path.stem + ".csv")

    stats = {
        "total_rows": 0,
        "corrupt_rows": 0,
        "missing_institute_code": 0,
        "output_path": str(output_path),
    }

    with pdfplumber.open(pdf_path) as pdf:
        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=OUTPUT_COLUMNS)
            writer.writeheader()

            total_pages = len(pdf.pages)
            log.info("   Total pages: %d", total_pages)

            for page_num, page in enumerate(pdf.pages, start=1):

                raw_rows = extract_table_from_page(page)

                if not raw_rows and page_num <= 3:
                    log.warning(
                        "   Page %d: no rows extracted — check table settings",
                        page_num,
                    )

                for raw in raw_rows:
                    institute_code = None
                    college_name = None
                    branch_name = None
                    choice_code = None
                    institute_match = None
                    choice_match = None
                    branch_match = None
                    percentile_match = None
                    rank_match = None
                    stats["total_rows"] += 1
                    try:
                        # -------------------------------------------------
                        # MERIT + PERCENTILE
                        # -------------------------------------------------

                        merit_match = re.search(
                            r"(\d+)\s+\(([\d.]+)\)",
                            raw
                        )

                        if not merit_match:
                            continue

                        rank_cutoff = int(merit_match.group(1))
                        percentile_cutoff = float(merit_match.group(2))

                        # -------------------------------------------------
                        # CHOICE CODE
                        # -------------------------------------------------

                        choice_match = re.search(
                            r"\)\s+(\d{9}[A-Z]?)",
                            raw
                        )

                        choice_code = (
                            choice_match.group(1)
                            if choice_match
                            else None
                        )

                        # -------------------------------------------------
                        # EXAM TYPE
                        # -------------------------------------------------

                        if "JEE(Main)" in raw:
                            exam_type = "JEE(Main)"

                        elif "MHT-CET" in raw:
                            exam_type = "MHT-CET"

                        else:
                            exam_type = "MHT-CET"

                        # -------------------------------------------------
                        # CATEGORY
                        # -------------------------------------------------

                        if "MI to AI MI" in raw:
                            category = "MI"

                        elif "MH-AI" in raw:
                            category = "MH-AI"

                        else:
                            category = "AI"

                        # -------------------------------------------------
                        # BRANCH EXTRACTION
                        # -------------------------------------------------
                        
                        branch_name = None
                        for branch in branch_patterns:
                            if branch in raw:
                                branch_name = branch
                                # split from RIGHT SIDE
                                left_part = raw.rsplit(branch, 1)[0]
                                # extract institute
                                institute_match = re.search(
                                    r"(\d{4})\s*-\s*(.*)",
                                    left_part
                                )
                                if institute_match:
                                    institute_code = institute_match.group(1).strip()
                                    college_name = institute_match.group(2).strip()
                                break
                    except Exception as e:
                        print("\nROW FAILED:\n")
                        print(raw)
                        print("\nERROR:\n")
                        print(e)
                        continue
                    # ── Corruption checks ───────────────────────────────
                    corrupt = False

                    if percentile_cutoff is None:
                        log.warning(
                            "   Page %d: could not parse merit '%s' — row skipped",
                            page_num, merit_match,
                        )
                        stats["corrupt_rows"] += 1
                        corrupt = True

                    if percentile_cutoff is not None and not (0.0 <= percentile_cutoff <= 100.0):
                        log.warning(
                            "   Page %d: percentile out of range: %s — row flagged",
                            page_num, percentile_cutoff,
                        )
                        stats["corrupt_rows"] += 1
                        corrupt = True

                    if not institute_code:
                        log.warning(
                            "   Page %d: missing institute_code for '%s'",
                            page_num, institute_match,
                        )
                        stats["missing_institute_code"] += 1

                    if branch_name is None:
                        log.warning("   Page %d: empty branch_name", page_num)
                        # corrupt = True
                        # stats["corrupt_rows"] += 1
                        branch_name = "UNKNOWN"
                        # print("\nUNKNOWN ROW:\n")
                        # log.debug(row)
                    if corrupt:
                        continue

                    # ── Write row ────────────────────────────────────────
                    writer.writerow({
                        "year":              meta["year"],
                        "round":             meta["round"],
                        "quota_type":        meta["quota_type"],
                        "choice_code":       choice_code,
                        "exam_type":         exam_type,
                        "institute_code":    institute_code,
                        "college_name":      college_name,
                        "branch_code":       None,          # not in AI PDFs
                        "branch_name":       branch_name,
                        "category":          category,          # fixed for AI quota
                        "percentile_cutoff": percentile_cutoff,
                        "rank_cutoff":       rank_cutoff,
                        "source_file":       filename,
                    })

    log.info(
        "   Done — %d rows written, %d corrupt, %d missing institute_code",
        stats["total_rows"] - stats["corrupt_rows"],
        stats["corrupt_rows"],
        stats["missing_institute_code"],
    )
    log.info("   Output: %s", output_path)
    return stats


# def _find_value(row_dict: dict, keywords: list) -> str:
#     """
#     Search a row dict for the first key containing any of the keywords.
#     Returns the value or empty string.
#     """
#     for key, value in row_dict.items():
#         for kw in keywords:
#             if kw in str(key).lower():
#                 return str(value).strip()
#     return ""

# ──────────────────────────────────────────────
# Batch runner
# ──────────────────────────────────────────────

def run_batch(input_path: Path, output_dir: Path):
    """
    If input_path is a file: extract that one PDF.
    If input_path is a directory: extract all AI PDFs in it.
    """
    if input_path.is_file():
        pdfs = [input_path]
    elif input_path.is_dir():
        # Only grab AI PDFs — files with _AI_ in their name
        pdfs = sorted(input_path.glob("*_AI_*.pdf"))
        log.info("Found %d AI PDF(s) in %s", len(pdfs), input_path)
    else:
        log.error("Input path does not exist: %s", input_path)
        return

    if not pdfs:
        log.warning("No AI PDFs found. Check your input path and filename pattern.")
        return

    all_stats = []
    for pdf_path in pdfs:
        stats = extract_pdf(pdf_path, output_dir)
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
        description="GradMap AI PDF Extractor — extracts AI quota cutoff data from CET PDFs"
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        required=True,
        help="Path to a single AI PDF or a directory containing AI PDFs",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=BASE_DIR / "extracted" / "ai",
        help="Output directory for extracted CSVs (default: extracted/ai/)",
    )
    args = parser.parse_args()

    run_batch(args.input, args.output)
"""
GradMap — MH Quota PDF Extractor
=================================
Extracts cutoff data from Maharashtra State (MH) quota PDFs (Grid format).

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
log = logging.getLogger("extract_mh")

# ──────────────────────────────────────────────
# Schema column order
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
# Regex Patterns
# ──────────────────────────────────────────────
# Matches: 1002 - Government College of Engineering, Amravati
INSTITUTE_PATTERN = re.compile(r"^(\d{4,5})\s*-\s*(.+)$")
# Matches: 100219110 - Civil Engineering
BRANCH_PATTERN = re.compile(r"^(\d{9,10})\s*-\s*(.+)$")
# Filename pattern: 2024ENGG_CAP1_CutOff_MH.pdf
FILENAME_PATTERN = re.compile(r"^(\d{4})ENGG_CAP(\d+)_CutOff_MH", re.IGNORECASE)

def parse_filename(filename: str) -> dict:
    m = FILENAME_PATTERN.match(filename)
    if not m:
        raise ValueError(f"Filename '{filename}' does not match expected MH pattern.")
    return {
        "year": int(m.group(1)),
        "round": int(m.group(2)),
        "quota_type": "MH",
    }

def clean_value(val):
    if not val: return None
    # Remove parentheses and newlines
    val = val.strip().replace("(", "").replace(")", "")
    try:
        return float(val)
    except:
        return None

def extract_pdf(pdf_path: Path, output_dir: Path):
    filename = pdf_path.name
    log.info("── Processing: %s", filename)

    try:
        meta = parse_filename(filename)
    except ValueError as e:
        log.error("Skipping file — %s", e)
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / (pdf_path.stem + ".csv")

    current_inst_code = None
    current_inst_name = None
    current_choice_code = None
    current_branch_name = None
    
    # Open CSV for writing
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()

        with pdfplumber.open(pdf_path) as pdf:
            total_rows = 0
            for i, page in enumerate(pdf.pages):
                if i % 10 == 0:
                    log.info("   ... processing page %d/%d", i + 1, len(pdf.pages))
                
                text = page.extract_text()
                if not text: continue
                
                lines = text.split("\n")
                
                # Step 1: Update Institute/Branch state from text
                for line in lines:
                    line = line.strip()
                    inst_match = INSTITUTE_PATTERN.match(line)
                    if inst_match:
                        current_inst_code = inst_match.group(1).lstrip("0")
                        current_inst_name = inst_match.group(2).strip()
                        continue
                    
                    branch_match = BRANCH_PATTERN.match(line)
                    if branch_match:
                        current_choice_code = branch_match.group(1)
                        current_branch_name = branch_match.group(2).strip()
                        continue

                # Step 2: Extract Tables
                tables = page.extract_tables()
                
                for table in tables:
                    if not table or len(table) < 2: continue
                    
                    headers = [h.replace("\n", "").strip() if h else "" for h in table[0]]
                    
                    if not any(h.startswith("G") or h.startswith("L") or h == "TFWS" for h in headers):
                        continue
                    
                    for row in table[1:]:
                        if not row or not row[0]: continue
                        stage = row[0].strip()
                        
                        for j in range(1, len(row)):
                            if j >= len(headers): break
                            cat = headers[j]
                            if not cat: continue
                            
                            cell_content = row[j]
                            if not cell_content: continue
                            
                            parts = cell_content.strip().split("\n")
                            rank_val = None
                            perc_val = None
                            
                            if len(parts) >= 2:
                                rank_val = parts[0].strip()
                                perc_val = parts[1].strip()
                            elif len(parts) == 1:
                                if "(" in parts[0]:
                                    perc_val = parts[0]
                                else:
                                    rank_val = parts[0]
                                    
                            perc = clean_value(perc_val)
                            if perc is None: continue
                            
                            try:
                                rank_int = int(float(rank_val.replace(",", ""))) if rank_val else None
                            except:
                                rank_int = None

                            writer.writerow({
                                "year": meta["year"],
                                "round": meta["round"],
                                "quota_type": meta["quota_type"],
                                "choice_code": current_choice_code,
                                "exam_type": "MHT-CET",
                                "institute_code": current_inst_code,
                                "college_name": current_inst_name,
                                "branch_code": None,
                                "branch_name": current_branch_name,
                                "category": cat,
                                "percentile_cutoff": perc,
                                "rank_cutoff": rank_int,
                                "source_file": filename,
                            })
                            total_rows += 1

    log.info("   Done — %d rows written to %s", total_rows, output_path.name)

def run_batch(input_path: Path, output_dir: Path):
    if input_path.is_file():
        pdfs = [input_path]
    elif input_path.is_dir():
        pdfs = sorted(input_path.glob("*_MH.pdf"))
    else:
        log.error("Input path does not exist: %s", input_path)
        return

    for pdf_path in pdfs:
        extract_pdf(pdf_path, output_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GradMap MH PDF Extractor")
    parser.add_argument("--input", "-i", type=Path, required=True)
    parser.add_argument("--output", "-o", type=Path, default=BASE_DIR / "extracted" / "mh")
    args = parser.parse_args()
    run_batch(args.input, args.output)

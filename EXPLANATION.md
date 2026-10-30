# GradMap — Deep Dive Explanation

> A comprehensive walkthrough of how GradMap works: its architecture, data flow, ML model, AI integration, and each major subsystem.

---

## Table of Contents

1. [What is GradMap?](#1-what-is-gradmap)
2. [System Architecture](#2-system-architecture)
3. [The Dataset](#3-the-dataset)
4. [Recommendation Engine (Core Pipeline)](#4-recommendation-engine-core-pipeline)
5. [Machine Learning Model](#5-machine-learning-model)
6. [Probability Ranking & Diversification](#6-probability-ranking--diversification)
7. [FastAPI Backend — Routes & Data Flow](#7-fastapi-backend--routes--data-flow)
8. [Google Gemini AI Counsellor](#8-google-gemini-ai-counsellor)
9. [CAP Round Simulator](#9-cap-round-simulator)
10. [Frontend Architecture](#10-frontend-architecture)
11. [Data Flow: End-to-End Request Lifecycle](#11-data-flow-end-to-end-request-lifecycle)
12. [Key Design Decisions](#12-key-design-decisions)

---

## 1. What is GradMap?

GradMap is an **engineering college counselling platform** for Maharashtra MHT-CET students. It answers the central question every aspirant faces:

> *"Given my percentile, category, and branch preference — which colleges should I apply to, and in what order?"*

It solves this with three complementary tools:

- **Recommendation Engine** — Ranks 300+ colleges using 4 years of historical cutoff data + ML
- **AI Counsellor** — A conversational assistant (Google Gemini) that explains and contextualises results
- **CAP Simulator** — Simulates official seat allotment to help students test their option forms

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                      │
│   Pages: Recommendations · Trends · Simulator · AI Chat     │
│   State: Zustand  |  Charts: Recharts  |  DnD: @dnd-kit     │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP (Axios)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND                           │
│                                                             │
│  /recommend  ──►  Recommendation Engine  ──►  ML Model      │
│  /trends     ──►  Dataset Analytics                         │
│  /simulate   ──►  CAP Allotment Simulator                   │
│  /ai/chat    ──►  Gemini AI Counsellor                      │
│                                                             │
│  Startup: Load 230k-row DataFrame into memory               │
│           Load Random Forest model into memory              │
└─────────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
  ┌─────────────┐               ┌──────────────────┐
  │  CSV Dataset │               │ Google Gemini API │
  │ (230k rows)  │               │  (Free Tier)      │
  └─────────────┘               └──────────────────┘
         │
         ▼
  ┌──────────────────────┐
  │  Random Forest Model  │
  │  admission_rfc_model  │
  │  .pkl (joblib)        │
  └──────────────────────┘
```

The backend is a **monolithic FastAPI application** that starts up by loading the entire dataset and ML model into RAM. This means zero disk I/O per request — every `/recommend` call works on a cached in-memory Pandas DataFrame.

---

## 3. The Dataset

### Source
Maharashtra CET Cell publishes official CAP cutoff lists as PDFs after each admission round. GradMap processes these into a normalized CSV dataset.

### Scale
- **230,000+ rows** across 4 years (2022–2025) and 3 CAP rounds per year
- **300+ engineering colleges** across Maharashtra
- **50+ branch variations** normalized into families

### Schema (key columns)

| Column | Type | Description |
|---|---|---|
| `institute_code` | str | Official CET Cell 4–5 digit code |
| `college_name` | str | Canonicalized institute name |
| `branch_name` | str | Exact branch as per CET (e.g., "Computer Engineering") |
| `category` | str | Reservation category (e.g., GOPEN, GOBC, GSC, LOPEN) |
| `round` | int | CAP round number (1, 2, or 3) |
| `year` | int | Academic year (2022–2025) |
| `percentile_cutoff` | float | Last admitted student's percentile in this cell |
| `rank_cutoff` | int | Approximate merit rank at cutoff |
| `quota_type` | str | State / Institute / NRI quota |
| `branch_family` | str | Engineered: CS_FAMILY, MECH_FAMILY, etc. |
| `institute_tier` | int | Engineered: 1 (top) / 2 (mid) / 3 (others) |
| `seat_competitiveness` | float | Engineered: derived from historical demand |
| `recommendation_score` | float | Engineered: composite scoring metric |

### Feature Engineering
Three key derived columns make the ML model effective:

**`branch_family`** — Collapses 50+ branches into functional families:
- `CS_FAMILY`: Computer Engineering, IT, AI&DS, Data Science, Computer Science
- `MECH_FAMILY`: Mechanical, Production, Automobile
- `ELEC_FAMILY`: Electronics, ENTC, EXTC, Electrical
- etc.

**`institute_tier`** — Heuristic tiering:
- Tier 1: COEP, VJTI, SPIT, PICT, DJSCE, Walchand (elite autonomous/government)
- Tier 2: Reputed private colleges with strong placement records
- Tier 3: All others

**`recommendation_score`** — A transparent composite metric:
```
score = ((percentile_cutoff / 100) × 50)
      + tier_weight         # Tier 1 = +20, Tier 2 = +10
      + branch_family_weight # CS/AI families = +5
      + recency_bonus        # 2025 = +8, 2024 = +5, etc.
```

---

## 4. Recommendation Engine (Core Pipeline)

The `recommend()` function in `recommendation_engine.py` is the heart of GradMap. It's a 12-step deterministic + ML-hybrid pipeline:

### Step-by-step

**Step 1 — Validate Input**  
`validate_user_input()` checks percentile range (0–100), category validity, and sets defaults.

**Step 2 — Load Dataset**  
Uses the in-memory `_dataset_cache` (passed from FastAPI) to avoid all disk I/O.

**Step 3 — Filter by Category**  
Keeps only rows matching the student's reservation category (e.g., `GOPEN` also matches `GOPEN_TFWS`, `GOPEN_PWD`).

**Step 4 — Filter by Branch Family**  
If the student prefers CS, only rows from `CS_FAMILY` branches are kept. If `None`, all branches pass.

**Step 5 — Filter by Tier**  
Optional filter to limit results to specific institute tiers.

**Step 6 — Percentile Window Filter**  
Shows colleges within a ±configurable margin of the student's percentile. For the Option Form Builder (large `top_n`), the window opens to 100% to show all colleges.

**Step 7 — Compute Percentile Gap**  
```python
percentile_gap = user_percentile - percentile_cutoff
```
This gap is the core signal for bucketing.

**Step 8 — Assign Buckets**
```
Gap ≥  2.0  →  SAFE      (comfortably above cutoff)
-1.0 ≤ Gap < 2.0  →  TARGET  (close to cutoff, competitive)
Gap < -1.0  →  AMBITIOUS  (below cutoff, aspirational)
```

**Step 9 — Year Recency Scoring**  
Recent years are weighted more heavily to reflect current trends.

**Step 10 — Deduplicate**  
Per college+branch, only the latest and highest-scoring row is kept. Prevents the same seat appearing multiple times (once per year/round).

**Step 11 — ML Inference**  
The Random Forest model predicts P(admission) for every row using 10 engineered features. If the model is unavailable, this step is skipped gracefully — results fall back to percentile-gap bucketing only.

**Step 12 — Rank, Diversify, Format**  
- Sort by ML probability (descending), then recommendation_score, then year
- Limit max 2 branches per college (diversification to avoid one college dominating)
- Reformat to the API schema

---

## 5. Machine Learning Model

### Model
**Scikit-learn Random Forest Classifier** — stored as `admission_rfc_model.pkl` (joblib).

### Task
Binary classification: **"Will this student be admitted to this seat?"**  
Output: Probability P(admitted) ∈ [0.0, 1.0]

### Features (10 inputs)
```python
REQUIRED_FEATURES = [
    "college_name",        # Encoded institute identifier
    "branch_name",         # Encoded branch identifier
    "category",            # Reservation category
    "round",               # CAP round number (1/2/3)
    "year",                # Academic year
    "quota_type",          # State / Institute / NRI
    "branch_family",       # Grouped branch family
    "institute_tier",      # College tier (1/2/3)
    "seat_competitiveness",# Derived demand metric
    "user_percentile",     # Injected at inference time
]
```

### Model Loading & Caching
```python
# Loaded once at startup, cached in _MODEL_CACHE global
load_model()   # Loads from disk the first time
get_model()    # Returns from cache on all subsequent calls
```

The model is loaded into memory during FastAPI startup via `lifespan()`. All subsequent prediction calls are pure CPU computation with no disk access.

### Inference
```python
# predict_proba returns shape (n_samples, n_classes)
# Class index 1 = "Admitted"
probabilities = model.predict_proba(X)[:, 1]
```

Each row in the filtered DataFrame gets its own probability score — this allows per-seat, per-student admission chance estimation.

---

## 6. Probability Ranking & Diversification

The `probability_ranker.py` module post-processes ML output:

### Bucket Assignment (from ML probability)
```python
def probability_bucket(prob: float) -> str:
    if prob >= 0.70:   return "SAFE"
    elif prob >= 0.45: return "TARGET"
    else:              return "AMBITIOUS"
```

### Confidence Labels
```python
def get_confidence_label(prob: float) -> str:
    if prob >= 0.95:  return "VERY_HIGH"
    elif prob >= 0.80: return "HIGH"
    elif prob >= 0.60: return "MODERATE"
    elif prob >= 0.40: return "LOW"
    else:              return "VERY_LOW"
```

### Smart Ranking
Colleges are sorted with a **multi-key sort**:
1. ML probability (descending) — primary signal
2. Recommendation score (descending) — secondary signal  
3. Year (descending) — prefer recent data

### Diversification
`diversify_recommendations(df, max_per_college=2)` prevents any single college from flooding results. At most 2 branches per college are shown, encouraging a well-balanced option form.

### Graceful Degradation
If the ML model is unavailable (e.g., `.pkl` file missing), the system **never fabricates a 50% placeholder**. Instead:
- `probability` column is set to `NaN`
- `confidence_label` and `probability_percent` are set to `None`
- Bucketing falls back to the percentile-gap method (Step 8)

---

## 7. FastAPI Backend — Routes & Data Flow

### Application Startup (`lifespan`)
```python
@asynccontextmanager
async def lifespan(app):
    # Load 230k-row CSV into memory once
    _dataset_cache = load_dataset()
    # Load Random Forest model into memory once
    load_model()
    yield
    _dataset_cache = None  # Cleanup on shutdown
```

### Route Summary

**`POST /recommend`**  
Takes: `{percentile, category, branch_family, preferred_tiers, top_n}`  
Does: Runs the full 12-step pipeline, returns `{SAFE: [...], TARGET: [...], AMBITIOUS: [...]}`

**`GET /trends?institute_code=&branch_name=&category=`**  
Does: Filters dataset for the given college+branch+category, computes per-year cutoffs across rounds, calculates volatility and trend direction.

**`GET /analytics/college?institute_code=&category=`**  
Does: Returns branch-wise analytics for a whole college — avg cutoff, latest cutoff, volatility, trend direction per branch.

**`GET /colleges`**  
Does: Returns all unique colleges with metadata (code, name, district, type).

**`POST /simulate`**  
Does: Iterates through the student's preference list in order, checks each against the real dataset using the highest recent cutoff, and returns the first matched allotment.

**`POST /ai/chat`**  
Does: Assembles grounded context from ML recommendations + dataset lookups, then calls Gemini for a conversational response.

### Error Handling Strategy
- `ValueError` from engine → HTTP 422 (Unprocessable Entity)
- Empty results → HTTP 404
- Internal exceptions → HTTP 500
- Dataset not loaded → HTTP 503

---

## 8. Google Gemini AI Counsellor

The `AICounsellor` class in `ai_counsellor.py` is a self-contained Gemini client with:

### Grounded Context Builder
Before every Gemini call, `build_grounded_context()` assembles a structured context block:

```
--- STUDENT PROFILE ---
- MHT-CET Percentile: 94.50%
- Estimated Merit Rank: ~6,600
- Reservation Category: GOPEN
- Preferred Branch Family: CS_FAMILY
- Preferred District: Pune

--- ML PREDICTED ADMISSION RECOMMENDATIONS ---
[SAFE] (Total: 8):
  * PICT Pune (6006) | Computer Engineering | Cutoff: 92.10% | Gap: +2.40% | ML: 84%
  * VIT Pune (6141) | Computer Engineering | Cutoff: 93.20% | Gap: +1.30% | ML: 67%

[TARGET] (Total: 5): ...
[AMBITIOUS] (Total: 3): ...

--- HISTORICAL CUTOFFS FOR MENTIONED COLLEGES ---
(filled when student mentions college names like "COEP" or "VJTI")

--- CAP RULES SUMMARY ---
Round 1: Preference #1 allotment is AUTO-FROZEN. ...
```

This context is injected as the user's message, ensuring every Gemini response is factually anchored to real data.

### System Instruction
The counsellor is given a detailed system prompt that enforces:
- No invention of college names, cutoffs, or admission chances
- Correct explanation of SAFE/TARGET/AMBITIOUS buckets
- Accurate CAP Round strategy (Freeze / Float / Slide rules)
- Warm, structured, markdown-formatted responses

### Retry Logic
```python
max_transient_retries = 3
backoff_delays = [1.5, 3.0, 5.0]  # seconds

for attempt in range(max_transient_retries):
    try:
        response = await client.aio.models.generate_content(...)
        break
    except Error as e:
        if "401" in str(e):   # Invalid key → fail immediately
            return invalid_key_response()
        if "404" in str(e):   # Model not found → try next fallback
            break
        if "503" or "429":    # Temporary → wait and retry
            time.sleep(backoff_delays[attempt])
```

### Hot Reload
`POST /ai/reload-env` calls `ai_counsellor.reload_config()`, which re-reads `backend/.env` and reinitializes the Gemini client — all without restarting the server.

---

## 9. CAP Round Simulator

The simulator (`POST /simulate`) models the official Maharashtra CET Cell allotment process:

### Input
```json
{
  "profile": {"percentile": 94.5, "category": "GOPEN"},
  "optionForm": [
    {"college_name": "COEP", "branch_name": "Computer Engineering", "college_code": "1119"},
    {"college_name": "PICT", "branch_name": "Computer Engineering", "college_code": "6006"},
    ...
  ],
  "currentRound": 1
}
```

### Logic
1. Convert percentile to approximate merit rank: `rank = ((100 - percentile) / 100) × 120,000`
2. Iterate through preferences **in order** (preference 1 first)
3. For each preference, find matching rows in the dataset (by code + branch + round + category)
4. Compute historical metrics (weighted average cutoff, volatility, trend)
5. Use the **highest recent cutoff** as the decision threshold (conservative/realistic)
6. If `student_percentile >= decision_cutoff` → allot and stop
7. If no preference qualifies → return "No seat allotted"

### Response
```json
{
  "allotted": true,
  "seat": {
    "college_name": "PICT Pune",
    "branch_name": "Computer Engineering",
    "preference_number": 2,
    "expected_cutoff": 92.4,
    "latest_cutoff": 93.1,
    "trend_direction": "RISING",
    "cutoff_volatility": 0.42
  },
  "merit_rank": 6600,
  "message": "Seat Allotted based on Deterministic CAP Logic."
}
```

---

## 10. Frontend Architecture

The frontend is a **React 19 Single Page Application** built with Vite 8.

### Pages
| Route | Page | Description |
|---|---|---|
| `/` | Dashboard / Home | Percentile & category entry, quick recommendation |
| `/recommendations` | Recommendations | SAFE/TARGET/AMBITIOUS cards with ML scores |
| `/trends` | Cutoff Trends | Per-college per-branch multi-year Recharts |
| `/simulator` | CAP Simulator | Option form builder + allotment simulation |
| `/ai` | AI Counsellor | Gemini-powered conversational chat |
| `/colleges` | College Explorer | Browse & filter all colleges |

### State Management (Zustand)
Zustand stores manage:
- Student profile (percentile, category, branch preference)
- Current recommendations
- Option form (ordered list of preferences)
- AI chat history

### Key Libraries
- **Recharts** — Line charts for cutoff trends, bar charts for branch comparison
- **Framer Motion** — Animated transitions between recommendation cards
- **@dnd-kit** — Drag-and-drop option form ordering with keyboard accessibility
- **react-markdown** — Renders Gemini's markdown-formatted counselling responses

---

## 11. Data Flow: End-to-End Request Lifecycle

Here's what happens when a student requests recommendations:

```
1. Student enters: percentile=94.5, category=GOPEN, branch=CS
   ↓
2. Frontend calls POST /recommend (Axios)
   ↓
3. FastAPI validates the request via Pydantic (RecommendRequest schema)
   ↓
4. recommend() is called with the in-memory _dataset_cache
   ↓
5. Dataset filtered: 230k → ~4,000 rows (GOPEN + CS_FAMILY + window)
   ↓
6. Percentile gap computed for each row
   ↓
7. Buckets assigned: SAFE (gap ≥2), TARGET (-1≤gap<2), AMBITIOUS (gap<-1)
   ↓
8. user_percentile=94.5 injected into DataFrame
   ↓
9. Random Forest model predicts P(admission) for all ~4,000 rows
   ↓
10. Probability metadata attached; rows ranked by P(admission)
    ↓
11. Diversified: max 2 branches per college
    ↓
12. Top N results formatted & returned as JSON
    ↓
13. Frontend renders cards in SAFE/TARGET/AMBITIOUS columns
    with confidence badges and trend indicators
```

---

## 12. Key Design Decisions

### Why in-memory caching?
Loading 230k rows from disk on every request would add 500ms+ latency. Loading once at startup and reusing the DataFrame makes every request near-instant.

### Why Random Forest, not a simple percentile comparison?
A pure percentile gap comparison (`user_percentile > cutoff`) is binary and doesn't account for:
- Year-over-year cutoff volatility
- Category-specific demand variations
- Branch competitiveness trends
- Round-specific allotment dynamics

The Random Forest model learns these non-linear patterns from 4 years of multi-dimensional data, producing a genuine probability rather than a threshold decision.

### Why Gemini Free Tier?
The project is student-facing and cost-sensitive. Gemini Free Tier (15 requests/minute) is sufficient for a counselling assistant that generates one response per student question. The system gracefully handles rate limits with exponential backoff.

### Why Factual Grounding instead of RAG?
Since the dataset is structured (tabular) rather than unstructured (documents), a traditional RAG vector database would be overkill. Instead, `build_grounded_context()` directly queries the Pandas DataFrame and injects structured facts into the prompt — a simpler, faster, and more controllable approach.

### Why no 50% fallback for ML?
Fabricating a 50% probability when the model is unavailable would mislead students into thinking they have moderate admission chances everywhere. The system instead explicitly marks ML data as unavailable and falls back to the transparent, explainable percentile-gap bucketing.

### Why diversify at max 2 branches per college?
Without diversification, a top-tier college with 10 branches could dominate all 20 recommendation slots. Limiting to 2 per college ensures students see a broader range of institutes, which better represents their real option form strategy.


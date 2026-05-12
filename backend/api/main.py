"""
GradMap — FastAPI Application
==============================
API wrapper around the existing GradMap recommendation engine.

This module ONLY handles:
  - CORS
  - HTTP request/response lifecycle
  - Input validation (via schemas.py)
  - Delegation to the recommendation engine
  - Structured error handling

It does NOT contain any recommendation logic.

Run from backend/ with:
    uvicorn api.main:app --reload

Author  : GradMap Pipeline
Version : 1.0.0
"""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ──────────────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger("gradmap.api")

# ──────────────────────────────────────────────────────────────────────
# Engine & Schema Imports
# ──────────────────────────────────────────────────────────────────────
try:
    from scripts.modeling.recommendation_engine import recommend
    from scripts.modeling.utils import load_dataset
except ImportError as e:
    log.critical("Failed to import recommendation engine: %s", e)
    log.critical("Make sure you are running from the backend/ directory.")
    raise

from api.schemas import (
    RecommendRequest, RecommendResponse, RecommendationItem,
    SimulateRequest, SimulateResponse, AllottedSeat, YearlyTrendItem,
    TrendSummary, TrendResponse
)

# ──────────────────────────────────────────────────────────────────────
# Helper Utilities for Historical Analytics
# ──────────────────────────────────────────────────────────────────────

def calculate_historical_metrics(data_df: pd.DataFrame) -> dict | None:
    """
    Computes weighted average, volatility, and trend across historical years.
    Weights: 2025: 0.4, 2024: 0.3, 2023: 0.2, 2022: 0.1
    """
    # 1. Group by year and get mean cutoff
    yearly_means = data_df.groupby("year")["percentile_cutoff"].mean().to_dict()
    
    if not yearly_means:
        return None
        
    # 2. Weighted Average Renormalization
    weights_map = {2025: 0.4, 2024: 0.3, 2023: 0.2, 2022: 0.1}
    weighted_sum = 0.0
    total_weight = 0.0
    available_years = sorted(yearly_means.keys())
    
    for year, weight in weights_map.items():
        if year in yearly_means:
            weighted_sum += yearly_means[year] * weight
            total_weight += weight
            
    expected_cutoff = weighted_sum / total_weight if total_weight > 0 else yearly_means[available_years[-1]]
    
    # 3. Cutoff Volatility (Standard Deviation)
    cutoffs = list(yearly_means.values())
    volatility = float(pd.Series(cutoffs).std()) if len(cutoffs) > 1 else 0.0
    
    # 4. Trend Direction Analysis
    trend = "STABLE"
    if len(cutoffs) >= 2:
        # Calculate slope between first and last available year
        first_val = yearly_means[available_years[0]]
        last_val = yearly_means[available_years[-1]]
        diff = last_val - first_val
        
        if diff > 0.4: trend = "RISING"
        elif diff < -0.4: trend = "FALLING"
        
    return {
        "expected_cutoff": round(expected_cutoff, 2),
        "latest_cutoff": round(yearly_means[available_years[-1]], 2),
        "volatility": round(volatility, 3),
        "trend_direction": trend,
        "historical_years_used": [int(y) for y in available_years]
    }

# ──────────────────────────────────────────────────────────────────────
# Dataset Cache
# Load once at startup to avoid re-reading 230k rows on every request.
# ──────────────────────────────────────────────────────────────────────
_dataset_cache: pd.DataFrame | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Loads the featured dataset into memory on startup so every
    recommendation request reuses the same in-memory DataFrame.
    """
    global _dataset_cache
    log.info("GradMap API starting up — loading dataset into memory...")
    try:
        _dataset_cache = load_dataset()
        log.info("Dataset loaded: %d rows cached.", len(_dataset_cache))
    except FileNotFoundError as e:
        log.critical("Dataset not found: %s", e)
        log.critical("Run the feature engineering pipeline first.")
        raise RuntimeError(str(e)) from e

    yield  # Application runs here

    log.info("GradMap API shutting down.")
    _dataset_cache = None


# ──────────────────────────────────────────────────────────────────────
# FastAPI Application
# ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="GradMap Recommendation API",
    description=(
        "AI-powered Maharashtra engineering counselling recommendation engine. "
        "Returns SAFE / TARGET / AMBITIOUS college suggestions based on "
        "historical CAP cutoff data (2022-2025)."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ──────────────────────────────────────────────────────────────────────
# CORS Middleware
# Allows the Vite frontend (localhost:5173) to call this API.
# ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",   # Fallback CRA / other ports
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────────────────────────────
# ROUTES
# ──────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def health_check():
    """
    Simple liveness check.
    Returns API status and whether the dataset is loaded.
    """
    return {
        "status": "ok",
        "service": "GradMap Recommendation API",
        "dataset_loaded": _dataset_cache is not None,
        "dataset_rows": len(_dataset_cache) if _dataset_cache is not None else 0,
    }


@app.post(
    "/recommend",
    response_model=RecommendResponse,
    status_code=status.HTTP_200_OK,
    summary="Get personalised college recommendations",
    tags=["Recommendation"],
)
def get_recommendations(body: RecommendRequest) -> RecommendResponse:
    """
    Run the GradMap recommendation engine for the given user profile.

    Returns colleges grouped into three buckets:
    - **SAFE**: User percentile comfortably above the historical cutoff (gap ≥ 2).
    - **TARGET**: Realistic choices where the cutoff is close (-1 ≤ gap < 2).
    - **AMBITIOUS**: Dream colleges where the user is below cutoff (gap < -1).

    Each recommendation contains the college name, branch, percentile cutoff,
    gap, recommendation score, and institute tier.
    """
    log.info(
        "Recommendation request — percentile=%.2f, category=%s, branch=%s, tiers=%s, top_n=%d",
        body.percentile, body.category, body.branch_family,
        body.preferred_tiers, body.top_n,
    )

    # Convert API schema to engine dict format
    engine_params = body.to_engine_params()

    try:
        raw_result: dict[str, list[dict[str, Any]]] = recommend(
            engine_params,
            df=_dataset_cache,   # Pass cached dataset — avoids disk I/O per request
        )
    except ValueError as e:
        # Validation errors from the engine (bad category, percentile, etc.)
        log.warning("Validation error in engine: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        log.exception("Unexpected engine error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred in the recommendation engine.",
        )

    # Build typed response
    response = RecommendResponse(
        SAFE=[RecommendationItem(**r) for r in raw_result.get("SAFE", [])],
        TARGET=[RecommendationItem(**r) for r in raw_result.get("TARGET", [])],
        AMBITIOUS=[RecommendationItem(**r) for r in raw_result.get("AMBITIOUS", [])],
    )

    total = len(response.SAFE) + len(response.TARGET) + len(response.AMBITIOUS)

    if total == 0:
        log.warning(
            "Engine returned 0 results for percentile=%.2f, category=%s",
            body.percentile, body.category,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "No recommendations found for the given profile. "
                "Try adjusting the category, branch family, or percentile."
            ),
        )

    log.info(
        "Response: SAFE=%d, TARGET=%d, AMBITIOUS=%d (total=%d)",
        len(response.SAFE), len(response.TARGET), len(response.AMBITIOUS), total,
    )
    return response


@app.get("/trends", response_model=TrendResponse, tags=["Analytics"])
def get_trends(institute_code: str, branch_name: str, category: str):
    """
    Get multi-year historical cutoff trends (2022–2025).
    Aggregates all years properly into a year-grouped structure with summary analytics.
    """
    if _dataset_cache is None:
        raise HTTPException(status_code=503, detail="Dataset not loaded")

    log.info("\n[DEBUG] Trends Request:")
    log.info("inst=%s", institute_code)
    log.info("branch=%s", branch_name)
    log.info("category=%s", category)

    # 1. Strict Institute Match
    inst_match = (_dataset_cache["institute_code"].astype(str) == str(institute_code))

    # 2. Normalized Branch Match
    branch_norm = branch_name.lower().replace("engineering", "").replace("technology", "").strip()
    if branch_norm in ["computer", "computer science", "cs", "cse", "ce"]:
        branch_match = _dataset_cache["branch_name"].str.contains("computer", na=False, case=False)
    elif branch_norm in ["information", "it"]:
        branch_match = _dataset_cache["branch_name"].str.contains("information technology", na=False, case=False)
    elif branch_norm in ["electronics and telecommunication", "extc", "entc"]:
        branch_match = _dataset_cache["branch_name"].str.contains("telecommunication", na=False, case=False)
    else:
        branch_match = _dataset_cache["branch_name"].str.contains(branch_norm, na=False, case=False)

    # 3. Category Match (Starts with base family)
    # E.g. GOPENH, GOPENS -> GOPEN
    cat_base = category
    if len(category) > 4 and category.startswith(("GOPEN", "LOPEN", "GOBC", "LOBC", "GSC", "LSC", "GST", "LST", "GNT", "LNT", "GVJ", "LVJ")):
        cat_base = category[:-1] # Remove the trailing H, O, or S
    elif category in ["TFWS", "EWS", "DEF1", "DEF2", "DEF3", "ORPHAN"]:
        cat_base = category
    
    cat_match = _dataset_cache["category"].astype(str).str.startswith(cat_base, na=False)

    # Filter Strategy: Institute + Branch + Category
    trends_df = _dataset_cache[inst_match & branch_match & cat_match].copy()
    
    # Fallback Strategy: Ignore Category (Sparsity fix)
    if trends_df.empty:
        trends_df = _dataset_cache[inst_match & branch_match].copy()

    log.info("[DEBUG] Matching rows found: %d (using category base: %s)", len(trends_df), cat_base)

    if not trends_df.empty:
        years_found = sorted(trends_df["year"].unique())
        log.info("[DEBUG] Years found: %s", years_found)
        log.info("[DEBUG] Cutoff range: %.2f → %.2f", trends_df["percentile_cutoff"].min(), trends_df["percentile_cutoff"].max())
        
        trend_items = []
        metrics = calculate_historical_metrics(trends_df)
        
        # Always return 4 years for continuous UI
        for year in [2022, 2023, 2024, 2025]:
            year_data = trends_df[trends_df["year"] == year]
            trend_items.append({
                "year": int(year),
                "round1": float(year_data[year_data["round"] == 1]["percentile_cutoff"].iloc[0]) if not year_data[year_data["round"] == 1].empty else None,
                "round2": float(year_data[year_data["round"] == 2]["percentile_cutoff"].iloc[0]) if not year_data[year_data["round"] == 2].empty else None,
                "round3": float(year_data[year_data["round"] == 3]["percentile_cutoff"].iloc[0]) if not year_data[year_data["round"] == 3].empty else None,
            })
            
        return {
            "trends": trend_items,
            "summary": TrendSummary(
                volatility=metrics["volatility"],
                trend_direction=metrics["trend_direction"],
                avg_cutoff=metrics["expected_cutoff"],
                latest_cutoff=metrics["latest_cutoff"]
            )
        }

    log.info("[DEBUG] Returning empty trends response. No fallbacks used.")
    return {
        "trends": [],
        "summary": TrendSummary(volatility=0.0, trend_direction="STABLE", avg_cutoff=0.0, latest_cutoff=0.0)
    }


@app.get("/analytics/college", tags=["Analytics"])
def get_college_analytics(institute_code: str, category: str):
    """
    Get detailed college-wide analytics for comparison.
    """
    if _dataset_cache is None:
        raise HTTPException(status_code=503, detail="Dataset not loaded")

    log.info("\n[DEBUG] Analytics Request:")
    log.info("inst=%s", institute_code)
    log.info("category=%s", category)

    college_mask = (_dataset_cache["institute_code"].astype(str) == str(institute_code))
    college_data = _dataset_cache[college_mask]

    log.info("[DEBUG] College data points found: %d", len(college_data))

    if college_data.empty:
        log.warning("[DEBUG] No college analytics found for inst=%s. Returning empty analytics.", institute_code)
        return {
            "branch_comparison": [],
            "scatter_data": [],
            "latest_year": 2025,
            "latest_round": 3,
        }

    log.info("College data points found: %d", len(college_data))

    latest_year = college_data["year"].max()
    latest_round = college_data[college_data["year"] == latest_year]["round"].max()

    # Calculate multi-year metrics per branch
    branch_analytics = []
    unique_branches = college_data["branch_name"].unique()
    
    for branch in unique_branches:
        branch_df = college_data[college_data["branch_name"] == branch]
        metrics = calculate_historical_metrics(branch_df)
        if metrics:
            branch_analytics.append({
                "branch_name": branch,
                "avg_cutoff": metrics["expected_cutoff"],
                "latest_cutoff": metrics["latest_cutoff"],
                "volatility": metrics["volatility"],
                "trend": metrics["trend_direction"],
                "tier": int(branch_df["institute_tier"].iloc[0]) if not branch_df.empty else 3
            })

    scatter_data = college_data[["percentile_cutoff", "rank_cutoff", "year", "round"]].dropna().to_dict(orient="records")

    return {
        "branch_comparison": branch_analytics,
        "scatter_data": scatter_data,
        "latest_year": int(latest_year),
        "latest_round": int(latest_round),
        "college_volatility": round(college_data.groupby("year")["percentile_cutoff"].mean().std(), 3) if college_data["year"].nunique() > 1 else 0.0
    }


@app.get("/colleges", tags=["Analytics"])
def get_colleges():
    """
    Get a list of all unique colleges with extracted metadata.
    """
    if _dataset_cache is None:
        raise HTTPException(status_code=503, detail="Dataset not loaded")

    colleges_df = _dataset_cache[["institute_code", "college_name"]].drop_duplicates("institute_code")
    
    results = []
    districts = ["Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad", "Amravati", "Jalgaon", "Kolhapur", "Sangli", "Satara"]
    
    for _, row in colleges_df.iterrows():
        name = str(row["college_name"])
        code = str(row["institute_code"])
        
        district = "Other"
        for d in districts:
            if d.lower() in name.lower():
                district = d
                break
        
        inst_type = "Un-Aided"
        if "government" in name.lower():
            inst_type = "Government"
        if "autonomous" in name.lower():
            inst_type += " Autonomous"
            
        results.append({
            "code": code,
            "name": name,
            "district": district,
            "type": inst_type.strip()
        })
    
    return results
@app.post("/simulate", response_model=SimulateResponse, tags=["Simulation"])
def simulate_allotment(request: SimulateRequest):
    """
    Deterministic CAP Allotment Simulator.
    Strictly follows the user's preference order and matches against the real dataset.
    """
    if _dataset_cache is None:
        raise HTTPException(status_code=503, detail="Dataset not loaded")

    profile = request.profile
    option_form = request.optionForm
    current_round = request.currentRound

    log.info("═══ SIMULATION START ═══")
    log.info("Profile: %.2f Percentile | Category: %s | Round: %d", 
             profile.percentile, profile.category, current_round)
    log.info("Preferences submitted: %d", len(option_form))

    # Deterministic Rank Approximation
    merit_rank = max(1, int(((100 - profile.percentile) / 100) * 120000))
    log.info("Calculated Merit Rank: %d", merit_rank)

    if not option_form:
        return SimulateResponse(
            allotted=False,
            seat=None,
            merit_rank=merit_rank,
            message="Your option form is empty. No seats can be allotted."
        )

    # Simulation Logic: Iterate through preferences IN ORDER
    for idx, pref in enumerate(option_form):
        pref_num = idx + 1
        log.info("Checking preference #%d", pref_num)
        log.info("College: %s", pref.college_name)
        log.info("Branch: %s", pref.branch_name)
        log.info("Category: %s", profile.category)

        # 1. Match in dataset across ALL years
        if pref.college_code:
            base_mask = (
                (_dataset_cache["institute_code"].astype(str) == str(pref.college_code)) &
                (_dataset_cache["branch_name"].str.contains(pref.branch_name, na=False, case=False)) &
                (_dataset_cache["round"] == current_round)
            )
        else:
            base_mask = (
                (_dataset_cache["college_name"].astype(str) == str(pref.college_name)) &
                (_dataset_cache["branch_name"].str.contains(pref.branch_name, na=False, case=False)) &
                (_dataset_cache["round"] == current_round)
            )
        
        # Category-family matching
        cat_mask = _dataset_cache["category"].astype(str).str.startswith(profile.category, na=False)
        
        matches = _dataset_cache[base_mask & cat_mask]
        
        # Category Fallback
        if matches.empty:
            matches = _dataset_cache[base_mask]

        if matches.empty:
            log.info("  [SKIP] No historical data found for this specific match.")
            continue

        # 2. Compute Historical Trend Metrics
        metrics = calculate_historical_metrics(matches)
        if not metrics:
            continue

        # SIMULATION SHOULD USE: MOST RECENT AVAILABLE YEAR
        latest_year = matches["year"].max()
        latest_matches = matches[matches["year"] == latest_year]
        
        # USE HIGHEST CUTOFF
        decision_cutoff = float(latest_matches["percentile_cutoff"].max())

        log.info("Rows found: %d", len(matches))
        log.info("Required cutoff: %.2f", decision_cutoff)
        log.info("User percentile: %.2f", profile.percentile)

        # 3. Check qualification based on requested deterministic logic
        if profile.percentile >= decision_cutoff:
            log.info("Qualified")
            return SimulateResponse(
                allotted=True,
                seat=AllottedSeat(
                    college_name=pref.college_name,
                    branch_name=pref.branch_name,
                    allotted_category=profile.category,
                    preference_number=pref_num,
                    round=current_round,
                    expected_cutoff=metrics["expected_cutoff"],
                    latest_cutoff=metrics["latest_cutoff"],
                    cutoff_volatility=metrics["volatility"],
                    trend_direction=metrics["trend_direction"],
                    historical_years_used=metrics["historical_years_used"]
                ),
                merit_rank=merit_rank,
                message="Seat Allotted based on Deterministic CAP Logic."
            )
        else:
            log.info("Rejected")

    log.info("═══ SIMULATION END: NO SEAT ALLOTTED ═══")
    return SimulateResponse(
        allotted=False,
        seat=None,
        merit_rank=merit_rank,
        message=f"No seat allotted in Round {current_round}. Try adding more safe choices."
    )

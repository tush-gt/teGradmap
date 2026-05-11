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

from api.schemas import RecommendRequest, RecommendResponse, RecommendationItem

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

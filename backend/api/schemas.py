"""
GradMap — API Request & Response Schemas
=========================================
Pydantic models for input validation and typed response structure.

Author  : GradMap Pipeline
Version : 1.0.0
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


# ──────────────────────────────────────────────────────────────────────
# REQUEST SCHEMA
# ──────────────────────────────────────────────────────────────────────

class RecommendRequest(BaseModel):
    """
    Validated user input for the /recommend endpoint.

    Maps to the engine's internal user_input dict:
        percentile        → user_percentile
        category          → user_category
        branch_family     → preferred_branch_family
        preferred_tiers   → preferred_tier
        top_n             → top_n
    """

    percentile: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="User's MHT-CET / JEE percentile score (0–100).",
        examples=[97.2],
    )
    category: str = Field(
        ...,
        min_length=1,
        description="Admission category code (e.g. GOPEN, GOBC, GSC, GST).",
        examples=["GOPEN"],
    )
    branch_family: Optional[str] = Field(
        default=None,
        description="Preferred branch family (e.g. CS_FAMILY, CIRCUITS_FAMILY). "
                    "Omit to receive recommendations across all branches.",
        examples=["CS_FAMILY"],
    )
    preferred_tiers: Optional[list[int]] = Field(
        default=None,
        description="Preferred institute tiers to filter (1=Elite, 2=Good, 3=Other). "
                    "Omit for all tiers.",
        examples=[[1, 2]],
    )
    top_n: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum total recommendations to return (split across buckets).",
        examples=[20],
    )

    @field_validator("category")
    @classmethod
    def upper_category(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("branch_family")
    @classmethod
    def upper_branch_family(cls, v: Optional[str]) -> Optional[str]:
        return v.strip().upper() if v else None

    @field_validator("preferred_tiers")
    @classmethod
    def validate_tiers(cls, v: Optional[list[int]]) -> Optional[list[int]]:
        if v is None:
            return None
        for t in v:
            if t not in (1, 2, 3):
                raise ValueError(f"Invalid tier value '{t}'. Must be 1, 2, or 3.")
        return v

    def to_engine_params(self) -> dict[str, Any]:
        """
        Convert the API schema into the dict the engine's recommend() expects.
        This decouples the API surface from internal engine key names.
        """
        return {
            "user_percentile": self.percentile,
            "user_category": self.category,
            "preferred_branch_family": self.branch_family,
            "preferred_tier": self.preferred_tiers,
            "top_n": self.top_n,
        }


# ──────────────────────────────────────────────────────────────────────
# RESPONSE SCHEMAS
# ──────────────────────────────────────────────────────────────────────

class RecommendationItem(BaseModel):
    """A single college recommendation as returned by the engine."""

    college_name: str
    branch_name: str
    category: str
    percentile_cutoff: float
    percentile_gap: float
    recommendation_bucket: str
    recommendation_score: float
    institute_tier: int
    admission_difficulty: Optional[str] = None
    round: Optional[int] = None
    year: Optional[int] = None
    choice_code: Optional[str] = None
    institute_code: Optional[int] = None
    college_code: Optional[str] = None


class RecommendResponse(BaseModel):
    """
    Grouped recommendation output split by bucket.

    The three buckets are always present, even if empty.
    """

    SAFE: list[RecommendationItem] = []
    TARGET: list[RecommendationItem] = []
    AMBITIOUS: list[RecommendationItem] = []


class ErrorResponse(BaseModel):
    """Standard error envelope returned on failure."""

    detail: str
    code: Optional[str] = None


# ──────────────────────────────────────────────────────────────────────
# SIMULATION SCHEMAS
# ──────────────────────────────────────────────────────────────────────

class UserProfile(BaseModel):
    """Candidate profile for simulation."""
    percentile: float
    category: str

class OptionItem(BaseModel):
    """A single choice in the user's option form."""
    college_code: Optional[str] = None
    college_name: str
    branch_name: str

class SimulateRequest(BaseModel):
    """Request payload for the /simulate endpoint."""
    profile: UserProfile
    optionForm: list[OptionItem]
    currentRound: int

class AllottedSeat(BaseModel):
    """Details of the successfully allotted seat with historical context."""
    college_name: str
    branch_name: str
    allotted_category: str
    preference_number: int
    round: int
    
    # Trend Analysis
    expected_cutoff: Optional[float] = None
    latest_cutoff: Optional[float] = None
    cutoff_volatility: Optional[float] = None
    trend_direction: Optional[str] = None
    historical_years_used: Optional[list[int]] = None

class SimulateResponse(BaseModel):
    """Response payload for the simulation result."""
    allotted: bool
    seat: Optional[AllottedSeat] = None
    merit_rank: int
    message: str


# ──────────────────────────────────────────────────────────────────────
# TRENDS SCHEMAS
# ──────────────────────────────────────────────────────────────────────

class YearlyTrendItem(BaseModel):
    """Aggregated cutoff data for a specific year across all rounds."""
    year: int
    round1: Optional[float] = None
    round2: Optional[float] = None
    round3: Optional[float] = None

class TrendSummary(BaseModel):
    """Overall analysis of the historical data."""
    volatility: float
    trend_direction: str
    avg_cutoff: float
    latest_cutoff: float

class TrendResponse(BaseModel):
    """Unified response for the /trends endpoint."""
    trends: list[YearlyTrendItem]
    summary: TrendSummary



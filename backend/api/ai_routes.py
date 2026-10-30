"""
GradMap — AI Counselling Routes (FastAPI APIRouter)
==================================================
Exposes conversational GenAI endpoints for the GradMap frontend.

Endpoints:
- POST /ai/chat       : Send student query with conversation history & profile
- GET  /ai/status     : Check API key configuration & model status
- GET  /ai/suggested  : Retrieve personalized suggested questions
- POST /ai/reload-env : Reload .env dynamically without restarting server

Author  : GradMap AI Integration
Version : 1.0.0
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from api.ai_counsellor import ai_counsellor

log = logging.getLogger("gradmap.ai_routes")

router = APIRouter(prefix="/ai", tags=["AI Counselling"])


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic Schemas for AI Chat
# ──────────────────────────────────────────────────────────────────────────────

class ChatTurn(BaseModel):
    role: str = Field(..., description="Role of the speaker: 'user' or 'assistant'", examples=["user"])
    content: str = Field(..., description="Message text content", examples=["What can I get with 95 percentile?"])


class StudentProfilePayload(BaseModel):
    percentile: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="MHT-CET percentile score")
    category: Optional[str] = Field(default="GOPEN", description="Candidate category (e.g. GOPEN, GOBC, GSC)")
    branch_family: Optional[str] = Field(default=None, description="Preferred branch family or specific branch")
    district: Optional[str] = Field(default=None, description="Preferred district or home location")


class AIChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User question or statement to the AI counsellor.",
        examples=["Why is PICT classified as Ambitious for my score?"],
    )
    history: Optional[list[ChatTurn]] = Field(
        default=[],
        description="Prior turns in the conversation for multi-turn context.",
    )
    profile: Optional[StudentProfilePayload] = Field(
        default=None,
        description="Active student profile (percentile, category, branch preferences).",
    )


class AIChatResponse(BaseModel):
    response: str = Field(..., description="Markdown-formatted counselling response from Gemini.")
    status: str = Field(..., description="'success', 'warning', or 'error'")
    model_used: str = Field(..., description="Model identifier used for inference.")
    grounded: bool = Field(..., description="Whether response was grounded in actual GradMap data.")
    suggestions: list[str] = Field(default=[], description="Suggested next questions for the student.")


class AIStatusResponse(BaseModel):
    configured: bool = Field(..., description="True if GEMINI_API_KEY is present and client is ready.")
    model: str = Field(..., description="Current configured Gemini model.")
    message: str = Field(..., description="Status description.")


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/status", response_model=AIStatusResponse, summary="Check AI Assistant readiness")
def get_ai_status() -> AIStatusResponse:
    """
    Checks if Google Gemini API key is configured and returns the model name.
    """
    configured = ai_counsellor.is_configured()
    if configured:
        return AIStatusResponse(
            configured=True,
            model=ai_counsellor.model_name,
            message="Google Gemini AI Counsellor is fully configured and ready.",
        )
    return AIStatusResponse(
        configured=False,
        model=ai_counsellor.model_name,
        message="GEMINI_API_KEY is not set. Add your free key to backend/.env to activate.",
    )


@router.post("/reload-env", summary="Reload .env file without restarting")
def reload_ai_env() -> dict[str, Any]:
    """
    Reloads the backend/.env file and re-initializes the Gemini client.
    Useful when the user pastes an API key while the server is running.
    """
    ai_counsellor.reload_config()
    is_ready = ai_counsellor.is_configured()
    return {
        "reloaded": True,
        "configured": is_ready,
        "model": ai_counsellor.model_name,
        "message": "Environment configuration reloaded successfully.",
    }


@router.get("/suggested", summary="Get personalized suggested questions")
def get_suggested_questions(
    percentile: Optional[float] = Query(None, ge=0.0, le=100.0),
    category: Optional[str] = Query(None),
) -> dict[str, list[str]]:
    """
    Returns contextual suggested questions based on the student's score.
    """
    profile = {"percentile": percentile, "category": category} if percentile else None
    suggestions = ai_counsellor.get_dynamic_suggestions(student_profile=profile)
    return {"suggestions": suggestions}


@router.post(
    "/chat",
    response_model=AIChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with GradMap AI Counselling Assistant",
)
def chat_with_counsellor(payload: AIChatRequest) -> AIChatResponse:
    """
    Engage in conversational admission counselling grounded in actual MHT-CET
    historical cutoffs and ML predictions.

    - Retrieves student's ML recommendations (SAFE / TARGET / AMBITIOUS).
    - Queries 230k+ cutoff dataset for relevant college trends.
    - Generates factual, empathetic advice using the Google Gemini Free Tier.
    """
    # Import recommendation engine and cached dataset from main
    try:
        from api.main import _dataset_cache
        from scripts.modeling.recommendation_engine import recommend
    except ImportError as e:
        log.error("Could not import GradMap engine dependencies: %s", e)
        _dataset_cache = None
        recommend = None

    # Convert Pydantic models to dicts for internal consumption
    history_dicts = [{"role": t.role, "content": t.content} for t in (payload.history or [])]
    profile_dict = payload.profile.model_dump() if payload.profile else None

    try:
        result = ai_counsellor.generate_counselling_response(
            user_message=payload.message,
            conversation_history=history_dicts,
            student_profile=profile_dict,
            dataset=_dataset_cache,
            recommend_fn=recommend,
        )
        return AIChatResponse(**result)
    except Exception as e:
        log.exception("Unexpected error in AI Chat endpoint: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while communicating with the AI Counsellor: {str(e)}",
        )

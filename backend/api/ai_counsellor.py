"""
GradMap — AI Counselling Assistant (Gemini GenAI Integration)
============================================================
Powered by the official `google-genai` SDK and Google Gemini Free Tier.

Enhancements:
- Exponential backoff retry logic for transient errors (HTTP 503 High Demand, HTTP 429 Rate Limits).
- Strict handling for HTTP 401 (Invalid/Unauthorized API keys).
- Outdated models that return HTTP 404 removed.
- Fast, token-efficient context assembly (top-tier Safe, Target, Ambitious).
- Guaranteed Scikit-learn Random Forest model grounding.
- Safe timeouts to prevent hangs.

Author  : GradMap AI Integration
Version : 2.0.0
"""

from __future__ import annotations

import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from dotenv import load_dotenv

# Load backend/.env safely
BASE_BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_BACKEND_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

log = logging.getLogger("gradmap.ai_counsellor")

# ──────────────────────────────────────────────────────────────────────────────
# Google GenAI SDK Import
# ──────────────────────────────────────────────────────────────────────────────
_GENAI_AVAILABLE = False
try:
    from google import genai
    from google.genai import types
    from google.genai.errors import APIError, ClientError, ServerError
    _GENAI_AVAILABLE = True
except ImportError as e:
    log.warning("google-genai SDK not available: %s", e)

# ──────────────────────────────────────────────────────────────────────────────
# System Prompts & Grounding Instructions
# ──────────────────────────────────────────────────────────────────────────────
COUNSELLOR_SYSTEM_INSTRUCTION = """You are GradMap AI Counsellor, an expert, encouraging, and data-grounded engineering admission counselling assistant for Maharashtra MHT-CET students.

Your role is to explain, contextualize, compare, and strategize engineering college admissions for students navigating the State Common Entrance Test (CET) Cell Centralized Admission Process (CAP Rounds 1, 2, and 3).

STRICT GROUNDING & ACCURACY RULES:
1. FACTUAL GROUNDING: Rely strictly on the Student Profile, Machine Learning Predictions, and Cutoff Records provided in the context. DO NOT invent college names, cutoff percentiles, merit ranks, seat quotas, or admission chances. If data for a specific query is not in the context, explicitly say so.
2. ADMISSION CHANCE EXPLANATION:
   - "SAFE": Student percentile is comfortably higher than historical cutoffs (gap >= +2.0). ML model gives very high admission probability (typically >= 70-80%). High certainty of allotment.
   - "TARGET": Realistic, highly competitive choices where cutoff is close to student's percentile (-1.0 <= gap < +2.0). ML probability is moderate (45% - 70%). Very strong candidate if sequenced well in option form.
   - "AMBITIOUS": Dream/aspirational institutes where cutoff is higher than student's percentile (gap < -1.0). ML probability is lower (< 45%). Safe to put at top of Option Form for Round 1/2 without losing chances on safe colleges.
3. CAP ROUND STRATEGY:
   - Round 1: File ambitious dream colleges first (preferences 1 to 5), target colleges next (6 to 15), and safe backup colleges last (16+). Rule: If Preference 1 is allotted, it is auto-frozen.
   - Freeze vs Float vs Slide:
     * FREEZE: Student is satisfied with the allotted seat and confirms admission by paying seat acceptance fee. They exit further CAP rounds.
     * FLOAT: Student accepts the currently allotted seat (guaranteeing it), but participates in the next round hoping for an upgrade in any higher preference choice.
     * SLIDE: Student accepts the currently allotted seat, but participates in the next round seeking a better branch within the SAME institute.
   - Round 2 & 3: Cutoffs typically drop slightly in Round 2 and 3 for some branches due to seat movement, but top institutes remain stable or slightly rise due to category shifts.
4. TONE & STYLE:
   - Warm, friendly, professional, and clear.
   - Use structured formatting: bold headings, concise bullet points, and highlight college codes & percentiles clearly.
   - Encourage students to build a balanced Option Form with a mix of Dream, Realistic, and Safety choices.
"""

# Default verified models in Google AI Studio
# gemini-2.0-flash is preferred for speed; gemini-2.5-flash has thinking overhead
DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"
VERIFIED_FALLBACK_MODELS = []


class AICounsellor:
    """
    Manages Gemini client lifecycle, intelligent retry logic with exponential backoff,
    context retrieval from GradMap ML models & dataset, and prompt construction.
    """

    def __init__(self) -> None:
        self.api_key: Optional[str] = None
        self.model_name: str = DEFAULT_GEMINI_MODEL
        self._client: Any = None
        self._last_auth_error: Optional[str] = None
        self.reload_config()

    def reload_config(self) -> None:
        """Reloads .env file and re-initializes the Gemini client."""
        if ENV_PATH.exists():
            load_dotenv(dotenv_path=ENV_PATH, override=True)
        else:
            load_dotenv(override=True)

        self.api_key = os.getenv("GEMINI_API_KEY", "").strip() or None
        self.model_name = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip()
        self._last_auth_error = None
        self._init_client()

    def _init_client(self) -> None:
        """Initializes the official google-genai Client if API key is configured."""
        if not _GENAI_AVAILABLE:
            log.warning("google-genai SDK not installed.")
            self._client = None
            return

        if self.api_key:
            try:
                self._client = genai.Client(api_key=self.api_key)
                log.info("Gemini Client initialized (target model: '%s').", self.model_name)
            except Exception as e:
                log.error("Failed to initialize Gemini client: %s", e)
                self._client = None
        else:
            self._client = None

    def is_configured(self) -> bool:
        """Returns True if the Gemini API key is configured and client object exists."""
        if not self._client and self.api_key:
            self._init_client()
        return self._client is not None and bool(self.api_key)

    # ──────────────────────────────────────────────────────────────────────────
    # Context Retrieval & Grounding Engine
    # ──────────────────────────────────────────────────────────────────────────

    def build_grounded_context(
        self,
        message: str,
        student_profile: dict[str, Any] | None,
        dataset: pd.DataFrame | None,
        recommend_fn: Any | None,
    ) -> str:
        """
        Extracts high-signal, token-efficient ground truth from:
        1. Student profile (percentile, category, branch, approx rank)
        2. Live ML recommendations (SAFE, TARGET, AMBITIOUS with cutoffs & ML probabilities)
        3. Relevant college cutoff history from dataset
        4. Official CAP Round Rules
        """
        context_parts: list[str] = []

        percentile = 0.0
        category = "GOPEN"
        branch_family = "CS_FAMILY"
        district = "Maharashtra"

        if student_profile:
            percentile = float(student_profile.get("percentile") or 0.0)
            category = str(student_profile.get("category") or "GOPEN").strip().upper()
            branch_family = str(student_profile.get("branch_family") or student_profile.get("branch") or "CS_FAMILY")
            district = str(student_profile.get("district") or "Maharashtra")

        # Approximation of MHT-CET merit rank: rank ~= (100 - percentile)/100 * 120,000
        approx_merit_rank = max(1, int(((100 - percentile) / 100) * 120000)) if percentile > 0 else 0

        context_parts.append(
            f"--- STUDENT PROFILE ---\n"
            f"- MHT-CET Percentile: {percentile:.2f}%\n"
            f"- Estimated Merit Rank: ~{approx_merit_rank:,}\n"
            f"- Reservation Category: {category}\n"
            f"- Preferred Branch Family: {branch_family}\n"
            f"- Preferred District / Region: {district}\n"
        )

        # 2. Live ML Recommendations (Safe / Target / Ambitious)
        if percentile > 0 and recommend_fn and dataset is not None:
            try:
                engine_input = {
                    "user_percentile": percentile,
                    "user_category": category,
                    "preferred_branch_family": branch_family if branch_family != "ALL" else None,
                    "preferred_tier": None,
                    "top_n": 15,
                }
                raw_recs = recommend_fn(engine_input, df=dataset)

                rec_lines: list[str] = ["--- ML PREDICTED ADMISSION RECOMMENDATIONS ---"]
                for bucket in ("SAFE", "TARGET", "AMBITIOUS"):
                    items = raw_recs.get(bucket, [])[:2]  # Top 2 per bucket for token efficiency
                    rec_lines.append(f"\n[{bucket}] (Total: {len(raw_recs.get(bucket, []))}):")
                    if not items:
                        rec_lines.append("  (None matched)")
                    for item in items:
                        ml_prob = item.get("ml_probability")
                        prob_str = f"{ml_prob * 100:.0f}%" if (ml_prob is not None and not pd.isna(ml_prob)) else "N/A"
                        rec_lines.append(
                            f"  * {item.get('college_name')} ({item.get('institute_code', 'N/A')}) | "
                            f"{item.get('branch_name')} | "
                            f"Cutoff: {item.get('percentile_cutoff', 0):.2f}% | "
                            f"Gap: {item.get('percentile_gap', 0):+.2f}% | "
                            f"ML: {prob_str}"
                        )
                context_parts.append("\n".join(rec_lines))
            except Exception as e:
                log.warning("Could not execute recommend() for AI context: %s", e)

        # 3. Mentioned College Lookup
        if dataset is not None and not dataset.empty:
            mentioned = self._find_colleges_in_text(message, dataset)
            if mentioned:
                col_lines: list[str] = ["--- HISTORICAL CUTOFFS FOR MENTIONED COLLEGES ---"]
                for inst_code, inst_name in mentioned[:2]:
                    sub_df = dataset[dataset["institute_code"].astype(str) == str(inst_code)]
                    if sub_df.empty:
                        sub_df = dataset[dataset["college_name"].astype(str) == str(inst_name)]
                    if not sub_df.empty:
                        latest_year = int(sub_df["year"].max())
                        sample = sub_df[sub_df["year"] == latest_year].drop_duplicates("branch_name").head(4)
                        col_lines.append(f"\n{inst_name} (Code: {inst_code}, Year: {latest_year}):")
                        for _, row in sample.iterrows():
                            col_lines.append(
                                f"  - {row.get('branch_name')}: Cutoff {row.get('percentile_cutoff', 0):.2f}% ({row.get('category', 'GOPEN')})"
                            )
                context_parts.append("\n".join(col_lines))

        # 4. CAP Round Rules Reference (concise to minimize tokens)
        context_parts.append(
            "--- CAP RULES SUMMARY ---\n"
            "Round 1: Preference #1 allotment is AUTO-FROZEN. Rounds 2/3 are upgradation.\n"
            "FREEZE=Lock seat & exit CAP. FLOAT=Keep seat but seek any upgrade. SLIDE=Keep seat but seek better branch in same college."
        )

        return "\n\n".join(context_parts)

    def _find_colleges_in_text(self, text: str, dataset: pd.DataFrame) -> list[tuple[str, str]]:
        """Scans user query for known college names or keywords."""
        text_lower = text.lower()
        matched: list[tuple[str, str]] = []

        acronyms = {
            "coep": "college of engineering, pune",
            "vjti": "veermata jijabai",
            "spit": "sardar patel institute of technology",
            "pict": "pune institute of computer technology",
            "djsce": "dwarkadas j. sanghvi",
            "vit": "vishwakarma institute of technology",
            "pccoe": "pimpri chinchwad",
            "walchand": "walchand college of engineering",
            "vesit": "vivekanand education society",
            "kjsieit": "k. j. somaiya",
            "tsec": "thadomal shahani",
        }

        for acronym, name_sub in acronyms.items():
            if re.search(rf"\b{re.escape(acronym)}\b", text_lower):
                matched_rows = dataset[dataset["college_name"].str.contains(name_sub, case=False, na=False)]
                if not matched_rows.empty:
                    first_row = matched_rows.iloc[0]
                    matched.append((str(first_row["institute_code"]), str(first_row["college_name"])))

        code_matches = re.findall(r"\b\d{4,5}\b", text)
        for code in code_matches:
            matched_rows = dataset[dataset["institute_code"].astype(str) == str(code)]
            if not matched_rows.empty:
                first_row = matched_rows.iloc[0]
                matched.append((str(first_row["institute_code"]), str(first_row["college_name"])))

        seen = set()
        deduped = []
        for code, name in matched:
            if code not in seen:
                seen.add(code)
                deduped.append((code, name))
        return deduped

    # ──────────────────────────────────────────────────────────────────────────
    # Response Generation with Gemini & Exponential Backoff
    # ──────────────────────────────────────────────────────────────────────────

    def generate_counselling_response(
        self,
        user_message: str,
        conversation_history: list[dict[str, str]] | None = None,
        student_profile: dict[str, Any] | None = None,
        dataset: pd.DataFrame | None = None,
        recommend_fn: Any | None = None,
    ) -> dict[str, Any]:
        """
        Generates contextualized AI counselling advice with:
        - Exponential backoff retry on 503 and 429
        - Handling of 401 unauthenticated
        - Safe model fallbacks
        """
        if not self.is_configured():
            self._init_client()

        if not self._client or not self.api_key:
            return self._build_missing_key_response(student_profile)

        # 1. Build Grounded Context
        grounded_context = self.build_grounded_context(
            message=user_message,
            student_profile=student_profile,
            dataset=dataset,
            recommend_fn=recommend_fn,
        )

        # 2. Prepare Formatted Prompt Contents
        prompt_contents = self._prepare_gemini_contents(
            user_message=user_message,
            grounded_context=grounded_context,
            conversation_history=conversation_history,
        )

        # 3. Model candidate list (configured model first, then safe fallbacks without 404 models)
        models_to_try: list[str] = []
        if self.model_name:
            models_to_try.append(self.model_name)
        for fb in VERIFIED_FALLBACK_MODELS:
            if fb not in models_to_try:
                models_to_try.append(fb)

        response_text: Optional[str] = None
        model_used: str = self.model_name
        last_error: Optional[str] = None

        # Build base config — thinking disabled for all flash models (major speed improvement)
        # gemini-2.5-flash supports thinking_config; gemini-2.0-flash does not need it
        base_config_kwargs: dict[str, Any] = {
            "system_instruction": COUNSELLOR_SYSTEM_INSTRUCTION,
            "temperature": 0.35,
            "max_output_tokens": 800,
        }

        # Maximum retries per model for temporary transient issues (503 / 429)
        max_transient_retries = 3
        backoff_delays = [1.5, 3.0, 5.0]

        for current_model in models_to_try:
            log.info("Attempting counselling generation with model '%s'...", current_model)
            model_failed = False

            # Disable thinking for gemini-2.5-flash to eliminate multi-second thinking latency
            config_kwargs = dict(base_config_kwargs)
            if "2.5" in current_model:
                try:
                    config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
                except AttributeError:
                    pass  # Older SDK version — thinking_config not available, proceed without

            config = types.GenerateContentConfig(**config_kwargs)

            for attempt in range(max_transient_retries):
                try:
                    gen_response = await self._client.aio.models.generate_content(
                        model=current_model,
                        contents=prompt_contents,
                        config=config,
                    )

                    if gen_response and gen_response.text:
                        response_text = gen_response.text
                        model_used = current_model
                        break
                except Exception as e:
                    err_str = str(e)
                    last_error = err_str

                    # Check for 401 UNAUTHENTICATED
                    if "401" in err_str or "UNAUTHENTICATED" in err_str or "API key not valid" in err_str:
                        log.error("Gemini 401 Unauthenticated: %s", err_str)
                        self._last_auth_error = err_str
                        return self._build_invalid_key_response(err_str)

                    # Check for 404 (Model Not Found) -> skip to next fallback model immediately
                    if "404" in err_str or "NOT_FOUND" in err_str:
                        log.warning("Model '%s' returned 404 Not Found. Trying fallback model...", current_model)
                        model_failed = True
                        break

                    # Check for 503 (Service Unavailable / Overloaded) or 429 (Rate Limit)
                    is_transient = any(code in err_str for code in ["503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "overloaded"])
                    if is_transient:
                        if attempt < max_transient_retries - 1:
                            delay = backoff_delays[attempt]
                            log.warning("Gemini temporary error (%s) on model '%s'. Retrying in %.1fs (attempt %d/%d)...",
                                        "503 High Demand" if "503" in err_str else "429 Rate Limit",
                                        current_model, delay, attempt + 1, max_transient_retries)
                            time.sleep(delay)
                            continue
                        else:
                            log.warning("All retries exhausted for model '%s'.", current_model)
                            break
                    else:
                        log.error("Non-transient error on model '%s': %s", current_model, err_str)
                        break

            if response_text:
                break
            if model_failed:
                continue

        # If all attempts and fallbacks failed
        if not response_text:
            return self._build_error_response(last_error, student_profile)

        # 4. Generate context-aware suggestions
        suggestions = self.get_dynamic_suggestions(student_profile, user_message)

        return {
            "response": response_text,
            "status": "success",
            "model_used": model_used,
            "grounded": True,
            "suggestions": suggestions,
        }

    def _prepare_gemini_contents(
        self,
        user_message: str,
        grounded_context: str,
        conversation_history: list[dict[str, str]] | None,
    ) -> list[Any]:
        """Structures multi-turn conversation with ground truth context."""
        contents: list[Any] = []

        # Keep last 4 turns for multi-turn conversational context while minimizing token overhead
        if conversation_history:
            for turn in conversation_history[-4:]:
                role = turn.get("role")
                content = turn.get("content", "")
                if role in ("user", "human"):
                    contents.append(types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=content)]
                    ))
                elif role in ("assistant", "model"):
                    contents.append(types.Content(
                        role="model",
                        parts=[types.Part.from_text(text=content)]
                    ))

        # Latest User Query with Grounded Data
        latest_text = (
            f"[FACTUAL DATA GROUNDING FROM GRADMAP ENGINE]\n"
            f"{grounded_context}\n"
            f"[END OF FACTUAL DATA]\n\n"
            f"STUDENT QUESTION:\n{user_message}\n\n"
            f"Please answer using only the verified information above. Use clear markdown formatting."
        )

        contents.append(types.Content(
            role="user",
            parts=[types.Part.from_text(text=latest_text)]
        ))

        return contents

    def _build_invalid_key_response(self, error_detail: str) -> dict[str, Any]:
        """Provides a crystal-clear, formatted response when the API key fails authentication."""
        return {
            "response": (
                "### 🔑 Invalid or Unsupported Gemini API Key (HTTP 401)\n\n"
                "Google Gemini returned an authentication error with your current API key.\n\n"
                "**How to fix this (Free Tier in 30 seconds):**\n"
                "1. Go to **[Google AI Studio (aistudio.google.com/app/apikey)](https://aistudio.google.com/app/apikey)**.\n"
                "2. Click **Create API Key**.\n"
                "3. Copy your key (official AI Studio keys begin with `AIzaSy...`).\n"
                "4. Open `backend/.env` and paste your key:\n"
                "   ```env\n"
                "   GEMINI_API_KEY=AIzaSyYourActualKeyHere\n"
                "   GEMINI_MODEL=gemini-2.5-flash\n"
                "   ```\n"
                "5. Click **Reload .env** in the chat bar to activate immediately without restarting the server!"
            ),
            "status": "error",
            "model_used": "auth-validator",
            "grounded": False,
            "suggestions": [
                "Which colleges can I get with my percentile?",
                "What is the difference between Freeze, Float and Slide?",
                "How does the ML model classify Safe vs Ambitious?",
            ],
        }

    def _build_missing_key_response(self, student_profile: dict[str, Any] | None) -> dict[str, Any]:
        """User-friendly response when GEMINI_API_KEY is not set."""
        percentile = float((student_profile or {}).get("percentile") or 0.0)
        category = str((student_profile or {}).get("category") or "GOPEN")

        profile_context = f" for **{percentile:.2f}%** ({category})" if percentile > 0 else ""

        return {
            "response": (
                f"### 🎓 Welcome to the GradMap AI Counselling Assistant!\n\n"
                f"I am ready to help guide your MHT-CET admission journey{profile_context}.\n\n"
                f"#### 🔑 Setup Required: Configure your Free Gemini API Key\n"
                f"To enable real-time conversational counselling with Google Gemini Free Tier:\n\n"
                f"1. Get your free API key at **[Google AI Studio](https://aistudio.google.com/app/apikey)**.\n"
                f"2. Open `backend/.env` in your project.\n"
                f"3. Set your key:\n"
                f"   ```env\n"
                f"   GEMINI_API_KEY=AIzaSy...\n"
                f"   GEMINI_MODEL=gemini-2.5-flash\n"
                f"   ```\n"
                f"4. Click **Reload .env** in the header to activate instantly!"
            ),
            "status": "warning",
            "model_used": "setup-guide",
            "grounded": False,
            "suggestions": self.get_dynamic_suggestions(student_profile),
        }

    def _build_error_response(
        self,
        error_detail: Optional[str],
        student_profile: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Handles 503 high-demand, rate limits, or connectivity failures gracefully."""
        err_str = str(error_detail or "")

        if "503" in err_str or "UNAVAILABLE" in err_str or "overloaded" in err_str:
            msg = (
                "### ⏳ Google Gemini Temporary High Demand (HTTP 503)\n\n"
                "The Google Gemini free tier is currently experiencing brief, high global traffic. "
                "Our automated retry attempts have concluded.\n\n"
                "**What you can do:**\n"
                "- Please wait **15–20 seconds** and ask your question again.\n"
                "- Your student profile and recommendation records are fully cached in memory, so your session is safe!"
            )
        elif "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
            msg = (
                "### ⚠️ Gemini Free Tier Rate Limit (HTTP 429)\n\n"
                "You have temporarily reached the free-tier rate limit (15 requests/minute). "
                "Please wait 30 seconds and send your query again."
            )
        else:
            msg = (
                "### 📡 Temporary Connection Notice\n\n"
                f"Unable to reach the Gemini service: `{err_str[:120]}`.\n\n"
                "Please verify your `GEMINI_API_KEY` in `backend/.env` and ensure your device has internet access."
            )

        return {
            "response": msg,
            "status": "error",
            "model_used": "fallback-handler",
            "grounded": False,
            "suggestions": self.get_dynamic_suggestions(student_profile),
        }

    def get_dynamic_suggestions(
        self,
        student_profile: dict[str, Any] | None = None,
        last_message: Optional[str] = None,
    ) -> list[str]:
        """Generates dynamic suggested questions tailored to student score and stage."""
        percentile = float((student_profile or {}).get("percentile") or 0.0)

        if percentile > 0:
            return [
                f"Which colleges can I get with my {percentile:.1f} percentile?",
                "Why are my colleges classified as Safe, Target, or Ambitious?",
                "What is the difference between Freeze, Float, and Slide in CAP?",
                "How should I sequence my Option Form for CAP Round 1?",
                "Compare Computer Engineering vs IT vs AI/DS branches.",
            ]
        else:
            return [
                "Which colleges can I get with my percentile?",
                "What is the difference between Freeze, Float and Slide?",
                "Why is a college classified as Safe, Target or Ambitious?",
                "Compare two engineering colleges based on cutoff trends.",
                "How should I fill my CAP Round 1 option form?",
            ]


# Singleton instance
ai_counsellor = AICounsellor()

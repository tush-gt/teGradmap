"""
GradMap — AI Counselling Assistant (Gemini GenAI Integration)
============================================================
Powered by the official `google-genai` SDK and Google Gemini Free Tier.

This module provides data-grounded, empathetic, and accurate admission
guidance to MHT-CET engineering aspirants.

CRITICAL ARCHITECTURAL CONSTRAINTS:
1. ML Model Integrity: Scikit-learn Random Forest model remains the sole
   authority for predictions and admission probabilities.
2. Grounded Truth: Gemini NEVER hallucinates or invents cutoffs, colleges,
   ranks, or eligibility rules. All factual context is retrieved from the
   GradMap dataset and ML recommendation engine.
3. Secure Configuration: API keys are read from environment variables (.env).
4. Graceful Degradation: Handles missing API key, rate limits, and network
   exceptions without crashing the FastAPI application.

Author  : GradMap AI Integration
Version : 1.0.0
"""

from __future__ import annotations

import logging
import os
import re
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
    load_dotenv()  # Fallback to current working directory

log = logging.getLogger("gradmap.ai_counsellor")

# ──────────────────────────────────────────────────────────────────────────────
# Google GenAI SDK Import
# ──────────────────────────────────────────────────────────────────────────────
_GENAI_AVAILABLE = False
try:
    from google import genai
    from google.genai import types
    from google.genai.errors import APIError
    _GENAI_AVAILABLE = True
except ImportError as e:
    log.warning("google-genai SDK not available: %s", e)

# ──────────────────────────────────────────────────────────────────────────────
# System Prompts & Grounding Instructions
# ──────────────────────────────────────────────────────────────────────────────
COUNSELLOR_SYSTEM_INSTRUCTION = """You are GradMap AI Counsellor, an expert, encouraging, and data-grounded engineering admission counselling assistant for Maharashtra MHT-CET students.

Your role is to explain, contextualize, compare, and strategize engineering college admissions for students navigating the State Common Entrance Test (CET) Cell Centralized Admission Process (CAP Rounds 1, 2, and 3).

STRICT GROUNDING & ACCURACY RULES:
1. FACTUAL GROUNDING: Rely strictly on the Student Profile, Machine Learning Predictions, and Cutoff Records provided in the context. DO NOT invent college names, cutoff percentiles, merit ranks, seat quotas, or admission chances.
2. ADMISSION CHANCE EXPLANATION:
   - "SAFE": Student percentile is comfortably higher than historical cutoffs (gap >= +2.0). ML model gives very high admission probability (typically >= 70-80%). High certainty of allotment.
   - "TARGET": Realistic, highly competitive choices where cutoff is close to student's percentile (-1.0 <= gap < +2.0). ML probability is moderate (45% - 70%). Very strong candidate if sequenced well in option form.
   - "AMBITIOUS": Dream/aspirational institutes where cutoff is higher than student's percentile (gap < -1.0). ML probability is low (< 45%). Safe to put at top of Option Form for Round 1/2 without losing chances on safe colleges.
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
   - If the student asks about a college not present in the provided context or dataset, politely state that you only have data for verified Maharashtra engineering colleges and guide them to check official DTE/CET Cell records.
   - Encourage students to build a balanced Option Form with a mix of Dream, Realistic, and Safety choices.
"""

# Default free-tier models (gemini-2.5-flash / gemini-2.0-flash / gemini-1.5-flash)
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
FALLBACK_MODELS = ["gemini-2.0-flash", "gemini-1.5-flash"]


class AICounsellor:
    """
    Manages Gemini client initialization, context retrieval from GradMap ML
    models & historical dataset, prompt construction, and response generation.
    """

    def __init__(self) -> None:
        self.api_key: Optional[str] = os.getenv("GEMINI_API_KEY", "").strip() or None
        self.model_name: str = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip()
        self._client: Any = None
        self._init_client()

    def _init_client(self) -> None:
        """Initializes the official google-genai Client if API key is configured."""
        if not _GENAI_AVAILABLE:
            log.warning("google-genai library is missing. AI Counsellor in fallback mode.")
            return

        # Refresh key from env if updated at runtime
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip() or None
        self.model_name = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip()

        if self.api_key:
            try:
                self._client = genai.Client(api_key=self.api_key)
                log.info("Gemini GenAI client initialized successfully with model '%s'.", self.model_name)
            except Exception as e:
                log.error("Failed to initialize Gemini client: %s", e)
                self._client = None
        else:
            log.info("Gemini API key is not yet set. AI Counsellor will provide guidance on configuration.")
            self._client = None

    def reload_config(self) -> None:
        """Reloads .env file and re-initializes client."""
        if ENV_PATH.exists():
            load_dotenv(dotenv_path=ENV_PATH, override=True)
        self._init_client()

    def is_configured(self) -> bool:
        """Returns True if the Gemini API key is configured and client is ready."""
        if not self._client:
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
        Gathers factual ground truth from:
        1. Student profile (percentile, category, branch, rank approximation)
        2. Live ML recommendations (SAFE, TARGET, AMBITIOUS with cutoffs & probabilities)
        3. Relevant college cutoff history from dataset
        4. Specific colleges mentioned in user message
        """
        context_parts: list[str] = []

        # 1. Student Profile Grounding
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
            f"- MHT-CET Percentile: {percentile:.2f}\n"
            f"- Estimated Merit Rank: ~{approx_merit_rank:,} (state rank approximation)\n"
            f"- Candidate Category: {category}\n"
            f"- Preferred Branch / Domain: {branch_family}\n"
            f"- Location Preference: {district}\n"
        )

        # 2. Live ML Recommendations (Safe / Target / Ambitious)
        if percentile > 0 and recommend_fn and dataset is not None:
            try:
                engine_input = {
                    "user_percentile": percentile,
                    "user_category": category,
                    "preferred_branch_family": branch_family if branch_family != "ALL" else None,
                    "preferred_tier": None,
                    "top_n": 20,
                }
                raw_recs = recommend_fn(engine_input, df=dataset)

                rec_lines: list[str] = ["--- ML PREDICTED ADMISSION RECOMMENDATIONS ---"]
                for bucket in ("SAFE", "TARGET", "AMBITIOUS"):
                    items = raw_recs.get(bucket, [])[:4]  # Top 4 per bucket to keep context crisp
                    rec_lines.append(f"\n[{bucket} CHOICES] (Count in bucket: {len(raw_recs.get(bucket, []))}):")
                    if not items:
                        rec_lines.append("  (No specific colleges matched in this bucket for current criteria)")
                    for item in items:
                        prob_pct = (item.get("ml_probability") or item.get("probability") or 0.5) * 100
                        rec_lines.append(
                            f"  * {item.get('college_name')} (Code: {item.get('institute_code', 'N/A')}) | "
                            f"Branch: {item.get('branch_name')} | "
                            f"Tier: {item.get('institute_tier', 3)} | "
                            f"Historical Cutoff: {item.get('percentile_cutoff', 0):.2f}% | "
                            f"Gap: {item.get('percentile_gap', 0):+.2f}% | "
                            f"ML Admission Chance: {prob_pct:.1f}% ({item.get('confidence_label', 'MODERATE')})"
                        )
                context_parts.append("\n".join(rec_lines))
            except Exception as e:
                log.warning("Could not run recommend() for AI context: %s", e)

        # 3. Specific College & Historical Cutoff Lookup
        if dataset is not None and not dataset.empty:
            mentioned_colleges = self._find_colleges_in_text(message, dataset)
            if mentioned_colleges:
                col_lines: list[str] = ["--- HISTORICAL CUTOFF DATA FOR MENTIONED INSTITUTES ---"]
                for inst_code, inst_name in mentioned_colleges[:3]:
                    sub_df = dataset[dataset["institute_code"].astype(str) == str(inst_code)]
                    if sub_df.empty:
                        sub_df = dataset[dataset["college_name"].astype(str) == str(inst_name)]
                    if not sub_df.empty:
                        latest_year = sub_df["year"].max()
                        branches_sample = sub_df[sub_df["year"] == latest_year].drop_duplicates("branch_name").head(5)
                        col_lines.append(f"\nInstitute: {inst_name} (Code: {inst_code})")
                        for _, row in branches_sample.iterrows():
                            col_lines.append(
                                f"  - Branch: {row.get('branch_name')} | "
                                f"Latest Cutoff ({latest_year}): {row.get('percentile_cutoff', 0):.2f}% | "
                                f"Category: {row.get('category', 'GOPEN')}"
                            )
                context_parts.append("\n".join(col_lines))

        # 4. CAP Round Rules Reference
        context_parts.append(
            "--- OFFICIAL MHT-CET CAP ADMISSION GUIDELINES ---\n"
            "- Round 1: Initial allotment based on merit score and option preference order. Rule 1: Allotment of Option #1 is AUTO-FROZEN; seat acceptance is compulsory.\n"
            "- Round 2: Vacancy-based upgradation. Candidates with non-first choice allotments who chose FLOAT or SLIDE can receive a higher preference without losing their Round 1 seat.\n"
            "- Round 3: Final Centralized Allotment round for general and unallocated seats, prior to institute-level spot rounds.\n"
            "- Freeze Option: Candidate locks the allotted seat, pays the seat acceptance fee, and exits the CAP process.\n"
            "- Float Option: Candidate claims the seat with acceptance fee, but remains in the next round for ANY better preference in any institute.\n"
            "- Slide Option: Candidate claims the seat with acceptance fee, but seeks a higher branch preference strictly within the SAME college.\n"
        )

        return "\n\n".join(context_parts)

    def _find_colleges_in_text(self, text: str, dataset: pd.DataFrame) -> list[tuple[str, str]]:
        """Scans user query for known college names or keywords."""
        text_lower = text.lower()
        matched: list[tuple[str, str]] = []

        # Common acronyms mapped to standard queries
        acronyms = {
            "coep": "college of engineering, pune",
            "vjti": "veermata jijabai technological institute",
            "spit": "sardar patel institute of technology",
            "pict": "pune institute of computer technology",
            "djsce": "dwarkadas j. sanghvi",
            "vit": "vishwakarma institute of technology",
            "pccoe": "pimpri chinchwad college of engineering",
            "walchand": "walchand college of engineering",
            "vesit": "vivekanand education society's institute of technology",
            "kjsieit": "k. j. somaiya",
            "somaiya": "somaiya",
            "tsec": "thadomal shahani",
            "dj sanghvi": "dwarkadas",
            "gcoea": "government college of engineering amravati",
            "gcoek": "government college of engineering karad",
            "gcoen": "government college of engineering nagpur",
            "gcoea": "government college of engineering aurangabad",
        }

        # Check for acronym matches
        for acronym, name_sub in acronyms.items():
            if re.search(rf"\b{re.escape(acronym)}\b", text_lower):
                matched_rows = dataset[dataset["college_name"].str.contains(name_sub, case=False, na=False)]
                if not matched_rows.empty:
                    first_row = matched_rows.iloc[0]
                    matched.append((str(first_row["institute_code"]), str(first_row["college_name"])))

        # Also search for institute codes if mentioned as numbers (e.g., 6006, 3012)
        code_matches = re.findall(r"\b\d{4,5}\b", text)
        for code in code_matches:
            matched_rows = dataset[dataset["institute_code"].astype(str) == str(code)]
            if not matched_rows.empty:
                first_row = matched_rows.iloc[0]
                matched.append((str(first_row["institute_code"]), str(first_row["college_name"])))

        # Deduplicate
        seen = set()
        deduped = []
        for code, name in matched:
            if code not in seen:
                seen.add(code)
                deduped.append((code, name))
        return deduped

    # ──────────────────────────────────────────────────────────────────────────
    # Response Generation with Gemini
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
        Generates a contextualized AI counselling answer.
        Returns a dict:
        {
            "response": str,
            "status": "success" | "warning" | "error",
            "model_used": str,
            "grounded": bool,
            "suggestions": list[str]
        }
        """
        # Ensure client is ready
        if not self.is_configured():
            self._init_client()

        # If still not configured, provide helpful configuration instructions
        if not self._client or not self.api_key:
            return self._build_missing_key_response(student_profile, user_message)

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

        # 3. Call Gemini Model with fallback
        target_model = self.model_name
        response_text: Optional[str] = None
        error_detail: Optional[str] = None

        models_to_try = [target_model] + [m for m in FALLBACK_MODELS if m != target_model]

        for model_candidate in models_to_try:
            try:
                log.info("Generating counselling response with model '%s'...", model_candidate)
                config = types.GenerateContentConfig(
                    system_instruction=COUNSELLOR_SYSTEM_INSTRUCTION,
                    temperature=0.35,  # Balanced for creativity + strict adherence to facts
                    max_output_tokens=1500,
                )

                gen_response = self._client.models.generate_content(
                    model=model_candidate,
                    contents=prompt_contents,
                    config=config,
                )

                if gen_response and gen_response.text:
                    response_text = gen_response.text
                    target_model = model_candidate
                    break
            except APIError as e:
                error_detail = str(e)
                log.warning("Gemini APIError with model '%s': %s", model_candidate, e)
                # Check for rate limit
                if "429" in error_detail or "RESOURCE_EXHAUSTED" in error_detail:
                    return {
                        "response": (
                            "⚠️ **Gemini Free Tier Rate Limit Notice**\n\n"
                            "The Google Gemini API free-tier rate limit has been temporarily reached. "
                            "Please wait about 20-30 seconds and send your question again!\n\n"
                            "💡 *Tip: Your student profile and predictions are safely cached, so you won't lose your spot.*"
                        ),
                        "status": "warning",
                        "model_used": model_candidate,
                        "grounded": True,
                        "suggestions": self.get_dynamic_suggestions(student_profile),
                    }
                # If model not found or quota, loop to next fallback
                continue
            except Exception as e:
                error_detail = str(e)
                log.error("Unexpected error with model '%s': %s", model_candidate, e)
                continue

        if not response_text:
            return self._build_graceful_fallback(error_detail, student_profile, user_message)

        # 4. Generate context-aware suggestions
        suggestions = self.get_dynamic_suggestions(student_profile, user_message)

        return {
            "response": response_text,
            "status": "success",
            "model_used": target_model,
            "grounded": True,
            "suggestions": suggestions,
        }

    def _prepare_gemini_contents(
        self,
        user_message: str,
        grounded_context: str,
        conversation_history: list[dict[str, str]] | None,
    ) -> list[Any]:
        """
        Structures conversation history and the latest user message with
        attached ground truth for the google-genai SDK.
        """
        contents: list[Any] = []

        # Include recent conversation turns (up to 4 turns to conserve tokens)
        if conversation_history:
            for turn in conversation_history[-6:]:
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
            f"[FACTUAL DATA GROUNDING PROVIDED BY GRADMAP ENGINE]\n"
            f"{grounded_context}\n"
            f"[END OF FACTUAL DATA]\n\n"
            f"STUDENT QUESTION:\n{user_message}\n\n"
            f"Answer the student thoroughly using the factual data provided above. "
            f"Structure your response with clear markdown headings and bullet points."
        )

        contents.append(types.Content(
            role="user",
            parts=[types.Part.from_text(text=latest_text)]
        ))

        return contents

    def _build_missing_key_response(
        self,
        student_profile: dict[str, Any] | None,
        user_message: str,
    ) -> dict[str, Any]:
        """User-friendly response when GEMINI_API_KEY is not set."""
        percentile = float((student_profile or {}).get("percentile") or 0.0)
        category = str((student_profile or {}).get("category") or "GOPEN")

        profile_context = ""
        if percentile > 0:
            profile_context = f" (detected profile: **{percentile:.2f} percentile**, category **{category}**)"

        return {
            "response": (
                f"### 🎓 Welcome to the GradMap AI Counselling Assistant!\n\n"
                f"I am ready to help guide your MHT-CET admission journey{profile_context}.\n\n"
                f"#### 🔑 Setup Required: Configure your Free Gemini API Key\n"
                f"To enable real-time conversational counselling with Google Gemini Free Tier:\n\n"
                f"1. Get your free API key at **[Google AI Studio](https://aistudio.google.com/app/apikey)** (takes ~30 seconds, 100% free tier).\n"
                f"2. Open the file `backend/.env` in your project.\n"
                f"3. Set your key:\n"
                f"   ```env\n"
                f"   GEMINI_API_KEY=AIzaSy...\n"
                f"   GEMINI_MODEL=gemini-2.5-flash\n"
                f"   ```\n"
                f"4. Save the file. The AI Counsellor will automatically detect it!\n\n"
                f"--- \n"
                f"*In the meantime, the **GradMap ML Recommendation Engine**, **Trends Analyzer**, and **CAP Simulator** are fully operational in the dashboard tabs.*"
            ),
            "status": "warning",
            "model_used": "offline-configuration-guide",
            "grounded": False,
            "suggestions": [
                "Which colleges can I get with my percentile?",
                "What is the difference between Freeze, Float, and Slide?",
                "How does the ML model classify Safe vs Ambitious?",
            ],
        }

    def _build_graceful_fallback(
        self,
        error_detail: Optional[str],
        student_profile: dict[str, Any] | None,
        user_message: str,
    ) -> dict[str, Any]:
        """Provides a safe, graceful response if Gemini API call fails."""
        log.warning("Providing graceful fallback due to API error: %s", error_detail)
        return {
            "response": (
                "### 📡 Temporary Connection Notice\n\n"
                "I was unable to reach the Google Gemini service at this moment. "
                "This usually happens due to a temporary network blip or an invalid API key.\n\n"
                "**Please verify:**\n"
                "- Check that your `GEMINI_API_KEY` in `backend/.env` is active and correct.\n"
                "- Ensure your system has an active internet connection.\n"
                "- Retry your question in a few moments."
            ),
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
        """Generates contextual suggested questions based on student state."""
        percentile = float((student_profile or {}).get("percentile") or 0.0)

        if percentile > 0:
            return [
                f"Which top colleges can I get with my {percentile:.1f} percentile?",
                "Why are some colleges classified as Safe, Target, or Ambitious?",
                "How should I order my preferences in CAP Round 1?",
                "Explain Freeze, Float, and Slide strategies for me.",
                "Compare Computer Engineering vs IT vs AI/DS branches.",
            ]
        else:
            return [
                "Which colleges can I get with my percentile?",
                "What is the difference between Freeze, Float and Slide in CAP?",
                "Why is a college classified as Safe, Target or Ambitious?",
                "Compare two top colleges based on cutoff trends.",
                "How should I fill my CAP Round 1 option form?",
            ]


# Singleton instance
ai_counsellor = AICounsellor()

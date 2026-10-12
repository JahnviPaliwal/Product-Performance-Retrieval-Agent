"""LLM integration module using Groq LLaMA 3.1 with Pydantic schema validation, exponential backoff retries, and fallback safety.
"""

import json
import os
import re
import time
from typing import Any, Dict, List, Literal, Optional
from groq import Groq, GroqError
from pydantic import BaseModel, Field
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .logging_config import log_llm_call
from .router import WHITELISTED_INSIGHTS

MODEL = "llama-3.1-8b-instant"

InsightTypeLiteral = Literal[
    "distribution",
    "missing_data",
    "categorical_patterns",
    "relationships",
    "outliers",
    "schema",
]


class InsightRecommendation(BaseModel):
    """Schema for an individual insight recommendation."""
    title: str = Field(description="Clear title of the analytical insight")
    description: str = Field(description="Explanation of what this insight reveals")
    insight_type: InsightTypeLiteral = Field(description="Whitelisted deterministic routine name")
    relevant_columns: List[str] = Field(default_factory=list, description="Columns involved in this analysis")


class InsightPlan(BaseModel):
    """Schema for the full set of recommended insights."""
    insights: List[InsightRecommendation] = Field(description="List of exactly 6 insight recommendations")
    is_fallback: bool = False
    warning_message: Optional[str] = None


class FollowUpAnswer(BaseModel):
    """Schema for follow-up conversational answers."""
    answer: str
    reasoning: Optional[str] = None


DEFAULT_FALLBACK_INSIGHTS: List[Dict[str, Any]] = [
    {
        "title": "Dataset Schema Overview",
        "description": "Understand column data types, row counts, and structural composition.",
        "insight_type": "schema",
        "relevant_columns": [],
    },
    {
        "title": "Missing Values Audit",
        "description": "Identify columns with missing data and assess data completeness.",
        "insight_type": "missing_data",
        "relevant_columns": [],
    },
    {
        "title": "Numerical Distributions",
        "description": "Summary statistics (mean, spread, quartiles) of numeric columns.",
        "insight_type": "distribution",
        "relevant_columns": [],
    },
    {
        "title": "Category Frequency Patterns",
        "description": "Most common categorical values and distinct frequencies.",
        "insight_type": "categorical_patterns",
        "relevant_columns": [],
    },
    {
        "title": "Feature Correlations",
        "description": "Explore linear relationships and associations between numeric columns.",
        "insight_type": "relationships",
        "relevant_columns": [],
    },
    {
        "title": "Outlier Detection",
        "description": "Detect anomalous data points exceeding IQR boundaries in numeric features.",
        "insight_type": "outliers",
        "relevant_columns": [],
    },
]


def _get_groq_client(api_key: Optional[str] = None) -> Groq:
    """Resolve Groq API key from argument or environment and return client."""
    key = api_key or os.environ.get("GROQ_API_KEY")
    if not key:
        raise ValueError("Groq API key must be provided via input or GROQ_API_KEY environment variable.")
    return Groq(api_key=key)


def _clean_and_extract_json(text: str) -> Optional[Any]:
    """Extract valid JSON from LLM markdown code blocks or raw response text."""
    # Strip markdown code fences if present
    cleaned = re.sub(r"^```(?:json)?", "", text.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"```$", "", cleaned.strip(), flags=re.MULTILINE).strip()

    # Attempt direct json load
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Regex search for JSON array or object
    array_match = re.search(r"\[\s*\{.*\}\s*\]", text, re.DOTALL)
    if array_match:
        try:
            return json.loads(array_match.group(0))
        except json.JSONDecodeError:
            pass

    object_match = re.search(r"\{\s*\"insights\"\s*:\s*\[.*\]\s*\}", text, re.DOTALL)
    if object_match:
        try:
            return json.loads(object_match.group(0))
        except json.JSONDecodeError:
            pass

    return None


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    retry=retry_if_exception_type((GroqError, ConnectionError, TimeoutError)),
    reraise=True,
)
def _call_groq_with_retry(client: Groq, prompt: str, temperature: float = 0.1) -> Any:
    """Execute Groq chat completion with exponential backoff on transient errors."""
    return client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )


def recommend_insights(
    profile: Dict[str, Any],
    api_key: Optional[str] = None,
    client: Optional[Groq] = None,
) -> InsightPlan:
    """Generate validated insight recommendations for a dataset profile.

    Args:
        profile: Profile dictionary generated by profiler.py.
        api_key: Optional Groq API key (defaults to GROQ_API_KEY env var).
        client: Optional injected Groq client for testing/mocking.

    Returns:
        InsightPlan containing validated InsightRecommendation objects.
    """
    start_time = time.time()
    prompt = f"""You are an expert data analyst. Given the dataset profile below, recommend exactly 6 distinct analytical insights.

Allowed insight types (you MUST ONLY use these exact names):
- distribution
- missing_data
- categorical_patterns
- relationships
- outliers
- schema

Dataset profile:
{json.dumps(profile, indent=2)}

Output ONLY valid JSON formatted as an array of 6 objects:
[
  {{
    "title": "Short descriptive title",
    "description": "One sentence explaining what to look for",
    "insight_type": "distribution | missing_data | categorical_patterns | relationships | outliers | schema",
    "relevant_columns": ["col1", "col2"]
  }}
]
"""
    prompt_chars = len(prompt)

    try:
        active_client = client or _get_groq_client(api_key)
        response = _call_groq_with_retry(active_client, prompt, temperature=0.1)
        latency_ms = (time.time() - start_time) * 1000.0

        content = response.choices[0].message.content or ""
        usage = getattr(response, "usage", None)

        extracted = _clean_and_extract_json(content)
        if extracted is None:
            raise ValueError("LLM response did not contain parseable JSON.")

        # Normalize extracted format to list of dicts
        raw_list = extracted.get("insights", []) if isinstance(extracted, dict) else extracted

        if not isinstance(raw_list, list):
            raise ValueError("Expected JSON array of insights.")

        valid_recommendations: List[InsightRecommendation] = []
        for item in raw_list:
            if not isinstance(item, dict):
                continue
            # Sanitize insight_type
            itype = str(item.get("insight_type", "")).strip().lower()
            if itype not in WHITELISTED_INSIGHTS:
                continue
            item["insight_type"] = itype
            rec = InsightRecommendation(**item)
            valid_recommendations.append(rec)

        if len(valid_recommendations) < 3:
            raise ValueError(f"Fewer than 3 valid whitelisted insights returned ({len(valid_recommendations)}).")

        # Pad to 6 if needed from default insights
        existing_types = {r.insight_type for r in valid_recommendations}
        for default_item in DEFAULT_FALLBACK_INSIGHTS:
            if len(valid_recommendations) >= 6:
                break
            if default_item["insight_type"] not in existing_types:
                valid_recommendations.append(InsightRecommendation(**default_item))
                existing_types.add(default_item["insight_type"])

        log_llm_call(MODEL, prompt_chars, latency_ms, usage=usage, status="success")
        return InsightPlan(insights=valid_recommendations[:6], is_fallback=False)

    except Exception as exc:
        latency_ms = (time.time() - start_time) * 1000.0
        err_msg = str(exc)
        log_llm_call(MODEL, prompt_chars, latency_ms, usage=None, status="fallback", error_message=err_msg)

        fallback_plan = [InsightRecommendation(**item) for item in DEFAULT_FALLBACK_INSIGHTS]
        return InsightPlan(
            insights=fallback_plan,
            is_fallback=True,
            warning_message=f"LLM insight planning encountered an issue ({err_msg}). Displaying standard exploratory plan.",
        )


def answer_followup(
    profile: Dict[str, Any],
    insight_title: str,
    insight_result: Any,
    user_question: str,
    api_key: Optional[str] = None,
    client: Optional[Groq] = None,
) -> FollowUpAnswer:
    """Answer a user follow-up question grounded strictly in the executed insight results.

    Args:
        profile: Dataset profile metadata.
        insight_title: Title of the analyzed insight.
        insight_result: Deterministic computation result (DataFrame, dict, etc.).
        user_question: Natural language question asked by user.
        api_key: Optional Groq API key.
        client: Optional injected Groq client for testing.

    Returns:
        FollowUpAnswer containing grounded answer and reasoning.
    """
    start_time = time.time()
    result_str = str(insight_result)
    if len(result_str) > 3000:
        result_str = result_str[:3000] + "... [truncated]"

    prompt = f"""You are a rigorous, careful data analyst.

Dataset profile summary:
- Rows: {profile.get('num_rows', 'Unknown')}
- Columns: {profile.get('num_columns', 'Unknown')}

Executed Insight:
Title: {insight_title}
Result data:
{result_str}

Rules:
1. Answer ONLY using the provided insight result data and dataset summary.
2. If the question cannot be answered strictly from the data above, state clearly:
   "This cannot be determined from the current analysis."
3. Do NOT extrapolate or assume missing values.

User question:
{user_question}
"""
    prompt_chars = len(prompt)

    try:
        active_client = client or _get_groq_client(api_key)
        response = _call_groq_with_retry(active_client, prompt, temperature=0.2)
        latency_ms = (time.time() - start_time) * 1000.0

        content = (response.choices[0].message.content or "").strip()
        usage = getattr(response, "usage", None)

        log_llm_call(MODEL, prompt_chars, latency_ms, usage=usage, status="success")
        return FollowUpAnswer(answer=content)

    except Exception as exc:
        latency_ms = (time.time() - start_time) * 1000.0
        err_msg = str(exc)
        log_llm_call(MODEL, prompt_chars, latency_ms, usage=None, status="error", error_message=err_msg)
        return FollowUpAnswer(
            answer=f"Unable to process question due to API error: {err_msg}. Please check your Groq API key or try again."
        )

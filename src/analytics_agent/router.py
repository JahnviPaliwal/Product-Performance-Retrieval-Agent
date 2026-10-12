"""Insight router module mapping whitelisted insight names to deterministic Python analysis routines.
"""

from enum import Enum
from typing import Any, Callable, Dict, Union
import pandas as pd
from pydantic import BaseModel

from . import analysis as af


class InsightType(str, Enum):
    """Enumeration of all supported deterministic insight routines."""
    DISTRIBUTION = "distribution"
    MISSING_DATA = "missing_data"
    CATEGORICAL_PATTERNS = "categorical_patterns"
    RELATIONSHIPS = "relationships"
    OUTLIERS = "outliers"
    SCHEMA = "schema"


WHITELISTED_INSIGHTS = {e.value for e in InsightType}

# Dispatch mapping for deterministic execution
INSIGHT_DISPATCH: Dict[str, Callable[[pd.DataFrame], Any]] = {
    InsightType.DISTRIBUTION.value: af.distribution,
    InsightType.MISSING_DATA.value: af.missing_data,
    InsightType.CATEGORICAL_PATTERNS.value: af.categorical_patterns,
    InsightType.RELATIONSHIPS.value: af.relationships,
    InsightType.OUTLIERS.value: af.outliers,
    InsightType.SCHEMA.value: af.schema,
}


class InsightExecutionResult(BaseModel):
    """Structured result of executing a routed insight."""
    insight_type: str
    success: bool
    data: Any
    error_message: Union[str, None] = None

    class Config:
        arbitrary_types_allowed = True


def run_insight(insight_type: str, df: pd.DataFrame) -> Any:
    """Execute the deterministic analysis function corresponding to insight_type.

    Args:
        insight_type: The name of the insight to execute (must be whitelisted).
        df: Input pandas DataFrame.

    Returns:
        The output produced by the analysis function.

    Raises:
        ValueError: If insight_type is not present in WHITELISTED_INSIGHTS.
    """
    normalized_type = str(insight_type).strip().lower()

    if normalized_type not in WHITELISTED_INSIGHTS:
        valid_list = ", ".join(sorted(WHITELISTED_INSIGHTS))
        raise ValueError(
            f"Unknown insight type '{insight_type}'. "
            f"Routable functions are strictly whitelisted to: [{valid_list}]."
        )

    handler = INSIGHT_DISPATCH[normalized_type]
    return handler(df)


def classify_intent_route(
    question: str,
    api_key: Union[str, None] = None,
    client: Any = None,
) -> str:
    """Route a natural language question to one of the 6 whitelisted deterministic routines.

    Uses LLM classification if an active Groq client/key is available, or deterministic
    semantic keyword matching for reproducible offline evaluation.

    Args:
        question: User query or analytical intent.
        api_key: Optional Groq API key.
        client: Optional injected Groq client.

    Returns:
        One of the whitelisted insight names.
    """
    normalized_q = question.lower()

    # If Groq client is provided or api_key exists, attempt LLM routing
    if client is not None or api_key or "GROQ_API_KEY" in __import__("os").environ:
        try:
            import os
            from groq import Groq
            k = api_key or os.environ.get("GROQ_API_KEY")
            active_client = client or Groq(api_key=k)
            prompt = (
                f"Classify this data question into EXACTLY one of these 6 categories:\n"
                f"- distribution\n- missing_data\n- categorical_patterns\n"
                f"- relationships\n- outliers\n- schema\n\n"
                f"Question: {question}\n\n"
                f"Reply with ONLY the single lowercase category name."
            )
            resp = active_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            raw_category = (resp.choices[0].message.content or "").strip().lower()
            for w in WHITELISTED_INSIGHTS:
                if w in raw_category:
                    return w
        except Exception:
            pass  # Fall back to deterministic semantic matcher

    # Deterministic semantic keyword matching
    if any(k in normalized_q for k in ["schema", "dtype", "data type", "table structure", "column structure"]):
        return InsightType.SCHEMA.value
    if any(k in normalized_q for k in ["missing", "unrecorded", "empty cells", "blank values"]) or ("null" in normalized_q and "non-null" not in normalized_q):
        return InsightType.MISSING_DATA.value
    if any(k in normalized_q for k in ["outlier", "extreme", "anomaly", "anomalous", "unusually"]):
        return InsightType.OUTLIERS.value
    if any(k in normalized_q for k in ["correlation", "correlate", "relationship", "coefficient", "linear relationship"]):
        return InsightType.RELATIONSHIPS.value
    if any(k in normalized_q for k in ["category", "frequency", "popular", "most frequent", "roles", "department", "payment method", "breakdown of paperless"]):
        return InsightType.CATEGORICAL_PATTERNS.value
    if any(k in normalized_q for k in ["distribution", "average", "spread", "median", "standard deviation", "quartile", "descriptive statistics"]):
        return InsightType.DISTRIBUTION.value

    # Default to distribution if ambiguous
    return InsightType.DISTRIBUTION.value


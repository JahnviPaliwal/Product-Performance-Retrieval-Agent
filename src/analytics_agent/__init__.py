"""Analytics Agent - LLM-Guided Data Analytics Agent.

Combines LLM planning with deterministic Python execution for safe,
explainable data exploration and reporting.
"""

from .profiler import profile_dataframe, ColumnProfile, DatasetProfile
from .quality import compute_data_quality, QualityWeights, QualityReport
from .analysis import (
    distribution,
    missing_data,
    categorical_patterns,
    relationships,
    outliers,
    schema,
)
from .charts import generate_chart, chart_to_png_bytes
from .router import run_insight, WHITELISTED_INSIGHTS, InsightType
from .retrieval import ColumnRetriever, retrieve_relevant_columns
from .llm import recommend_insights, answer_followup, InsightRecommendation, InsightPlan
from .report import generate_pdf_report, REPORTLAB_AVAILABLE
from .logging_config import get_logger

__all__ = [
    "profile_dataframe",
    "ColumnProfile",
    "DatasetProfile",
    "compute_data_quality",
    "QualityWeights",
    "QualityReport",
    "distribution",
    "missing_data",
    "categorical_patterns",
    "relationships",
    "outliers",
    "schema",
    "generate_chart",
    "chart_to_png_bytes",
    "run_insight",
    "WHITELISTED_INSIGHTS",
    "InsightType",
    "ColumnRetriever",
    "retrieve_relevant_columns",
    "recommend_insights",
    "answer_followup",
    "InsightRecommendation",
    "InsightPlan",
    "generate_pdf_report",
    "REPORTLAB_AVAILABLE",
    "get_logger",
]

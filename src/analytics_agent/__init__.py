"""Analytics Agent - LLM-Guided Data Analytics Agent.

Combines LLM planning with deterministic Python execution for safe,
explainable data exploration and reporting.
"""

from typing import Any

__version__ = "1.0.0"

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


def __getattr__(name: str) -> Any:
    """Lazy load submodules on attribute access to prevent import deadlocks in multi-threaded environments."""
    if name in {"profile_dataframe", "ColumnProfile", "DatasetProfile"}:
        from . import profiler
        return getattr(profiler, name)

    if name in {"compute_data_quality", "QualityWeights", "QualityReport"}:
        from . import quality
        return getattr(quality, name)

    if name in {
        "distribution",
        "missing_data",
        "categorical_patterns",
        "relationships",
        "outliers",
        "schema",
    }:
        from . import analysis
        return getattr(analysis, name)

    if name in {"generate_chart", "chart_to_png_bytes"}:
        from . import charts
        return getattr(charts, name)

    if name in {"run_insight", "WHITELISTED_INSIGHTS", "InsightType"}:
        from . import router
        return getattr(router, name)

    if name in {"ColumnRetriever", "retrieve_relevant_columns"}:
        from . import retrieval
        return getattr(retrieval, name)

    if name in {
        "recommend_insights",
        "answer_followup",
        "InsightRecommendation",
        "InsightPlan",
    }:
        from . import llm
        return getattr(llm, name)

    if name in {"generate_pdf_report", "REPORTLAB_AVAILABLE"}:
        from . import report
        return getattr(report, name)

    if name == "get_logger":
        from . import logging_config
        return getattr(logging_config, name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

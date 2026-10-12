"""Unit tests for LLM planning, Pydantic schema validation, and fallback mechanisms."""

import json
from unittest.mock import MagicMock
import pytest
from analytics_agent.llm import (
    InsightPlan,
    answer_followup,
    recommend_insights,
)
from analytics_agent.router import WHITELISTED_INSIGHTS


@pytest.fixture
def mock_profile():
    return {
        "num_rows": 100,
        "num_columns": 3,
        "columns": [
            {"name": "sales", "dtype": "float64", "nulls": 0, "unique": 90},
            {"name": "cost", "dtype": "float64", "nulls": 5, "unique": 80},
            {"name": "region", "dtype": "object", "nulls": 0, "unique": 4},
        ],
    }


def test_recommend_insights_valid_json(mock_profile):
    mock_client = MagicMock()
    valid_json = json.dumps([
        {"title": "Sales Distribution", "description": "Check spread of sales", "insight_type": "distribution", "relevant_columns": ["sales"]},
        {"title": "Cost Outliers", "description": "Identify extreme costs", "insight_type": "outliers", "relevant_columns": ["cost"]},
        {"title": "Missing Values Audit", "description": "Inspect missing data", "insight_type": "missing_data", "relevant_columns": ["cost"]},
        {"title": "Regional Frequency", "description": "Check region distribution", "insight_type": "categorical_patterns", "relevant_columns": ["region"]},
        {"title": "Sales-Cost Relationship", "description": "Correlation between sales and cost", "insight_type": "relationships", "relevant_columns": ["sales", "cost"]},
        {"title": "Schema Overview", "description": "Understand column data types", "insight_type": "schema", "relevant_columns": []},
    ])

    choice = MagicMock()
    choice.message.content = f"```json\n{valid_json}\n```"
    mock_client.chat.completions.create.return_value = MagicMock(choices=[choice], usage=MagicMock(prompt_tokens=100, completion_tokens=80, total_tokens=180))

    plan = recommend_insights(mock_profile, client=mock_client)
    assert isinstance(plan, InsightPlan)
    assert not plan.is_fallback
    assert len(plan.insights) == 6
    for ins in plan.insights:
        assert ins.insight_type in WHITELISTED_INSIGHTS


def test_recommend_insights_malformed_json_fallback(mock_profile):
    mock_client = MagicMock()
    choice = MagicMock()
    choice.message.content = "Here is some random text without valid JSON {not: valid}"
    mock_client.chat.completions.create.return_value = MagicMock(choices=[choice], usage=None)

    plan = recommend_insights(mock_profile, client=mock_client)
    assert isinstance(plan, InsightPlan)
    assert plan.is_fallback
    assert len(plan.insights) == 6
    assert "LLM insight planning encountered an issue" in plan.warning_message


def test_recommend_insights_unknown_insight_names_filtered(mock_profile):
    mock_client = MagicMock()
    json_with_bad_types = json.dumps([
        {"title": "Valid One", "description": "desc", "insight_type": "distribution", "relevant_columns": []},
        {"title": "Invalid Two", "description": "desc", "insight_type": "neural_net_magic", "relevant_columns": []},
        {"title": "Valid Three", "description": "desc", "insight_type": "outliers", "relevant_columns": []},
        {"title": "Valid Four", "description": "desc", "insight_type": "missing_data", "relevant_columns": []},
    ])

    choice = MagicMock()
    choice.message.content = json_with_bad_types
    mock_client.chat.completions.create.return_value = MagicMock(choices=[choice], usage=None)

    plan = recommend_insights(mock_profile, client=mock_client)
    assert isinstance(plan, InsightPlan)
    # The unknown type "neural_net_magic" is filtered out, padded with defaults up to 6
    for ins in plan.insights:
        assert ins.insight_type in WHITELISTED_INSIGHTS


def test_answer_followup_mocked(mock_profile):
    mock_client = MagicMock()
    choice = MagicMock()
    choice.message.content = "Based on the correlation matrix, sales and cost have a 0.85 positive correlation."
    mock_client.chat.completions.create.return_value = MagicMock(choices=[choice], usage=None)

    answer = answer_followup(
        profile=mock_profile,
        insight_title="Feature Relationships",
        insight_result={"sales_cost_corr": 0.85},
        user_question="What is the correlation between sales and cost?",
        client=mock_client,
    )
    assert "0.85 positive correlation" in answer.answer

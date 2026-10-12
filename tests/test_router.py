"""Unit tests for router validation and execution dispatch."""

import pandas as pd
import pytest
from analytics_agent.router import (
    WHITELISTED_INSIGHTS,
    InsightType,
    classify_intent_route,
    run_insight,
)


@pytest.fixture
def df():
    return pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})


def test_whitelisted_insights_complete():
    expected = {"distribution", "missing_data", "categorical_patterns", "relationships", "outliers", "schema"}
    assert WHITELISTED_INSIGHTS == expected


def test_run_valid_insights(df):
    for itype in WHITELISTED_INSIGHTS:
        result = run_insight(itype, df)
        assert result is not None


def test_run_invalid_insight_raises_value_error(df):
    with pytest.raises(ValueError) as exc_info:
        run_insight("arbitrary_hacked_function", df)
    assert "strictly whitelisted" in str(exc_info.value)


def test_classify_intent_route_offline():
    assert classify_intent_route("Find missing values in table") == InsightType.MISSING_DATA.value
    assert classify_intent_route("Show me the numerical distribution of prices") == InsightType.DISTRIBUTION.value
    assert classify_intent_route("Are there any anomalous outliers in salary?") == InsightType.OUTLIERS.value
    assert classify_intent_route("What is the correlation between age and income?") == InsightType.RELATIONSHIPS.value
    assert classify_intent_route("Display the table schema and data types") == InsightType.SCHEMA.value
    assert classify_intent_route("What is the frequency of payment categories?") == InsightType.CATEGORICAL_PATTERNS.value

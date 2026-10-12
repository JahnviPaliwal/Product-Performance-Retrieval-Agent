"""Unit tests for deterministic analysis functions."""

import pandas as pd
import pytest
from analytics_agent.analysis import (
    categorical_patterns,
    distribution,
    missing_data,
    outliers,
    relationships,
    schema,
)


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "age": [25, 30, 35, 40, 120],  # 120 is an IQR outlier
        "salary": [50000, 60000, 70000, 80000, 90000],
        "department": ["Sales", "Engineering", "Sales", "HR", "Sales"],
        "notes": ["ok", None, "good", None, "ok"],
    })


def test_distribution(sample_df):
    result = distribution(sample_df)
    assert isinstance(result, pd.DataFrame)
    assert "age" in result.columns
    assert "salary" in result.columns
    assert "mean" in result.index


def test_distribution_no_numeric():
    df = pd.DataFrame({"name": ["Alice", "Bob"]})
    result = distribution(df)
    assert isinstance(result, dict)
    assert "message" in result


def test_missing_data(sample_df):
    result = missing_data(sample_df)
    assert isinstance(result, pd.DataFrame)
    assert "Missing_Count" in result.columns
    assert result.loc["notes", "Missing_Count"] == 2
    assert result.loc["age", "Missing_Count"] == 0


def test_missing_data_empty_df():
    df = pd.DataFrame()
    result = missing_data(df)
    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_categorical_patterns(sample_df):
    result = categorical_patterns(sample_df, top_n=3)
    assert "department" in result
    assert result["department"]["Sales"] == 3
    assert result["department"]["Engineering"] == 1


def test_categorical_patterns_no_categorical():
    df = pd.DataFrame({"val": [1, 2, 3]})
    result = categorical_patterns(df)
    assert "message" in result


def test_relationships(sample_df):
    result = relationships(sample_df)
    assert isinstance(result, pd.DataFrame)
    assert result.loc["salary", "salary"] == 1.0


def test_relationships_single_numeric():
    df = pd.DataFrame({"val": [1, 2, 3], "cat": ["a", "b", "c"]})
    result = relationships(df)
    assert isinstance(result, dict)
    assert "message" in result


def test_outliers(sample_df):
    result = outliers(sample_df)
    assert "age" in result
    assert result["age"]["outlier_count"] >= 1
    assert result["age"]["upper_bound"] < 120


def test_outliers_no_numeric():
    df = pd.DataFrame({"name": ["A", "B", "C"]})
    result = outliers(df)
    assert "message" in result


def test_schema(sample_df):
    result = schema(sample_df)
    assert isinstance(result, pd.DataFrame)
    assert "Data_Type" in result.columns
    assert "Non_Null_Count" in result.columns
    assert result.loc["notes", "Non_Null_Count"] == 3

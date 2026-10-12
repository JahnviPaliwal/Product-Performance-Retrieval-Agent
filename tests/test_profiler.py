"""Unit tests for dataset profiler module."""

import pandas as pd
from analytics_agent.profiler import profile_dataframe


def test_profile_normal_dataframe():
    df = pd.DataFrame({
        "num_col": [1.0, 2.5, 3.0, 4.5],
        "cat_col": ["A", "B", "A", "C"],
        "has_nulls": [10, None, 30, None],
    })
    profile = profile_dataframe(df)

    assert profile["num_rows"] == 4
    assert profile["num_columns"] == 3
    assert profile["memory_usage_kb"] > 0
    assert len(profile["columns"]) == 3

    col_map = {c["name"]: c for c in profile["columns"]}
    assert col_map["num_col"]["nulls"] == 0
    assert col_map["has_nulls"]["nulls"] == 2
    assert col_map["has_nulls"]["null_percentage"] == 50.0
    assert col_map["cat_col"]["unique"] == 3
    assert len(col_map["cat_col"]["sample_values"]) <= 4


def test_profile_empty_dataframe():
    df = pd.DataFrame(columns=["empty_a", "empty_b"])
    profile = profile_dataframe(df)

    assert profile["num_rows"] == 0
    assert profile["num_columns"] == 2
    assert len(profile["columns"]) == 2
    assert profile["columns"][0]["nulls"] == 0


def test_profile_all_nulls_column():
    df = pd.DataFrame({"all_nulls": [None, None, None]})
    profile = profile_dataframe(df)

    assert profile["num_rows"] == 3
    col = profile["columns"][0]
    assert col["nulls"] == 3
    assert col["null_percentage"] == 100.0
    assert col["unique"] == 0
    assert col["sample_values"] == []

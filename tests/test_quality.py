"""Unit tests for configurable data quality calculation."""

import pandas as pd
import pytest
from analytics_agent.quality import QualityWeights, compute_data_quality, compute_quality_report


def test_perfect_quality_data():
    df = pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "score": [10.0, 11.0, 12.0, 13.0, 14.0],
    })
    report = compute_quality_report(df)
    assert report.score == 100.0
    assert report.missing_cells == 0
    assert report.duplicate_rows == 0
    assert report.outlier_count == 0


def test_quality_penalties():
    # 50% missing, 1 duplicate, outliers present
    df = pd.DataFrame({
        "val1": [10, None, 10, None],
        "val2": [20, None, 20, 500],  # 500 outlier, row 0 and 2 duplicates
    })
    score = compute_data_quality(df)
    assert 0.0 <= score < 90.0


def test_custom_configurable_weights():
    df = pd.DataFrame({
        "a": [1, 2, None, None],
        "b": [1, 2, None, None],
    })
    # If missing weight is 1.0 and others 0.0
    strict_missing_weights = QualityWeights(
        missing_weight=1.0,
        duplicate_weight=0.0,
        outlier_weight=0.0,
    )
    report_strict = compute_quality_report(df, strict_missing_weights)
    # missing ratio is 4 / 8 = 0.5, penalty is 0.5 * 100 = 50.0
    assert report_strict.score == 50.0

    # If missing weight is 0.0 and duplicate weight is 1.0
    no_missing_penalty_weights = QualityWeights(
        missing_weight=0.0,
        duplicate_weight=1.0,
        outlier_weight=0.0,
    )
    report_no_missing = compute_quality_report(df, no_missing_penalty_weights)
    # 1 duplicate row out of 4 = 0.25 penalty -> 75.0
    assert report_no_missing.score == 75.0


def test_quality_weights_normalization():
    weights = QualityWeights(missing_weight=0.8, duplicate_weight=0.6, outlier_weight=0.6)
    # Total is 2.0 -> should normalize to sum to 1.0
    total = weights.missing_weight + weights.duplicate_weight + weights.outlier_weight
    assert pytest.approx(total, 0.01) == 1.0


def test_empty_dataframe_quality():
    df = pd.DataFrame()
    report = compute_quality_report(df)
    assert report.score == 0.0

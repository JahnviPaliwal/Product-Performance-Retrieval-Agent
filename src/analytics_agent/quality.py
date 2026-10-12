"""Data quality scoring module with configurable penalties for missing data, duplicates, and outliers.
"""

from typing import Dict, Optional, Any
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field, model_validator


class QualityWeights(BaseModel):
    """Configurable weights for data quality computation.

    Weights must be non-negative and sum to 1.0 (or be normalized).
    """
    missing_weight: float = Field(default=0.4, ge=0.0, le=1.0, description="Weight penalty for missing cell ratio")
    duplicate_weight: float = Field(default=0.3, ge=0.0, le=1.0, description="Weight penalty for duplicate row ratio")
    outlier_weight: float = Field(default=0.3, ge=0.0, le=1.0, description="Weight penalty for IQR outlier ratio")

    @model_validator(mode="after")
    def validate_weights_sum(self) -> "QualityWeights":
        """Ensure total weight is positive and close to 1.0; normalize if needed."""
        total = self.missing_weight + self.duplicate_weight + self.outlier_weight
        if total <= 0:
            raise ValueError("Total weights must be greater than zero.")
        # If slight floating point discrepancy or custom scaling, normalize
        if not np.isclose(total, 1.0):
            object.__setattr__(self, "missing_weight", round(self.missing_weight / total, 4))
            object.__setattr__(self, "duplicate_weight", round(self.duplicate_weight / total, 4))
            object.__setattr__(self, "outlier_weight", round(self.outlier_weight / total, 4))
        return self


class QualityReport(BaseModel):
    """Detailed breakdown of the data quality computation."""
    score: float
    total_cells: int
    missing_cells: int
    missing_ratio: float
    total_rows: int
    duplicate_rows: int
    duplicate_ratio: float
    numeric_columns: int
    outlier_count: int
    outlier_ratio: float
    weights: QualityWeights
    penalties: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary format."""
        return self.model_dump()


def compute_quality_report(
    df: pd.DataFrame,
    weights: Optional[QualityWeights] = None
) -> QualityReport:
    """Compute detailed data quality breakdown and composite score (0-100).

    Args:
        df: Input pandas DataFrame.
        weights: Configurable weights for missing, duplicate, and outlier penalties.

    Returns:
        QualityReport with score and individual metric penalties.
    """
    if weights is None:
        weights = QualityWeights()

    if df.empty:
        return QualityReport(
            score=0.0,
            total_cells=0,
            missing_cells=0,
            missing_ratio=0.0,
            total_rows=0,
            duplicate_rows=0,
            duplicate_ratio=0.0,
            numeric_columns=0,
            outlier_count=0,
            outlier_ratio=0.0,
            weights=weights,
            penalties={"missing": 0.0, "duplicate": 0.0, "outlier": 0.0},
        )

    num_rows, num_cols = df.shape
    total_cells = num_rows * num_cols

    # 1. Missing data ratio
    missing_cells = int(df.isna().sum().sum())
    missing_ratio = float(missing_cells / total_cells) if total_cells > 0 else 0.0

    # 2. Duplicate rows ratio
    duplicate_rows = int(df.duplicated().sum())
    duplicate_ratio = float(duplicate_rows / num_rows) if num_rows > 0 else 0.0

    # 3. IQR Outliers on numeric columns
    numeric_cols = df.select_dtypes(include=[np.number])
    num_numeric = len(numeric_cols.columns)
    outlier_count = 0

    if num_numeric > 0 and num_rows > 3:
        for col in numeric_cols.columns:
            series = numeric_cols[col].dropna()
            if len(series) < 4:
                continue
            q1 = float(series.quantile(0.25))
            q3 = float(series.quantile(0.75))
            iqr = q3 - q1
            if iqr > 0:
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                outliers_in_col = int(((series < lower_bound) | (series > upper_bound)).sum())
                outlier_count += outliers_in_col

    total_possible_numeric_cells = num_rows * max(num_numeric, 1)
    outlier_ratio = float(outlier_count / total_possible_numeric_cells)

    # Calculate penalties
    penalty_missing = weights.missing_weight * missing_ratio
    penalty_duplicate = weights.duplicate_weight * duplicate_ratio
    penalty_outlier = weights.outlier_weight * outlier_ratio

    total_penalty = penalty_missing + penalty_duplicate + penalty_outlier
    score = 100.0 * (1.0 - total_penalty)
    clamped_score = max(0.0, min(100.0, round(score, 1)))

    return QualityReport(
        score=clamped_score,
        total_cells=total_cells,
        missing_cells=missing_cells,
        missing_ratio=round(missing_ratio, 4),
        total_rows=num_rows,
        duplicate_rows=duplicate_rows,
        duplicate_ratio=round(duplicate_ratio, 4),
        numeric_columns=num_numeric,
        outlier_count=outlier_count,
        outlier_ratio=round(outlier_ratio, 4),
        weights=weights,
        penalties={
            "missing_penalty": round(penalty_missing * 100.0, 2),
            "duplicate_penalty": round(penalty_duplicate * 100.0, 2),
            "outlier_penalty": round(penalty_outlier * 100.0, 2),
        },
    )


def compute_data_quality(
    df: pd.DataFrame,
    weights: Optional[QualityWeights] = None
) -> float:
    """Convenience helper to compute composite data quality score (0-100).

    Args:
        df: Input pandas DataFrame.
        weights: Optional configurable weights.

    Returns:
        Float score between 0.0 and 100.0.
    """
    report = compute_quality_report(df, weights)
    return report.score

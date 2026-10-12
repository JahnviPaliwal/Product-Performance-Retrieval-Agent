"""Deterministic analysis functions executing pandas statistical routines safely.
"""

from typing import Any, Dict, Union
import numpy as np
import pandas as pd


def distribution(df: pd.DataFrame) -> Union[pd.DataFrame, Dict[str, str]]:
    """Compute numerical distribution summary (count, mean, std, min, quartiles, max).

    Args:
        df: Input pandas DataFrame.

    Returns:
        DataFrame containing summary statistics for numeric columns.
    """
    numeric = df.select_dtypes(include=[np.number])
    if numeric.empty:
        return {"message": "No numeric columns found in dataset to compute distribution."}
    return numeric.describe().round(4)


def missing_data(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate missing values and missing percentages for all columns.

    Args:
        df: Input pandas DataFrame.

    Returns:
        DataFrame summarizing missing counts and percentages per column.
    """
    if df.empty:
        return pd.DataFrame(columns=["Missing_Count", "Missing_Percentage"])

    null_counts = df.isna().sum()
    null_pct = (null_counts / len(df) * 100.0).round(2)
    summary = pd.DataFrame({
        "Missing_Count": null_counts,
        "Missing_Percentage": null_pct,
    })
    return summary.sort_values(by="Missing_Count", ascending=False)


def categorical_patterns(df: pd.DataFrame, top_n: int = 5) -> Dict[str, Dict[str, int]]:
    """Analyze high-frequency values for categorical and string columns.

    Args:
        df: Input pandas DataFrame.
        top_n: Maximum number of top frequent categories to return per column.

    Returns:
        Dictionary mapping column names to top category frequency mappings.
    """
    categorical_cols = df.select_dtypes(include=["object", "category"])
    if categorical_cols.empty:
        return {"message": {"No categorical columns found": 0}}

    patterns: Dict[str, Dict[str, int]] = {}
    for col in categorical_cols.columns:
        counts = df[col].astype(str).value_counts().head(top_n).to_dict()
        patterns[str(col)] = {str(k): int(v) for k, v in counts.items()}
    return patterns


def relationships(df: pd.DataFrame) -> Union[pd.DataFrame, Dict[str, str]]:
    """Compute Pearson correlation matrix across numerical variables.

    Args:
        df: Input pandas DataFrame.

    Returns:
        Correlation matrix DataFrame, or message if fewer than 2 numeric columns.
    """
    numeric = df.select_dtypes(include=[np.number])
    if len(numeric.columns) < 2:
        return {"message": "At least 2 numerical columns are required to calculate correlations."}
    return numeric.corr().round(4)


def outliers(df: pd.DataFrame) -> Dict[str, Any]:
    """Identify IQR outliers across numerical columns.

    Args:
        df: Input pandas DataFrame.

    Returns:
        Dictionary of outlier counts, boundaries, and percentages per numeric column.
    """
    numeric = df.select_dtypes(include=[np.number])
    if numeric.empty:
        return {"message": "No numeric columns found to detect outliers."}

    summary: Dict[str, Any] = {}
    num_rows = len(df)

    for col in numeric.columns:
        series = numeric[col].dropna()
        if len(series) < 4:
            continue
        q1 = float(series.quantile(0.25))
        q3 = float(series.quantile(0.75))
        iqr = q3 - q1
        lower_bound = round(q1 - 1.5 * iqr, 4)
        upper_bound = round(q3 + 1.5 * iqr, 4)
        outlier_mask = (series < lower_bound) | (series > upper_bound)
        count = int(outlier_mask.sum())
        pct = round((count / num_rows) * 100.0, 2) if num_rows > 0 else 0.0

        summary[str(col)] = {
            "outlier_count": count,
            "outlier_percentage": pct,
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
        }

    return summary if summary else {"message": "Insufficient data points to compute IQR outliers."}


def schema(df: pd.DataFrame) -> pd.DataFrame:
    """Extract schema summary including data types, nulls, and non-null counts.

    Args:
        df: Input pandas DataFrame.

    Returns:
        DataFrame detailing column names, data types, and non-null counts.
    """
    return pd.DataFrame({
        "Data_Type": df.dtypes.astype(str),
        "Non_Null_Count": df.notna().sum(),
        "Null_Count": df.isna().sum(),
    })

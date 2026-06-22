"""
analytics/analysis_engine.py
Statistical analysis functions reused and extended from the original project.
"""
import io
import pandas as pd
import numpy as np


def profile_dataframe(df: pd.DataFrame) -> dict:
    return {
        "num_rows": len(df),
        "num_columns": len(df.columns),
        "columns": [
            {
                "name": col,
                "dtype": str(df[col].dtype),
                "nulls": int(df[col].isna().sum()),
                "unique": int(df[col].nunique()),
                "sample": str(df[col].dropna().head(3).tolist()),
            }
            for col in df.columns
        ],
    }


def compute_data_quality(df: pd.DataFrame) -> float:
    total_cells = df.shape[0] * df.shape[1]
    missing_ratio = df.isnull().sum().sum() / total_cells
    duplicate_ratio = df.duplicated().sum() / len(df)
    outlier_count = 0
    numeric_cols = df.select_dtypes(include="number").columns
    for col in numeric_cols:
        q1, q3 = df[col].quantile(0.25), df[col].quantile(0.75)
        iqr = q3 - q1
        outlier_count += int(((df[col] < q1 - 1.5 * iqr) | (df[col] > q3 + 1.5 * iqr)).sum())
    outlier_ratio = outlier_count / (len(df) * max(len(numeric_cols), 1))
    score = 100 * (1 - 0.4 * missing_ratio - 0.3 * duplicate_ratio - 0.3 * outlier_ratio)
    return max(0.0, round(score, 1))


def distribution(df: pd.DataFrame) -> str:
    return df.describe(include="all").to_string()


def missing_data(df: pd.DataFrame) -> dict:
    return df.isnull().sum().to_dict()


def categorical_patterns(df: pd.DataFrame) -> dict:
    result = {}
    for col in df.select_dtypes(include="object").columns:
        result[col] = df[col].value_counts().head(10).to_dict()
    return result


def relationships(df: pd.DataFrame) -> dict:
    numeric = df.select_dtypes(include="number")
    if numeric.empty:
        return {}
    corr = numeric.corr().round(3)
    return corr.to_dict()


def outliers(df: pd.DataFrame) -> dict:
    summary = {}
    for col in df.select_dtypes(include="number").columns:
        q1, q3 = df[col].quantile(0.25), df[col].quantile(0.75)
        iqr = q3 - q1
        mask = (df[col] < q1 - 1.5 * iqr) | (df[col] > q3 + 1.5 * iqr)
        outlier_vals = df[col][mask].tolist()
        summary[col] = {"count": int(mask.sum()), "values": outlier_vals[:10]}
    return summary


def schema(df: pd.DataFrame) -> dict:
    return {col: str(df[col].dtype) for col in df.columns}


def trends(df: pd.DataFrame) -> dict:
    """Detect date column and compute per-period averages for numeric cols."""
    date_col = None
    for col in df.columns:
        if "date" in col.lower() or "time" in col.lower():
            try:
                df[col] = pd.to_datetime(df[col])
                date_col = col
                break
            except Exception:
                continue
    if date_col is None:
        return {"error": "No date/time column detected for trend analysis."}
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if not numeric_cols:
        return {"error": "No numeric columns for trend."}
    df_sorted = df.sort_values(date_col)
    result = {}
    for col in numeric_cols[:3]:
        result[col] = df_sorted[[date_col, col]].dropna().tail(20).to_dict(orient="list")
    return result


def group_summary(df: pd.DataFrame, group_col: str, agg_col: str) -> dict:
    if group_col not in df.columns or agg_col not in df.columns:
        return {"error": f"Column not found: {group_col} or {agg_col}"}
    grouped = df.groupby(group_col)[agg_col].agg(["mean", "sum", "count", "min", "max"]).round(2)
    return grouped.to_dict()


def run_analysis(analysis_type: str, df: pd.DataFrame, **kwargs) -> dict:
    ROUTER = {
        "distribution": lambda: {"result": distribution(df)},
        "missing_data": lambda: {"result": missing_data(df)},
        "categorical_patterns": lambda: {"result": categorical_patterns(df)},
        "relationships": lambda: {"result": relationships(df)},
        "outliers": lambda: {"result": outliers(df)},
        "schema": lambda: {"result": schema(df)},
        "trends": lambda: {"result": trends(df)},
        "quality": lambda: {"result": compute_data_quality(df)},
        "profile": lambda: {"result": profile_dataframe(df)},
    }
    if analysis_type in ROUTER:
        try:
            return ROUTER[analysis_type]()
        except Exception as e:
            return {"error": str(e)}
    return {"error": f"Unknown analysis type: {analysis_type}"}

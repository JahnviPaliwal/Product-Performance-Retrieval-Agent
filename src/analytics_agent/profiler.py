"""Dataset profiler module for extracting metadata, column distributions, and sample values.
"""

from typing import Any, Dict, List
import pandas as pd
from pydantic import BaseModel, Field


class ColumnProfile(BaseModel):
    """Metadata and summary statistics for a single column."""
    name: str
    dtype: str
    nulls: int
    null_percentage: float
    unique: int
    sample_values: List[str] = Field(default_factory=list)
    semantic_summary: str = ""


class DatasetProfile(BaseModel):
    """Dataset-level metadata and list of column profiles."""
    num_rows: int
    num_columns: int
    memory_usage_kb: float
    columns: List[ColumnProfile]

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to serializable dictionary."""
        return self.model_dump()


def profile_dataframe(df: pd.DataFrame, max_samples: int = 4) -> Dict[str, Any]:
    """Profile a pandas DataFrame to extract metadata, distributions, and sample values.

    Args:
        df: Input pandas DataFrame to profile.
        max_samples: Number of sample unique values to extract for column retrieval.

    Returns:
        A dictionary containing dataset-level statistics and detailed column profiles.
    """
    if df.empty:
        return {
            "num_rows": 0,
            "num_columns": len(df.columns),
            "memory_usage_kb": 0.0,
            "columns": [
                {
                    "name": str(col),
                    "dtype": str(df[col].dtype),
                    "nulls": 0,
                    "null_percentage": 0.0,
                    "unique": 0,
                    "sample_values": [],
                    "semantic_summary": f"Empty column {col}",
                }
                for col in df.columns
            ],
        }

    num_rows = len(df)
    num_cols = len(df.columns)
    mem_kb = round(df.memory_usage(deep=True).sum() / 1024.0, 2)

    col_profiles: List[Dict[str, Any]] = []

    for col in df.columns:
        series = df[col]
        null_count = int(series.isna().sum())
        null_pct = round((null_count / num_rows) * 100.0, 2) if num_rows > 0 else 0.0
        unique_count = int(series.nunique(dropna=True))

        # Extract representative distinct non-null samples
        non_null = series.dropna()
        if not non_null.empty:
            samples = [str(val)[:50] for val in non_null.unique()[:max_samples]]
        else:
            samples = []

        # Generate concise semantic summary for embeddings / LLM context
        dtype_str = str(series.dtype)
        if pd.api.types.is_numeric_dtype(series):
            min_val = round(float(series.min()), 2) if not series.empty and pd.notna(series.min()) else "N/A"
            max_val = round(float(series.max()), 2) if not series.empty and pd.notna(series.max()) else "N/A"
            summary = f"Numeric column ({dtype_str}) ranging from {min_val} to {max_val}."
        elif pd.api.types.is_datetime64_any_dtype(series):
            summary = f"Datetime column ({dtype_str}) with {unique_count} distinct timestamps."
        else:
            top_samples = ", ".join(samples[:3]) if samples else "None"
            summary = f"Categorical/Text column ({dtype_str}) with {unique_count} unique values. Examples: {top_samples}."

        col_profiles.append({
            "name": str(col),
            "dtype": dtype_str,
            "nulls": null_count,
            "null_percentage": null_pct,
            "unique": unique_count,
            "sample_values": samples,
            "semantic_summary": summary,
        })

    return {
        "num_rows": num_rows,
        "num_columns": num_cols,
        "memory_usage_kb": mem_kb,
        "columns": col_profiles,
    }

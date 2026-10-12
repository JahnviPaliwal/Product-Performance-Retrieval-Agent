"""Headless chart generation module using Matplotlib for Streamlit rendering and PDF report embedding.
"""

import io
from typing import Optional
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend safe for servers and multithreading
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def chart_to_png_bytes(fig: plt.Figure) -> bytes:
    """Convert a matplotlib Figure to raw PNG bytes.

    Args:
        fig: Matplotlib Figure instance.

    Returns:
        PNG image bytes.
    """
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def generate_chart(insight_type: str, df: pd.DataFrame) -> Optional[plt.Figure]:
    """Generate a clean Matplotlib Figure for the requested insight type.

    Args:
        insight_type: Whitelisted insight name.
        df: Input pandas DataFrame.

    Returns:
        Matplotlib Figure object, or None if data cannot be visualized.
    """
    if df.empty:
        return None

    numeric = df.select_dtypes(include=[np.number])
    categorical = df.select_dtypes(include=["object", "category"])

    fig, ax = plt.subplots(figsize=(8, 4.5), constrained_layout=True)

    if insight_type == "distribution":
        if numeric.empty:
            ax.text(0.5, 0.5, "No numeric columns to plot distribution.", ha="center", va="center")
            ax.axis("off")
        else:
            # Plot distributions of up to first 3 numeric columns
            cols = numeric.columns[:3]
            for col in cols:
                series = numeric[col].dropna()
                if not series.empty:
                    ax.hist(series, bins=20, alpha=0.5, label=str(col), edgecolor="black")
            ax.set_title("Distribution Overview (Histogram)")
            ax.set_xlabel("Value")
            ax.set_ylabel("Frequency")
            ax.legend()
            ax.grid(True, linestyle="--", alpha=0.5)

    elif insight_type == "missing_data":
        null_counts = df.isna().sum()
        cols_with_nulls = null_counts[null_counts > 0]
        if cols_with_nulls.empty:
            ax.text(0.5, 0.5, "No missing values found in dataset!", ha="center", va="center", color="green", fontsize=12)
            ax.axis("off")
        else:
            cols_with_nulls.plot(kind="bar", ax=ax, color="#e74c3c", edgecolor="black")
            ax.set_title("Missing Values Count by Column")
            ax.set_ylabel("Count of Missing Cells")
            ax.tick_params(axis="x", rotation=45)
            ax.grid(axis="y", linestyle="--", alpha=0.5)

    elif insight_type == "categorical_patterns":
        if categorical.empty:
            ax.text(0.5, 0.5, "No categorical columns to visualize.", ha="center", va="center")
            ax.axis("off")
        else:
            col = categorical.columns[0]
            top_cats = df[col].astype(str).value_counts().head(8)
            top_cats.plot(kind="barh", ax=ax, color="#3498db", edgecolor="black")
            ax.set_title(f"Top Categories in '{col}'")
            ax.set_xlabel("Count")
            ax.invert_yaxis()
            ax.grid(axis="x", linestyle="--", alpha=0.5)

    elif insight_type == "relationships":
        if len(numeric.columns) < 2:
            ax.text(0.5, 0.5, "Need at least 2 numeric columns for correlation heatmap.", ha="center", va="center")
            ax.axis("off")
        else:
            corr = numeric.corr()
            cax = ax.matshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
            fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04)
            ticks = np.arange(len(corr.columns))
            ax.set_xticks(ticks)
            ax.set_yticks(ticks)
            ax.set_xticklabels(corr.columns, rotation=45, ha="left")
            ax.set_yticklabels(corr.columns)
            ax.set_title("Numeric Correlation Heatmap", pad=20)

    elif insight_type == "outliers":
        if numeric.empty:
            ax.text(0.5, 0.5, "No numeric columns for outlier boxplots.", ha="center", va="center")
            ax.axis("off")
        else:
            # Boxplot of normalized or raw numeric columns (up to 4)
            cols = numeric.columns[:4]
            data_to_plot = [numeric[c].dropna() for c in cols if not numeric[c].dropna().empty]
            if data_to_plot:
                ax.boxplot(data_to_plot, labels=[str(c) for c in cols[:len(data_to_plot)]], patch_artist=True)
                ax.set_title("Outlier Analysis (Boxplot)")
                ax.set_ylabel("Values")
                ax.tick_params(axis="x", rotation=30)
                ax.grid(True, linestyle="--", alpha=0.5)
            else:
                ax.text(0.5, 0.5, "Insufficient numeric data for boxplot.", ha="center", va="center")
                ax.axis("off")

    elif insight_type == "schema":
        dtype_counts = df.dtypes.astype(str).value_counts()
        dtype_counts.plot(kind="pie", ax=ax, autopct="%1.1f%%", startangle=90, colors=["#2ecc71", "#3498db", "#f39c12", "#9b59b6"])
        ax.set_ylabel("")
        ax.set_title("Column Data Type Composition")

    else:
        ax.text(0.5, 0.5, f"No chart implementation for '{insight_type}'.", ha="center", va="center")
        ax.axis("off")

    return fig

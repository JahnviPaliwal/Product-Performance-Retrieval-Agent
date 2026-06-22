"""
analytics/chart_generator.py
Generate chart images as base64 PNG strings using matplotlib.
Auto-select best chart type based on data characteristics.
"""
import io
import base64
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm


def _fig_to_b64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight", facecolor="white")
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return encoded


def bar_chart(labels, values, title="Bar Chart", xlabel="", ylabel="") -> str:
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = cm.Blues(np.linspace(0.4, 0.85, len(labels)))
    bars = ax.bar([str(l) for l in labels], values, color=colors, edgecolor="white", linewidth=0.8)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel(xlabel, fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.tick_params(axis="x", rotation=30)
    ax.spines[["top", "right"]].set_visible(False)
    # Value labels
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h * 1.01,
                f"{h:,.1f}", ha="center", va="bottom", fontsize=9)
    fig.tight_layout()
    return _fig_to_b64(fig)


def line_chart(x, y, title="Line Chart", xlabel="", ylabel="", label="") -> str:
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(x, y, marker="o", markersize=4, linewidth=2,
            color="#1565C0", markerfacecolor="#42A5F5")
    ax.fill_between(range(len(x)), y, alpha=0.12, color="#1565C0")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel(xlabel, fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.tick_params(axis="x", rotation=30)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return _fig_to_b64(fig)


def pie_chart(labels, values, title="Pie Chart") -> str:
    # Collapse small slices into "Other"
    total = sum(values)
    threshold = total * 0.02
    main_labels, main_vals, other_val = [], [], 0
    for l, v in zip(labels, values):
        if v >= threshold:
            main_labels.append(str(l))
            main_vals.append(v)
        else:
            other_val += v
    if other_val > 0:
        main_labels.append("Other")
        main_vals.append(other_val)

    fig, ax = plt.subplots(figsize=(8, 6))
    colors = cm.Set3(np.linspace(0, 1, len(main_labels)))
    wedges, texts, autotexts = ax.pie(
        main_vals, labels=main_labels, autopct="%1.1f%%",
        startangle=140, colors=colors,
        pctdistance=0.82, wedgeprops=dict(width=0.65, edgecolor="white", linewidth=1.5),
    )
    for autotext in autotexts:
        autotext.set_fontsize(9)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=16)
    fig.tight_layout()
    return _fig_to_b64(fig)


def scatter_chart(x, y, title="Scatter Plot", xlabel="", ylabel="") -> str:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(x, y, alpha=0.6, color="#1565C0", edgecolors="white", linewidths=0.5, s=50)
    # Trend line
    try:
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)
        x_sorted = sorted(x)
        ax.plot(x_sorted, p(x_sorted), "r--", linewidth=1.5, alpha=0.7, label="Trend")
        ax.legend()
    except Exception:
        pass
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel(xlabel, fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return _fig_to_b64(fig)


def histogram(values, col_name="Value", bins=20) -> str:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(values, bins=bins, color="#1565C0", edgecolor="white", linewidth=0.6, alpha=0.85)
    ax.axvline(np.mean(values), color="red", linestyle="--", linewidth=1.5, label=f"Mean: {np.mean(values):.2f}")
    ax.set_title(f"Distribution of {col_name}", fontsize=14, fontweight="bold")
    ax.set_xlabel(col_name, fontsize=11)
    ax.set_ylabel("Frequency", fontsize=11)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend()
    fig.tight_layout()
    return _fig_to_b64(fig)


def heatmap(corr_df: pd.DataFrame, title="Correlation Matrix") -> str:
    fig, ax = plt.subplots(figsize=(max(6, len(corr_df) * 0.9), max(5, len(corr_df) * 0.8)))
    data = corr_df.values
    im = ax.imshow(data, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr_df.columns)))
    ax.set_yticks(range(len(corr_df.columns)))
    ax.set_xticklabels(corr_df.columns, rotation=45, ha="right", fontsize=9)
    ax.set_yticklabels(corr_df.columns, fontsize=9)
    for i in range(len(corr_df)):
        for j in range(len(corr_df.columns)):
            ax.text(j, i, f"{data[i, j]:.2f}", ha="center", va="center",
                    fontsize=8, color="white" if abs(data[i, j]) > 0.5 else "black")
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
    fig.tight_layout()
    return _fig_to_b64(fig)


def boxplot(df: pd.DataFrame, title="Box Plot") -> str:
    numeric = df.select_dtypes(include="number")
    if numeric.empty:
        return ""
    cols = numeric.columns[:8].tolist()
    fig, ax = plt.subplots(figsize=(max(7, len(cols) * 1.2), 5))
    bp = ax.boxplot([numeric[c].dropna().tolist() for c in cols],
                    labels=cols, patch_artist=True, notch=False,
                    medianprops=dict(color="red", linewidth=2))
    colors = cm.Blues(np.linspace(0.3, 0.75, len(cols)))
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.tick_params(axis="x", rotation=30)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return _fig_to_b64(fig)


def auto_chart(df: pd.DataFrame, query_hint: str = "") -> dict:
    """
    Auto-select best chart(s) based on data shape and optional query hint.
    Returns {"chart_type": str, "image_b64": str, "title": str}
    """
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(include="object").columns.tolist()
    n_rows = len(df)
    hint = query_hint.lower()

    charts = []

    # Time-series line chart
    date_col = None
    for col in df.columns:
        if "date" in col.lower() or "time" in col.lower() or "month" in col.lower() or "year" in col.lower():
            try:
                df[col] = pd.to_datetime(df[col])
                date_col = col
                break
            except Exception:
                pass

    if date_col and numeric_cols:
        col = numeric_cols[0]
        df_s = df.sort_values(date_col)
        x_labels = df_s[date_col].dt.strftime("%Y-%m").tolist()
        y_vals = df_s[col].tolist()
        charts.append({
            "chart_type": "line",
            "image_b64": line_chart(x_labels, y_vals, title=f"{col} Over Time", xlabel=date_col, ylabel=col),
            "title": f"{col} Over Time",
        })

    # Categorical bar chart
    if cat_cols and numeric_cols:
        cat = cat_cols[0]
        num = numeric_cols[0]
        grouped = df.groupby(cat)[num].mean().sort_values(ascending=False).head(15)
        charts.append({
            "chart_type": "bar",
            "image_b64": bar_chart(grouped.index.tolist(), grouped.values.tolist(),
                                   title=f"Avg {num} by {cat}", xlabel=cat, ylabel=f"Mean {num}"),
            "title": f"Avg {num} by {cat}",
        })

    # Distribution histogram
    if numeric_cols:
        col = numeric_cols[0]
        charts.append({
            "chart_type": "histogram",
            "image_b64": histogram(df[col].dropna().tolist(), col_name=col),
            "title": f"Distribution of {col}",
        })

    # Correlation heatmap
    if len(numeric_cols) >= 2:
        corr_df = df[numeric_cols].corr()
        charts.append({
            "chart_type": "heatmap",
            "image_b64": heatmap(corr_df),
            "title": "Correlation Matrix",
        })

    # Scatter if two numeric cols
    if len(numeric_cols) >= 2 and ("scatter" in hint or "correlat" in hint or "relationship" in hint):
        x_vals = df[numeric_cols[0]].dropna().tolist()
        y_vals_s = df[numeric_cols[1]].dropna().tolist()
        min_len = min(len(x_vals), len(y_vals_s))
        charts.append({
            "chart_type": "scatter",
            "image_b64": scatter_chart(x_vals[:min_len], y_vals_s[:min_len],
                                       title=f"{numeric_cols[0]} vs {numeric_cols[1]}",
                                       xlabel=numeric_cols[0], ylabel=numeric_cols[1]),
            "title": f"{numeric_cols[0]} vs {numeric_cols[1]}",
        })

    return charts[:4]  # Return up to 4 charts

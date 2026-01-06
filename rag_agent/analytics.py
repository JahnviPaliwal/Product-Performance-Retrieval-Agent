import pandas as pd
import altair as alt

def analyze_data(df: pd.DataFrame, prompt: str):
    chart = None
    result = ""

    if "summary" in prompt.lower():
        result = df.describe().to_string()

    if "highest" in prompt.lower():
        col = df.select_dtypes(include="number").columns[0]
        row = df.loc[df[col].idxmax()]
        result = f"Highest {col}:\n{row}"

    if "plot" in prompt.lower() or "chart" in prompt.lower():
        numeric_cols = df.select_dtypes(include="number").columns
        if len(numeric_cols) >= 1:
            x = df.columns[0]
            y = numeric_cols[0]

            chart = alt.Chart(df).mark_line().encode(
                x=x,
                y=y
            )

            result = f"Generated chart for {y} vs {x}"

    return result, chart

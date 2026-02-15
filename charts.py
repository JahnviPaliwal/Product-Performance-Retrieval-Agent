import streamlit as st
import pandas as pd

def render_chart(insight_type, df):
    numeric = df.select_dtypes(include="number")
    categorical = df.select_dtypes(include="object")

    if insight_type == "distribution" and not numeric.empty:
        st.subheader("Distribution Overview")
        st.bar_chart(numeric)

    elif insight_type == "categorical_patterns" and not categorical.empty:
        col = categorical.columns[0]
        st.subheader(f"Top Categories: {col}")
        st.bar_chart(df[col].value_counts().head(10))

    elif insight_type == "relationships" and not numeric.empty:
        st.subheader("Correlation Heatmap")
        st.dataframe(numeric.corr().style.background_gradient(cmap="coolwarm"))

    elif insight_type == "missing_data":
        st.subheader("Missing Values")
        st.bar_chart(df.isnull().sum())

    elif insight_type == "outliers":
        st.subheader("Outlier Distribution")
        st.bar_chart(numeric)

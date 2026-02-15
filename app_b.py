import streamlit as st
import pandas as pd
from profiler import profile_dataframe
from llm import recommend_insights
from router import run_insight
from charts import render_chart
from quality import compute_data_quality

st.set_page_config(page_title="AI Data Agent", layout="wide")
st.title("AI Agent for Excel & CSV Analysis")


api_key = st.text_input(
    "Groq API Key",
    type="password"
)

uploaded_file = st.file_uploader(
    "Upload dataset (Excel or CSV)",
    type=["xlsx", "xls", "csv"]
)

if uploaded_file and api_key:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    profile = profile_dataframe(df)

    
    quality_score = compute_data_quality(df)
    st.metric("Data Quality Score", f"{quality_score} / 100")

    if "insights" not in st.session_state:
        with st.spinner("AI agent is thinking..."):
            st.session_state.insights = recommend_insights(profile, api_key)

    st.subheader(" Suggested Insights")

    for idx, insight in enumerate(st.session_state.insights):
        with st.expander(f"{idx+1}. {insight['title']}"):
            st.write(insight["description"])

            if st.button("Run Analysis", key=f"run_{idx}"):
                result = run_insight(insight["insight_type"], df)

                st.subheader("Result")
                st.write(result)

                render_chart(insight["insight_type"], df)

elif uploaded_file and not api_key:
    st.warning("Please enter your Groq API key to continue.")

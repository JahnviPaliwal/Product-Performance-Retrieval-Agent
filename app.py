"""app.py - Main Streamlit user interface for the LLM-guided data analytics agent.

Run with:
    streamlit run app.py
"""

import os
import sys
import pandas as pd
import streamlit as st

# Ensure src is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from analytics_agent.profiler import profile_dataframe
from analytics_agent.quality import QualityWeights, compute_quality_report
from analytics_agent.retrieval import filter_profile_for_query
from analytics_agent.llm import recommend_insights, answer_followup
from analytics_agent.router import run_insight
from analytics_agent.charts import generate_chart
from analytics_agent.report import generate_pdf_report, REPORTLAB_AVAILABLE

st.set_page_config(
    page_title="AI Data Analytics Agent",
    page_icon="📊",
    layout="wide",
)

# ── Sidebar: Configuration ───────────────────────────────────────────────────
st.sidebar.title("⚙️ Agent Settings")

env_api_key = os.environ.get("GROQ_API_KEY", "")
api_key = st.sidebar.text_input(
    "Groq API Key",
    value=env_api_key,
    type="password",
    help="Provided via GROQ_API_KEY environment variable or enter here.",
)

st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Retrieval Layer")
enable_retrieval = st.sidebar.checkbox(
    "Enable Vector Column Retrieval",
    value=True,
    help="Uses SentenceTransformers + FAISS to retrieve top-k semantically relevant columns for wide datasets.",
)
top_k_columns = st.sidebar.slider("Top-K Columns to Retrieve", min_value=4, max_value=20, value=8)

st.sidebar.markdown("---")
with st.sidebar.expander("⚖️ Data Quality Weights", expanded=False):
    st.caption("Adjust relative penalties (formula normalizes weights to sum to 1.0).")
    w_missing = st.slider("Missing Values Weight", 0.0, 1.0, 0.4, 0.05)
    w_duplicate = st.slider("Duplicates Weight", 0.0, 1.0, 0.3, 0.05)
    w_outlier = st.slider("Outliers Weight", 0.0, 1.0, 0.3, 0.05)
    quality_weights = QualityWeights(
        missing_weight=w_missing,
        duplicate_weight=w_duplicate,
        outlier_weight=w_outlier,
    )

# ── Main Header ─────────────────────────────────────────────────────────────
st.title("📊 LLM-Guided Data Analytics Agent")
st.markdown(
    "Upload a **CSV** or **Excel** dataset. The agent profiles data, computes an explainable quality score, "
    "uses Groq LLaMA 3.1 to plan insights, and deterministically executes Python analysis."
)

uploaded_file = st.file_uploader(
    "Upload dataset (Excel or CSV)",
    type=["xlsx", "xls", "csv"],
)

# ── Session State Management (Fix Stale Session Bug) ────────────────────────
if "current_file_id" not in st.session_state:
    st.session_state.current_file_id = None
    st.session_state.insights = []
    st.session_state.executed_results = {}
    st.session_state.qa_history = []

if uploaded_file is not None:
    file_id = f"{uploaded_file.name}_{uploaded_file.size}"
    # Invalidate stale cache if a new file is uploaded
    if st.session_state.current_file_id != file_id:
        st.session_state.current_file_id = file_id
        st.session_state.insights = []
        st.session_state.executed_results = {}
        st.session_state.qa_history = []

    # Load dataset
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Failed to load dataset: {e}")
        st.stop()

    # Profile & Quality
    raw_profile = profile_dataframe(df)
    quality_report = compute_quality_report(df, quality_weights)

    # Top Metrics Bar
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Rows", f"{len(df):,}")
    col2.metric("Columns", f"{len(df.columns):,}")
    col3.metric("Data Quality Score", f"{quality_report.score} / 100")
    col4.metric("Memory", f"{raw_profile.get('memory_usage_kb', 0):.1f} KB")

    # Quality breakdown expander
    with st.expander("📋 View Data Quality Breakdown"):
        st.write(f"- **Missing Cells Ratio:** {quality_report.missing_ratio:.2%} (Penalty: -{quality_report.penalties['missing_penalty']} pts)")
        st.write(f"- **Duplicate Rows Ratio:** {quality_report.duplicate_ratio:.2%} (Penalty: -{quality_report.penalties['duplicate_penalty']} pts)")
        st.write(f"- **IQR Outlier Ratio:** {quality_report.outlier_ratio:.2%} (Penalty: -{quality_report.penalties['outlier_penalty']} pts)")
        st.caption(f"Active Weights: Missing={quality_report.weights.missing_weight}, Duplicate={quality_report.weights.duplicate_weight}, Outlier={quality_report.weights.outlier_weight}")

    # Column Retrieval for Wide Datasets
    if enable_retrieval and len(df.columns) > top_k_columns:
        effective_profile = filter_profile_for_query(
            raw_profile,
            query="Analyze product and business performance, sales, distributions, and trends",
            top_k=top_k_columns,
            enable_retrieval=True,
        )
        st.info(
            f"🔍 **Vector Retrieval Active:** Dataset has {len(df.columns)} columns. "
            f"Retrieved top {len(effective_profile['columns'])} most relevant columns via FAISS for LLM planning."
        )
    else:
        effective_profile = raw_profile

    # Plan Insights with Groq LLM
    if not st.session_state.insights:
        if not api_key:
            st.warning("⚠️ Enter your Groq API key in the sidebar to generate AI insight recommendations.")
        else:
            with st.spinner("AI agent is evaluating dataset profile and planning insights..."):
                plan = recommend_insights(effective_profile, api_key=api_key)
                st.session_state.insights = [ins.model_dump() for ins in plan.insights]
                if plan.is_fallback and plan.warning_message:
                    st.warning(f"⚠️ {plan.warning_message}")

    # Render Insights
    if st.session_state.insights:
        st.subheader("💡 Recommended Analytical Insights")

        for idx, insight in enumerate(st.session_state.insights):
            itype = insight.get("insight_type", "")
            title = insight.get("title", f"Insight {idx+1}")
            desc = insight.get("description", "")

            with st.expander(f"{idx+1}. {title} ({itype})", expanded=(idx < 2)):
                st.write(desc)

                if st.button(f"▶️ Run Analysis: {title}", key=f"run_btn_{idx}"):
                    try:
                        res = run_insight(itype, df)
                        st.session_state.executed_results[itype] = res
                    except Exception as err:
                        st.error(f"Analysis error: {err}")

                # Display executed results if present
                if itype in st.session_state.executed_results:
                    res = st.session_state.executed_results[itype]
                    st.markdown("#### Execution Result")
                    if isinstance(res, pd.DataFrame):
                        st.dataframe(res, use_container_width=True)
                    elif isinstance(res, dict):
                        st.json(res)
                    else:
                        st.write(res)

                    # Render Matplotlib Chart
                    fig = generate_chart(itype, df)
                    if fig:
                        st.pyplot(fig)

                    # Follow-Up Q&A
                    st.markdown("##### 💬 Follow-Up Question")
                    q_key = f"q_input_{idx}_{itype}"
                    user_q = st.text_input(
                        "Ask a question about this specific insight:",
                        key=q_key,
                        placeholder="e.g. Which category has the highest frequency?",
                    )
                    if st.button("Submit Question", key=f"q_btn_{idx}_{itype}") and user_q:
                        if not api_key:
                            st.error("Please enter a Groq API Key to ask follow-up questions.")
                        else:
                            with st.spinner("Analyzing insight results..."):
                                ans = answer_followup(
                                    profile=raw_profile,
                                    insight_title=title,
                                    insight_result=res,
                                    user_question=user_q,
                                    api_key=api_key,
                                )
                                st.markdown(f"**Answer:** {ans.answer}")
                                st.session_state.qa_history.append({
                                    "question": f"[{title}] {user_q}",
                                    "answer": ans.answer,
                                })

        # PDF Export Section
        st.markdown("---")
        st.subheader("📄 Export Report")
        if not REPORTLAB_AVAILABLE:
            st.warning(
                "⚠️ ReportLab is not installed in the active environment. "
                "To enable PDF generation, run: `pip install reportlab` or launch Streamlit using `python -m streamlit run app.py`."
            )
        else:
            if st.button("Generate Comprehensive PDF Report"):
                with st.spinner("Compiling PDF report with ReportLab..."):
                    pdf_bytes = generate_pdf_report(
                        dataset_name=uploaded_file.name,
                        df=df,
                        quality_report=quality_report,
                        insights=st.session_state.insights,
                        executed_results=st.session_state.executed_results,
                        qa_history=st.session_state.qa_history,
                    )
                    st.download_button(
                        label="⬇️ Download PDF Report",
                        data=pdf_bytes,
                        file_name=f"{uploaded_file.name}_analytics_report.pdf",
                        mime="application/pdf",
                    )
                    st.success("✅ PDF Report successfully generated!")

else:
    st.info("👆 Please upload a CSV or Excel file above to begin.")

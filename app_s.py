# import streamlit as st
# import pandas as pd
# from traditional.prompt_parser import parse_prompt_local
# from traditional.prompt_handler import process_plan
#
# st.set_page_config(page_title="Agentic AI Analytics", layout="wide")
# st.title("Agentic AI Analytics Demo")
#
# uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
# user_prompt = st.text_area("Enter your analytics request")
#
# if uploaded_file and user_prompt:
#
#     df = pd.read_csv(uploaded_file)
#     from traditional.column_mapper import normalize_columns
#
#     column_map = normalize_columns(df)
#     st.subheader("Detected Column Mapping")
#     st.json(column_map)
#
#     st.subheader("Dataset Preview")
#     st.dataframe(df.head())
#
#     if st.button("Analyze"):
#         with st.spinner("Running analytics agent..."):
#
#             plan = parse_prompt_local(user_prompt)
#
#             if plan is None:
#                 st.error("Could not understand the prompt. Try rephrasing.")
#             else:
#                 st.subheader("Execution Plan")
#                 st.json(plan)
#
#                 results = process_plan(plan, df)
#                 print("1")
#                 st.subheader("Results")
#                 st.json(results)
#
#                 if "graphs" in results:
#                     for fig in results["graphs"].values():
#                         st.plotly_chart(fig)




import streamlit as st
import pandas as pd

# ------------------ PAGE CONFIG ------------------
st.set_page_config(page_title="Agentic AI Analytics Platform", layout="wide")
st.title("📊 Agentic AI Analytics Platform")

# ------------------ SIDEBAR ------------------
st.sidebar.title("⚙️ Analytics Mode")

mode = st.sidebar.radio(
    "Choose Analysis Mode",
    [
        "Traditional Analytics (No LLM)",
        "RAG + OpenAI Analytics"
    ]
)

st.sidebar.markdown("---")

# ------------------ FILE UPLOAD ------------------
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
user_prompt = st.text_area("Enter your analytics request")

if not uploaded_file or not user_prompt:
    st.warning("Please upload a CSV and enter a prompt.")
    st.stop()

df = pd.read_csv(uploaded_file)

st.subheader("📄 Dataset Preview")
st.dataframe(df.head())

# =================================================
# ============ MODE 1: TRADITIONAL =================
# =================================================
if mode == "Traditional Analytics (No LLM)":

    st.info("🔍 Running deterministic, planner-based analytics (no OpenAI)")

    from traditional.column_mapper import normalize_columns
    from traditional.prompt_parser import parse_prompt_local
    from traditional.prompt_handler import process_plan

    column_map = normalize_columns(df)
    st.subheader("Detected Column Mapping")
    st.json(column_map)

    if st.button("Analyze (Traditional)"):

        with st.spinner("Running traditional analytics agent..."):

            plan = parse_prompt_local(user_prompt)

            if plan is None:
                st.error("Could not understand the prompt. Try rephrasing.")
                st.stop()

            st.subheader("🧠 Execution Plan")
            st.json(plan)

            results = process_plan(plan, df)

            st.subheader("📊 Results")
            st.json(results)

            if "graphs" in results:
                st.subheader("📈 Visualizations")
                for fig in results["graphs"].values():
                    st.plotly_chart(fig, use_container_width=True)

# =================================================
# ============ MODE 2: RAG + OPENAI =================
# =================================================
elif mode == "RAG + OpenAI Analytics":

    st.info(
        "🤖 Running AI-powered analytics using RAG + OpenAI\n\n"
        "🔐 Your API key is **never stored or logged**."
    )

    openai_key = st.text_input(
        "Enter your OpenAI API Key",
        type="password"
    )

    if not openai_key:
        st.warning("Please enter your OpenAI API key.")
        st.stop()

    if st.button("Analyze (RAG + LLM)"):

        with st.spinner("Running RAG-based AI agent..."):

            from rag_agent.analytics import compute_metrics
            from rag_agent.forecasting import run_forecast
            from rag_agent.rag import generate_rag_answer

            # --- Structured Analytics ---
            metrics = compute_metrics(df)

            # --- Forecasting ---
            forecast = run_forecast(df)

            # --- RAG + LLM ---
            ai_response = generate_rag_answer(
                df=df,
                prompt=user_prompt,
                api_key=openai_key,
                metrics=metrics,
                forecast=forecast
            )

            st.subheader("🤖 AI Response")
            st.write(ai_response)

            st.subheader("📊 Key Metrics")
            st.json(metrics)

            if forecast:
                st.subheader("📈 Forecast")
                st.plotly_chart(forecast, use_container_width=True)

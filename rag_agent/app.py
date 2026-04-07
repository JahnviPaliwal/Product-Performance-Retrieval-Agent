"""
app.py – Streamlit frontend for the LLM-Powered Retrieval & Analytics Agent
Run with:  streamlit run app.py
"""

import os
import sqlite3
import streamlit as st
from retrieval_agent import retrieve, build_vector_index, DB_PATH, DOCS_PATH
from reasoning_agent  import reason_and_answer

# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RAG Analytics Agent",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 LLM-Powered Retrieval & Analytics Agent")
st.markdown(
    "Ask questions in plain English. The agent retrieves data from both a "
    "**SQL database** and **text documents**, then reasons over them to give "
    "you a grounded answer."
)

# ── API key check ───────────────────────────────────────────────────────────
if not os.environ.get("GROQ_API_KEY"):
    st.error("⚠️  Please set the `GROQ_API_KEY` environment variable before running.")
    st.stop()

# ── One-time setup: build vector index ──────────────────────────────────────
@st.cache_resource
def setup():
    """Build the vector index once and cache it."""
    if os.path.exists(DOCS_PATH):
        build_vector_index()
        return True
    return False

ready = setup()
if not ready:
    st.error("docs.txt not found in data/ folder.")
    st.stop()

# ── Sidebar: peek at the database ───────────────────────────────────────────
st.sidebar.header("🗄️ Database Preview")
if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("SELECT * FROM employees LIMIT 5").fetchall()
        import pandas as pd
        st.sidebar.dataframe(pd.DataFrame([dict(r) for r in rows]),
                             use_container_width=True)
        st.sidebar.caption("employees table (first 5 rows)")
    except Exception:
        st.sidebar.info("Could not preview table.")
    conn.close()

# ── Sample questions ─────────────────────────────────────────────────────────
st.sidebar.header("💡 Sample Questions")
samples = [
    "Who are the top 3 highest-paid employees?",
    "How many employees work in the Engineering department?",
    "What is the average salary by department?",
    "Tell me about the company's remote work policy.",
    "Which employees joined after 2022?",
]
for q in samples:
    if st.sidebar.button(q, key=q):
        st.session_state["query"] = q

# ── Query input ──────────────────────────────────────────────────────────────
query = st.text_input(
    "Enter your question:",
    value=st.session_state.get("query", ""),
    placeholder="e.g. Who are the highest-paid engineers?",
)

if st.button("🔍 Ask Agent", type="primary") and query:
    # Step 1: Retrieve
    with st.spinner("Retrieval agent fetching data…"):
        retrieval_output = retrieve(query)

    # Step 2: Reason
    with st.spinner("Reasoning agent synthesising answer…"):
        result = reason_and_answer(query, retrieval_output)

    # ── Display results ────────────────────────────────────────────────────
    st.success("✅ Answer ready!")

    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("💬 Final Answer")
        st.markdown(result["answer"])

        st.subheader("🧠 Reasoning Trace")
        with st.expander("Show reasoning trace", expanded=True):
            st.write(result["reasoning_trace"])

    with col2:
        st.subheader("🔧 Retrieval Details")

        with st.expander("📊 Generated SQL"):
            st.code(retrieval_output["generated_sql"], language="sql")

        with st.expander("📋 SQL Results"):
            if retrieval_output["sql_results"]:
                import pandas as pd
                st.dataframe(pd.DataFrame(retrieval_output["sql_results"]),
                             use_container_width=True)
            else:
                st.write("No SQL rows returned.")

        with st.expander("📄 Retrieved Text Chunks"):
            for i, chunk in enumerate(retrieval_output["text_chunks"], 1):
                st.markdown(f"**Chunk {i}:** {chunk}")
                st.divider()

"""
services/agent.py
Pure-Groq agent (no langchain, no langgraph) — fully compatible with Python 3.14.
Implements the same routing logic: classify → retrieve/analytics/general → followups.
"""
from __future__ import annotations
import json
from groq import Groq

from utils.session_store import get_all_documents
from document_processors.csv_processor import load_dataframe

GROQ_MODEL = "llama-3.3-70b-versatile"


def _chat(api_key: str, system: str, human: str, temperature: float = 0.2) -> str:
    client = Groq(api_key=api_key)
    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": human},
        ],
    )
    return resp.choices[0].message.content.strip()


# ── Step 1: Classify ─────────────────────────────────────────────────────────

def _classify(query: str, api_key: str) -> str:
    """Returns 'rag' | 'analytics' | 'general'"""
    docs = get_all_documents()
    if not docs:
        return "general"

    doc_summaries = "\n".join(
        f"- {d['filename']} ({d['file_type']}): {d['text'][:250]}…"
        for d in docs.values()
    )

    answer = _chat(
        api_key,
        system=(
            "You are a routing agent. Respond with exactly one word.\n"
            "Modes:\n"
            "  rag       – query is about content IN the documents\n"
            "  analytics – query needs statistics/charts/trends from a CSV dataset\n"
            "  general   – query is unrelated to the uploaded documents\n"
            "Output ONLY one of: rag | analytics | general"
        ),
        human=f"Uploaded documents:\n{doc_summaries}\n\nUser query: \"{query}\"",
        temperature=0,
    )
    word = answer.strip().lower().split()[0]
    return word if word in ("rag", "analytics", "general") else "rag"


# ── Step 2a: RAG ─────────────────────────────────────────────────────────────

def _rag_answer(query: str, api_key: str) -> tuple[str, list[str]]:
    docs = get_all_documents()
    all_chunks, sources = [], []
    for doc in docs.values():
        vs = doc.get("vector_store")
        if vs:
            for chunk in vs.retrieve(query, top_k=4):
                all_chunks.append(chunk)
                sources.append(doc["filename"])

    context = "\n\n---\n\n".join(all_chunks[:8]) if all_chunks else "No relevant content found."
    unique_sources = list(dict.fromkeys(sources))

    answer = _chat(
        api_key,
        system=(
            "You are a business intelligence assistant. "
            "Answer using ONLY the provided document context. "
            "Be specific, cite relevant figures/facts, and structure your response clearly. "
            "If the context is insufficient, say so honestly."
        ),
        human=f"Document context:\n{context}\n\nQuestion: {query}",
    )
    return answer, unique_sources


# ── Step 2b: Analytics ───────────────────────────────────────────────────────

def _analytics_answer(query: str, api_key: str) -> tuple[str, list[dict]]:
    from analytics.analysis_engine import (
        distribution, missing_data, categorical_patterns,
        relationships, outliers, profile_dataframe, trends,
    )
    from analytics.chart_generator import auto_chart

    docs = get_all_documents()
    csv_docs = [d for d in docs.values() if d["file_type"] == "csv"]
    if not csv_docs:
        # Fall back to RAG
        answer, sources = _rag_answer(query, api_key)
        return answer, []

    doc = csv_docs[0]
    df = load_dataframe(doc["file_path"])
    q = query.lower()

    results: dict = {}
    if any(w in q for w in ["missing", "null", "empty", "nan"]):
        results["Missing Data"] = missing_data(df)
    if any(w in q for w in ["outlier", "anomaly", "unusual"]):
        results["Outliers"] = outliers(df)
    if any(w in q for w in ["correlat", "relationship", "between"]):
        results["Correlations"] = relationships(df)
    if any(w in q for w in ["category", "categor", "group", "type", "segment"]):
        results["Categorical Patterns"] = categorical_patterns(df)
    if any(w in q for w in ["trend", "over time", "time series", "monthly", "yearly"]):
        results["Trends"] = trends(df)
    if any(w in q for w in ["distribut", "histogram", "spread", "range"]):
        results["Distribution"] = distribution(df)
    if not results:
        results["Profile"] = profile_dataframe(df)
        results["Distribution"] = distribution(df)

    charts = auto_chart(df, query_hint=query)

    analytics_str = json.dumps(
        {k: str(v)[:1500] for k, v in results.items()},
        indent=2, default=str,
    )

    answer = _chat(
        api_key,
        system=(
            "You are a senior data analyst and business intelligence expert. "
            "Interpret the analytics results and provide clear, actionable business insights. "
            "Highlight key findings, patterns, risks, and opportunities. "
            "Use bullet points and structure your response."
        ),
        human=(
            f"Analytics results for dataset \"{doc['filename']}\":\n"
            f"{analytics_str}\n\n"
            f"User question: {query}\n\n"
            "Provide clear, actionable insights."
        ),
    )
    return answer, charts


# ── Step 2c: General ─────────────────────────────────────────────────────────

def _general_answer(query: str, api_key: str) -> str:
    return _chat(
        api_key,
        system=(
            "You are a knowledgeable business intelligence assistant. "
            "Answer the user's question using your general knowledge. "
            "Be accurate, clear, and comprehensive."
        ),
        human=query,
    )


# ── Step 3: Follow-ups ───────────────────────────────────────────────────────

def _followups(query: str, answer: str, api_key: str) -> list[str]:
    raw = _chat(
        api_key,
        system="You generate follow-up questions. Respond ONLY with a valid JSON array of 4 strings.",
        human=(
            f"Q: {query}\n"
            f"A (summary): {answer[:400]}\n\n"
            "Generate 4 insightful follow-up questions a business analyst would ask next.\n"
            'Return ONLY a JSON array: ["Q1?", "Q2?", "Q3?", "Q4?"]'
        ),
        temperature=0.3,
    )
    try:
        start, end = raw.find("["), raw.rfind("]") + 1
        if start >= 0 and end > start:
            return json.loads(raw[start:end])
    except Exception:
        pass
    return [
        "What are the key trends in this data?",
        "What risks should be prioritized?",
        "Which metric needs the most attention?",
        "What strategic actions do you recommend?",
    ]


# ── Public entry point ────────────────────────────────────────────────────────

def run_agent(query: str, api_key: str) -> dict:
    mode = _classify(query, api_key)
    sources: list[str] = []
    charts:  list[dict] = []
    is_irrelevant = False

    if mode == "rag":
        answer, sources = _rag_answer(query, api_key)
        # If RAG couldn't find anything, treat as general
        if not sources:
            answer = _general_answer(query, api_key)
            is_irrelevant = True
            mode = "general"
    elif mode == "analytics":
        answer, charts = _analytics_answer(query, api_key)
    else:
        answer = _general_answer(query, api_key)
        is_irrelevant = True

    followups = _followups(query, answer, api_key)

    return {
        "answer":       answer,
        "mode":         mode,
        "is_irrelevant": is_irrelevant,
        "sources":      sources,
        "charts":       charts,
        "followups":    followups,
    }

"""
retrieval_agent.py
Handles retrieval from:
  - An SQLite database (structured data)
  - A FAISS vector store built from text documents (unstructured data)
"""

import os
import sqlite3
import pickle
import numpy as np
from groq import Groq

# ── Groq client ────────────────────────────────────────────────────────────
client = Groq()
MODEL  = "llama-3.1-8b-instant"

# ── Paths ──────────────────────────────────────────────────────────────────
DATA_DIR   = os.path.join(os.path.dirname(__file__), "data")
DB_PATH    = os.path.join(DATA_DIR, "company.db")
DOCS_PATH  = os.path.join(DATA_DIR, "docs.txt")
INDEX_PATH = os.path.join(DATA_DIR, "faiss_index.pkl")


# ─────────────────────────────────────────────────────────────────────────────
# SQL retrieval helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_sql_schema() -> str:
    """Returns the DDL / column names so the LLM can write correct SQL."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    schema_parts = []
    for (table,) in tables:
        cursor.execute(f"PRAGMA table_info({table});")
        cols = cursor.fetchall()
        col_names = ", ".join(c[1] for c in cols)
        schema_parts.append(f"Table `{table}` columns: {col_names}")
    conn.close()
    return "\n".join(schema_parts)


def run_sql_query(query: str) -> list[dict]:
    """
    Runs a SELECT query against the SQLite database.
    Returns a list of row dicts.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        return [{"error": str(e)}]


def generate_sql(user_query: str, schema: str) -> str:
    """
    Asks the LLM to translate a natural-language question into SQL.
    """
    prompt = f"""You are a SQL expert.
Given this database schema:
{schema}

Write a single valid SQLite SELECT statement to answer this question.
Return ONLY the SQL – no explanation, no markdown.

Question: {user_query}
"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    sql = response.choices[0].message.content.strip()
    # Strip markdown code fences if present
    sql = sql.replace("```sql", "").replace("```", "").strip()
    return sql


# ─────────────────────────────────────────────────────────────────────────────
# Vector / text retrieval helpers
# ─────────────────────────────────────────────────────────────────────────────

def embed_text(text: str) -> np.ndarray:
    """
    Creates a simple TF-IDF-style bag-of-words embedding.
    We keep it dependency-light: no external embedding model needed.
    The vector is L2-normalised so cosine similarity = dot product.
    """
    words = text.lower().split()
    # Build a hash-based feature vector of fixed size
    vec = np.zeros(512, dtype=np.float32)
    for word in words:
        idx = hash(word) % 512
        vec[idx] += 1.0
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec /= norm
    return vec


def build_vector_index(docs_path: str = DOCS_PATH,
                       index_path: str = INDEX_PATH) -> list[str]:
    """
    Reads docs.txt (one paragraph per block separated by blank lines),
    embeds each chunk, and saves the index as a pickle file.
    Returns the list of text chunks.
    """
    with open(docs_path, "r") as f:
        raw = f.read()

    # Split on double newlines to get paragraphs / chunks
    chunks = [c.strip() for c in raw.split("\n\n") if c.strip()]

    vectors = np.array([embed_text(c) for c in chunks], dtype=np.float32)

    # Save index + chunks together
    with open(index_path, "wb") as f:
        pickle.dump({"chunks": chunks, "vectors": vectors}, f)

    return chunks


def load_vector_index(index_path: str = INDEX_PATH):
    """Loads the pickled index. Builds it first if missing."""
    if not os.path.exists(index_path):
        build_vector_index()
    with open(index_path, "rb") as f:
        return pickle.load(f)


def vector_search(query: str, top_k: int = 3) -> list[str]:
    """
    Retrieves the top-k text chunks most relevant to the query
    using cosine similarity on bag-of-words embeddings.
    """
    index = load_vector_index()
    chunks   = index["chunks"]
    vectors  = index["vectors"]

    q_vec    = embed_text(query)
    scores   = vectors @ q_vec          # cosine similarities
    top_idxs = np.argsort(scores)[::-1][:top_k]
    return [chunks[i] for i in top_idxs]


# ─────────────────────────────────────────────────────────────────────────────
# Main retrieval function called by the orchestrator
# ─────────────────────────────────────────────────────────────────────────────

def retrieve(user_query: str) -> dict:
    """
    Runs both SQL retrieval and vector search for the given query.
    Returns a dict with sql_results and text_chunks.
    """
    schema       = get_sql_schema()
    sql_query    = generate_sql(user_query, schema)
    sql_results  = run_sql_query(sql_query)
    text_chunks  = vector_search(user_query, top_k=3)

    return {
        "generated_sql": sql_query,
        "sql_results":   sql_results,
        "text_chunks":   text_chunks,
    }

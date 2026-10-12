# Audit Report: Product Performance Retrieval Agent Codebase

**Date:** 2026-10-12  
**Auditor:** Antigravity Engineering Agent  
**Subject:** Full Audit of Repository Codebase Prior to Refactoring and Upgrades

---

## 1. Executive Summary

This audit reviews every file in the repository, compares existing code against the claims made in `README.md`, identifies dead and duplicate code, and verifies whether features such as ReportLab PDF generation or retrieval/embedding logic actually exist.

**Key Findings:**
1. **Severe README vs. Implementation Discrepancies:** The README advertises interactive follow-up Q&A, session-aware caching, and retrieval capabilities. In reality, the follow-up Q&A UI is missing from the main frontend, the backend follow-up function has a fatal `NameError: name 'client' is not defined`, and the session state does not invalidate when a new dataset is uploaded.
2. **Missing Technologies:** Neither ReportLab nor any production-grade retrieval/embedding system (such as Sentence-Transformers or FAISS) existed in the primary analytics tool.
3. **Disjointed Toy Agent:** A secondary subdirectory `rag_agent/` contains a disconnected prototype for SQLite querying and a toy bag-of-words hash embedding over a dummy text file, entirely unintegrated with the CSV/Excel analytics pipeline.
4. **Duplicate & Unpinned Dependencies:** `requirements.txt` and `requirements_2.txt` are byte-for-byte identical, containing only 5 unpinned packages.
5. **Architectural Gaps:** The project lacked package structure, type hints, Pydantic validation, error handling/retry logic, configurable data quality weights, and test coverage.

---

## 2. File-by-File Breakdown

### Root Directory Files

| File | Purpose & Behavior | Deficiencies & Issues |
| :--- | :--- | :--- |
| `app_b.py` | Main Streamlit user interface (55 lines). Handles file upload (CSV/Excel), calls profiler, computes quality score, triggers LLM insight recommendation, and runs analysis on button click. | • Misnamed (README instructs `streamlit run app.py`).<br>• Only accepts API key via UI text box; ignores `GROQ_API_KEY` environment variable.<br>• Stale session state bug: `st.session_state.insights` is checked without checking if `uploaded_file` changed.<br>• Does not include any Follow-up Q&A UI.<br>• No PDF export button.<br>• No error boundary around LLM or analysis execution. |
| `profiler.py` | Profiles a pandas DataFrame (17 lines). Returns a dictionary with `num_rows`, `num_columns`, and list of column metadata (`name`, `dtype`, `nulls`, `unique`). | • Lacks type annotations and docstrings.<br>• Does not extract column sample values or summary statistics needed for semantic retrieval or wide-table selection. |
| `quality.py` | Calculates a composite data quality score from 0 to 100 based on missing values, duplicates, and IQR outliers (31 lines). | • Weights (0.4, 0.3, 0.3) are hardcoded with no configuration options.<br>• Formula is undocumented in README.<br>• Lacks type annotations and docstrings. |
| `analysis_functions.py` | Contains 6 deterministic analytical functions: `distribution`, `missing_data`, `categorical_patterns`, `relationships`, `outliers`, `schema` (32 lines). | • No docstrings or type hints.<br>• Fragile under edge cases: raises errors or returns empty/unhandled shapes when DataFrames have no numeric columns, are empty, or contain all-null values. |
| `charts.py` | Renders Streamlit native charts (`st.bar_chart`, `st.dataframe`) for insight types (28 lines). | • Coupled directly to Streamlit rendering commands; does not generate standalone `Figure` objects that can be saved as images or embedded in PDF reports.<br>• In `categorical_patterns`, arbitrarily plots only the very first categorical column.<br>• In `outliers`, plots raw numeric data instead of an outlier visualization (e.g. boxplot). |
| `router.py` | Maps 6 string keys to functions in `analysis_functions.py` via `INSIGHT_ROUTER` dictionary (14 lines). | • No validation against a whitelist.<br>• Raises an unhandled `KeyError` if the LLM produces an unrecognized insight name.<br>• No type hints or docstrings. |
| `llm.py` | Interacts with Groq API using `llama-3.1-8b-instant` (118 lines). Contains `recommend_insights` and `answer_followup`. | • Fragile regex extraction `r"\[.*\]"` fails on complex markdown or surrounding explanations.<br>• No Pydantic schema validation.<br>• No exponential backoff or retry logic for Groq rate limits or connection errors.<br>• **Critical Bug in `answer_followup`:** Calls `client.chat.completions.create(...)`, but `client` is only instantiated inside `recommend_insights` locally. Calling `answer_followup` immediately crashes with `NameError: name 'client' is not defined`.<br>• `answer_followup` is never imported or called anywhere in the UI. |
| `requirements.txt` | Unpinned package list (6 lines): `streamlit`, `pandas`, `openpyxl`, `groq`, `numpy`. | • No pinned versions.<br>• Missing essential dependencies like `pydantic`, `reportlab`, `matplotlib`, `pytest`, `faiss-cpu`, `sentence-transformers`. |
| `requirements_2.txt` | Unpinned package list (6 lines). | • Exact byte-for-byte duplicate of `requirements.txt`. |
| `README.md` | Project documentation (115 lines). | • Inaccurate and out-of-sync with code (see Section 3). |

---

### Subdirectory: `rag_agent/`

The directory `rag_agent/` contains an entirely separate, disconnected experiment based on SQLite and text files:

| File | Purpose & Behavior | Audit Assessment |
| :--- | :--- | :--- |
| `rag_agent/app.py` | Separate Streamlit app for asking questions over `company.db` and `docs.txt`. | Completely unintegrated with the primary CSV/Excel analytics tool. Dead code in relation to the main agent. |
| `rag_agent/retrieval_agent.py` | Uses SQLite introspection to generate SQL via Groq, and embeds paragraphs from `docs.txt`. | Uses a toy bag-of-words hash mod 512 embedding (`embed_text(c)`). It does **not** use `sentence-transformers` and does **not** use `FAISS` (it saves a pickle file containing a numpy array and computes a dot product). |
| `rag_agent/reasoning_agent.py` | Calls Groq LLM to synthesize answers combining SQL results and text chunks. | Disconnected from tabular data analytics. |
| `rag_agent/setup_db.py` | Creates and seeds `company.db` with sample departments and employees. | Unrelated to the main agent. |
| `rag_agent/requirements.txt` | Lists `streamlit`, `groq`, `numpy`, `pandas`. | Redundant requirement file. |
| `rag_agent/data/*` | Contains `company.db` and `docs.txt`. | Sample data for the disconnected toy script. |

**Verdict on `rag_agent/`:** Dead code. It must be audited (done here) and removed to eliminate confusion and repository bloat.

---

## 3. README Claims vs. Code Reality

| Claim in README | Reality in Code | Status |
| :--- | :--- | :--- |
| **"Interactive follow-up Q&A on results"** | `app_b.py` contains zero input widgets or logic for follow-up Q&A. `llm.py` defines `answer_followup`, but the function throws `NameError: name 'client' is not defined` because `client` is unassigned. | ❌ False claim / Broken code |
| **"Session-aware: prevents stale outputs if a new file is uploaded"** | `app_b.py` checks `if "insights" not in st.session_state:`. If a user uploads file A, receives insights, and then uploads file B, `insights` remains in `st.session_state`, showing file A's insights on file B! | ❌ False claim / Buggy state |
| **"Clone URL: `https://github.com/yourusername/ai_excel_agent.git`"** | Placeholder dummy URL. | ⚠️ Unfinished placeholder |
| **"streamlit run app.py"** | The file in the repository was named `app_b.py`. Running `streamlit run app.py` failed with `FileDoesNotExist`. | ❌ Broken command |
| **"Target Users: Recruiters & demo evaluators looking for AI-powered solutions for recruiters."** | Unprofessional boilerplate text targeted at recruiters rather than data practitioners. | ⚠️ Unnecessary copy |
| **"Product Performance Retrival Agent" (Title)** | Typo ("Retrival") in heading. No retrieval logic existed in the Excel/CSV agent. | ❌ Typo & Misleading |
| **Data Quality Score** | Claimed 0–100 score exists in code, but the exact formula and weightings were never explained in the README. | ⚠️ Incomplete documentation |

---

## 4. Verification of Specific Features

### A. Does ReportLab Exist?
- **Status:** **DOES NOT EXIST.**
- **Details:** Grepping for `reportlab` across all files yields 0 matches. No PDF generation code, classes, or exports existed in the codebase.

### B. Does Retrieval / Embedding Logic Exist for Datasets?
- **Status:** **DOES NOT EXIST.**
- **Details:**
  - The tabular analytics agent (`app_b.py`, `llm.py`, `profiler.py`) has no embedding or retrieval mechanism.
  - The `rag_agent/` subdirectory has an unrelated toy `embed_text` function using `hash(word) % 512` over text paragraphs, without sentence-transformers or FAISS.
  - No column-level retrieval for wide datasets existed anywhere in the repository.

---

## 5. Required Action Plan

1. **Delete Dead & Duplicate Files:**
   - Remove `requirements_2.txt`.
   - Remove the `rag_agent/` directory.
   - Rename/replace `app_b.py` with `app.py`.
2. **Package Architecture:**
   - Organize into `src/analytics_agent/`:
     - `profiler.py`: DataFrame metadata & sample extraction.
     - `quality.py`: Configurable quality score with weights.
     - `analysis.py`: Safe deterministic analytics.
     - `charts.py`: Headless Matplotlib figures for UI and PDF export.
     - `router.py`: Whitelisted insight dispatcher.
     - `retrieval.py`: Column retrieval with `sentence-transformers` & `faiss-cpu`.
     - `llm.py`: Pydantic schema validation, exponential backoff retries, robust Q&A.
     - `report.py`: Professional ReportLab PDF export.
     - `logging_config.py`: Structured LLM interaction logs without raw user data.
3. **Evaluation & Verification:**
   - Create `eval/` harness with 20+ test cases across 3 datasets (`results/eval.json`).
   - Create comprehensive unit test suite in `tests/` covering all modules with mocked LLM.
   - Set up GitHub Actions CI workflow (`ruff` + `pytest`).
   - Add `Dockerfile`, `docker-compose.yml`, `.gitignore`, `LICENSE`.
   - Rewrite `README.md` to accurately document the architecture, formula, and commands.

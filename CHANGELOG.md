# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-12

### Added
- **Modular Package Structure (`src/analytics_agent/`)**:
  - `profiler.py`: DataFrame metadata profiling, memory consumption, column types, and sample value extraction.
  - `quality.py`: Configurable data quality scoring (`QualityWeights`) with detailed penalty breakdown.
  - `analysis.py`: Safe, deterministic Python statistical functions (`distribution`, `missing_data`, `categorical_patterns`, `relationships`, `outliers`, `schema`).
  - `charts.py`: Headless Matplotlib chart generation exportable to PNG and PDF.
  - `router.py`: Strict whitelist verification and dispatch with query classification.
  - `retrieval.py`: Real vector retrieval layer using Sentence-Transformers (`all-MiniLM-L6-v2`) and FAISS (`faiss-cpu`) to prune wide tables for LLM context.
  - `llm.py`: Pydantic schema validation (`InsightPlan`, `InsightRecommendation`), exponential backoff retry via Tenacity, and deterministic fallback.
  - `report.py`: Comprehensive PDF report generation via ReportLab (executive overview, quality score, charts, tables, Q&A history).
  - `logging_config.py`: Structured privacy-preserving JSON logging for LLM calls (latency, token counts, model; zero raw user data).
- **Evaluation Harness (`eval/`)**:
  - 3 realistic sample datasets (`ecommerce_sales.csv`, `customer_churn.csv`, `employee_attrition.csv`).
  - 24 natural language test cases mapped to expected insight routes in `eval/test_cases.json` (marked with `needs_human_review: true`).
  - `eval/run_eval.py` measuring router accuracy, latency, and failure types, writing real measured output to `results/eval.json` and `results/eval_summary.md`.
- **Testing & Continuous Integration**:
  - 32 pytest unit tests covering all modules with mocked Groq client (`tests/`).
  - GitHub Actions CI workflow (`.github/workflows/ci.yml`) running `ruff check .` and `pytest`.
- **Packaging & Deployment**:
  - Containerization via `Dockerfile` and `docker-compose.yml`.
  - Pinned `requirements.txt`.
  - `.gitignore` and `LICENSE` (MIT).

### Changed
- Replaced misnamed `app_b.py` with top-level `app.py`.
- Upgraded Streamlit UI with sidebar settings for API key, retrieval toggle, quality weight sliders, and interactive follow-up Q&A widgets.
- Rewrote `README.md` with an accurate Mermaid architecture flowchart, exact mathematical quality formula, realistic feature list, evaluation guide, Docker instructions, and limitations section.

### Fixed
- **Stale Session Bug**: Fixed session state persistence where uploading a new dataset previously reused insights from the previous file.
- **Undefined Client Error**: Fixed fatal `NameError: name 'client' is not defined` in `answer_followup`.
- **Malformed JSON & Regex Failures**: Replaced fragile regex extraction with Pydantic validation, retry with backoff, and graceful fallback.
- **Console Encoding**: Resolved Windows `charmap` UnicodeEncodeError in evaluation printing.

### Removed
- Removed duplicate `requirements_2.txt`.
- Removed legacy and disconnected SQLite toy agent directory `rag_agent/`.
- Removed unprofessional "recruiters & demo evaluators" marketing text from documentation.

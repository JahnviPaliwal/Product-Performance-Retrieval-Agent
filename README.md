
# Product Performance Retrival Agent  




## Project Overview

This project is an AI-powered analytical agent that allows users to explore **Excel or CSV datasets** effortlessly. It combines **LLM reasoning** with **deterministic Python analysis** to provide:

* Automatic insight recommendations (6 per dataset)
* Data quality scoring (0–100)
* Auto-generated charts and visualizations
* Interactive follow-up Q&A on results

The system is **safe, token-efficient, explainable**, and ideal for non-technical users to explore data intelligently.

---

## Key Features

1. Upload Excel / CSV files.
2. Dynamic insight recommendations based on dataset metadata.
3. Deterministic analysis ensures reproducible results.
4. Automatic visualization for each insight.
5. Data quality scoring: missing data, outliers, duplicates.
6. Follow-up Q&A to interactively explore insights.
7. Secure API usage: users provide their own Groq API key.

---

## Architecture

**Workflow:**

1. User Interface (Streamlit) – upload file and API key.
2. Dataset Profiler – extracts metadata (columns, types, missing values, cardinality).
3. LLM Reasoning Layer (Groq) – recommends insights.
4. Insight Router – maps suggestions to deterministic Python functions.
5. Analysis Layer – executes analysis (distribution, outliers, correlations, missing data).
6. Visualization Layer – auto-generates charts.
7. Data Quality Layer – computes composite score.
---

## Tech Stack

| Layer                   | Technology                               |
| ----------------------- | ---------------------------------------- |
| Frontend/UI             | Streamlit                                |
| Data Loading & Analysis | Python, Pandas, NumPy                    |
| LLM Reasoning           | Groq API, LLaMA 3.1                      |
| Visualization           | Streamlit charts                         |
| Security                | User-provided API key, local computation |
| Version Control         | Git                                      |

---

## How It Works

1. Upload Excel or CSV file.
2. Enter your Groq API key in the frontend.
3. The system extracts metadata and sends it to the LLM.
4. LLM returns six insight recommendations.
5. Click a recommendation → system executes analysis locally.
6. Visualizations and metrics are displayed.
7. Ask follow-up questions to explore insights further.

---

## Highlights

* Safe AI usage: LLM guides decisions; computations are local.
* Adaptive insights: recommendations adjust to each dataset.
* Session-aware: prevents stale outputs if a new file is uploaded.
* Demo-ready: recruiters can see the system in under five minutes.

---

## Installation & Usage

```bash
# Clone the repository
git clone https://github.com/yourusername/ai_excel_agent.git
cd ai_excel_agent

# Install dependencies
pip install -r requirements.txt

# Run Streamlit app
streamlit run app.py
```

* Upload your file and enter your **Groq API key**.
* Click on recommended insights to see results.

---

## Live Demo

Try the AI Agent online:

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://jd-data-retrieval-agent.streamlit.app/)

* Upload Excel or CSV files
* Enter your Groq API key
* Get instant insight recommendations, charts, and data quality scores
* Interact with follow-up Q&A

---

## Target Users

* Data Analysts who want fast automated insights
* Non-technical professionals exploring datasets
* Recruiters & demo evaluators looking for AI-powered solutions for recruiters.



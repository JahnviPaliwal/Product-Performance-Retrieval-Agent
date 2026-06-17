# BI RAG Assistant

A **Business Intelligence + Multi-Document RAG Assistant** built with Flask, LangGraph, and Groq.

## Features

- Upload PDF, CSV, PPTX, DOCX, TXT documents
- RAG pipeline with FAISS vector store (in-memory, no persistence)
- LangGraph agent automatically routes to:
  - **Document Mode** – answers grounded in uploaded files
  - **Analytics Mode** – statistical analysis + auto-generated charts from CSV
  - **General Mode** – LLM general knowledge (with ⚠️ notice)
- Auto-generates 4 follow-up questions after every response
- Business intelligence: summaries, SWOT, risk analysis, KPI extraction
- Chart generation: bar, line, pie, scatter, histogram, heatmap
- Clean light-theme dashboard UI

## Setup

### 1. Clone / extract the project

```bash
cd bi_rag_assistant
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate       # Linux/macOS
# or: venv\Scripts\activate    # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
python app.py
```

Open `http://localhost:5000` in your browser.

### 5. Enter your Groq API key

Paste your Groq API key (starts with `gsk_`) in the top-right input field.  
Get one free at https://console.groq.com

## Architecture

```
bi_rag_assistant/
├── app.py                        # Flask entry point
├── routes/
│   ├── chat.py                   # /api/chat, /api/documents
│   ├── upload.py                 # /api/upload, DELETE /api/documents/<id>
│   └── analytics.py              # /api/analytics/<id>
├── services/
│   └── agent.py                  # LangGraph agent (classify→retrieve→answer→followups)
├── rag/
│   ├── ingestion.py              # parse → chunk → embed → store
│   ├── chunker.py                # RecursiveCharacterTextSplitter
│   └── vector_store.py           # FAISS in-memory per-document
├── document_processors/
│   ├── dispatcher.py             # Route by extension
│   ├── pdf_processor.py          # pypdf
│   ├── csv_processor.py          # pandas
│   ├── pptx_processor.py         # python-pptx
│   ├── docx_processor.py         # python-docx
│   └── txt_processor.py          # plain text
├── analytics/
│   ├── analysis_engine.py        # stats: distribution, outliers, correlations, etc.
│   └── chart_generator.py        # matplotlib charts → base64 PNG
├── utils/
│   └── session_store.py          # In-memory doc registry (no DB)
├── templates/
│   └── index.html
├── static/
│   ├── css/style.css
│   └── js/app.js
└── uploads/                      # Temp file storage (session only)
```

## Key Design Decisions

- **No database**: all state is in-memory Python dicts; cleared on server restart
- **Session-scoped**: uploading a file stores it in `uploads/` and its embeddings in RAM
- **Irrelevant query handling**: the LangGraph classifier detects off-topic questions and adds a visible ⚠️ notice before answering from general knowledge
- **Model**: `llama-3.3-70b-versatile` via Groq API
- **Embeddings**: `all-MiniLM-L6-v2` via sentence-transformers (runs locally, no API cost)

## Data Privacy

- Files are saved only to the `uploads/` folder during the server session
- Deleting a document removes the file from disk AND its embeddings from memory
- No data is sent to external services except the Groq LLM API (query + retrieved chunks)

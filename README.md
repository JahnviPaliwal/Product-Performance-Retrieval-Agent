---
title: BI RAG Assistant
emoji: 📊
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# BI RAG Assistant

Upload PDFs, CSVs, PPTX, DOCX, or TXT files and ask business intelligence questions.

- **RAG mode** — answers from your documents using TF-IDF retrieval
- **Analytics mode** — statistical insights + charts from CSV datasets
- **General mode** — falls back to LLM knowledge when docs aren't relevant

Your uploaded documents are **persisted** across server restarts using SQLite + disk storage.

### Setup
Enter your [Groq API key](https://console.groq.com) in the top-right input, upload documents, and start asking questions.

"""
utils/session_store.py
SQLite-backed persistent document store.
- Metadata stored in SQLite at /data/documents.db
- Files stored at /data/uploads/
- Vector stores rebuilt in memory on startup from disk files
- Users can delete via UI (removes DB row + file)
"""
from __future__ import annotations
import os
import sqlite3
import threading
from typing import Dict, Any

DATA_DIR = os.environ.get("DATA_DIR", "/data")
DB_PATH  = os.path.join(DATA_DIR, "documents.db")
FILE_DIR = os.path.join(DATA_DIR, "uploads")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(FILE_DIR, exist_ok=True)

_lock: threading.Lock = threading.Lock()
_documents: Dict[str, Dict[str, Any]] = {}


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                doc_id    TEXT PRIMARY KEY,
                filename  TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_path TEXT NOT NULL
            )
        """)
        conn.commit()


_init_db()


def add_document(doc_id: str, meta: Dict[str, Any]):
    with _lock:
        _documents[doc_id] = meta
        with _get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO documents (doc_id, filename, file_type, file_path) VALUES (?, ?, ?, ?)",
                (doc_id, meta["filename"], meta["file_type"], meta["file_path"]),
            )
            conn.commit()


def get_document(doc_id: str) -> Dict[str, Any] | None:
    with _lock:
        return _documents.get(doc_id)


def get_all_documents() -> Dict[str, Dict[str, Any]]:
    with _lock:
        return dict(_documents)


def delete_document(doc_id: str):
    with _lock:
        meta = _documents.pop(doc_id, None)
        if meta:
            fp = meta.get("file_path")
            if fp and os.path.exists(fp):
                try:
                    os.remove(fp)
                except OSError:
                    pass
        with _get_conn() as conn:
            conn.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
            conn.commit()


def clear_all():
    with _lock:
        for doc_id in list(_documents.keys()):
            meta = _documents.pop(doc_id, None)
            if meta:
                fp = meta.get("file_path")
                if fp and os.path.exists(fp):
                    try:
                        os.remove(fp)
                    except OSError:
                        pass
        with _get_conn() as conn:
            conn.execute("DELETE FROM documents")
            conn.commit()


def _rebuild_cache():
    """Re-ingest all files from SQLite on startup."""
    from rag.chunker import chunk_text
    from rag.vector_store import DocumentVectorStore
    from document_processors.dispatcher import extract_text

    with _get_conn() as conn:
        rows = conn.execute("SELECT * FROM documents").fetchall()

    for row in rows:
        doc_id    = row["doc_id"]
        filename  = row["filename"]
        file_type = row["file_type"]
        file_path = row["file_path"]

        if not os.path.exists(file_path):
            with _get_conn() as conn:
                conn.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
                conn.commit()
            continue

        try:
            text   = extract_text(file_path)
            chunks = chunk_text(text)
            vs     = DocumentVectorStore(chunks)
            with _lock:
                _documents[doc_id] = {
                    "doc_id": doc_id, "filename": filename,
                    "file_type": file_type, "file_path": file_path,
                    "text": text, "chunks": chunks, "vector_store": vs,
                }
        except Exception as e:
            print(f"[startup] Failed to rebuild {filename}: {e}")

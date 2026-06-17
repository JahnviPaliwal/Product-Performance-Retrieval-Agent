"""
rag/ingestion.py
Orchestrate document parsing → chunking → embedding → vector store.
"""
import uuid
from document_processors.dispatcher import extract_text, get_file_type
from rag.chunker import chunk_text
from rag.vector_store import DocumentVectorStore
from utils.session_store import add_document


def ingest_document(file_path: str, original_filename: str) -> str:
    """Parse, chunk, embed a document. Return its doc_id."""
    doc_id = str(uuid.uuid4())
    file_type = get_file_type(file_path)

    text = extract_text(file_path)
    chunks = chunk_text(text)
    vector_store = DocumentVectorStore(chunks)

    add_document(doc_id, {
        "doc_id": doc_id,
        "filename": original_filename,
        "file_type": file_type,
        "file_path": file_path,
        "text": text,
        "chunks": chunks,
        "vector_store": vector_store,
    })
    return doc_id

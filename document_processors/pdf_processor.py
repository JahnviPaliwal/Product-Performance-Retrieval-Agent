"""
document_processors/pdf_processor.py
Extract text (and best-effort tables) from PDF files.
"""
from pypdf import PdfReader


def extract_text(file_path: str) -> str:
    reader = PdfReader(file_path)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            pages.append(f"[Page {i+1}]\n{text}")
    return "\n\n".join(pages)

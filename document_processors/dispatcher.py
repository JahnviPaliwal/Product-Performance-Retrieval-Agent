"""
document_processors/dispatcher.py
Route file to appropriate processor based on extension.
"""
import os
from . import pdf_processor, csv_processor, pptx_processor, docx_processor, txt_processor


SUPPORTED_EXTENSIONS = {".pdf", ".csv", ".pptx", ".docx", ".txt"}


def extract_text(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return pdf_processor.extract_text(file_path)
    elif ext == ".csv":
        return csv_processor.extract_text(file_path)
    elif ext == ".pptx":
        return pptx_processor.extract_text(file_path)
    elif ext == ".docx":
        return docx_processor.extract_text(file_path)
    elif ext == ".txt":
        return txt_processor.extract_text(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def get_file_type(file_path: str) -> str:
    return os.path.splitext(file_path)[1].lower().lstrip(".")

"""
routes/upload.py
Saves uploaded files to /data/uploads (persistent), ingests them into SQLite + memory.
"""
import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from rag.ingestion import ingest_document
from utils.session_store import delete_document, get_all_documents, FILE_DIR
from document_processors.dispatcher import SUPPORTED_EXTENSIONS

upload_bp = Blueprint("upload", __name__)


@upload_bp.route("/api/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file provided."}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Empty filename."}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return jsonify({"error": f"Unsupported file type: {ext}. Supported: {', '.join(SUPPORTED_EXTENSIONS)}"}), 400

    filename  = secure_filename(file.filename)
    file_path = os.path.join(FILE_DIR, filename)
    file.save(file_path)

    try:
        doc_id = ingest_document(file_path, file.filename)
    except Exception as e:
        os.remove(file_path)
        return jsonify({"error": f"Failed to process document: {str(e)}"}), 500

    return jsonify({"doc_id": doc_id, "filename": file.filename, "message": "Document uploaded and indexed."})


@upload_bp.route("/api/documents/<doc_id>", methods=["DELETE"])
def delete_doc(doc_id: str):
    doc = get_all_documents().get(doc_id)
    if not doc:
        return jsonify({"error": "Document not found."}), 404
    delete_document(doc_id)
    return jsonify({"message": f"Document '{doc['filename']}' deleted."})


@upload_bp.route("/api/documents/clear", methods=["DELETE"])
def clear_all_docs():
    """Nuke all documents — exposed for the 'Clear All' button in the UI."""
    from utils.session_store import clear_all
    clear_all()
    return jsonify({"message": "All documents deleted."})

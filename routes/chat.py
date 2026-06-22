"""
routes/chat.py
"""
from flask import Blueprint, request, jsonify, render_template
from services.agent import run_agent
from utils.session_store import get_all_documents

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/")
def index():
    return render_template("index.html")


@chat_bp.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    query = (data or {}).get("query", "").strip()
    api_key = (data or {}).get("api_key", "").strip()

    if not query:
        return jsonify({"error": "Query is required."}), 400
    if not api_key:
        return jsonify({"error": "Groq API key is required."}), 400

    try:
        result = run_agent(query, api_key)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@chat_bp.route("/api/documents", methods=["GET"])
def list_documents():
    docs = get_all_documents()
    summary = [
        {"doc_id": d["doc_id"], "filename": d["filename"], "file_type": d["file_type"]}
        for d in docs.values()
    ]
    return jsonify({"documents": summary})

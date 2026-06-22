"""
routes/analytics.py
Dedicated endpoint for explicit CSV analytics requests.
"""
from flask import Blueprint, request, jsonify
from utils.session_store import get_all_documents
from document_processors.csv_processor import load_dataframe
from analytics.analysis_engine import run_analysis, profile_dataframe, compute_data_quality
from analytics.chart_generator import auto_chart

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/api/analytics/<doc_id>", methods=["POST"])
def run_analytics(doc_id: str):
    docs = get_all_documents()
    doc = docs.get(doc_id)
    if not doc:
        return jsonify({"error": "Document not found."}), 404
    if doc["file_type"] != "csv":
        return jsonify({"error": "Analytics only supported for CSV files."}), 400

    data = request.get_json() or {}
    analysis_type = data.get("type", "profile")

    df = load_dataframe(doc["file_path"])
    result = run_analysis(analysis_type, df)
    return jsonify(result)


@analytics_bp.route("/api/analytics/<doc_id>/charts", methods=["GET"])
def get_charts(doc_id: str):
    docs = get_all_documents()
    doc = docs.get(doc_id)
    if not doc or doc["file_type"] != "csv":
        return jsonify({"error": "CSV document not found."}), 404

    df = load_dataframe(doc["file_path"])
    charts = auto_chart(df)
    # Strip heavy image data from list response, keep metadata only
    chart_meta = [{"chart_type": c["chart_type"], "title": c["title"]} for c in charts]
    return jsonify({"charts": chart_meta})


@analytics_bp.route("/api/analytics/<doc_id>/profile", methods=["GET"])
def get_profile(doc_id: str):
    docs = get_all_documents()
    doc = docs.get(doc_id)
    if not doc or doc["file_type"] != "csv":
        return jsonify({"error": "CSV document not found."}), 404
    df = load_dataframe(doc["file_path"])
    return jsonify({
        "profile": profile_dataframe(df),
        "quality_score": compute_data_quality(df),
    })

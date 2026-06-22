"""
app.py - Flask entry point for BI RAG Assistant
Deployed on Hugging Face Spaces (Docker) - port 7860
"""
import os
import sys

# Add project root to path so all modules resolve correctly
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask
from routes.chat import chat_bp
from routes.upload import upload_bp
from routes.analytics import analytics_bp
from utils.session_store import _rebuild_cache, FILE_DIR


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))
    app.config["UPLOAD_FOLDER"] = FILE_DIR
    app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB

    app.register_blueprint(chat_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(analytics_bp)

    return app


if __name__ == "__main__":
    # Rebuild vector stores from persisted SQLite + disk files
    print("[startup] Rebuilding document cache from persistent storage...")
    _rebuild_cache()
    print("[startup] Cache ready.")

    app = create_app()
    port = int(os.environ.get("PORT", 7860))
    app.run(host="0.0.0.0", port=port, debug=False)

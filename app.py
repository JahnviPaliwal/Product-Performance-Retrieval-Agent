"""
app.py – Flask entry point for BI + Multi-Document RAG Assistant
"""
import os
from flask import Flask
from routes.chat import chat_bp
from routes.upload import upload_bp
from routes.analytics import analytics_bp

def create_app():
    app = Flask(__name__)
    app.secret_key = os.urandom(24)
    app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "uploads")
    app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    app.register_blueprint(chat_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(analytics_bp)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)

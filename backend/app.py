import os
import sys
from pathlib import Path
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

# Ensure backend directory and project root are in sys.path
backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import Config
from database.db import init_db, is_cloud_db, query_db
from database.seed_data import seed_database
from knowledge_base.ingest import ingest_all_documents
from routes.services import services_bp
from routes.checklist import checklist_bp
from routes.chatbot import chatbot_bp
from routes.auth import auth_bp
from services.auth_service import seed_demo_user

def create_app():
    app = Flask(__name__, static_folder=None)
    CORS(app)

    # Ensure DB schema and demo user exist
    if is_cloud_db():
        init_db()
        try:
            services_row = query_db("SELECT COUNT(*) as cnt FROM services", one=True)
            if not services_row or services_row.get("cnt", 0) == 0:
                print("Cloud database is empty. Seeding services and rules...")
                seed_database()
        except Exception as e:
            print(f"Cloud DB check/seed notice: {e}")
    elif not Config.DATABASE_PATH.exists():
        print("Database not found. Initializing and seeding...")
        seed_database()
    else:
        init_db()

    try:
        seed_demo_user()
    except Exception:
        pass

    # Ensure Knowledge Base chunks exist
    if not Config.CHUNKS_FILE.exists():
        try:
            ingest_all_documents()
        except Exception as e:
            print(f"Knowledge base ingestion notice: {e}")

    # Register Blueprints
    app.register_blueprint(services_bp)
    app.register_blueprint(checklist_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(auth_bp)

    # Health check
    @app.route('/api/health', methods=['GET'])
    def health():
        return jsonify({
            "status": "healthy",
            "service": "Aadhaar, PAN & Passport Process Helper API",
            "version": "1.0.0"
        })

    # Serve Frontend HTML Pages & Static Assets
    @app.route('/')
    def root():
        return send_from_directory(Config.PAGES_DIR, "index.html")

    @app.route('/<path:filename>')
    def serve_frontend(filename):
        if (Config.PAGES_DIR / filename).is_file():
            return send_from_directory(Config.PAGES_DIR, filename)

        if filename.startswith("pages/"):
            sub_file = filename[len("pages/"):]
            if (Config.PAGES_DIR / sub_file).is_file():
                return send_from_directory(Config.PAGES_DIR, sub_file)

        if (Config.FRONTEND_DIR / filename).is_file():
            return send_from_directory(Config.FRONTEND_DIR, filename)

        if not filename.endswith(".html") and (Config.PAGES_DIR / f"{filename}.html").is_file():
            return send_from_directory(Config.PAGES_DIR, f"{filename}.html")

        return send_from_directory(Config.PAGES_DIR, "index.html")

    return app

# Expose WSGI application instance for production servers (gunicorn, render, etc.)
app = create_app()

def is_running_in_streamlit() -> bool:
    """Detects if script is currently being run under Streamlit."""
    try:
        import streamlit as st
        if hasattr(st, "runtime") and st.runtime.exists():
            return True
    except Exception:
        pass
    return "STREAMLIT_SERVER_PORT" in os.environ or any("streamlit" in str(arg).lower() for arg in sys.argv)


def run_streamlit_portal():
    """Renders the Streamlit Citizen Helper UI when loaded on Streamlit Community Cloud."""
    try:
        import importlib
        import streamlit_app
        importlib.reload(streamlit_app)
    except Exception as e:
        print(f"Streamlit portal execution notice: {e}")


# Main Entry Point
if is_running_in_streamlit():
    run_streamlit_portal()
elif __name__ == '__main__':
    print(f"🚀 Starting Aadhaar, PAN & Passport Process Helper on http://127.0.0.1:{Config.PORT}")
    app.run(host='0.0.0.0', port=Config.PORT, debug=Config.DEBUG, use_reloader=False)

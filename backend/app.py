import os
import sys
from pathlib import Path
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from config import Config
from database.db import init_db
from database.seed_data import seed_database
from knowledge_base.ingest import ingest_all_documents
from routes.services import services_bp
from routes.checklist import checklist_bp
from routes.chatbot import chatbot_bp

def create_app():
    app = Flask(__name__, static_folder=None)
    CORS(app)

    # Ensure DB exists
    if not Config.DATABASE_PATH.exists():
        print("Database not found. Initializing and seeding...")
        seed_database()

    # Ensure Knowledge Base chunks exist
    if not Config.CHUNKS_FILE.exists():
        print("Ingesting knowledge base documents...")
        ingest_all_documents()

    # Register Blueprints
    app.register_blueprint(services_bp)
    app.register_blueprint(checklist_bp)
    app.register_blueprint(chatbot_bp)

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
        # 1. Direct match in pages/
        if (Config.PAGES_DIR / filename).is_file():
            return send_from_directory(Config.PAGES_DIR, filename)

        # 2. Check if requested with 'pages/' prefix (e.g. pages/aadhaar.html)
        if filename.startswith("pages/"):
            sub_file = filename[len("pages/"):]
            if (Config.PAGES_DIR / sub_file).is_file():
                return send_from_directory(Config.PAGES_DIR, sub_file)

        # 3. Direct match in frontend root (e.g. css/style.css, js/main.js, assets/...)
        if (Config.FRONTEND_DIR / filename).is_file():
            return send_from_directory(Config.FRONTEND_DIR, filename)

        # 4. Fallback if filename has .html extension but was requested without pages/
        if not filename.endswith(".html") and (Config.PAGES_DIR / f"{filename}.html").is_file():
            return send_from_directory(Config.PAGES_DIR, f"{filename}.html")

        # 5. Fallback to index.html
        return send_from_directory(Config.PAGES_DIR, "index.html")

    return app

if __name__ == '__main__':
    app = create_app()
    print(f"🚀 Starting Aadhaar, PAN & Passport Process Helper on http://127.0.0.1:{Config.PORT}")
    app.run(host='0.0.0.0', port=Config.PORT, debug=Config.DEBUG)

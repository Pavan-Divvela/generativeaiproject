import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"

# Load .env
load_dotenv(BACKEND_DIR / ".env", override=True)

class Config:
    PORT = int(os.getenv("PORT", 5000))
    DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    SECRET_KEY = os.getenv("SECRET_KEY", "aadhaar-pan-passport-secret-key-2026")
    
    # Database
    DATABASE_PATH = BACKEND_DIR / "database" / "identity_helper.db"
    SCHEMA_PATH = BACKEND_DIR / "database" / "schema.sql"
    
    # Knowledge Base
    KNOWLEDGE_BASE_DIR = BACKEND_DIR / "knowledge_base"
    DOCUMENTS_DIR = KNOWLEDGE_BASE_DIR / "documents"
    PROCESSED_DIR = KNOWLEDGE_BASE_DIR / "processed"
    CHUNKS_FILE = PROCESSED_DIR / "chunks.json"
    
    # LLM & AI
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
    
    # Static & Frontend paths
    FRONTEND_DIR = FRONTEND_DIR
    STATIC_DIR = FRONTEND_DIR
    PAGES_DIR = FRONTEND_DIR / "pages"

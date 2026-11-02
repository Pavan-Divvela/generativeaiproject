"""
RAG Configuration — reads from environment variables / .env
All RAG-specific settings are centralized here.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve paths relative to the backend/ directory
BACKEND_DIR = Path(__file__).resolve().parent.parent  # backend/
PROJECT_ROOT = BACKEND_DIR.parent                      # project root

# Load .env from backend/
load_dotenv(BACKEND_DIR / ".env", override=False)


class RAGConfig:
    # ── Gemini API ────────────────────────────────────────────────────────
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    # Model used for answer generation (gemini-3-flash-preview confirmed active)
    GENERATION_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")

    # ── ChromaDB ──────────────────────────────────────────────────────────
    CHROMA_PATH: Path = Path(os.getenv(
        "CHROMA_PATH",
        str(PROJECT_ROOT / "data" / "chroma_db")
    ))
    CHROMA_COLLECTION: str = os.getenv("CHROMA_COLLECTION", "aadhaar_pan_passport")

    # ── PDF Ingestion ─────────────────────────────────────────────────────
    RAW_DATA_DIR: Path = Path(os.getenv(
        "RAW_DATA_DIR",
        str(PROJECT_ROOT / "data" / "raw")
    ))
    SOURCE_MANIFEST: Path = Path(os.getenv(
        "SOURCE_MANIFEST",
        str(PROJECT_ROOT / "data" / "source_manifest.json")
    ))

    # ── Chunking ──────────────────────────────────────────────────────────
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))    # characters
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "80"))

    # ── Retrieval ─────────────────────────────────────────────────────────
    TOP_K: int = int(os.getenv("TOP_K", "4"))

    # ── Input limits ─────────────────────────────────────────────────────
    MAX_QUESTION_LEN: int = int(os.getenv("MAX_QUESTION_LEN", "1000"))

    @classmethod
    def validate(cls) -> list[str]:
        """Returns a list of validation warnings (non-fatal)."""
        warnings: list[str] = []
        if not cls.GEMINI_API_KEY:
            warnings.append("GEMINI_API_KEY is not set — LLM generation will be unavailable.")
        if not cls.CHROMA_PATH.exists():
            cls.CHROMA_PATH.mkdir(parents=True, exist_ok=True)
        if not cls.RAW_DATA_DIR.exists():
            warnings.append(f"RAW_DATA_DIR does not exist: {cls.RAW_DATA_DIR}")
        return warnings

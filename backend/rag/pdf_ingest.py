"""
PDF Ingestion pipeline for RAG.

Usage (from project root):
    python -m backend.rag.pdf_ingest            # incremental upsert
    python -m backend.rag.pdf_ingest --rebuild  # wipe and rebuild

For each PDF it:
  1. Extracts text page by page using pypdf
  2. Warns if a page is empty (may need OCR)
  3. Splits text into overlapping character chunks
  4. Attaches metadata (service, title, source_url, filename, page_range, chunk_id)
  5. Upserts into ChromaDB using deterministic IDs (no duplicates on re-run)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from datetime import date
from pathlib import Path
from typing import Any

# ── Path bootstrap ─────────────────────────────────────────────────────────────
_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from rag.config import RAGConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("rag.ingest")

# ── Lazy imports (only available after pip install) ────────────────────────────
try:
    import pypdf  # type: ignore
except ImportError:
    pypdf = None  # type: ignore

try:
    import chromadb  # type: ignore
    from chromadb.utils import embedding_functions  # type: ignore
except ImportError:
    chromadb = None  # type: ignore


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split *text* into overlapping character chunks."""
    if not text.strip():
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        start = end - overlap
    return chunks


def _deterministic_id(filename: str, page_label: str, chunk_index: int) -> str:
    """Create a stable chunk ID from (filename, page, index) so re-runs don't duplicate."""
    raw = f"{filename}::{page_label}::{chunk_index}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def _load_manifest() -> dict[str, Any]:
    if not RAGConfig.SOURCE_MANIFEST.exists():
        log.warning("source_manifest.json not found at %s", RAGConfig.SOURCE_MANIFEST)
        return {}
    with open(RAGConfig.SOURCE_MANIFEST, encoding="utf-8") as f:
        return json.load(f)


def _get_chroma_collection(rebuild: bool = False):
    """Return (or create) the persistent ChromaDB collection."""
    if chromadb is None:
        raise ImportError("chromadb is not installed. Run: pip install chromadb")

    client = chromadb.PersistentClient(path=str(RAGConfig.CHROMA_PATH))

    if rebuild:
        try:
            client.delete_collection(RAGConfig.CHROMA_COLLECTION)
            log.info("Deleted existing collection '%s'.", RAGConfig.CHROMA_COLLECTION)
        except Exception:
            pass

    # Default embedding function uses sentence-transformers locally (no API key needed)
    ef = embedding_functions.DefaultEmbeddingFunction()
    collection = client.get_or_create_collection(
        name=RAGConfig.CHROMA_COLLECTION,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )
    return collection


# ──────────────────────────────────────────────────────────────────────────────
# Core ingestion
# ──────────────────────────────────────────────────────────────────────────────

def ingest_pdf(pdf_path: Path, service: str, manifest_entry: dict, collection) -> int:
    """
    Extract, chunk, embed, and upsert a single PDF into ChromaDB.
    Returns the number of chunks upserted.
    """
    if pypdf is None:
        raise ImportError("pypdf is not installed. Run: pip install pypdf")

    title = manifest_entry.get("title", pdf_path.stem)
    official_url = manifest_entry.get("official_url", "")
    today = date.today().isoformat()
    filename = pdf_path.name

    log.info("Processing: %s", pdf_path)

    try:
        reader = pypdf.PdfReader(str(pdf_path))
    except Exception as exc:
        log.error("Cannot open PDF '%s': %s", pdf_path.name, exc)
        return 0

    total_pages = len(reader.pages)
    all_chunks: list[str] = []
    chunk_page_labels: list[str] = []  # tracks which page(s) each chunk comes from

    for page_num, page in enumerate(reader.pages, start=1):
        try:
            page_text = page.extract_text() or ""
        except Exception as exc:
            log.warning("Page %d/%d text extraction failed in '%s': %s",
                        page_num, total_pages, filename, exc)
            page_text = ""

        if not page_text.strip():
            log.warning(
                "Page %d of '%s' is empty — it may be a scanned image. "
                "OCR (e.g. pytesseract + pdf2image) is required to extract text "
                "from scanned PDFs. Skipping this page.",
                page_num, filename
            )
            continue

        page_chunks = _chunk_text(page_text, RAGConfig.CHUNK_SIZE, RAGConfig.CHUNK_OVERLAP)
        for chunk in page_chunks:
            all_chunks.append(chunk)
            chunk_page_labels.append(f"p{page_num}")

    if not all_chunks:
        log.warning("No text extracted from '%s'. "
                    "If this is a scanned PDF, install pytesseract + pdf2image for OCR.", filename)
        return 0

    # Build ChromaDB upsert payload
    ids, documents, metadatas = [], [], []
    for idx, (chunk_text, page_label) in enumerate(zip(all_chunks, chunk_page_labels)):
        chunk_id = _deterministic_id(filename, page_label, idx)
        ids.append(chunk_id)
        documents.append(chunk_text)
        metadatas.append({
            "service": service,
            "title": title,
            "official_url": official_url,
            "filename": filename,
            "page_range": page_label,
            "chunk_index": idx,
            "ingestion_date": today,
        })

    # Upsert in batches of 100 to avoid memory spikes
    batch_size = 100
    upserted = 0
    for i in range(0, len(ids), batch_size):
        collection.upsert(
            ids=ids[i:i+batch_size],
            documents=documents[i:i+batch_size],
            metadatas=metadatas[i:i+batch_size],
        )
        upserted += len(ids[i:i+batch_size])

    log.info("  ✓ %s: %d chunks upserted (%d pages)", filename, upserted, total_pages)
    return upserted


def run_ingestion(rebuild: bool = False) -> None:
    """Main entry point: walk data/raw/<service>/ dirs and ingest all PDFs."""
    warnings = RAGConfig.validate()
    for w in warnings:
        log.warning(w)

    manifest = _load_manifest()
    collection = _get_chroma_collection(rebuild=rebuild)

    services = ["aadhaar", "pan", "passport"]
    total_docs = 0
    total_chunks = 0

    for service in services:
        service_dir = RAGConfig.RAW_DATA_DIR / service
        if not service_dir.exists():
            log.info("No directory found for service '%s' — skipping.", service)
            continue

        pdf_files = list(service_dir.glob("*.pdf"))
        if not pdf_files:
            log.info("No PDFs found in %s — skipping.", service_dir)
            continue

        service_manifest = manifest.get(service, {})
        for pdf_path in pdf_files:
            entry = service_manifest.get(pdf_path.name, {
                "title": pdf_path.stem.replace("_", " ").title(),
                "official_url": "",
            })
            if not entry.get("official_url"):
                log.warning(
                    "No official_url in source_manifest.json for '%s/%s'. "
                    "Please add the verified government source URL.",
                    service, pdf_path.name
                )
            chunks = ingest_pdf(pdf_path, service, entry, collection)
            if chunks > 0:
                total_docs += 1
                total_chunks += chunks

    existing_count = collection.count()
    log.info("─" * 60)
    log.info("Ingestion complete: %d documents processed, %d new chunks upserted.",
             total_docs, total_chunks)
    log.info("ChromaDB collection '%s' now contains %d total chunks.",
             RAGConfig.CHROMA_COLLECTION, existing_count)

    if existing_count == 0:
        log.warning(
            "The knowledge base is empty. "
            "Download official PDFs and place them in:\n"
            "  data/raw/aadhaar/   → UIDAI PDFs\n"
            "  data/raw/pan/       → Income Tax / CBDT PDFs\n"
            "  data/raw/passport/  → MEA / Passport Seva PDFs\n"
            "Then re-run: python -m backend.rag.pdf_ingest"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ingest official government PDFs into ChromaDB for RAG."
    )
    parser.add_argument(
        "--rebuild", action="store_true",
        help="Wipe the existing ChromaDB collection and rebuild from scratch."
    )
    args = parser.parse_args()
    run_ingestion(rebuild=args.rebuild)

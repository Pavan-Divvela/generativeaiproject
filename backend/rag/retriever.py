"""
ChromaDB Retrieval — embeds the user's question and fetches the most relevant chunks.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from rag.config import RAGConfig

log = logging.getLogger("rag.retriever")

# Lazy imports
try:
    import chromadb  # type: ignore
    from chromadb.utils import embedding_functions  # type: ignore
    _CHROMA_AVAILABLE = True
except ImportError:
    _CHROMA_AVAILABLE = False

_collection = None  # module-level singleton


def _get_collection():
    """Return the persistent ChromaDB collection (lazy-init singleton)."""
    global _collection
    if _collection is not None:
        return _collection

    if not _CHROMA_AVAILABLE:
        raise ImportError("chromadb is not installed. Run: pip install chromadb")

    client = chromadb.PersistentClient(path=str(RAGConfig.CHROMA_PATH))
    ef = embedding_functions.DefaultEmbeddingFunction()
    _collection = client.get_or_create_collection(
        name=RAGConfig.CHROMA_COLLECTION,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )
    return _collection


def is_knowledge_base_empty() -> bool:
    """Returns True when ChromaDB collection has no documents."""
    try:
        return _get_collection().count() == 0
    except Exception:
        return True


def retrieve_chunks(
    question: str,
    service: Optional[str] = None,
    top_k: int | None = None,
) -> list[dict]:
    """
    Embed *question* and return the top-k most relevant chunks from ChromaDB.

    Args:
        question: The user's raw question text.
        service:  Optional filter — "aadhaar", "pan", or "passport".
        top_k:    Number of results to return (defaults to RAGConfig.TOP_K).

    Returns:
        A list of dicts, each with keys:
          id, document, service, title, official_url, filename,
          page_range, chunk_index, distance
    """
    if not question or not question.strip():
        log.warning("retrieve_chunks called with empty question.")
        return []

    k = top_k if top_k is not None else RAGConfig.TOP_K

    try:
        collection = _get_collection()
    except Exception as exc:
        log.error("Cannot connect to ChromaDB: %s", exc)
        return []

    if collection.count() == 0:
        log.info("ChromaDB collection is empty — no chunks to retrieve.")
        return []

    # Build optional where-clause for service filtering
    where: dict | None = None
    if service and service in {"aadhaar", "pan", "passport"}:
        where = {"service": {"$eq": service}}

    try:
        results = collection.query(
            query_texts=[question.strip()],
            n_results=min(k, collection.count()),
            where=where,
            include=["documents", "metadatas", "distances"],
        )
    except Exception as exc:
        log.error("ChromaDB query failed: %s", exc)
        return []

    # Flatten results
    chunks: list[dict] = []
    ids = (results.get("ids") or [[]])[0]
    docs = (results.get("documents") or [[]])[0]
    metas = (results.get("metadatas") or [[]])[0]
    dists = (results.get("distances") or [[]])[0]

    for chunk_id, doc_text, meta, dist in zip(ids, docs, metas, dists):
        chunks.append({
            "id": chunk_id,
            "document": doc_text,
            "service": meta.get("service", ""),
            "title": meta.get("title", ""),
            "official_url": meta.get("official_url", ""),
            "filename": meta.get("filename", ""),
            "page_range": meta.get("page_range", ""),
            "chunk_index": meta.get("chunk_index", 0),
            "distance": dist,  # cosine distance: lower = more similar
        })

    log.info("Retrieved %d chunks for question (service=%s).", len(chunks), service or "all")
    return chunks

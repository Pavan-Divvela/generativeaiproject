"""
Main RAG service — orchestrates retrieval + generation.

When ChromaDB is populated (PDFs ingested), uses the full RAG pipeline.
When ChromaDB is empty, falls back to the existing keyword-based synthesizer
so the chatbot keeps working even before any PDFs are added.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

log = logging.getLogger("services.rag_service")

# ── Try to import the new ChromaDB RAG pipeline ──────────────────────────────
_RAG_AVAILABLE = False
try:
    from rag.retriever import retrieve_chunks, is_knowledge_base_empty
    from rag.generator import generate_rag_answer
    _RAG_AVAILABLE = True
except Exception as exc:
    log.warning("ChromaDB RAG pipeline unavailable (%s). Using keyword fallback.", exc)

# ── Always available: existing BM25 + keyword pipeline ───────────────────────
from knowledge_base.retriever import retrieve_context
from services.llm_service import synthesize_rag_response


# ──────────────────────────────────────────────────────────────────────────────
# Suggestion engine (shared)
# ──────────────────────────────────────────────────────────────────────────────

def _get_suggestions(query: str) -> list[str]:
    q = query.lower()
    if "pan" in q or "link" in q or "challan" in q:
        return [
            "What if my name has initials on Aadhaar but not on PAN?",
            "How long does the ₹1,000 challan payment take to update?",
            "Can I apply for instant e-PAN if mobile is not linked?",
        ]
    elif "passport" in q or "tatkaal" in q:
        return [
            "What are the 3 documents required for Tatkaal passport?",
            "Can I use a rental agreement as address proof for passport?",
            "How does police verification work for passport?",
        ]
    elif "aadhaar" in q or "update" in q or "biometric" in q:
        return [
            "How many times can I change Date of Birth in Aadhaar?",
            "How to order an official Aadhaar PVC card?",
            "What is Masked Aadhaar and where is it accepted?",
        ]
    else:
        return [
            "In what order should I correct my documents?",
            "How to fix single name / blank surname on passport?",
            "What documents are acceptable as Proof of Date of Birth?",
        ]


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def get_rag_chat_response(query: str, service: Optional[str] = None) -> dict:
    """
    End-to-end RAG response for a user query.

    Pipeline:
      1. If ChromaDB RAG is available and the knowledge base is not empty:
         → retrieve relevant chunks → generate grounded Gemini answer with citations
      2. Otherwise fall back to the existing BM25 retriever + keyword synthesizer.

    Returns a dict with keys: answer, sources, citations, suggestions, source_mode
    """
    if not query or not query.strip():
        return {
            "answer": "Please ask a question regarding Aadhaar, PAN card, or Indian Passport procedures.",
            "sources": [],
            "citations": [],
            "suggestions": [
                "How to link PAN with Aadhaar?",
                "What documents are needed for Tatkaal passport?",
                "How to resolve name mismatch between 10th marksheet and Aadhaar?",
                "What is Non-ECR passport status?",
            ],
            "source_mode": "empty_query",
        }

    # ── Path A: ChromaDB RAG ─────────────────────────────────────────────────
    if _RAG_AVAILABLE:
        try:
            kb_empty = is_knowledge_base_empty()
            if not kb_empty:
                chunks = retrieve_chunks(query, service=service, top_k=4)
                answer, citations = generate_rag_answer(query, chunks)

                return {
                    "answer": answer,
                    "sources": [
                        {
                            "id": c.id,
                            "title": c.title,
                            "document": c.filename,
                            "service": c.service,
                            "official_url": c.official_url,
                            "page_range": c.page_range,
                        }
                        for c in citations
                    ],
                    "citations": [c.model_dump() for c in citations],
                    "suggestions": _get_suggestions(query),
                    "source_mode": "chroma_rag",
                }
        except Exception as exc:
            log.error("ChromaDB RAG pipeline error: %s — falling back.", exc)

    # ── Path B: Existing BM25 keyword fallback ───────────────────────────────
    log.info("Using keyword fallback (ChromaDB empty or unavailable).")
    bm25_chunks = retrieve_context(query, top_k=3)
    answer = synthesize_rag_response(query, bm25_chunks)

    sources = [
        {
            "id": c.get("id"),
            "title": c.get("title"),
            "document": c.get("document"),
            "service": c.get("service", ""),
            "official_url": "",
            "score": c.get("relevance_score"),
        }
        for c in bm25_chunks
    ]

    return {
        "answer": answer,
        "sources": sources,
        "citations": [],
        "suggestions": _get_suggestions(query),
        "source_mode": "keyword_fallback",
    }

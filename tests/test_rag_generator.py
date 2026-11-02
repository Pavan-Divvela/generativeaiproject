"""
Tests for the RAG generator module.
All Gemini API calls are mocked — no real API credits used.
Run: python -m pytest tests/test_rag_generator.py -v
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))


SAMPLE_CHUNKS = [
    {
        "id": "abc123",
        "document": "To update your name in Aadhaar, visit the nearest Aadhaar Seva Kendra with a valid proof of identity.",
        "service": "aadhaar",
        "title": "Aadhaar Update Guide",
        "official_url": "https://uidai.gov.in",
        "filename": "aadhaar_update.pdf",
        "page_range": "p3",
        "chunk_index": 2,
        "distance": 0.15,
    },
    {
        "id": "def456",
        "document": "Name change in Aadhaar is allowed only 2 times in a lifetime.",
        "service": "aadhaar",
        "title": "UIDAI Circular",
        "official_url": "https://uidai.gov.in/circular",
        "filename": "uidai_circular.pdf",
        "page_range": "p1",
        "chunk_index": 0,
        "distance": 0.22,
    },
]


class TestGenerateRagAnswer:
    def test_empty_chunks_returns_fallback_message(self):
        from rag.generator import generate_rag_answer
        answer, citations = generate_rag_answer("How do I update Aadhaar?", chunks=[])
        assert "official" in answer.lower() or "portal" in answer.lower()
        assert citations == []

    def test_returns_gemini_answer_when_api_succeeds(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"text": "Visit Aadhaar Seva Kendra with a valid proof of identity."}]
                }
            }]
        }

        with patch("rag.generator.requests.post", return_value=mock_resp):
            from rag.generator import generate_rag_answer
            answer, citations = generate_rag_answer("How to update Aadhaar name?", SAMPLE_CHUNKS)

        assert "Aadhaar" in answer or "proof" in answer.lower()
        assert len(citations) == 2

    def test_citations_have_correct_ids(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "Some answer."}]}}]
        }

        with patch("rag.generator.requests.post", return_value=mock_resp):
            from rag.generator import generate_rag_answer
            _, citations = generate_rag_answer("test question", SAMPLE_CHUNKS)

        assert citations[0].id == "source-1"
        assert citations[1].id == "source-2"

    def test_citations_contain_required_fields(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "Answer text."}]}}]
        }

        with patch("rag.generator.requests.post", return_value=mock_resp):
            from rag.generator import generate_rag_answer
            _, citations = generate_rag_answer("question", SAMPLE_CHUNKS)

        for c in citations:
            assert c.id.startswith("source-")
            assert c.title
            assert c.service
            assert c.official_url
            assert c.filename

    def test_api_failure_returns_raw_excerpt_fallback(self):
        """When Gemini returns an error, the fallback should include the top chunk content."""
        mock_resp = MagicMock()
        mock_resp.status_code = 503
        mock_resp.text = "Service Unavailable"

        with patch("rag.generator.requests.post", return_value=mock_resp):
            from rag.generator import generate_rag_answer
            answer, citations = generate_rag_answer("How to update?", SAMPLE_CHUNKS)

        # Should still return something (raw excerpt fallback)
        assert len(answer) > 20
        assert len(citations) == 2

    def test_api_timeout_handled_gracefully(self):
        import requests as req_module
        with patch("rag.generator.requests.post", side_effect=req_module.Timeout()):
            from rag.generator import generate_rag_answer
            answer, citations = generate_rag_answer("What is PAN?", SAMPLE_CHUNKS)

        # Should fall back gracefully
        assert len(answer) > 0

    def test_no_api_key_returns_raw_excerpt(self):
        with patch("rag.generator.RAGConfig.GEMINI_API_KEY", ""):
            from rag.generator import generate_rag_answer
            answer, citations = generate_rag_answer("How to apply for PAN?", SAMPLE_CHUNKS)

        assert len(answer) > 0
        assert len(citations) == 2

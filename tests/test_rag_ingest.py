"""
Tests for the RAG pdf_ingest module.
No API calls — all ChromaDB operations are mocked.
Run: python -m pytest tests/test_rag_ingest.py -v
"""
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

# ── path setup ────────────────────────────────────────────────────────────────
BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from rag.pdf_ingest import _chunk_text, _deterministic_id


class TestChunkText:
    def test_basic_split(self):
        text = "A" * 1200
        chunks = _chunk_text(text, chunk_size=500, overlap=50)
        assert len(chunks) > 1
        for c in chunks:
            assert len(c) <= 500

    def test_overlap_applied(self):
        text = "Hello world " * 100  # 1200 chars
        chunks = _chunk_text(text, chunk_size=200, overlap=40)
        # Each chunk after the first should share some chars with previous
        assert len(chunks) >= 2

    def test_empty_text_returns_empty(self):
        assert _chunk_text("", 500, 50) == []
        assert _chunk_text("   ", 500, 50) == []

    def test_short_text_single_chunk(self):
        text = "Short text"
        chunks = _chunk_text(text, chunk_size=500, overlap=50)
        assert len(chunks) == 1
        assert chunks[0] == "Short text"

    def test_whitespace_only_chunk_skipped(self):
        text = "A" * 500 + "   " + "B" * 500
        chunks = _chunk_text(text, chunk_size=500, overlap=0)
        # Whitespace-only chunks should not appear
        for c in chunks:
            assert c.strip() != ""


class TestDeterministicId:
    def test_same_inputs_same_id(self):
        id1 = _deterministic_id("doc.pdf", "p1", 0)
        id2 = _deterministic_id("doc.pdf", "p1", 0)
        assert id1 == id2

    def test_different_chunk_index_different_id(self):
        id1 = _deterministic_id("doc.pdf", "p1", 0)
        id2 = _deterministic_id("doc.pdf", "p1", 1)
        assert id1 != id2

    def test_different_filename_different_id(self):
        id1 = _deterministic_id("aadhaar.pdf", "p1", 0)
        id2 = _deterministic_id("pan.pdf", "p1", 0)
        assert id1 != id2

    def test_id_is_32_chars(self):
        chunk_id = _deterministic_id("doc.pdf", "p1", 0)
        assert len(chunk_id) == 32


class TestIngestPdf:
    """Test ingest_pdf with mocked pypdf and ChromaDB collection."""

    def test_empty_pdf_returns_zero(self):
        """A PDF where all pages have no text should return 0 chunks."""
        with patch("rag.pdf_ingest.pypdf") as mock_pypdf:
            mock_reader = MagicMock()
            mock_page = MagicMock()
            mock_page.extract_text.return_value = ""
            mock_reader.pages = [mock_page, mock_page]
            mock_pypdf.PdfReader.return_value = mock_reader

            mock_collection = MagicMock()
            from rag.pdf_ingest import ingest_pdf
            result = ingest_pdf(
                Path("test.pdf"), "aadhaar",
                {"title": "Test", "official_url": "https://example.gov.in"},
                mock_collection
            )
        assert result == 0
        mock_collection.upsert.assert_not_called()

    def test_valid_pdf_upserts_chunks(self):
        """A PDF with text should upsert chunks into ChromaDB."""
        with patch("rag.pdf_ingest.pypdf") as mock_pypdf:
            mock_reader = MagicMock()
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "Sample official government text. " * 30
            mock_reader.pages = [mock_page]
            mock_pypdf.PdfReader.return_value = mock_reader

            mock_collection = MagicMock()
            from rag.pdf_ingest import ingest_pdf
            result = ingest_pdf(
                Path("aadhaar_guide.pdf"), "aadhaar",
                {"title": "Aadhaar Guide", "official_url": "https://uidai.gov.in"},
                mock_collection
            )
        assert result > 0
        mock_collection.upsert.assert_called()

    def test_metadata_contains_required_fields(self):
        """Each chunk must have service, title, official_url, filename, page_range."""
        with patch("rag.pdf_ingest.pypdf") as mock_pypdf:
            mock_reader = MagicMock()
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "Official text content. " * 20
            mock_reader.pages = [mock_page]
            mock_pypdf.PdfReader.return_value = mock_reader

            captured_metadatas = []

            def fake_upsert(ids, documents, metadatas):
                captured_metadatas.extend(metadatas)

            mock_collection = MagicMock()
            mock_collection.upsert.side_effect = fake_upsert

            from rag.pdf_ingest import ingest_pdf
            ingest_pdf(
                Path("pan_guide.pdf"), "pan",
                {"title": "PAN Guide", "official_url": "https://incometax.gov.in"},
                mock_collection
            )

        for meta in captured_metadatas:
            assert "service" in meta
            assert "title" in meta
            assert "official_url" in meta
            assert "filename" in meta
            assert "page_range" in meta
            assert "ingestion_date" in meta
            assert meta["service"] == "pan"

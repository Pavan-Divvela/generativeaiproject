"""
Tests for the RAG retriever module.
All ChromaDB calls are mocked — no network required.
Run: python -m pytest tests/test_rag_retrieval.py -v
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))


class TestIsKnowledgeBaseEmpty:
    def test_returns_true_when_count_zero(self):
        with patch("rag.retriever._get_collection") as mock_get:
            mock_get.return_value.count.return_value = 0
            # Reset module-level singleton
            import rag.retriever as ret
            ret._collection = None
            with patch("rag.retriever._get_collection", return_value=MagicMock(count=lambda: 0)):
                from rag.retriever import is_knowledge_base_empty
                assert is_knowledge_base_empty() is True

    def test_returns_false_when_count_positive(self):
        import rag.retriever as ret
        ret._collection = None
        with patch("rag.retriever._get_collection", return_value=MagicMock(count=lambda: 10)):
            from rag.retriever import is_knowledge_base_empty
            assert is_knowledge_base_empty() is False


class TestRetrieveChunks:
    def _make_mock_collection(self, count=5, results=None):
        col = MagicMock()
        col.count.return_value = count
        if results is None:
            results = {
                "ids": [["id1", "id2"]],
                "documents": [["chunk text one", "chunk text two"]],
                "metadatas": [[
                    {"service": "aadhaar", "title": "T1", "official_url": "https://u1.gov",
                     "filename": "f1.pdf", "page_range": "p1", "chunk_index": 0},
                    {"service": "aadhaar", "title": "T2", "official_url": "https://u2.gov",
                     "filename": "f2.pdf", "page_range": "p2", "chunk_index": 1},
                ]],
                "distances": [[0.1, 0.3]],
            }
        col.query.return_value = results
        return col

    def test_returns_correct_structure(self):
        import rag.retriever as ret
        ret._collection = self._make_mock_collection()

        from rag.retriever import retrieve_chunks
        results = retrieve_chunks("How to update Aadhaar?")

        assert isinstance(results, list)
        assert len(results) == 2
        assert "id" in results[0]
        assert "document" in results[0]
        assert "official_url" in results[0]
        assert "service" in results[0]

    def test_empty_question_returns_empty(self):
        import rag.retriever as ret
        ret._collection = self._make_mock_collection()

        from rag.retriever import retrieve_chunks
        assert retrieve_chunks("") == []
        assert retrieve_chunks("   ") == []

    def test_empty_collection_returns_empty(self):
        import rag.retriever as ret
        ret._collection = self._make_mock_collection(count=0)

        from rag.retriever import retrieve_chunks
        result = retrieve_chunks("What is PAN card?")
        assert result == []

    def test_service_filter_passed_to_chromadb(self):
        """When service='pan', the where clause should be forwarded to ChromaDB."""
        mock_col = self._make_mock_collection()
        import rag.retriever as ret
        ret._collection = mock_col

        from rag.retriever import retrieve_chunks
        retrieve_chunks("Apply for PAN", service="pan")

        call_kwargs = mock_col.query.call_args
        assert call_kwargs is not None
        where = call_kwargs.kwargs.get("where") or (call_kwargs.args[3] if len(call_kwargs.args) > 3 else None)
        # The where clause should restrict to service=="pan"
        assert where is not None
        assert where.get("service") == {"$eq": "pan"}

    def test_invalid_service_ignored(self):
        """An unrecognized service value should not crash; no filter applied."""
        mock_col = self._make_mock_collection()
        import rag.retriever as ret
        ret._collection = mock_col

        from rag.retriever import retrieve_chunks
        result = retrieve_chunks("some question", service="invalid_service")
        assert isinstance(result, list)

    def test_chroma_exception_returns_empty(self):
        """If ChromaDB throws, return empty list gracefully."""
        import rag.retriever as ret
        mock_col = MagicMock()
        mock_col.count.return_value = 5
        mock_col.query.side_effect = Exception("ChromaDB error")
        ret._collection = mock_col

        from rag.retriever import retrieve_chunks
        result = retrieve_chunks("What is passport?")
        assert result == []

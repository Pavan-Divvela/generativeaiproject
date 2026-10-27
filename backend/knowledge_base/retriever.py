import json
from pathlib import Path
from config import Config
from knowledge_base.vector_store import VectorStore
from knowledge_base.ingest import ingest_all_documents

_vector_store_instance = None

def get_retriever():
    """Singleton getter for the VectorStore populated with processed chunks."""
    global _vector_store_instance
    if _vector_store_instance is None:
        if not Config.CHUNKS_FILE.exists():
            ingest_all_documents()
        
        with open(Config.CHUNKS_FILE, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        store = VectorStore()
        store.add_documents(chunks)
        _vector_store_instance = store

    return _vector_store_instance

def retrieve_context(query: str, top_k: int = 3):
    """Retrieves top_k context chunks for a given query."""
    retriever = get_retriever()
    results = retriever.search(query, top_k=top_k)
    return results

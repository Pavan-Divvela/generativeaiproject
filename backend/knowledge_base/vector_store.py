import math
import re
from typing import List, Dict, Any

def tokenize(text: str) -> List[str]:
    """Tokenizes text into lowercase alphanumeric words."""
    return re.findall(r'[a-zA-Z0-9]+', text.lower())

class VectorStore:
    """
    Lightweight, robust pure-Python BM25 / TF-IDF hybrid vector store.
    Provides fast, dependency-free semantic and keyword search.
    """
    def __init__(self):
        self.documents = []  # List of chunk dictionaries
        self.doc_freq = {}   # term -> number of documents containing term
        self.total_docs = 0
        self.avg_doc_len = 0.0

    def add_documents(self, docs: List[Dict[str, Any]]):
        """Adds a list of document chunks and builds index statistics."""
        self.documents = docs
        self.total_docs = len(docs)
        self.doc_freq = {}
        total_len = 0

        for doc in docs:
            tokens = set(tokenize(doc.get("content", "")))
            total_len += len(tokenize(doc.get("content", "")))
            for token in tokens:
                self.doc_freq[token] = self.doc_freq.get(token, 0) + 1

        self.avg_doc_len = (total_len / self.total_docs) if self.total_docs > 0 else 1.0

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Calculates BM25 relevance scores for the query across all documents.
        Returns top_k most relevant chunks.
        """
        if not self.documents:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return self.documents[:top_k]

        k1 = 1.5
        b = 0.75
        scores = []

        for idx, doc in enumerate(self.documents):
            doc_tokens = tokenize(doc.get("content", ""))
            doc_len = len(doc_tokens)
            doc_token_counts = {}
            for t in doc_tokens:
                doc_token_counts[t] = doc_token_counts.get(t, 0) + 1

            score = 0.0
            for qt in query_tokens:
                if qt in doc_token_counts:
                    freq = doc_token_counts[qt]
                    # Inverse Document Frequency (IDF)
                    df = self.doc_freq.get(qt, 0)
                    idf = math.log(1.0 + (self.total_docs - df + 0.5) / (df + 0.5))
                    # BM25 term weighting
                    tf = (freq * (k1 + 1.0)) / (freq + k1 * (1.0 - b + b * (doc_len / self.avg_doc_len)))
                    score += idf * tf

            # Title matching boost
            title_tokens = set(tokenize(doc.get("title", "")))
            for qt in query_tokens:
                if qt in title_tokens:
                    score += 2.0

            scores.append((score, idx))

        # Sort descending by score
        scores.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, idx in scores[:top_k]:
            doc_copy = dict(self.documents[idx])
            doc_copy["relevance_score"] = round(score, 4)
            results.append(doc_copy)

        return results

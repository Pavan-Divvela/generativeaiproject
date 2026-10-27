from knowledge_base.retriever import retrieve_context
from services.llm_service import synthesize_rag_response

def get_rag_chat_response(query: str):
    """
    Executes end-to-end RAG pipeline:
    1. Retrieve relevant knowledge chunks from vector store.
    2. Synthesize clear answer with domain guidelines or LLM.
    3. Generate dynamic follow-up suggestions based on intent.
    """
    if not query or not query.strip():
        return {
            "answer": "Please ask a question regarding Aadhaar, PAN card, or Indian Passport procedures.",
            "sources": [],
            "suggestions": [
                "How to link PAN with Aadhaar?",
                "What documents are needed for Tatkaal passport?",
                "How to resolve name mismatch between 10th marksheet and Aadhaar?",
                "What is Non-ECR passport status?"
            ]
        }

    # Retrieve context chunks
    chunks = retrieve_context(query, top_k=3)
    
    # Generate synthesized answer
    answer = synthesize_rag_response(query, chunks)

    # Format sources for transparency
    sources = []
    for c in chunks:
        sources.append({
            "id": c.get("id"),
            "title": c.get("title"),
            "document": c.get("document"),
            "score": c.get("relevance_score")
        })

    # Provide smart contextual follow-up suggestions
    q_lower = query.lower()
    if "pan" in q_lower or "link" in q_lower:
        suggestions = [
            "What if my name has initials on Aadhaar but not on PAN?",
            "How long does the ₹1,000 challan payment take to update?",
            "Can I apply for instant e-PAN if mobile is not linked?"
        ]
    elif "passport" in q_lower or "tatkaal" in q_lower:
        suggestions = [
            "What are the 3 documents required for Tatkaal passport?",
            "Can I use a rental agreement as address proof for passport?",
            "How does police verification work for passport?"
        ]
    elif "aadhaar" in q_lower or "update" in q_lower:
        suggestions = [
            "How many times can I change Date of Birth in Aadhaar?",
            "How to order an official Aadhaar PVC card?",
            "What is Masked Aadhaar and where is it accepted?"
        ]
    else:
        suggestions = [
            "In what order should I correct my documents?",
            "How to fix single name / blank surname on passport?",
            "What documents are acceptable as Proof of Date of Birth?"
        ]

    return {
        "answer": answer,
        "sources": sources,
        "suggestions": suggestions
    }

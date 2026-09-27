"""
Ties together vector similarity search and LLM answer generation for the
/chat endpoint.
"""
from typing import List, Optional

from app.rag.vector_store import similarity_search
from app.rag.qa_chain import generate_answer
from app.config import settings


def answer_question(question: str, document_ids: Optional[List[str]] = None) -> dict:
    retrieved = similarity_search(
        query=question,
        top_k=settings.TOP_K_RESULTS,
        document_ids=document_ids,
    )

    answer_text, found_context = generate_answer(question, retrieved)

    sources = [
        {
            "document_id": c["document_id"],
            "document_name": c["document_name"],
            "page": c["page"],
            "text": c["text"],
            "similarity_score": c["score"],
        }
        for c in retrieved
    ] if found_context else []

    return {
        "answer": answer_text,
        "sources": sources,
        "found_context": found_context,
    }

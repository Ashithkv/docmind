from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models.schemas import ChatRequest, ChatResponse
from app.services.chat_service import answer_question
from app.services import document_store

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question must not be empty.")

    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY is not configured on the server. Add it to .env and restart.",
        )

    docs = document_store.list_documents()
    ready_docs = [d for d in docs if d["status"] == "ready"]
    if not ready_docs:
        raise HTTPException(
            status_code=400,
            detail="No documents have been uploaded yet. Upload a PDF before asking questions.",
        )

    try:
        result = answer_question(question, document_ids=request.document_ids)
    except ValueError as e:
        # Raised by qa_chain.get_llm() if the API key is missing/misconfigured.
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM request failed: {e}")

    return ChatResponse(**result)

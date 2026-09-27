"""
Pydantic schemas used for API request/response validation.

Keeping these separate from the SQL/DB layer (there isn't one here — document
metadata lives in a small JSON-backed registry, see services/document_store.py)
keeps the API contract explicit and easy to read for anyone reviewing the code.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class DocumentInfo(BaseModel):
    """Metadata about a single uploaded document."""
    document_id: str
    filename: str
    num_pages: int
    num_chunks: int
    uploaded_at: str
    status: str  # "processing" | "ready" | "failed"
    error: Optional[str] = None


class UploadResponse(BaseModel):
    uploaded: List[DocumentInfo]
    failed: List[dict] = Field(default_factory=list)


class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]


class ChatRequest(BaseModel):
    question: str
    # Optional: restrict the search to specific document_ids. If empty/omitted,
    # search across all uploaded documents.
    document_ids: Optional[List[str]] = None


class SourceChunk(BaseModel):
    document_id: str
    document_name: str
    page: int
    text: str
    similarity_score: float


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceChunk]
    found_context: bool


class DeleteResponse(BaseModel):
    document_id: str
    deleted: bool
    message: str

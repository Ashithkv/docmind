import os
import uuid
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.config import settings
from app.models.schemas import (
    UploadResponse,
    DocumentInfo,
    DocumentListResponse,
    DeleteResponse,
)
from app.services.document_processor import process_uploaded_pdf
from app.services import document_store
from app.rag.vector_store import delete_document as delete_from_vector_store
from app.rag.pdf_loader import InvalidPDFError, EmptyPDFError

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=UploadResponse)
async def upload_documents(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files were provided.")

    uploaded: List[DocumentInfo] = []
    failed: List[dict] = []

    for upload_file in files:
        if not upload_file.filename.lower().endswith(".pdf"):
            failed.append(
                {"filename": upload_file.filename, "error": "Only PDF files are supported."}
            )
            continue

        contents = await upload_file.read()
        size_mb = len(contents) / (1024 * 1024)
        if size_mb > settings.MAX_FILE_SIZE_MB:
            failed.append(
                {
                    "filename": upload_file.filename,
                    "error": f"File exceeds max size of {settings.MAX_FILE_SIZE_MB}MB.",
                }
            )
            continue

        if len(contents) == 0:
            failed.append({"filename": upload_file.filename, "error": "File is empty."})
            continue

        temp_path = os.path.join(settings.UPLOAD_DIR, f"{uuid.uuid4()}.pdf")
        with open(temp_path, "wb") as f:
            f.write(contents)

        try:
            record = process_uploaded_pdf(temp_path, upload_file.filename)
            uploaded.append(DocumentInfo(**record))
        except (InvalidPDFError, EmptyPDFError) as e:
            failed.append({"filename": upload_file.filename, "error": str(e)})
        except Exception as e:
            failed.append({"filename": upload_file.filename, "error": f"Processing failed: {e}"})

    return UploadResponse(uploaded=uploaded, failed=failed)


@router.get("", response_model=DocumentListResponse)
async def list_documents():
    docs = document_store.list_documents()
    return DocumentListResponse(documents=[DocumentInfo(**d) for d in docs])


@router.delete("/{document_id}", response_model=DeleteResponse)
async def delete_document(document_id: str):
    record = document_store.get_document(document_id)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found.")

    deleted_chunks = delete_from_vector_store(document_id)
    document_store.delete_document(document_id)

    return DeleteResponse(
        document_id=document_id,
        deleted=True,
        message=f"Deleted document and {deleted_chunks} associated chunks.",
    )

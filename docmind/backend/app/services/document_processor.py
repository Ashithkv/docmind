"""
Orchestrates the full "upload a PDF" pipeline by wiring together the RAG
modules in app/rag/. This is the one place that calls, in order:

    pdf_loader.extract_pages()
    chunker.split_pages_into_chunks()
    vector_store.add_document_chunks()

and records the result in the document registry.
"""
import os
import uuid
from datetime import datetime, timezone

from app.rag.pdf_loader import extract_pages, InvalidPDFError, EmptyPDFError
from app.rag.chunker import split_pages_into_chunks
from app.rag.vector_store import add_document_chunks
from app.services import document_store
from app.config import settings


def process_uploaded_pdf(file_path: str, original_filename: str) -> dict:
    """
    Run the full pipeline for one uploaded PDF file already saved to disk.
    Returns the document record (dict) that was saved to the registry.
    Raises InvalidPDFError / EmptyPDFError on bad input.
    """
    document_id = str(uuid.uuid4())

    record = {
        "document_id": document_id,
        "filename": original_filename,
        "num_pages": 0,
        "num_chunks": 0,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "status": "processing",
        "error": None,
    }
    document_store.upsert_document(document_id, record)

    try:
        pages = extract_pages(file_path)
        chunks = split_pages_into_chunks(pages)

        if not chunks:
            raise EmptyPDFError("No text chunks could be produced from this PDF.")

        add_document_chunks(document_id, original_filename, chunks)

        record.update(
            {
                "num_pages": len(pages),
                "num_chunks": len(chunks),
                "status": "ready",
            }
        )
        document_store.upsert_document(document_id, record)
        return record

    except (InvalidPDFError, EmptyPDFError) as e:
        record.update({"status": "failed", "error": str(e)})
        document_store.upsert_document(document_id, record)
        raise
    except Exception as e:
        record.update({"status": "failed", "error": f"Unexpected error: {e}"})
        document_store.upsert_document(document_id, record)
        raise
    finally:
        # Clean up the temporary uploaded file regardless of outcome.
        if os.path.exists(file_path):
            os.remove(file_path)

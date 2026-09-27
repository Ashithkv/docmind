"""
Step 1 of the RAG pipeline: PDF -> text.

We extract text page-by-page (not the whole PDF as one blob) because we want
to keep track of which page every chunk came from later, for citations.
"""
from dataclasses import dataclass
from typing import List
from pypdf import PdfReader
from pypdf.errors import PdfReadError


@dataclass
class PageText:
    page_number: int  # 1-indexed, human-friendly
    text: str


class InvalidPDFError(Exception):
    """Raised when a file is not a readable PDF."""
    pass


class EmptyPDFError(Exception):
    """Raised when a PDF has no extractable text (e.g. scanned images only)."""
    pass


def extract_pages(file_path: str) -> List[PageText]:
    """
    Read a PDF file from disk and return a list of PageText objects,
    one per page, skipping pages with no extractable text.
    """
    try:
        reader = PdfReader(file_path)
    except PdfReadError as e:
        raise InvalidPDFError(f"Could not read PDF file: {e}")
    except Exception as e:
        raise InvalidPDFError(f"Unexpected error opening PDF: {e}")

    if len(reader.pages) == 0:
        raise EmptyPDFError("PDF has no pages.")

    pages: List[PageText] = []
    for i, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        text = text.strip()
        if text:
            pages.append(PageText(page_number=i + 1, text=text))

    if not pages:
        raise EmptyPDFError(
            "No extractable text found in this PDF. It may be a scanned "
            "image-only document that requires OCR (not supported here)."
        )

    return pages

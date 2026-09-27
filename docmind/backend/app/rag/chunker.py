"""
Step 2 of the RAG pipeline: text -> chunks.

We use LangChain's RecursiveCharacterTextSplitter, which tries to split on
paragraph breaks first, then sentences, then words — only falling back to a
hard character cut if nothing else fits. This keeps chunks semantically
coherent instead of cutting sentences in half.

Each chunk keeps a reference to the page it came from so citations work even
though a single page can produce multiple chunks, and a long paragraph could
in theory span two pages (we accept the small edge case of attributing that
chunk to the page it started on).
"""
from dataclasses import dataclass
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.rag.pdf_loader import PageText
from app.config import settings


@dataclass
class Chunk:
    text: str
    page_number: int
    chunk_index: int  # index within the whole document, used for the chunk id


def split_pages_into_chunks(pages: List[PageText]) -> List[Chunk]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks: List[Chunk] = []
    running_index = 0
    for page in pages:
        page_chunks = splitter.split_text(page.text)
        for text in page_chunks:
            chunks.append(
                Chunk(text=text, page_number=page.page_number, chunk_index=running_index)
            )
            running_index += 1

    return chunks

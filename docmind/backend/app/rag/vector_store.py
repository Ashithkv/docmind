"""
Steps 3 & 4 of the RAG pipeline: chunks -> embeddings -> ChromaDB storage,
and later, query -> embedding -> similarity search.

Embeddings are generated locally with sentence-transformers (no API key or
network call needed for this part — only the final answer-generation step
calls out to the LLM). This keeps the "search" half of RAG fast, free, and
fully working out of the box.
"""
from typing import List, Optional
import chromadb
from sentence_transformers import SentenceTransformer

from app.config import settings
from app.rag.chunker import Chunk

_embedding_model: Optional[SentenceTransformer] = None
_chroma_client = None
_collection = None


def get_embedding_model() -> SentenceTransformer:
    """Lazily load the embedding model once and reuse it (it's not tiny)."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _embedding_model


def get_collection():
    """Lazily create/connect to the persistent ChromaDB collection."""
    global _chroma_client, _collection
    if _collection is None:
        _chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_DB_PATH,
            settings=chromadb.Settings(anonymized_telemetry=False),
        )
        _collection = _chroma_client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def embed_texts(texts: List[str]) -> List[List[float]]:
    model = get_embedding_model()
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    return embeddings.tolist()


def add_document_chunks(
    document_id: str, document_name: str, chunks: List[Chunk]
) -> None:
    """Embed a document's chunks and store them in ChromaDB with metadata."""
    if not chunks:
        return

    collection = get_collection()
    texts = [c.text for c in chunks]
    embeddings = embed_texts(texts)

    ids = [f"{document_id}_chunk_{c.chunk_index}" for c in chunks]
    metadatas = [
        {
            "document_id": document_id,
            "document_name": document_name,
            "page": c.page_number,
            "chunk_index": c.chunk_index,
        }
        for c in chunks
    ]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )


def similarity_search(
    query: str, top_k: int, document_ids: Optional[List[str]] = None
):
    """
    Embed the query and search ChromaDB for the most similar chunks.
    Optionally restrict the search to a subset of document_ids.

    Returns a list of dicts: {text, document_id, document_name, page, score}
    """
    collection = get_collection()
    if collection.count() == 0:
        return []

    query_embedding = embed_texts([query])[0]

    where_filter = None
    if document_ids:
        if len(document_ids) == 1:
            where_filter = {"document_id": document_ids[0]}
        else:
            where_filter = {"document_id": {"$in": document_ids}}

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        where=where_filter,
    )

    output = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for text, meta, distance in zip(docs, metas, distances):
        # ChromaDB with cosine space returns a distance in [0, 2]; convert to
        # an intuitive similarity score in roughly [0, 1] for display.
        similarity = max(0.0, 1 - (distance / 2))
        output.append(
            {
                "text": text,
                "document_id": meta["document_id"],
                "document_name": meta["document_name"],
                "page": meta["page"],
                "score": round(similarity, 4),
            }
        )

    return output


def delete_document(document_id: str) -> int:
    """Delete all chunks belonging to a document. Returns number deleted."""
    collection = get_collection()
    existing = collection.get(where={"document_id": document_id})
    ids = existing.get("ids", [])
    if ids:
        collection.delete(ids=ids)
    return len(ids)

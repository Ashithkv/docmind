"""
A tiny persistent registry for document metadata (filename, page count,
status, etc). We deliberately do NOT bring in a full SQL database for this
portfolio project — a single JSON file is enough to track "which documents
have been uploaded" and keeps the project easy to run with zero setup.

The actual document *content* (chunks + embeddings) lives in ChromaDB; this
store only tracks metadata used to list/delete documents in the UI.
"""
import json
import os
import threading
from typing import List, Optional, Dict

from app.config import settings

_REGISTRY_PATH = os.path.join(settings.CHROMA_DB_PATH, "document_registry.json")
_lock = threading.Lock()


def _load() -> Dict[str, dict]:
    if not os.path.exists(_REGISTRY_PATH):
        return {}
    with open(_REGISTRY_PATH, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _save(data: Dict[str, dict]) -> None:
    with open(_REGISTRY_PATH, "w") as f:
        json.dump(data, f, indent=2)


def upsert_document(document_id: str, record: dict) -> None:
    with _lock:
        data = _load()
        data[document_id] = record
        _save(data)


def get_document(document_id: str) -> Optional[dict]:
    with _lock:
        data = _load()
        return data.get(document_id)


def list_documents() -> List[dict]:
    with _lock:
        data = _load()
        return list(data.values())


def delete_document(document_id: str) -> bool:
    with _lock:
        data = _load()
        if document_id in data:
            del data[document_id]
            _save(data)
            return True
        return False

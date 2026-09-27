"""
Application configuration.

All configurable values are loaded from environment variables (see .env.example).
Nothing sensitive is hardcoded here.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # OpenAI / LLM settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")

    # Embedding model (runs locally via sentence-transformers, no API key needed)
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # ChromaDB
    CHROMA_DB_PATH: str = os.getenv("CHROMA_DB_PATH", "./chroma_data")
    CHROMA_COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "docmind_documents")

    # Chunking
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "150"))

    # Retrieval
    TOP_K_RESULTS: int = int(os.getenv("TOP_K_RESULTS", "4"))

    # Uploads
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "20"))


settings = Settings()

# Make sure required directories exist on startup.
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.CHROMA_DB_PATH, exist_ok=True)

# DocMind — RAG Document Q&A

DocMind, fully working Retrieval-Augmented Generation (RAG) application.
Upload PDF documents, ask natural-language questions about them, and get answers
grounded in the documents themselves — with page-level citations, and a clear
"not found" response when the answer isn't in your documents.

Built as a portfolio project to demonstrate a real, end-to-end RAG pipeline: PDF
parsing, chunking, embeddings, vector search, and LLM answer generation, wired
together without unnecessary layers.

---

## 1. Overview

- **Problem it solves:** "I have a pile of PDFs and don't want to read all of them
  to find one answer." DocMind lets you upload documents and ask questions in
  plain English, with every answer traceable back to the exact page it came from.
- **Scope:** Intentionally small. No auth, no multi-tenant accounts, no
  Kubernetes/Redis/Celery. One FastAPI backend, one React frontend, one vector
  database. Everything that's advertised actually works end to end.

## 2. Architecture

```
┌─────────────┐        HTTP/JSON        ┌───────────────────┐
│   React UI   │  ───────────────────▶  │   FastAPI backend  │
│ (Vite, JS)   │  ◀───────────────────  │                    │
└─────────────┘                         └─────────┬──────────┘
                                                    │
                          ┌─────────────────────────┼─────────────────────────┐
                          │                         │                         │
                   PDF upload path            Question path             Metadata
                          │                         │                         │
                 ┌────────▼────────┐       ┌────────▼────────┐      ┌─────────▼────────┐
                 │  pypdf: extract  │       │ sentence-       │      │ document_registry │
                 │  text per page   │       │ transformers:   │      │   .json (local)   │
                 └────────┬────────┘       │ embed question  │      └────────────────────┘
                          │                └────────┬────────┘
                 ┌────────▼────────┐                │
                 │ LangChain text  │                │
                 │ splitter: chunk │                │
                 └────────┬────────┘                │
                          │                          │
                 ┌────────▼────────┐        ┌────────▼────────┐
                 │ sentence-       │        │  ChromaDB        │
                 │ transformers:   │───────▶│  similarity      │
                 │ embed chunks    │        │  search (top-k)  │
                 └─────────────────┘        └────────┬────────┘
                                                       │
                                              ┌────────▼────────┐
                                              │ LangChain +      │
                                              │ OpenAI: generate │
                                              │ grounded answer  │
                                              └────────┬────────┘
                                                        │
                                              answer + page citations
```

**Backend layout:**

```
backend/
  app/
    main.py              FastAPI app, CORS, global error handler
    config.py             Loads settings from .env
    routes/
      documents.py        POST /documents/upload, GET /documents, DELETE /documents/{id}
      chat.py              POST /chat
    services/
      document_processor.py  Orchestrates the upload pipeline
      document_store.py      JSON-backed document metadata registry
      chat_service.py        Orchestrates retrieval + answer generation
    rag/
      pdf_loader.py       PDF -> per-page text (pypdf)
      chunker.py           Text -> chunks (LangChain RecursiveCharacterTextSplitter)
      vector_store.py     Chunks -> embeddings -> ChromaDB, + similarity search
      qa_chain.py          Retrieved context -> LLM prompt -> grounded answer
    models/
      schemas.py           Pydantic request/response models
  requirements.txt
  .env.example
```

The RAG pipeline is intentionally **not** hidden behind one abstraction — each
step (`pdf_loader` → `chunker` → `vector_store` → `qa_chain`) is its own small,
readable module, wired together explicitly in `document_processor.py` and
`chat_service.py`. This is deliberate: it makes the flow easy to trace and
explain, which matters both for maintenance and for interview walkthroughs.

## 3. Features

- Upload one or many PDF files at once
- Per-page text extraction (page numbers are preserved for citations)
- Chunking with configurable size/overlap
- Local embeddings via `sentence-transformers` (no API key needed for this step)
- Persistent vector storage in ChromaDB
- Question answering grounded strictly in retrieved context — the LLM is
  instructed to say so explicitly when the answer isn't in the documents,
  rather than guessing
- Every answer includes citations: document name, page number, and the
  matching excerpt
- Document management: list uploaded documents (with status/page/chunk counts),
  delete a document (which also removes its vectors from ChromaDB)
- Clean React chat UI: upload panel, document list, chat window, inline citations
- Real, structured error handling for invalid/empty PDFs, missing API keys, no
  documents uploaded, no relevant context found, and LLM/API failures

## 4. Technologies

| Layer | Tech |
|---|---|
| Backend framework | FastAPI |
| RAG orchestration | LangChain (`langchain-openai`, `langchain-text-splitters`) |
| Vector database | ChromaDB (persistent, local) |
| Embeddings | `sentence-transformers` (`all-MiniLM-L6-v2`, local, free) |
| LLM | OpenAI chat models, via LangChain — configurable through `.env` |
| PDF parsing | `pypdf` |
| Frontend | React 18 + Vite (JavaScript, no TypeScript) |
| HTTP client | axios |
| Styling | Plain CSS |

## 5. Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- An OpenAI API key ([platform.openai.com](https://platform.openai.com/api-keys))

### Backend setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set OPENAI_API_KEY
```

### Frontend setup

```bash
cd frontend
npm install
```

## 6. Environment variables

Set these in `backend/.env` (see `backend/.env.example`):

| Variable | Description | Default |
|---|---|---|
| `OPENAI_API_KEY` | Your OpenAI API key. Required for `/chat`. | *(empty)* |
| `LLM_MODEL` | Any OpenAI chat model | `gpt-4o-mini` |
| `EMBEDDING_MODEL` | sentence-transformers model name | `all-MiniLM-L6-v2` |
| `CHROMA_DB_PATH` | Where ChromaDB persists data on disk | `./chroma_data` |
| `CHROMA_COLLECTION_NAME` | ChromaDB collection name | `docmind_documents` |
| `CHUNK_SIZE` | Characters per chunk | `1000` |
| `CHUNK_OVERLAP` | Character overlap between chunks | `150` |
| `TOP_K_RESULTS` | Chunks retrieved per question | `4` |
| `UPLOAD_DIR` | Temp storage for uploaded files during processing | `./uploads` |
| `MAX_FILE_SIZE_MB` | Max upload size per file | `20` |

The frontend optionally reads `VITE_API_URL` (defaults to `http://localhost:8000`)
if you need to point it at a non-default backend URL — create `frontend/.env`
with `VITE_API_URL=http://your-backend-host:8000` if so.

## 7. How to run

**Backend** (from `backend/`, with venv active):
```bash
uvicorn app.main:app --reload --port 8000
```
API docs (auto-generated by FastAPI) are then at `http://localhost:8000/docs`.

**Frontend** (from `frontend/`, in a separate terminal):
```bash
npm run dev
```
The app opens at `http://localhost:5173`.

> **Note on first run:** the first time you upload a document, the embedding
> model (`all-MiniLM-L6-v2`, ~80MB) is downloaded automatically from Hugging
> Face and cached locally. This requires internet access once; after that it
> runs fully offline.

## 8. Example usage

1. Open `http://localhost:5173`.
2. Drag a PDF (e.g. an employee handbook) into the upload panel.
3. Once it shows "Ready", type a question, e.g. *"How many days of paid leave
   do employees get?"*
4. DocMind returns an answer plus a **Sources** section showing exactly which
   document and page(s) it came from, with the matching excerpt.
5. Ask something not covered in the document — DocMind will say the
   information wasn't found, instead of guessing.

You can also drive the API directly:

```bash
curl -X POST http://localhost:8000/documents/upload \
  -F "files=@employee_policy.pdf"

curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the return policy?"}'
```

## 9. RAG flow, step by step

```
PDF file
  │  pypdf.PdfReader — extract text per page, skip empty pages
  ▼
Per-page text (with page numbers preserved)
  │  LangChain RecursiveCharacterTextSplitter
  │  (tries paragraph → sentence → word boundaries before a hard cut)
  ▼
Chunks (~1000 chars, 150 overlap), each tagged with its source page
  │  sentence-transformers .encode()
  ▼
Embedding vectors
  │  ChromaDB collection.add(ids, embeddings, documents, metadatas)
  ▼
Persisted in ChromaDB (cosine similarity index)

── at question time ──

User question
  │  sentence-transformers .encode()
  ▼
Query embedding
  │  ChromaDB collection.query() — cosine similarity, top-k
  ▼
Retrieved chunks (with document name + page metadata)
  │  Prompt template: numbered excerpts + strict "context-only" instructions
  ▼
LangChain → OpenAI chat model
  │  If the model can't answer from context, it returns a fixed marker,
  │  which the backend converts into a clear "not found" response.
  ▼
Answer + citations (document, page, excerpt) → returned to the UI
```

## 10. Design notes / trade-offs

- **Why ChromaDB, not Pinecone/Weaviate/pgvector:** it's embedded and local —
  zero infrastructure to stand up, persists to disk, and is more than
  sufficient at this scale. Swapping it for a hosted vector DB later would
  only mean changing `app/rag/vector_store.py`.
- **Why local embeddings instead of OpenAI embeddings:** keeps the "search"
  half of the app free and fast, and only spends API calls/tokens on the part
  that actually needs a large model — generating the final answer.
- **Why a JSON file for document metadata, not SQL:** the only metadata being
  tracked is "which documents exist and their status" — small, low-write-volume
  data that doesn't need a relational database for a project this size. Swapping
  in SQLite/Postgres later would only touch `document_store.py`.
- **Why explicit modules instead of a LangChain `RetrievalQA` chain:** so every
  step of the pipeline is visible and independently testable, which matters
  both for debugging and for being able to explain the system clearly.

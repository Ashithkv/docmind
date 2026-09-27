from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routes import documents, chat

app = FastAPI(
    title="DocMind API",
    description="RAG-powered document Q&A backend (FastAPI + LangChain + ChromaDB).",
    version="1.0.0",
)

# Allow the React dev server (and any origin, for simplicity in this demo) to
# call the API directly from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(chat.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )


@app.get("/")
async def root():
    return {"status": "ok", "service": "DocMind API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

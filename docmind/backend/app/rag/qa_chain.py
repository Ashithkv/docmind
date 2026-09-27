"""
Step 5 of the RAG pipeline: retrieved context -> LLM -> grounded answer.

This is deliberately a plain prompt-template + LLM call rather than a deep
LangChain abstraction (no RetrievalQA chain, no black-box agent) so the
whole flow stays readable and easy to explain line-by-line in an interview.
"""
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.config import settings

NOT_FOUND_MARKER = "NOT_FOUND_IN_DOCUMENTS"

SYSTEM_PROMPT = f"""You are DocMind, a document question-answering assistant.

Rules you must follow strictly:
1. Answer the user's question using ONLY the context excerpts provided below.
2. Do NOT use any outside knowledge, even if you know the answer.
3. If the context does not contain enough information to answer the question,
   respond with exactly: {NOT_FOUND_MARKER}
   Do not guess or make up an answer.
4. Be concise and directly answer the question first, then add supporting
   detail if useful.
5. When you state a fact, you may reference which excerpt it came from using
   its number, e.g. "[1]", but do not fabricate excerpt numbers that were not
   provided.
"""

USER_PROMPT_TEMPLATE = """Context excerpts:
{context}

Question: {question}

Answer:"""


def _format_context(chunks: List[dict]) -> str:
    parts = []
    for i, c in enumerate(chunks, start=1):
        parts.append(
            f"[{i}] (Source: {c['document_name']}, Page {c['page']})\n{c['text']}"
        )
    return "\n\n".join(parts)


def get_llm() -> ChatOpenAI:
    if not settings.OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY is not set. Add it to your .env file to enable "
            "question answering."
        )
    return ChatOpenAI(
        model=settings.LLM_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=0,
    )


def generate_answer(question: str, retrieved_chunks: List[dict]) -> tuple[str, bool]:
    """
    Given a question and the retrieved context chunks, call the LLM and
    return (answer_text, found_context: bool).
    """
    if not retrieved_chunks:
        return (
            "I couldn't find any relevant information in the uploaded documents "
            "to answer this question.",
            False,
        )

    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("user", USER_PROMPT_TEMPLATE),
        ]
    )
    chain = prompt | llm | StrOutputParser()

    context_str = _format_context(retrieved_chunks)
    answer = chain.invoke({"context": context_str, "question": question})
    answer = answer.strip()

    if NOT_FOUND_MARKER in answer:
        return (
            "The information needed to answer this question was not found in "
            "the uploaded documents.",
            False,
        )

    return answer, True

# backend/app/routers/rag.py

"""
RAG router: Defines the API endpoint for Retrieval-Augmented Generation (RAG).

This module provides a FastAPI router with a single POST endpoint `/query` that:
1. Retrieves relevant document fragments using the retriever service.
2. Checks if the query is within scope based on a distance threshold.
3. Generates an answer via the LLM using only the snippet texts.
4. Stores the interaction in the database, with references derived from the fragments.
"""

import os
import sys
import logging

# 0) Add project root to sys.path for absolute imports
PROJECT_ROOT = os.path.abspath(
    os.path.join(__file__, os.pardir, os.pardir, os.pardir, os.pardir)
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from backend.app.services.retriever_openai import retrieve_fragments_openai
from backend.app.services.llm_gemini import generate_answer_with_references_gemini
from backend.app.db import add_chat_entry

router = APIRouter(tags=["RAG"])
logger = logging.getLogger("rag_router")


class RAGQuery(BaseModel):
    user_id: str
    query: str


class RAGResponse(BaseModel):
    answer: str
    references: List[str]


# If the minimum distance exceeds this, we consider the query out of scope
DISTANCE_THRESHOLD = 1.5


@router.post("/query", response_model=RAGResponse)
async def rag_query(payload: RAGQuery):
    # 1) Retrieve top-4 fragments: each is (text, distance, source)
    fragments = retrieve_fragments_openai(payload.query, k=4)
    if not fragments:
        # KB not indexed or empty
        raise HTTPException(404, "Knowledge base not indexed or contains no documents")

    # 2) Detect out-of-scope by minimum distance
    distances = [dist for (_, dist, _) in fragments]
    if min(distances) > DISTANCE_THRESHOLD:
        answer = "Sorry, I have no information on that."
        # Persist the “no info” interaction
        add_chat_entry(payload.user_id, payload.query, answer, [])
        return RAGResponse(answer=answer, references=[])

    # 3) Prepare only snippet texts for the LLM
    snippet_texts = [text for (text, _, _) in fragments]

    # 4) Generate answer via Gemini (only 'answer' key is used)
    rag_output = generate_answer_with_references_gemini(snippet_texts, payload.query)
    answer_text = rag_output.get("answer", "").strip()

    # 5) Build references from fragment sources, preserving order and dedup
    references = list(dict.fromkeys([src for (_, _, src) in fragments]))

    # 6) Persist the chat entry
    add_chat_entry(payload.user_id, payload.query, answer_text, references)

    # 7) Log for debugging
    logger.info(
        f"[RAG] user={payload.user_id} query='{payload.query}' "
        f"-> answer_length={len(answer_text)} refs={references}"
    )

    return RAGResponse(answer=answer_text, references=references)

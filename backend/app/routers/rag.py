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

from fastapi import APIRouter
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

DISTANCE_THRESHOLD = 1.25

@router.post("/query", response_model=RAGResponse)
async def rag_query(payload: RAGQuery):
    logger.info(f"→ RAG query start: user={payload.user_id!r} query={payload.query!r}")

    # 1) Retrieve fragments; if none, send out-of-scope fallback
    fragments = retrieve_fragments_openai(payload.query, k=3)
    logger.debug(f"Fragments received: {[(round(d,3), src) for _, d, src in fragments]}")

    if not fragments:
        answer = "Sorry, I have no information on that."
        logger.info("Out-of-scope: no relevant fragments returned, sending fallback answer")
        add_chat_entry(payload.user_id, payload.query, answer, [])
        return RAGResponse(answer=answer, references=[])

    # 2) Out-of-scope detection by distance
    distances = [dist for (_, dist, _) in fragments]
    if min(distances) > DISTANCE_THRESHOLD:
        answer = "Sorry, I have no information on that."
        logger.info(f"Out-of-scope (min_distance={min(distances):.3f}), sending fallback answer")
        add_chat_entry(payload.user_id, payload.query, answer, [])
        return RAGResponse(answer=answer, references=[])

    # 3) Prepare snippets for LLM
    snippet_texts = [text for (text, _, _) in fragments]
    logger.debug(f"Passing {len(snippet_texts)} snippets to LLM")

    # 4) Call Gemini to generate answer
    logger.info("Invoking LLM (Gemini) for response generation")
    rag_output = generate_answer_with_references_gemini(snippet_texts, payload.query)
    answer_text = rag_output.get("answer", "").strip()
    logger.debug(f"LLM answer (len={len(answer_text)}): {answer_text!r}")

    # 5) Build and dedupe references
    references = list(dict.fromkeys(src for (_, _, src) in fragments))
    logger.debug(f"References extracted: {references}")

    # 6) Persist interaction
    add_chat_entry(payload.user_id, payload.query, answer_text, references)
    logger.info("Chat entry persisted to database")

    logger.info("← RAG query end")
    return RAGResponse(answer=answer_text, references=references)

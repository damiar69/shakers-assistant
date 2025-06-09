"""
RAG router: Defines the API endpoint for Retrieval-Augmented Generation (RAG).

This module provides a FastAPI router with a single POST endpoint `/query` that:
1. Retrieves relevant document fragments using the retriever service.
2. Checks if the query is within scope based on a distance threshold.
3. Generates an answer with citations via an LLM.
4. Stores the interaction in the database.
"""

import os
import sys

# ────────────────────────────────────────────────────────────────────────────
# 0) Add project root (shakers-case-study) to sys.path
# ────────────────────────────────────────────────────────────────────────────
# This file is located at: shakers-case-study/backend/app/routers/rag.py
# Ascend four levels to reach project root
PROJECT_ROOT = os.path.abspath(
    os.path.join(__file__, os.pardir, os.pardir, os.pardir, os.pardir)
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ────────────────────────────────────────────────────────────────────────────
# 1) Standard imports
# ────────────────────────────────────────────────────────────────────────────
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

# RAG services
from backend.app.services.retriever_openai import retrieve_fragments_openai
from backend.app.services.llm_gemini import generate_answer_with_references_gemini
from backend.app.db import add_chat_entry

# FastAPI router setup
router = APIRouter(tags=["RAG"])


class RAGQuery(BaseModel):
    user_id: str  # Unique identifier for the user
    query: str  # User's question text


class RAGResponse(BaseModel):
    answer: str
    references: List[str]


# Distance threshold: if the minimum similarity distance exceeds this value,
# the query is considered out-of-scope
DISTANCE_THRESHOLD = 1.5


@router.post("/query", response_model=RAGResponse)
async def rag_query(payload: RAGQuery):
    """
    Handle RAG query:
    1) Retrieve top-k document fragments (default k=4).
    2) If the smallest distance > threshold, return an out-of-scope message.
    3) Otherwise, generate an answer with citations via Gemini.
    4) Store the conversation entry in the database.
    """
    # 1) Fetch top-k fragments: each tuple = (text, distance, source)
    fragments = retrieve_fragments_openai(payload.query, k=4)
    if not fragments:
        # No fragments found: KB not indexed or is empty
        raise HTTPException(
            status_code=404,
            detail="Knowledge base not indexed or contains no documents",
        )

    # 2) Compute minimum distance to detect out-of-scope queries
    distances = [score for (_, score, _) in fragments]
    min_distance = min(distances)
    if min_distance > DISTANCE_THRESHOLD:
        return RAGResponse(
            answer="Sorry, I have no information on that.", references=[]
        )

    # 3) Prepare fragments for the LLM: list of dicts
    fragments_payload = [
        {"text": text, "score": score, "source": source}
        for text, score, source in fragments
    ]

    # Call the LLM service to generate the answer and references
    rag_output = generate_answer_with_references_gemini(
        fragments_payload, payload.query
    )

    # Remove duplicate references while preserving order
    unique_refs = list(dict.fromkeys(rag_output.get("references", [])))

    # 4) Log the interaction in the database
    add_chat_entry(
        user_id=payload.user_id,
        question=payload.query,
        answer=rag_output.get("answer", ""),
        references=unique_refs,
    )

    # 5) Debug output
    print(f"[RAG] Query: {payload.query}")
    print(f"[RAG] Retrieved fragments (text, score, source): {fragments}")
    print(f"[RAG] References returned: {unique_refs}")

    return RAGResponse(answer=rag_output.get("answer", ""), references=unique_refs)

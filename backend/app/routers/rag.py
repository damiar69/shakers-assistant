# backend/app/routers/rag.py

import os
import sys

# ────────────────────────────────────────────────────────────────────────────
# 0) ADD THE PROJECT ROOT FOLDER (shakers-case-study) TO sys.path
# ────────────────────────────────────────────────────────────────────────────
# This file is located at: shakers-case-study/backend/app/routers/rag.py
# We go up FOUR levels to reach shakers-case-study/
PROJECT_ROOT = os.path.abspath(
    os.path.join(__file__, os.pardir, os.pardir, os.pardir, os.pardir)
)
# Now PROJECT_ROOT points to: C:\Users\ddol\Desktop\shakers-case-study

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ────────────────────────────────────────────────────────────────────────────
# 1) ROUTER IMPORTS
# ────────────────────────────────────────────────────────────────────────────
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

# Import service-layer functions
from backend.app.services.retriever_openai import retrieve_fragments_openai
from backend.app.services.llm_gemini import generate_answer_with_references_gemini
from backend.app.db import add_chat_entry


# ────────────────────────────────────────────────────────────────────────────
# 2) ROUTER CONFIGURATION
# ────────────────────────────────────────────────────────────────────────────
router = APIRouter(tags=["RAG"])


class RAGQuery(BaseModel):
    user_id: str  # Could be used later for personalized recommendations
    query: str


class RAGResponse(BaseModel):
    answer: str
    references: List[str]


DISTANCE_THRESHOLD = 1.5


@router.post("/query", response_model=RAGResponse)
async def rag_query(payload: RAGQuery):
    """
    1) Retrieve the closest fragments (k=3).
    2) If the minimum distance exceeds the threshold, return “out of scope.”
    3) Otherwise, call Gemini to generate the answer and return {answer, references}.
    """
    # 1) Retrieve the top-3 fragments
    frags = retrieve_fragments_openai(payload.query, k=4)
    if not frags:
        # If no fragments are found (empty index or error), return 404
        raise HTTPException(
            status_code=404, detail="Knowledge base not indexed or empty"
        )

    # 2) Calculate minimum distance (Chroma returns “distance,” not “similarity”)
    distances = [score for (_, score, _) in frags]
    min_dist = min(distances)

    if min_dist > DISTANCE_THRESHOLD:
        # Out of scope: return a message without references
        return RAGResponse(
            answer="Sorry, I have no information on that.", references=[]
        )

    # 3) Convert the fragments into dictionaries for Gemini
    frags_dict = [{"text": t, "score": s, "source": src} for (t, s, src) in frags]

    # 4) Generate answer and references using Gemini
    rag_res = generate_answer_with_references_gemini(frags_dict, payload.query)
    # Deduplicate references
    refs = list(dict.fromkeys(rag_res["references"]))

    # See on terminal what we are doing
    print(f"[RAG] query: {payload.query} \n")
    print(f"[RAG] top fragments: {frags} \n")
    print(f"[RAG] references sent back: {refs}")

    return RAGResponse(answer=rag_res["answer"], references=refs)

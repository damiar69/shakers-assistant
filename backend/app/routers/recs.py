"""
Recommendations router module for personalized resource suggestions.

1. Defines clear Pydantic models for request/response and leverages FastAPI’s validation.
2. Retrieves user history from the database and transforms it into the required format.
3. Integrates the recommend_resources service combining user profile and query.
4. Structured logging at INFO and ERROR levels for traceability.
5. Error handling with HTTPException for robust API responses.
"""

import os
import sys
import logging
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.db import get_user_history
from backend.app.services.recommendations import recommend_resources

router = APIRouter(tags=["Recommendations"])
logger = logging.getLogger("recs_router")


# ─────────────────────────────────────────────────────────────────────────────
# Request and response models
# ─────────────────────────────────────────────────────────────────────────────
class RecsRequest(BaseModel):
    user_id: str
    current_query: str


class SingleRec(BaseModel):
    doc: str
    reason: str


class RecsResponse(BaseModel):
    recommendations: List[SingleRec]


# ─────────────────────────────────────────────────────────────────────────────
# POST /recs/personalized endpoint
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/personalized", response_model=RecsResponse)
async def personalized_recs(payload: RecsRequest):
    logger.info(
        f"Generating recommendations for user={payload.user_id!r}, query={payload.current_query!r}"
    )

    # 1) Retrieve full chat history for the user
    chat_entries = get_user_history(payload.user_id)

    # 2) Format history for recommendation service
    history_list = []
    for row in chat_entries:
        refs_list = row.references.split(",") if row.references else []
        history_list.append({"q": row.question, "a": row.answer, "refs": refs_list})

    # 3) Generate recommendations combining profile + current query
    try:
        recs = recommend_resources(
            chat_history=history_list,
            current_query=payload.current_query,
            k=3,
            alpha=0.6,
        )
    except Exception as e:
        logger.error(f"Recommendation generation failed: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to generate recommendations"
        )

    logger.info(f"Returning {len(recs)} recommendations")
    return RecsResponse(recommendations=recs)

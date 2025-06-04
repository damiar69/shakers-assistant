# backend/app/routers/recs.py

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
# IMPORTS NORMALES
# ────────────────────────────────────────────────────────────────────────────
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict

# Importar la función que lee el historial desde SQLite
from backend.app.db import get_user_history

# Importar el módulo de recomendaciones basado en embeddings
from backend.app.services.recommendations import recommend_resources

router = APIRouter(tags=["Recommendations"])


class RecsRequest(BaseModel):
    user_id: str
    current_query: str  # actualmente no se usa dentro de la lógica


class SingleRec(BaseModel):
    doc: str
    reason: str


class RecsResponse(BaseModel):
    recommendations: List[SingleRec]


@router.post("/personalized", response_model=RecsResponse)
async def personalized_recs(payload: RecsRequest):
    user_id = payload.user_id

    # 1) Leer historial real de SQLite
    chat_entries = get_user_history(user_id)

    # 2) Convertir cada fila ChatEntry a dict con lista de refs
    history_list = []
    for row in chat_entries:
        refs_list = row.references.split(",") if row.references else []
        history_list.append({"q": row.question, "a": row.answer, "refs": refs_list})

    # 3) Generar recomendaciones usando embeddings
    recs_raw = recommend_resources(history_list, k=3)

    # 4) Formatear la salida para que encaje con SingleRec
    out = [{"doc": r["doc"], "reason": r["reason"]} for r in recs_raw]
    return RecsResponse(recommendations=out)

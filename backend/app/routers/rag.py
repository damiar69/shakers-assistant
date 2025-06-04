# backend/app/routers/rag.py

import os
import sys

# ────────────────────────────────────────────────────────────────────────────
# 0) AÑADIMOS LA CARPETA RAÍZ (shakers-case-study) A sys.path
# ────────────────────────────────────────────────────────────────────────────
# Este archivo está en: shakers-case-study/backend/app/routers/rag.py
# Subimos CUATRO niveles para llegar a shakers-case-study/
PROJECT_ROOT = os.path.abspath(
    os.path.join(__file__, os.pardir, os.pardir, os.pardir, os.pardir)
)
# Ahora PROJECT_ROOT apunta a: C:\Users\ddol\Desktop\shakers-case-study

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ────────────────────────────────────────────────────────────────────────────
# 1) IMPORTS DEL ROUTER
# ────────────────────────────────────────────────────────────────────────────
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

# Importamos las funciones de la capa de servicios
from backend.app.services.retriever_openai import retrieve_fragments_openai
from backend.app.services.llm_gemini import generate_answer_with_references_gemini

# ────────────────────────────────────────────────────────────────────────────
# 2) CONFIGURACIÓN DEL ROUTER
# ────────────────────────────────────────────────────────────────────────────
router = APIRouter(tags=["RAG"])


class RAGQuery(BaseModel):
    user_id: str  # Podrías usarlo luego para recomendaciones personalizadas
    query: str


class RAGResponse(BaseModel):
    answer: str
    references: List[str]


UMBRAL_DISTANCIA = 1.0


@router.post("/query", response_model=RAGResponse)
async def rag_query(payload: RAGQuery):
    """
    1) Recupera los fragments más cercanos (k=3).
    2) Si la distancia mínima excede el umbral, devolvemos “out of scope”.
    3) Si no, llamamos a Gemini para generar la respuesta y devolvemos {answer, references}.
    """
    # 1) Recuperar los top-3 fragments
    frags = retrieve_fragments_openai(payload.query, k=3)
    if not frags:
        # Si no hay fragments (índice vacío o error), devolvemos 404
        raise HTTPException(
            status_code=404, detail="Knowledge base no indexada o vacía"
        )

    # 2) Calcular distancia mínima (Chroma devuelve “distance”, no “similarity”)
    distances = [score for (_, score, _) in frags]
    min_dist = min(distances)

    if min_dist > UMBRAL_DISTANCIA:
        # Fuera de contexto: devolvemos mensaje sin referencias
        return RAGResponse(
            answer="Lo siento, no tengo información sobre eso.", references=[]
        )

    # 3) Convertir los fragments a diccionarios para Gemini
    frags_dict = [{"text": t, "score": s, "source": src} for (t, s, src) in frags]

    # 4) Generar respuesta y referencias con Gemini
    rag_res = generate_answer_with_references_gemini(frags_dict, payload.query)
    # Deduplicar referencias
    refs = list(dict.fromkeys(rag_res["references"]))

    return RAGResponse(answer=rag_res["answer"], references=refs)

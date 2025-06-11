from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import os
import json

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/summary")
async def metrics_summary():
    """
    Devuelve las métricas de evaluación (JSON) generadas por evaluation/evaluate.py
    """
    # Localiza evaluation/metrics_summary.json
    metrics_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "evaluation",
            "metrics_summary.json",
        )
    )
    if not os.path.exists(metrics_path):
        raise HTTPException(
            status_code=404,
            detail="Metrics summary not found. Run evaluation/evaluate.py first.",
        )
    try:
        with open(metrics_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading metrics: {e}")
    return JSONResponse(content=data)

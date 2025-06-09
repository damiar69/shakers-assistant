import json
import os
import numpy as np
from typing import List, Dict

from backend.app.services.retriever_openai import get_openai_embedding

# ─────────────────────────────────────────────────────────────────────────────
# 1) PATH TO JSON WITH EMBEDDINGS
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(__file__)
DOC_EMBED_FILE = os.path.abspath(
    os.path.join(BASE_DIR, "../../../data/doc_embeddings.json")
)

# ─────────────────────────────────────────────────────────────────────────────
# 2) LOAD EMBEDDINGS INTO MEMORY
# ─────────────────────────────────────────────────────────────────────────────
with open(DOC_EMBED_FILE, "r", encoding="utf-8") as f:
    raw = json.load(f)
    DOC_EMBEDDINGS = {doc: np.array(vec, dtype=float) for doc, vec in raw.items()}


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute the cosine similarity between two vectors."""
    return float(a.dot(b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def recommend_resources(
    chat_history: List[Dict],
    current_query: str,
    k: int = 3,
    alpha: float = 0.6,
) -> List[Dict]:
    """
    Generate up to k personalized recommendations by combining:
      1) The user's historical interests (average embedding of seen docs).
      2) The relevance to the current query.
    Returns a list of dicts with 'doc' and 'reason'.
    """
    # 1) Extract seen documents
    seen_docs = {src for entry in chat_history for src in entry.get("refs", [])}

    # 2) Build historical profile embedding (if user has history)
    user_emb = None
    if seen_docs:
        seen_embs = [DOC_EMBEDDINGS[d] for d in seen_docs if d in DOC_EMBEDDINGS]
        if seen_embs:
            user_emb = np.mean(np.stack(seen_embs), axis=0)
            # Ensure numpy array
            user_emb = np.array(user_emb, dtype=float)

    # 3) Compute embedding of the current query
    raw_query_emb = get_openai_embedding(current_query)
    # Convert to numpy array if needed
    if isinstance(raw_query_emb, list):
        query_emb = np.array(raw_query_emb, dtype=float)
    else:
        query_emb = raw_query_emb

    # 4) Score each unseen document by a weighted sum of profile & query similarity
    candidates = []
    for doc, emb in DOC_EMBEDDINGS.items():
        if doc in seen_docs:
            continue
        sim_profile = cosine_similarity(user_emb, emb) if user_emb is not None else 0.0
        sim_query = cosine_similarity(query_emb, emb)
        score = alpha * sim_profile + (1 - alpha) * sim_query
        candidates.append((doc, score))

    # 5) Sort descending by combined score
    candidates.sort(key=lambda x: x[1], reverse=True)

    # 6) Select top-k without additional diversity filter
    recs = []
    for doc, score in candidates[:k]:
        reason = f"This document '{doc}' scores {score:.2f} by combining your historical interests and the current query."
        recs.append({"doc": doc, "reason": reason})

    return recs

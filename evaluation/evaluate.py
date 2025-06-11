"""
Batch evaluation script for RAG and Recommendations services.

Usage:
    python evaluation/evaluate.py

Ensure your API server is running at http://127.0.0.1:8000 and you have:
    - tests/simulated_data/test_questions.json
    - tests/simulated_data/user_profiles.json
"""

import os
import json
import requests

API_URL = "http://127.0.0.1:8000"


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def word_overlap_ratio(ideal, generated):
    s1 = set(ideal.lower().split())
    s2 = set(generated.lower().split())
    if not s1:
        return 0.0
    return len(s1 & s2) / len(s1)


def evaluate_rag(questions):
    print("\n=== RAG Evaluation ===")
    total = len(questions)
    overlap_scores = []
    reference_recalls = []

    for entry in questions:
        qid = entry["id"]
        resp = requests.post(
            f"{API_URL}/rag/query",
            json={"user_id": f"eval_{qid}", "query": entry["question"]},
        )
        if resp.status_code != 200:
            print(f"QID {qid}: HTTP {resp.status_code}")
            continue

        data = resp.json()
        overlap = word_overlap_ratio(
            entry.get("ideal_answer", ""), data.get("answer", "")
        )
        ideal_refs = set(entry.get("references", []))
        recall = 0.0
        if ideal_refs:
            recall = len(set(data.get("references", [])) & ideal_refs) / len(ideal_refs)

        overlap_scores.append(overlap)
        reference_recalls.append(recall)
        print(f"[RAG] QID {qid}: overlap={overlap:.2%}, recall={recall:.2%}")

    avg_overlap = sum(overlap_scores) / total if total else 0.0
    avg_recall = sum(reference_recalls) / total if total else 0.0
    print(
        f"\nRAG Summary: Total={total}, "
        f"AvgOverlap={avg_overlap:.2%}, AvgRecall={avg_recall:.2%}\n"
    )
    return {"total": total, "avg_overlap": avg_overlap, "avg_recall": avg_recall}


def evaluate_recs(profiles, default_query):
    print("\n=== Recommendations Evaluation ===")
    recommendation_counts = []
    unique_document_counts = []

    for profile in profiles:
        user_id = profile["user_id"]
        history = profile.get("history", [])
        current_query = history[-1]["q"] if history else default_query

        resp = requests.post(
            f"{API_URL}/recs/personalized",
            json={"user_id": user_id, "current_query": current_query},
        )
        if resp.status_code != 200:
            print(f"[Recs] User {user_id}: HTTP {resp.status_code}")
            continue

        recs = resp.json().get("recommendations", [])
        docs = [r["doc"] for r in recs]

        recommendation_counts.append(len(docs))
        unique_document_counts.append(len(set(docs)))
        print(f"[Recs] {user_id}: recs={len(docs)}, unique={len(set(docs))}")

    total_users = len(profiles)
    avg_recs = sum(recommendation_counts) / total_users if total_users else 0.0
    avg_unique = sum(unique_document_counts) / total_users if total_users else 0.0
    print(
        f"\nRecs Summary: Users={total_users}, "
        f"AvgRecs={avg_recs:.2f}, AvgUnique={avg_unique:.2f}\n"
    )
    return {"total_users": total_users, "avg_recs": avg_recs, "avg_unique": avg_unique}


def save_summary(rag_summary: dict, recs_summary: dict):
    # Saving JSON
    script_dir = os.path.dirname(__file__)
    out = {
        "rag": {
            "total_queries": rag_summary["total"],
            "avg_overlap": rag_summary["avg_overlap"],
            "avg_recall": rag_summary["avg_recall"],
        },
        "recs": {
            "total_users": recs_summary["total_users"],
            "avg_recs": recs_summary["avg_recs"],
            "avg_unique": recs_summary["avg_unique"],
        },
    }
    path = os.path.join(script_dir, "metrics_summary.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"Saved metrics summary to {path}")


if __name__ == "__main__":
    base = os.path.dirname(__file__)
    qs_path = os.path.join(base, "../tests/simulated_data/test_questions.json")
    pf_path = os.path.join(base, "../tests/simulated_data/user_profiles.json")

    questions = load_json(qs_path)
    profiles = load_json(pf_path)
    default_q = "How do payments work on Shakers?"

    rag = evaluate_rag(questions)
    recs = evaluate_recs(profiles, default_q)
    save_summary(rag, recs)

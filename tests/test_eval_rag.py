import json
import pytest
import warnings
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

# Load real questions
with open("tests/simulated_data/test_questions.json", encoding="utf-8") as f:
    QUESTIONS = json.load(f)


@pytest.mark.parametrize("entry", QUESTIONS)
def test_e2e_rag_query(entry):
    """
    E2E test for /rag/query using your real KB and evaluation JSON.
    1) HTTP 200
    2) At least one reference matches the expected ones (warning if not)
    3) Overlap >= 10% with the ideal answer (warning if not)
    """
    response = client.post(
        "/rag/query",
        json={"user_id": f"eval_{entry['id']}", "query": entry["question"]},
    )
    assert response.status_code == 200, f"HTTP {response.status_code}"
    data = response.json()

    # Verify references
    returned_refs = set(data.get("references", []))
    expected_refs = set(entry.get("references", []))
    if not (returned_refs & expected_refs):
        warnings.warn(
            f"QID {entry['id']}: no expected references found in returned {returned_refs}"
        )

    # Verify minimum 10% overlap
    ideal_words = entry.get("ideal_answer", "").lower().split()
    if ideal_words:
        generated_words = set(data.get("answer", "").lower().split())
        overlap_ratio = len(set(ideal_words) & generated_words) / len(ideal_words)
        if overlap_ratio < 0.1:
            warnings.warn(
                f"QID {entry['id']}: low overlap ({overlap_ratio:.2%}) with ideal"
            )

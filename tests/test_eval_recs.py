import json
import pytest
import warnings
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

# Load your real user profiles\ nwith open("tests/simulated_data/user_profiles.json", encoding="utf-8") as f:
with open("tests/simulated_data/user_profiles.json", encoding="utf-8") as f:
    PROFILES = json.load(f)


def last_query(profile):
    hist = profile.get("history", [])
    return hist[-1]["q"] if hist else "How do payments work on Shakers?"


@pytest.mark.parametrize("profile", PROFILES)
def test_e2e_recs_query(profile):
    """
    E2E test for /recs/personalized using your real system and evaluation JSON.
    1) HTTP 200
    2) Returns between 1 and 3 recommendations
    3) If any recommendation appears in the user's history, emit a warning but do not fail the test
    """
    user_id = profile["user_id"]
    query = last_query(profile)
    resp = client.post(
        "/recs/personalized",
        json={"user_id": user_id, "current_query": query},
    )
    assert resp.status_code == 200, f"HTTP {resp.status_code}"
    recs = resp.json().get("recommendations", [])

    # 2) Count of recommendations
    assert 1 <= len(recs) <= 3, f"{user_id} recibió {len(recs)} recomendaciones"

    # 3) Warn if a recommendation is already in the user's history but do not fail
    seen = {r for h in profile.get("history", []) for r in h.get("refs", [])}
    for r in recs:
        if r["doc"] in seen:
            warnings.warn(f"Usuario {user_id} recibió histórico '{r['doc']}'")

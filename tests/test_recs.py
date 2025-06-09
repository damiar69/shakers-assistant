import os
import sys
import json
import pytest
from fastapi.testclient import TestClient


PROJECT_ROOT = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir))
# PROJECT_ROOT apunta ahora a C:\Users\ddol\Desktop\shakers-case-study

# 2) Añadimos esa carpeta al comienzo de sys.path
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from backend.app.main import app
from backend.app.db import engine, SQLModel, add_chat_entry

# Cargamos los perfiles simulados
with open("tests/simulated_data/user_profiles.json", encoding="utf-8") as f:
    PROFILES = json.load(f)

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_and_seed_history():
    # Reiniciar tablas
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    # Poblar historial
    for profile in PROFILES:
        for entry in profile["history"]:
            add_chat_entry(
                user_id=profile["user_id"],
                question=entry["q"],
                answer=entry["a"],
                references_list=entry["refs"],
            )
    yield


def test_recommendations_logic():
    for profile in PROFILES:
        resp = client.post(
            "/recs/personalized",
            json={
                "user_id": profile["user_id"],
                "current_query": "How do I post a project?",
            },
        )
        assert resp.status_code == 200
        recs = resp.json()["recommendations"]
        # Si no tiene historial, permitimos recomendaciones vacías o basadas solo en query
        if not profile["history"]:
            continue
        # Para perfiles con historia, ninguna recomendación debe ser un doc ya visto
        seen = {r for h in profile["history"] for r in h["refs"]}
        for rec in recs:
            assert (
                rec["doc"] not in seen
            ), f"{rec['doc']} ya visto por {profile['user_id']}"
        assert len(recs) <= 3

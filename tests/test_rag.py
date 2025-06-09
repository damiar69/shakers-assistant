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
from backend.app.db import engine, SQLModel


# Cargamos las preguntas simuladas
with open("tests/simulated_data/test_questions.json", encoding="utf-8") as f:
    TEST_QS = json.load(f)

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_db():
    # Reiniciar la tabla ChatEntry antes de cada test
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    yield


def test_rag_basic():
    for item in TEST_QS:
        resp = client.post(
            "/rag/query", json={"user_id": "test_user", "query": item["question"]}
        )
        assert resp.status_code == 200, f"RAG error en {item['question']}"
        data = resp.json()
        # Comprueba que la respuesta contenga al menos la primera palabra de la ideal_answer
        first_word = item["ideal_answer"].split()[0].lower()
        assert first_word in data["answer"].lower()
        # Comprueba que todas las referencias esperadas estén en la respuesta
        for ref in item["references"]:
            assert (
                ref in data["references"]
            ), f"Falta {ref} en refs para '{item['question']}'"

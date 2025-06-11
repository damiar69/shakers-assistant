import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


# ---- Tests for /rag/query ----


def test_rag_query_in_scope(monkeypatch, client):
    # patch the function imported by the router
    import backend.app.routers.rag as rag_module

    monkeypatch.setattr(
        rag_module,
        "retrieve_fragments_openai",
        lambda q, k: [("Here goes content", 0.5, "doc1.md")],
    )
    # patch the function imported by the router
    monkeypatch.setattr(
        rag_module,
        "generate_answer_with_references_gemini",
        lambda snippets, query: {
            "answer": "Test answer",
            "gemini_time_seconds": 0.1,
            "prompt": "",
        },
    )
    # patch add_chat_entry where the router imports it
    import backend.app.routers.rag as rag_db_module

    monkeypatch.setattr(
        rag_db_module, "add_chat_entry", lambda user_id, question, answer, refs: None
    )

    resp = client.post(
        "/rag/query", json={"user_id": "user1", "query": "How does it work?"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["answer"] == "Test answer"
    assert data["references"] == ["doc1.md"]


def test_rag_query_out_of_scope(monkeypatch, client):
    import backend.app.routers.rag as rag_module

    # retrieve a fragment with distance > threshold
    monkeypatch.setattr(
        rag_module,
        "retrieve_fragments_openai",
        lambda q, k: [("Irrelevant content", 2.0, "docX.md")],
    )
    # patch persistence
    monkeypatch.setattr(
        rag_module, "add_chat_entry", lambda user_id, question, answer, refs: None
    )

    resp = client.post(
        "/rag/query", json={"user_id": "user2", "query": "Something out of scope"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["answer"] == "Sorry, I have no information on that."
    assert data["references"] == []


def test_rag_query_no_fragments(monkeypatch, client):
    import backend.app.routers.rag as rag_module

    monkeypatch.setattr(rag_module, "retrieve_fragments_openai", lambda q, k: [])

    resp = client.post("/rag/query", json={"user_id": "user3", "query": "Nothing?"})
    assert resp.status_code == 404


# ---- Tests for /recs/personalized ----


def test_recs_personalized(monkeypatch, client):
    # patch get_user_history in the router
    import backend.app.routers.recs as recs_module

    class Row:
        def __init__(self, references, question, answer):
            self.references = references
            self.question = question
            self.answer = answer

    fake_history = [Row(references="docA,docB", question="q1", answer="a1")]
    monkeypatch.setattr(recs_module, "get_user_history", lambda user_id: fake_history)
    # patch the recommendation function in the router
    monkeypatch.setattr(
        recs_module,
        "recommend_resources",
        lambda chat_history, current_query, k, alpha: [
            {"doc": "docC.md", "reason": "Because yes"}
        ],
    )

    resp = client.post(
        "/recs/personalized", json={"user_id": "userX", "current_query": "query"}
    )
    assert resp.status_code == 200
    data = resp.json()
    recs = data.get("recommendations", [])
    assert recs[0]["doc"] == "docC.md"
    assert recs[0]["reason"] == "Because yes"

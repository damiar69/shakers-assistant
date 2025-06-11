import numpy as np
import pytest
from backend.app.services import recommendations


@pytest.fixture(autouse=True)
def patch_embeddings(monkeypatch):
    """
    Patch the document embeddings and the OpenAI embedding function
    for consistent and reproducible recommendation tests.
    """
    # Set up fake document embeddings
    embeddings = {
        "doc1.md": np.array([1.0, 0.0]),
        "doc2.md": np.array([0.0, 1.0]),
        "doc3.md": np.array([1.0, 1.0]),
    }
    monkeypatch.setattr(recommendations, "DOC_EMBEDDINGS", embeddings)

    # Define a fake embedding function based on keywords in the query
    def fake_get_embedding(query):
        lower_q = query.lower()
        if "one" in lower_q:
            return [1.0, 0.0]
        if "two" in lower_q:
            return [0.0, 1.0]
        return [1.0, 1.0]

    monkeypatch.setattr(
        recommendations,
        "get_openai_embedding",
        fake_get_embedding,
    )
    yield


def test_recommend_empty_history():
    """
    Test recommendations when the user has no history.
    Expected order of documents: doc2, doc3, doc1.
    Each reason should mention its document ID.
    """
    recs = recommendations.recommend_resources([], "two", k=3)
    docs = [r["doc"] for r in recs]
    assert docs == ["doc2.md", "doc3.md", "doc1.md"]
    for rec in recs:
        assert rec["doc"] in rec["reason"]


def test_recommend_with_history():
    """
    Test recommendations when the user has existing history.
    Recommendations should exclude documents already seen in history.
    """
    history = [{"refs": ["doc1.md"]}]
    recs = recommendations.recommend_resources(history, "one", k=3)
    docs = [r["doc"] for r in recs]

    # The historical document should not be recommended
    assert "doc1.md" not in docs
    # The top recommendation should be doc3
    assert docs[0] == "doc3.md"
    # Only two documents remain to recommend
    assert len(docs) == 2

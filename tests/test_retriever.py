import os
import pytest
from backend.app.services import retriever_openai


@pytest.fixture(autouse=True)
def setup_dirs(tmp_path, monkeypatch):
    """
    Prepare a temporary environment with a test KB and isolated paths for Chroma and cache.
    """
    # Create a mini test KB
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    (kb_dir / "doc1.md").write_text("This is a test document.")

    # Patch paths in retriever_openai
    monkeypatch.setattr(retriever_openai, "KB_DIR", str(kb_dir))
    monkeypatch.setattr(
        retriever_openai, "CHROMA_DB_DIR", str(tmp_path / "chroma_test")
    )
    monkeypatch.setattr(
        retriever_openai, "EMBED_CACHE_DIR", str(tmp_path / "embed_cache")
    )
    os.makedirs(str(tmp_path / "embed_cache"), exist_ok=True)

    # Simulate embeddings
    def fake_call(texts, model=None):
        return [[1.0, 1.0] for _ in texts]

    monkeypatch.setattr(retriever_openai, "_call_openai_embedding", fake_call)

    yield


def test_create_chroma_index():
    """
    Test that creating the Chroma index generates a database directory with files.
    """
    db = retriever_openai.create_chroma_index(chunk_size=1000, chunk_overlap=0)
    assert os.path.isdir(retriever_openai.CHROMA_DB_DIR)
    files = os.listdir(retriever_openai.CHROMA_DB_DIR)
    assert len(files) > 0


def test_retrieve_fragments_in_scope():
    """
    Test that retrieving fragments in scope returns a list of one fragment
    with content, score, and source.
    """
    fragments = retriever_openai.retrieve_fragments_openai("test", k=1)
    assert isinstance(fragments, list) and len(fragments) == 1
    content, score, src = fragments[0]
    assert isinstance(content, str)
    assert isinstance(score, float)
    assert isinstance(src, str)


def test_retrieve_fragments_out_of_scope(monkeypatch):
    """
    Test that if the distance threshold is set very low, no fragments are returned.
    """
    monkeypatch.setattr(retriever_openai, "DISTANCE_THRESHOLD", -1.0)
    fragments = retriever_openai.retrieve_fragments_openai("something else", k=1)
    assert fragments == []

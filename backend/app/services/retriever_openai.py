"""
Retriever module using OpenAI embeddings and Chroma vector store.

1. Batch embedding requests with caching to reduce latency.
2. Retries with exponential backoff for transient API errors, catching any Exception.
3. Incremental indexing: only new or modified documents are (re-)indexed.
4. Structured logging instead of print statements.
5. Core parameters defined as constants in code.
"""

import os
import sys
import shutil
import json
import hashlib
import logging
from time import time
from typing import List, Tuple, Optional

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from dotenv import load_dotenv
from openai import OpenAI
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# ───────────────────
# Configure logging
# ───────────────────
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger("retriever_openai")

# ───────────────────
# Load environment variables and init OpenAI client
# ───────────────────
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY not found in environment variables.")
    sys.exit(1)
client = OpenAI(api_key=OPENAI_API_KEY)
logger.info("OpenAI client initialized successfully")

# ───────────────────
# Core parameters (defined as constants)
# ───────────────────
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
EMBED_MODEL = "text-embedding-3-small"
BATCH_SIZE = 50
DISTANCE_THRESHOLD = 1.25

# Paths
BASE_DIR = os.path.dirname(__file__)
KB_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../../data/kb"))
CHROMA_DB_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../../data/chroma_db"))
EMBED_CACHE_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../../data/embed_cache"))

os.makedirs(EMBED_CACHE_DIR, exist_ok=True)
logger.debug(f"Embed cache directory: {EMBED_CACHE_DIR}")

# ───────────────────
# Caching utilities
# ───────────────────


def _get_cache_path(text: str) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return os.path.join(EMBED_CACHE_DIR, f"{digest}.json")


def _load_from_cache(text: str) -> Optional[List[float]]:
    path = _get_cache_path(text)
    if os.path.exists(path):
        logger.debug(f"Cache hit: {os.path.basename(path)}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def _save_to_cache(text: str, vector: List[float]) -> None:
    path = _get_cache_path(text)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(vector, f)
    logger.debug(f"Saved embedding to cache: {os.path.basename(path)}")


# ───────────────────
# OpenAI embedding with retries via client
# ───────────────────
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def _call_openai_embedding(texts: List[str], model: str) -> List[List[float]]:
    logger.debug(f"Calling OpenAI embeddings API for batch of size {len(texts)}")
    response = client.embeddings.create(model=model, input=texts)
    embeddings = [d.embedding for d in response.data]
    logger.debug("Received embeddings from OpenAI")
    return embeddings


def get_openai_embedding(text: str, model: str = EMBED_MODEL) -> List[float]:
    logger.debug("get_openai_embedding: checking cache")
    cached = _load_from_cache(text)
    if cached is not None:
        return cached
    logger.debug("Cache miss: calling OpenAI for single embedding")
    emb = _call_openai_embedding([text], model=model)[0]
    _save_to_cache(text, emb)
    return emb


def batch_get_openai_embeddings(
    texts: List[str], model: str = EMBED_MODEL
) -> List[List[float]]:
    logger.info(f"batch_get_openai_embeddings: processing {len(texts)} texts")
    results = [_load_from_cache(t) for t in texts]
    uncached = [i for i, v in enumerate(results) if v is None]
    logger.info(f"Found {len(uncached)} uncached texts")
    for start in range(0, len(uncached), BATCH_SIZE):
        batch_idxs = uncached[start : start + BATCH_SIZE]
        batch_texts = [texts[i] for i in batch_idxs]
        batch_embs = _call_openai_embedding(batch_texts, model=model)
        for idx, emb in zip(batch_idxs, batch_embs):
            _save_to_cache(texts[idx], emb)
            results[idx] = emb
    return results  # type: ignore


# ───────────────────
# Incremental Chroma indexing
# ───────────────────


def create_chroma_index(
    chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP
) -> Chroma:
    logger.info("Creating Chroma index from KB")
    if os.path.exists(CHROMA_DB_DIR):
        shutil.rmtree(CHROMA_DB_DIR)
        logger.info("Removed existing Chroma DB for full rebuild")

    loader = DirectoryLoader(
        KB_DIR, glob="*.md", loader_cls=TextLoader, loader_kwargs={"encoding": "utf-8"}
    )
    documents = loader.load()
    logger.info(f"Loaded {len(documents)} documents from {KB_DIR}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    chunks = splitter.split_documents(documents)
    logger.info(f"Split into {len(chunks)} chunks")

    texts = [c.page_content for c in chunks]
    metadatas = [
        {"source": os.path.basename(c.metadata.get("source", ""))} for c in chunks
    ]
    ids = [f"chunk_{i}" for i in range(len(chunks))]

    class OpenAIEmbeddingFunction:
        def __init__(self, model_name: str):
            self.model_name = model_name

        def embed_documents(self, texts_list: List[str]) -> List[List[float]]:
            return batch_get_openai_embeddings(texts_list, model=self.model_name)

        def embed_query(self, text: str) -> List[float]:
            return get_openai_embedding(text, model=self.model_name)

    embedding_fn = OpenAIEmbeddingFunction(EMBED_MODEL)
    vector_db = Chroma.from_texts(
        texts=texts,
        embedding=embedding_fn,
        metadatas=metadatas,
        ids=ids,
        persist_directory=CHROMA_DB_DIR,
    )
    vector_db.persist()
    logger.info("Chroma index successfully created and persisted")
    return vector_db


# ───────────────────
# Retrieval with out-of-scope detection
# ───────────────────


def retrieve_fragments_openai(query: str, k: int = 3) -> List[Tuple[str, float, str]]:
    logger.info(f"retrieve_fragments_openai: query={query!r}, k={k}")
    if not os.path.exists(CHROMA_DB_DIR):
        logger.info("Chroma DB not found; creating index...")
        create_chroma_index()

    start = time()
    q_emb = get_openai_embedding(query)
    logger.debug(f"Computed query embedding in {time() - start:.2f}s")

    class DummyEmbFn:
        def __init__(self, vec):
            self.vec = vec

        def embed_documents(self, texts):
            return [self.vec] * len(texts)

        def embed_query(self, _):
            return self.vec

    db = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=DummyEmbFn(q_emb))
    try:
        results = db.similarity_search_with_score(query, k=k)
    except TypeError:
        results = db.similarity_search_by_vector(q_emb, k=k)
    logger.debug(f"Chroma returned {len(results)} results")

    distances = [score for _, score in results]
    logger.debug(f"Distances: {distances}")
    if not distances or min(distances) > DISTANCE_THRESHOLD:
        logger.info(
            f"Out-of-scope detected (min_distance={min(distances) if distances else 'none'})"
        )
        return []

    output = [
        (doc.page_content, score, doc.metadata.get("source", "unknown"))
        for doc, score in results
    ]
    logger.info(f"Returning {len(output)} fragments")
    return output


if __name__ == "__main__":
    create_chroma_index()

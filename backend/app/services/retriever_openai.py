# backend/app/services/retriever_openai.py

#### LIBRARIES
import os  # for path manipulations and file operations
import shutil  # to delete existing directories
import json  # to read/write JSON files for caching embeddings
from typing import List, Tuple, Optional  # type hints for functions
import hashlib  # to compute SHA-256 hashes for cache filenames

from dotenv import load_dotenv  # to load environment variables
import openai  # OpenAI Python client

from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# ─────────────────────────────────────────────────────────────────────────────
# 1) Load environment variables and configure OpenAI
# ─────────────────────────────────────────────────────────────────────────────
load_dotenv()  # load .env file into environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables.")
openai.api_key = OPENAI_API_KEY

# ─────────────────────────────────────────────────────────────────────────────
# 2) Define base directories for knowledge base, Chroma DB, and cache
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(__file__)
KB_DIR = os.path.abspath(
    os.path.join(BASE_DIR, "../../../data/kb")
)  # folder with markdown docs
CHROMA_DB_DIR = os.path.abspath(
    os.path.join(BASE_DIR, "../../../data/chroma_db")
)  # where Chroma will persist
EMBED_CACHE_DIR = os.path.abspath(
    os.path.join(BASE_DIR, "../../../data/embed_cache")
)  # local cache for embeddings
DOC_EMBED_FILE = os.path.abspath(
    os.path.join(BASE_DIR, "../../../data/doc_embeddings.json")
)  # aggregated doc embeddings

os.makedirs(EMBED_CACHE_DIR, exist_ok=True)  # ensure cache folder exists


# ─────────────────────────────────────────────────────────────────────────────
# 3) Embedding cache utilities
# ─────────────────────────────────────────────────────────────────────────────
def _get_cache_path(text: str) -> str:
    """
    Compute SHA-256 hash of the text to use as the cache filename.
    """
    hash_digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return os.path.join(EMBED_CACHE_DIR, f"{hash_digest}.json")


def _load_embedding_from_cache(text: str) -> Optional[List[float]]:
    """
    Attempt to load the embedding for `text` from local cache.
    Returns a list of floats if found, otherwise None.
    """
    cache_file = _get_cache_path(text)
    if os.path.isfile(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def _save_embedding_to_cache(text: str, vector: List[float]) -> None:
    """
    Save the embedding vector to a JSON file identified by the hash of the text.
    """
    cache_file = _get_cache_path(text)
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(vector, f)


# ─────────────────────────────────────────────────────────────────────────────
# 4) OpenAI embedding function with local cache
# ─────────────────────────────────────────────────────────────────────────────
def get_openai_embedding(
    text: str, model: str = "text-embedding-3-small"
) -> List[float]:
    """
    Get embedding for `text` using OpenAI API with local caching:
    1. Check local cache.
    2. If absent, call OpenAI Embedding endpoint.
    3. Save result to cache.
    4. Return embedding vector.
    """
    # 1) Check cache
    cached_vector = _load_embedding_from_cache(text)
    if cached_vector is not None:
        return cached_vector

    # 2) Call OpenAI API if not in cache
    try:
        response = openai.embeddings.create(model=model, input=[text])
        vector = response.data[0].embedding
    except Exception as e:
        print(f"[ERROR] OpenAI Embedding failed: {e}")
        raise

    # 3) Save to cache
    _save_embedding_to_cache(text, vector)
    return vector


# ─────────────────────────────────────────────────────────────────────────────
# 5) Chroma index creation using OpenAI embeddings
# ─────────────────────────────────────────────────────────────────────────────
def create_chroma_index(chunk_size: int = 500, chunk_overlap: int = 50) -> Chroma:
    """
    1. Remove existing Chroma index if present.
    2. Load all Markdown files from data/kb.
    3. Split each document into chunks.
    4. Compute embeddings for each chunk and collect per-document lists.
    5. Aggregate chunk embeddings into a single embedding per document.
    6. Save document embeddings to JSON for recommender uses.
    7. Build and persist Chroma index with chunk-level embeddings.
    """
    # 1) Remove existing Chroma DB
    if os.path.exists(CHROMA_DB_DIR):
        print(f"Removing existing Chroma DB at '{CHROMA_DB_DIR}'...")
        shutil.rmtree(CHROMA_DB_DIR)

    # 2) Load markdown documents
    loader = DirectoryLoader(
        KB_DIR,
        glob="*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    documents = loader.load()
    print(f"Loaded {len(documents)} documents from '{KB_DIR}'.")

    # 3) Split documents into text chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    split_docs = text_splitter.split_documents(documents)
    print(
        f"Generated {len(split_docs)} chunks (size={chunk_size}, overlap={chunk_overlap})."
    )

    texts: List[str] = []
    metadatas: List[dict] = []
    ids: List[str] = []
    doc_to_chunk_embeddings: dict = {}

    # 4) Compute embeddings for each chunk and organize by document
    for i, chunk in enumerate(split_docs):
        content = chunk.page_content
        source_path = chunk.metadata.get("source", "unknown")
        doc_name = os.path.basename(source_path)

        texts.append(content)
        metadatas.append({"source": doc_name})
        ids.append(f"chunk_{i}")

        emb = get_openai_embedding(content)
        doc_to_chunk_embeddings.setdefault(doc_name, []).append(emb)

    # 5) Aggregate chunk embeddings to get a single vector per document
    doc_embeddings = {}
    for doc_name, chunk_embs in doc_to_chunk_embeddings.items():
        dim = len(chunk_embs[0])
        avg_vector = [0.0] * dim
        for emb in chunk_embs:
            for j in range(dim):
                avg_vector[j] += emb[j]
        count = len(chunk_embs)
        avg_vector = [v / count for v in avg_vector]
        doc_embeddings[doc_name] = avg_vector

    # 6) Save aggregated document embeddings to JSON
    with open(DOC_EMBED_FILE, "w", encoding="utf-8") as f:
        json.dump(doc_embeddings, f, ensure_ascii=False)
    print(f"Saved {len(doc_embeddings)} document embeddings to '{DOC_EMBED_FILE}'.")

    # 7) Define an embedding function wrapper for Chroma
    class OpenAIEmbeddingFunction:
        def __init__(self, model_name: str):
            self.model_name = model_name

        def embed_documents(self, texts_list: List[str]) -> List[List[float]]:
            return [
                get_openai_embedding(text, model=self.model_name) for text in texts_list
            ]

        def embed_query(self, text: str) -> List[float]:
            return get_openai_embedding(text, model=self.model_name)

    embedding_fn = OpenAIEmbeddingFunction(model_name="text-embedding-3-small")

    # Build and persist Chroma vector store using chunk-level embeddings
    vector_db = Chroma.from_texts(
        texts=texts,
        embedding=embedding_fn,
        metadatas=metadatas,
        ids=ids,
        persist_directory=CHROMA_DB_DIR,
    )
    print("Chroma index successfully created with OpenAI embeddings.")
    print(f"Chroma DB stored at '{CHROMA_DB_DIR}'.")
    return vector_db


# ─────────────────────────────────────────────────────────────────────────────
# 6) Retrieve top-k fragments (RAG) using Chroma
# ─────────────────────────────────────────────────────────────────────────────
def retrieve_fragments_openai(query: str, k: int = 3) -> List[Tuple[str, float, str]]:
    """
    1. Create Chroma index if it does not exist (calls create_chroma_index()).
    2. Compute embedding for the query using cached OpenAI embeddings.
    3. Load the Chroma collection from disk.
    4. Perform semantic search (similarity_search_with_score).
    5. Return a list of tuples: (chunk_text, similarity_score, source_filename).
    """
    # 1) Ensure Chroma DB exists
    if not os.path.exists(CHROMA_DB_DIR):
        print("Chroma DB not found; creating index with OpenAI embeddings...")
        create_chroma_index()

    # 2) Compute embedding for the query
    query_emb = get_openai_embedding(query)
    print("Using OpenAI embedding for query.")

    # 3) Define a dummy embedding function that always returns the query vector
    class DummyEmbeddingFunction:
        def __init__(self, vector: List[float]):
            self.vector = vector

        def embed_documents(self, texts_list: List[str]) -> List[List[float]]:
            return [self.vector] * len(texts_list)

        def embed_query(self, text: str) -> List[float]:
            return self.vector

    # 4) Load Chroma with the dummy embedding function for retrieval
    vector_db = Chroma(
        persist_directory=CHROMA_DB_DIR,
        embedding_function=DummyEmbeddingFunction(query_emb),
    )

    # Perform semantic search (fallback if method signature differs)
    try:
        results = vector_db.similarity_search_with_score(query, k=k)
    except TypeError:
        results = vector_db.similarity_search_by_vector(query_emb, k=k)

    # 5) Format and return results
    output: List[Tuple[str, float, str]] = []
    for doc, score in results:
        text = doc.page_content
        source = doc.metadata.get("source", "unknown")
        output.append((text, score, source))
    return output


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    create_chroma_index(600, 60)

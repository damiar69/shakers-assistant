import os
import shutil
import json
from typing import List, Tuple, Optional

from dotenv import load_dotenv
from openai import OpenAI

from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter


# Load environment variables from a .env file
load_dotenv()
# Retrieve the OpenAI API key from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables.")

# Initialize the OpenAI client with the retrieved API key
openai_client = OpenAI(api_key=OPENAI_API_KEY)


# Determine base directories for knowledge base and Chroma database
BASE_DIR = os.path.dirname(__file__)
KB_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../../data/kb"))
CHROMA_DB_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../../data/chroma_db"))

# Directory for caching embeddings locally (to avoid re-querying OpenAI)
EMBED_CACHE_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../../data/embed_cache"))
os.makedirs(EMBED_CACHE_DIR, exist_ok=True)


# -------------------------------------------------------------------
# 3. EMBEDDING CACHE UTILITIES
# -------------------------------------------------------------------
def _cache_path_for_text(text: str) -> str:
    """
    Compute a file path for storing the embedding of a given text.
    Uses SHA-256 hash of the text to create a unique filename.
    """
    import hashlib

    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return os.path.join(EMBED_CACHE_DIR, f"{h}.json")


def _load_embedding_from_cache(text: str) -> Optional[List[float]]:
    """
    Attempt to load a previously cached embedding for the given text.
    Returns the embedding (list of floats) if found, otherwise None.
    """
    cache_file = _cache_path_for_text(text)
    if os.path.isfile(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def _save_embedding_to_cache(text: str, vector: List[float]) -> None:
    """
    Save the embedding vector for a given text to the local cache.
    Writes a JSON file named by the text's hash.
    """
    cache_file = _cache_path_for_text(text)
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(vector, f)


# -------------------------------------------------------------------
# 4. FUNCTION TO GET EMBEDDING (OPENAI WITH LOCAL CACHE)
# -------------------------------------------------------------------
def get_openai_embedding(
    text: str, model: str = "text-embedding-3-small"
) -> List[float]:
    """
    Generate (or retrieve from cache) the embedding for `text` using OpenAI.
    Steps:
    1. Check local cache: if embedding exists, return it.
    2. Otherwise, call OpenAI's embeddings API.
    3. Save the resulting vector to cache.
    4. Return the embedding vector.
    """
    # Try to load from cache first
    cached = _load_embedding_from_cache(text)
    if cached is not None:
        return cached

    try:
        # Request embedding from OpenAI
        resp = openai_client.embeddings.create(input=[text], model=model)
        # In the latest OpenAI client, the response is a CreateEmbeddingResponse object
        vector = resp.data[0].embedding
    except Exception as e:
        print(f"[ERROR] OpenAI Embedding failed: {e}")
        raise

    # Save to cache for future reuse
    _save_embedding_to_cache(text, vector)
    return vector


# -------------------------------------------------------------------
# 5. INDEXING THE KNOWLEDGE BASE (CHROMA + OPENAI)
# -------------------------------------------------------------------
def Chroma_creator_openai(chunk_size: int = 500, chunk_overlap: int = 50) -> Chroma:
    """
    1) Remove any existing Chroma index (if it exists).
    2) Load all Markdown files under data/kb.
    3) Split each document into smaller chunks.
    4) Build lists of chunk texts, metadata, and unique IDs.
    5) Call Chroma.from_texts(...) to create the vector index using OpenAI embeddings.
    6) Persist the Chroma database on disk.
    """
    # 1) Delete previous Chroma database if it exists
    if os.path.exists(CHROMA_DB_DIR):
        print(f"Deleting existing Chroma DB at {CHROMA_DB_DIR}…")
        shutil.rmtree(CHROMA_DB_DIR)

    # 2) Load all Markdown documents from the knowledge base directory
    loader = DirectoryLoader(
        KB_DIR, glob="*.md", loader_cls=TextLoader, loader_kwargs={"encoding": "utf-8"}
    )
    documents = loader.load()
    print(f"Loaded {len(documents)} documents from {KB_DIR}.")

    # 3) Split each document into chunks of text with overlap
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    split_docs = text_splitter.split_documents(documents)
    print(
        f"Generated {len(split_docs)} text chunks "
        f"(chunk_size={chunk_size}, chunk_overlap={chunk_overlap})."
    )

    # 4) Prepare three parallel lists:
    #    - texts: the chunk content strings
    #    - metadatas: dictionaries containing metadata for each chunk (e.g. source file)
    #    - ids: unique string IDs for each chunk to avoid duplication
    texts: List[str] = []
    metadatas: List[dict] = []
    ids: List[str] = []
    for i, chunk in enumerate(split_docs):
        texts.append(chunk.page_content)
        source_path = chunk.metadata.get("source", "unknown")
        metadatas.append({"source": source_path})
        ids.append(f"chunk_{i}")

    # 5) Define a custom embedding function class for OpenAI
    class OpenAIEmbeddingFunction:
        def __init__(self, model_name: str):
            self.model_name = model_name

        def embed_documents(self, texts_list: List[str]) -> List[List[float]]:
            """
            Given a list of strings, return a list of embedding vectors by
            calling get_openai_embedding on each.
            """
            vectors = []
            for txt in texts_list:
                vec = get_openai_embedding(txt, model=self.model_name)
                vectors.append(vec)
            return vectors

        def embed_query(self, text: str) -> List[float]:
            """
            Given a single query string, return its embedding vector.
            """
            return get_openai_embedding(text, model=self.model_name)

    embedding_fn = OpenAIEmbeddingFunction(model_name="text-embedding-3-small")

    # 6) Use Chroma.from_texts to create/persist the index, passing:
    #    - texts: list of chunk strings
    #    - embedding_fn: the object with embed_documents/embed_query methods
    #    - metadatas: list of dicts, each containing “source” info
    #    - ids: list of unique IDs for each chunk
    #    - persist_directory: where to store the Chroma database
    vector_db = Chroma.from_texts(
        texts,  # list of chunk strings
        embedding_fn,  # object implementing embed_documents/embed_query
        metadatas=metadatas,  # list of metadata dicts (with "source")
        ids=ids,  # list of unique IDs ("chunk_0", "chunk_1", …)
        persist_directory=CHROMA_DB_DIR,
    )
    print("Index built successfully with OpenAI embeddings.")
    print(f"Chroma DB saved at {CHROMA_DB_DIR}.")
    return vector_db


# -------------------------------------------------------------------
# 6. FUNCTION TO RETRIEVE TOP-k FRAGMENTS (RAG) USING OPENAI EMBEDDINGS
# -------------------------------------------------------------------
def retrieve_fragments_openai(query: str, k: int = 3) -> List[Tuple[str, float, str]]:
    """
    1) If the Chroma database does not exist, build it using Chroma_creator_openai().
    2) Compute the embedding for the input `query`.
    3) Load the existing Chroma database from disk.
    4) Perform a similarity search (top-k) and return a list of tuples:
       (chunk_text, similarity_score, source_path).
    """
    # 1) If no index exists, create it
    if not os.path.exists(CHROMA_DB_DIR):
        print("Chroma DB not found; building with OpenAI embeddings…")
        Chroma_creator_openai()

    # 2) Get embedding for the query string
    query_emb = get_openai_embedding(query, model="text-embedding-3-small")
    print("Using OpenAI embedding for retrieval.")

    # 3) Define a dummy embedding function that returns the query vector
    #    Chroma requires an embedding_function, even though search_by_vector will be used.
    class DummyEmbeddingFunction:
        def __init__(self, vector: List[float]):
            self.vector = vector

        def embed_documents(self, texts_list: List[str]) -> List[List[float]]:
            """
            Not used during retrieval, but Chroma expects this method to exist.
            We return the same query vector for each requested text (unused).
            """
            return [self.vector] * len(texts_list)

        def embed_query(self, text: str) -> List[float]:
            """
            Return the precomputed query embedding vector.
            """
            return self.vector

    # 4) Instantiate Chroma by specifying named arguments:
    #    - persist_directory: path to the existing Chroma DB on disk
    #    - embedding_function: dummy class to satisfy Chroma's requirements
    vector_db = Chroma(
        persist_directory=CHROMA_DB_DIR,
        embedding_function=DummyEmbeddingFunction(query_emb),
        # (Optionally) collection_name="langchain"
    )

    # 5) Perform semantic similarity search:
    try:
        results = vector_db.similarity_search_with_score(query, k=k)
    except TypeError:
        # Some versions require passing the vector directly:
        results = vector_db.similarity_search_by_vector(query_emb, k=k)

    # 6) Collect and return the top-k results as (text, score, source)
    output: List[Tuple[str, float, str]] = []
    for doc, score in results:
        text = doc.page_content
        source = doc.metadata.get("source", "unknown")
        output.append((text, score, source))
    return output


# -------------------------------------------------------------------
# 7. QUICK TEST (if this script is run directly)
# -------------------------------------------------------------------
if __name__ == "__main__":
    Chroma_creator_openai()

#### LIBRARIES
import os  # to create folder paths
import shutil  # to delete folder
from typing import List, Tuple  # get data from functions on x type
from dotenv import load_dotenv  # import api key gemini
from langchain_community.document_loaders import (
    DirectoryLoader,
    TextLoader,
)  # read all .md files in a folder and return a list of documents.
from langchain.text_splitter import RecursiveCharacterTextSplitter  # splits in chunks
from langchain_community.vectorstores import Chroma  # local vector store
from langchain_google_genai._common import GoogleGenerativeAIError
from langchain_google_genai import (
    GoogleGenerativeAIEmbeddings,
)  # create embeddings API GEMINI
from langchain_huggingface import (
    HuggingFaceEmbeddings,
)  # embeddings with local model if we don't have credits on Gemini

load_dotenv()  # environment var with API key

BASE_DIR = os.path.dirname(__file__)
KB_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../../data/kb"))
CHROMA_DB_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../../data/chroma_db"))


def _create_gemini_embeddings():
    """
    Create Gemini embeddings
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")

    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-exp-03-07", api_key=api_key
    )


def _create_fallback_embeddings():
    """
    Return a local HuggingFace embedding, 'all-MiniLM-L6-v2' model
    """
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


def Chroma_creator(ck_size: int, ck_lap: int = 3) -> Chroma:
    """
    1. Load all .md files from data/kb/
    2. Split each document into fragments
    3. Attempt to build the index with Gemini; if it fails at any point,
       fall back to HuggingFace
    4. Persist the index in Chroma
    """
    # Delete existing index if it exists
    if os.path.exists(CHROMA_DB_DIR):
        print(f"Deleting existing Chroma DB at {CHROMA_DB_DIR}")
        shutil.rmtree(CHROMA_DB_DIR)

    # Load markdown documents
    loader = DirectoryLoader(
        KB_DIR, glob="*.md", loader_cls=TextLoader, loader_kwargs={"encoding": "utf-8"}
    )
    documents = loader.load()
    print(f"Loaded {len(documents)} documents from {KB_DIR}")

    # Create text chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=ck_size, chunk_overlap=ck_lap
    )
    split_documents = text_splitter.split_documents(documents)
    print(f"Generated {len(split_documents)} text chunks")

    # Try to build index with Gemini embeddings (test quota first)
    try:
        print("Trying to initialize Gemini embeddings (and validate quota)...")
        gemini_embedder = _create_gemini_embeddings()
        # quick test call to force error if quota is exhausted
        _ = gemini_embedder.embed_documents(["__test__"])
        print("Gemini embeddings OK; attempting to build index with Gemini...")

        vector_db = Chroma.from_documents(
            documents=split_documents,
            embedding=gemini_embedder,
            persist_directory=CHROMA_DB_DIR,
        )
        vector_db.persist()
        print("Index built successfully with Gemini embeddings")
        print(f"Chroma DB saved at {CHROMA_DB_DIR}.")
        return vector_db

    except (GoogleGenerativeAIError, ValueError) as e:
        # Catch quota errors or missing API key
        print(
            f"Gemini failed at index time ({e}); falling back to HuggingFace embeddings."
        )

        hf_embedder = _create_fallback_embeddings()
        vector_db = Chroma.from_documents(
            documents=split_documents,
            embedding=hf_embedder,
            persist_directory=CHROMA_DB_DIR,
        )
        vector_db.persist()
        print("Index built successfully with HuggingFace embeddings.")
        print(f"Chroma DB saved at {CHROMA_DB_DIR}.")
        return vector_db


def retrieve_fragments(query: str, k: int = 3) -> List[Tuple[str, float, str]]:
    """
    Given a text query, return the k most similar fragments.
    Uses the persisted Chroma index and embeddings (Gemini or HuggingFace).
    """
    # If the index doesn't exist, create it
    if not os.path.exists(CHROMA_DB_DIR):
        Chroma_creator(500, 50)

    # Decide on embedding function for retrieval
    try:
        embeddings = _create_gemini_embeddings()
        # quick test to ensure quota is still valid
        _ = embeddings.embed_queries([query])
        print("Using Gemini embeddings for retrieval.")
    except Exception:
        embeddings = _create_fallback_embeddings()
        print("Using HuggingFace embeddings for retrieval.")

    # Perform semantic search from Chroma
    vector_db = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)
    results = vector_db.similarity_search_with_score(query, k=k)

    output: List[Tuple[str, float, str]] = []
    for doc, score in results:
        text = doc.page_content
        source = doc.metadata.get("source", "unknown")
        output.append((text, score, source))
    return output


if __name__ == "__main__":
    Chroma_creator(500, 50)

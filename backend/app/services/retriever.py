#### LIBRERIAS
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
from langchain_google_genai import (
    GoogleGenerativeAIEmbeddings,
)  # create embeddings API GEMINI
from langchain_huggingface import (
    HuggingFaceEmbeddings,
)  # embeddings with loca modal if we dont have credits on gemini

# Carga la variable GOOGLE_API_KEY desde .env
load_dotenv()

BASE_DIR = os.path.dirname(__file__)
KB_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../../data/kb"))
CHROMA_DB_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../../data/chroma_db"))


def _create_gemini_embeddings():
    """
    Create Gemini embeddings
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables.")

    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-exp-03-07", api_key=api_key
    )  # using gemini but we can also uso another provider


def _create_fallback_embeddings():
    """
    Return a local HuggingFace embedding as a fallback.
    We use the 'all-MiniLM-L6-v2' model.
    """
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


def index_knowledge_base() -> Chroma:
    """
    1. Load all .md files from data/kb/
    2. Split each document into fragments
    3. Attempt to build the index with Gemini; if it fails, use HuggingFace
    4. Persist the index in Chroma
    """
    # 1) If an existing index exists, delete it
    if os.path.exists(CHROMA_DB_DIR):
        print(f"Deleting existing Chroma DB at {CHROMA_DB_DIR}…")
        shutil.rmtree(CHROMA_DB_DIR)

    # 2) Load Markdown documents
    loader = DirectoryLoader(
        KB_DIR, glob="*.md", loader_cls=TextLoader, loader_kwargs={"encoding": "utf-8"}
    )
    documents = loader.load()
    print(f"Loaded {len(documents)} documents from {KB_DIR}.")

    # 3) Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    split_documents = text_splitter.split_documents(documents)
    print(f"Generated {len(split_documents)} text chunks.")

    # 4) Attempt to create embeddings with Gemini
    try:
        print("Trying to build index with Gemini embeddings...")
        gemini_embeddings = _create_gemini_embeddings()
        # Instead of a separate test embed, directly attempt to build the index:
        # if it fails here, execution goes to the except block.
        vector_db = Chroma.from_documents(
            documents=split_documents,
            embedding=gemini_embeddings,
            persist_directory=CHROMA_DB_DIR,
        )
        vector_db.persist()
        print("Index built successfully with Gemini embeddings.")
        print(f"Chroma DB saved at {CHROMA_DB_DIR}.")
        return vector_db

    except Exception as e:
        # Catch any error (e.g., quota exhausted)
        print(
            f"Gemini embeddings failed ({e}); falling back to HuggingFace embeddings."
        )

        # Create HuggingFace embeddings
        hf_embeddings = _create_fallback_embeddings()

        # Rebuild the index using HuggingFace
        vector_db = Chroma.from_documents(
            documents=split_documents,
            embedding=hf_embeddings,
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
    # 1) If the index doesn't exist, create it
    if not os.path.exists(CHROMA_DB_DIR):
        index_knowledge_base()

    # 2) Attempt to load Gemini embeddings; if it fails, fallback to HuggingFace
    try:
        embeddings = _create_gemini_embeddings()
        # Try embedding the query: if it fails, execution goes to the except block
        _ = embeddings.embed_queries([query])
        print("Using Gemini embeddings for retrieval.")
    except Exception:
        embeddings = _create_fallback_embeddings()
        print("Using HuggingFace embeddings for retrieval.")

    # 3) Load Chroma and perform semantic search
    vector_db = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)
    results = vector_db.similarity_search_with_score(query, k=k)

    output: List[Tuple[str, float, str]] = []
    for doc, score in results:
        text = doc.page_content
        source = doc.metadata.get("source", "unknown")
        output.append((text, score, source))
    return output


if __name__ == "__main__":
    index_knowledge_base()

import os
import shutil
from typing import List, Tuple

from dotenv import load_dotenv

# Evitar warnings deprecados: loaders desde langchain_community
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

# Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.embeddings import HuggingFaceEmbeddings

# Carga la variable GOOGLE_API_KEY desde .env
load_dotenv()

BASE_DIR = os.path.dirname(__file__)
KB_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../../data/kb"))
CHROMA_DB_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../../data/chroma_db"))


def _create_gemini_embeddings():
    """
    Instancia Gemini Embeddings con la API Key.
    Si falta la clave, lanza ValueError.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables.")

    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-exp-03-07", api_key=api_key
    )


def _create_fallback_embeddings():
    """
    Retorna un embedding de HuggingFace local como fallback.
    Usamos el modelo 'all-MiniLM-L6-v2'.
    """
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


def index_knowledge_base() -> Chroma:
    """
    1. Carga todos los .md de data/kb/
    2. Divide cada documento en fragments
    3. Intenta generar el índice con Gemini; si falla, usa HuggingFace
    4. Persiste el índice en Chroma
    """
    # 1) Si ya existe un índice previo, lo eliminamos
    if os.path.exists(CHROMA_DB_DIR):
        print(f"Deleting existing Chroma DB at {CHROMA_DB_DIR}…")
        shutil.rmtree(CHROMA_DB_DIR)

    # 2) Cargar documentos Markdown
    loader = DirectoryLoader(
        KB_DIR, glob="*.md", loader_cls=TextLoader, loader_kwargs={"encoding": "utf-8"}
    )
    documents = loader.load()
    print(f"Loaded {len(documents)} documents from {KB_DIR}.")

    # 3) Dividir en chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    split_documents = text_splitter.split_documents(documents)
    print(f"Generated {len(split_documents)} text chunks.")

    # 4) Intentar crear embeddings con Gemini
    try:
        print("Trying to build index with Gemini embeddings...")
        gemini_embeddings = _create_gemini_embeddings()
        # En lugar de hacer un test embed por separado, simplemente
        # intentamos crear el índice: si falla aquí, cae al except.
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
        # Capturamos cualquier error (como 429 de cuota)
        print(
            f"Gemini embeddings failed ({e}); falling back to HuggingFace embeddings."
        )

        # Crear embeddings de HuggingFace
        hf_embeddings = _create_fallback_embeddings()

        # Reconstruir el índice usando HuggingFace
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
    Dada una consulta de texto, devuelve los k fragments más similares.
    Usa el índice Chroma ya persistido y los embeddings (Gemini o HuggingFace).
    """
    # 1) Si no existe el índice, crearlo
    if not os.path.exists(CHROMA_DB_DIR):
        index_knowledge_base()

    # 2) Intentar cargar embeddings de Gemini; si falla, fallback a HuggingFace
    try:
        embeddings = _create_gemini_embeddings()
        # Probar embed de la query: si falla, pasamos al except
        _ = embeddings.embed_queries([query])
        print("Using Gemini embeddings for retrieval.")
    except Exception:
        embeddings = _create_fallback_embeddings()
        print("Using HuggingFace embeddings for retrieval.")

    # 3) Cargar Chroma y hacer la búsqueda semántica
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

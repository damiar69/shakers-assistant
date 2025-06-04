# backend/app/db.py

import os
from typing import Optional, List

from sqlmodel import SQLModel, create_engine, Field, Session, select


# ─────────────────────────────────────────────────────────────────────────────
# 1) DEFINICIÓN DEL MODELO ChatEntry (SQLModel)
# ─────────────────────────────────────────────────────────────────────────────
class ChatEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str
    question: str
    answer: str
    # Guardamos las referencias como cadena "archivo1.md,archivo2.md"
    references: str


# ─────────────────────────────────────────────────────────────────────────────
# 2) CONFIGURACIÓN DE LA BASE DE DATOS (SQLite)
# ─────────────────────────────────────────────────────────────────────────────
# Queremos que el fichero .db esté en: shakers-case-study/data/shakers.db
# Para ello, obtenemos la ruta absoluta desde este archivo.
DB_FILE = os.path.abspath(
    os.path.join(__file__, os.pardir, os.pardir, os.pardir, "data", "shakers.db")
)
DB_URL = f"sqlite:///{DB_FILE}"

# Creamos el engine de SQLModel (SQLite) con check_same_thread=False para evitar bloqueos.
engine = create_engine(DB_URL, echo=False, connect_args={"check_same_thread": False})


# ─────────────────────────────────────────────────────────────────────────────
# 3) init_db(): crear las tablas (si no existen) al iniciar la aplicación
# ─────────────────────────────────────────────────────────────────────────────
def init_db():
    """
    Inicializa la base de datos. Crea la tabla ChatEntry si no existe.
    Llamar a esta función al arrancar FastAPI (startup event).
    """
    SQLModel.metadata.create_all(engine)


# ─────────────────────────────────────────────────────────────────────────────
# 4) add_chat_entry(): insertar una entrada en la tabla chatentry
# ─────────────────────────────────────────────────────────────────────────────
def add_chat_entry(
    user_id: str, question: str, answer: str, references_list: List[str]
):
    """
    Inserta un nuevo registro en ChatEntry.
    - user_id: identificador del usuario (p. ej. “david”).
    - question: texto de la pregunta que hizo el usuario.
    - answer: texto de la respuesta generada por el sistema.
    - references_list: lista de strings con nombres de archivos (["payments.md","find_freelancer.md"]).
    """
    # Convertimos la lista de referencias en un string separado por comas.
    refs_str = ",".join(references_list) if references_list else ""
    entry = ChatEntry(
        user_id=user_id,
        question=question,
        answer=answer,
        references=refs_str,
    )
    with Session(engine) as session:
        session.add(entry)
        session.commit()
        session.refresh(entry)
        return entry  # opcional: devuelve la instancia recién creada


# ─────────────────────────────────────────────────────────────────────────────
# 5) get_user_history(): recuperar todas las entradas de un user_id
# ─────────────────────────────────────────────────────────────────────────────
def get_user_history(user_id: str) -> List[ChatEntry]:
    """
    Devuelve todas las filas ChatEntry para el user_id dado, ordenadas por id (orden de inserción).
    """
    with Session(engine) as session:
        statement = (
            select(ChatEntry).where(ChatEntry.user_id == user_id).order_by(ChatEntry.id)
        )
        return session.exec(statement).all()

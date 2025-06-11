import os
from typing import Optional, List

from sqlmodel import SQLModel, create_engine, Field, Session, select


# ─────────────────────────────────────────────────────────────────────────────
# 1) Definition of the ChatEntry model (SQLModel)
# ─────────────────────────────────────────────────────────────────────────────
class ChatEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str
    question: str
    answer: str
    # We store references as a comma-separated string "file1.md,file2.md"
    references: str


# ─────────────────────────────────────────────────────────────────────────────
# 2) Database configuration (SQLite)
# ─────────────────────────────────────────────────────────────────────────────
# We want the .db file at: shakers-case-study/data/shakers.db
# To do this, we get the absolute path relative to this db.py file.
DB_FILE = os.path.abspath(
    os.path.join(__file__, os.pardir, os.pardir, os.pardir, "data", "shakers.db")
)
DB_URL = f"sqlite:///{DB_FILE}"

# Create the SQLModel engine (SQLite) with check_same_thread=False to avoid locking.
engine = create_engine(DB_URL, echo=False, connect_args={"check_same_thread": False})


# ─────────────────────────────────────────────────────────────────────────────
# 3) init_db(): create tables (if they don't exist) at application startup
# ─────────────────────────────────────────────────────────────────────────────
def init_db():
    """
    Initializes the database. Creates the ChatEntry table if it doesn't exist.
    Call this function on FastAPI startup.
    """
    SQLModel.metadata.create_all(engine)


# ─────────────────────────────────────────────────────────────────────────────
# 4) add_chat_entry(): insert a new entry into the chatentry table
# ─────────────────────────────────────────────────────────────────────────────
def add_chat_entry(
    user_id: str, question: str, answer: str, references_list: List[str]
):
    """
    Inserts a new record into ChatEntry.
    - user_id: identifier of the user (e.g. "david").
    - question: the text of the user's question.
    - answer: the text of the system's generated answer.
    - references_list: list of filenames (["payments.md", "find_freelancer.md"]).
    """
    # Convert the list of references into a comma-separated string.
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
        return entry  # optional: return the newly created instance


# ─────────────────────────────────────────────────────────────────────────────
# 5) get_user_history(): retrieve all entries for a given user_id
# ─────────────────────────────────────────────────────────────────────────────
def get_user_history(user_id: str) -> List[ChatEntry]:
    """
    Returns all ChatEntry rows for the given user_id, ordered by id (insertion order).
    """
    with Session(engine) as session:
        statement = (
            select(ChatEntry).where(ChatEntry.user_id == user_id).order_by(ChatEntry.id)
        )
        return session.exec(statement).all()

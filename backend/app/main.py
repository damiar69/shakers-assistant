# backend/app/main.py

import os
import sys
from fastapi import FastAPI
import pathlib
from contextlib import asynccontextmanager


# ────────────────────────────────────────────────────────────────────────────
# 0) AÑADIMOS LA CARPETA RAÍZ (shakers-case-study) A sys.path
# ────────────────────────────────────────────────────────────────────────────
# Este archivo está en: shakers-case-study/backend/app/main.py
# subimos TRES niveles para llegar a shakers-case-study/
PROJECT_ROOT = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir, os.pardir))
# Ahora PROJECT_ROOT apunta a: C:\Users\ddol\Desktop\shakers-case-study (o ruta equivalente)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ────────────────────────────────────────────────────────────────────────────
# 1) Imports
# ────────────────────────────────────────────────────────────────────────────
import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv

# Cargamos variables de entorno de un .env en la raíz (por ejemplo, GOOGLE_API_KEY, OPENAI_API_KEY, etc.)
load_dotenv()

# Importamos el router de RAG
from backend.app.routers.rag import router as rag_router
from backend.app.routers.recs import router as recs_router
from backend.app.db import init_db


# Crear carpeta data/ si no existe
DATA_DIR = pathlib.Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


# ────────────────────────────────────────────────────────────────────────────
# 1) Creamos la instancia de FastAPI y registramos los routers
# ────────────────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Esto se ejecuta una vez al arrancar
    init_db()
    yield
    # Aquí podrías hacer cosas al “shutdown” si quisieras
    # (por ejemplo, cerrar conexiones si fuese necesario)


app = FastAPI(title="Shakers Platform AI", version="0.1.0", lifespan=lifespan)

app.include_router(rag_router, prefix="/rag")
app.include_router(recs_router, prefix="/recs")


# ────────────────────────────────────────────────────────────────────────────
# 3) Si se ejecuta 'python main.py', arrancamos Uvicorn
# ────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)

import os
import sys
import pathlib
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from dotenv import load_dotenv
import uvicorn

# ─────────────────────────────────────────────────────────────────────────────
# Configure global logging
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger("main")

# ─────────────────────────────────────────────────────────────────────────────
# 0) Add project root to sys.path for absolute imports
# ─────────────────────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir, os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
    logger.debug(f"Added PROJECT_ROOT to sys.path: {PROJECT_ROOT}")

# ─────────────────────────────────────────────────────────────────────────────
# 1) Load environment variables
# ─────────────────────────────────────────────────────────────────────────────
load_dotenv()  # Reads .env in project root (e.g. OPENAI_API_KEY, GOOGLE_API_KEY)
logger.info("Environment variables loaded")

# ─────────────────────────────────────────────────────────────────────────────
# 2) Import routers and database initializer
# ─────────────────────────────────────────────────────────────────────────────
from backend.app.routers.rag import router as rag_router
from backend.app.routers.recs import router as recs_router
from backend.app.db import init_db
from backend.app.routers.metrics import router as metrics_router

# ─────────────────────────────────────────────────────────────────────────────
# 3) Ensure data directory exists
# ─────────────────────────────────────────────────────────────────────────────
DATA_DIR = pathlib.Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
logger.debug(f"Data directory ensured at: {DATA_DIR}")


# ─────────────────────────────────────────────────────────────────────────────
# 4) Define lifespan event to initialize the database
# ─────────────────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database")
    init_db()
    yield
    logger.info("Shutting down application")


# ─────────────────────────────────────────────────────────────────────────────
# 5) Create FastAPI app and include routers
# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(title="Shakers Platform AI", version="0.1.0", lifespan=lifespan)
app.include_router(rag_router, prefix="/rag")
app.include_router(recs_router, prefix="/recs")
app.include_router(metrics_router, prefix="/metrics")

# ─────────────────────────────────────────────────────────────────────────────
# 6) Run the application with Uvicorn if executed directly
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("Starting Uvicorn server")
    uvicorn.run(
        "backend.app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="debug",
    )

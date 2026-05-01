import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables IMMEDIATELY to ensure all imports see them
load_dotenv()

import uvicorn
from fastapi import FastAPI, Request

# --- Path Hardening (Ensure root-level rover_tools are discoverable) ---
# If in Docker, root is /app. Locally, it's the repo root.
CURRENT_DIR = Path(__file__).resolve().parent
if (CURRENT_DIR.parent / "src").exists() and (CURRENT_DIR.parent.parent / "backend").exists():
    # We are in backend/src/
    ROOT_DIR = CURRENT_DIR.parent.parent.parent
else:
    # Fallback or different structure
    ROOT_DIR = CURRENT_DIR.parent.parent.parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.routes import router as api_router
from src.utils.db_manager import db
from src.utils.logger import get_logger
import asyncio

logger = get_logger(__name__)

# Initialize the Graphite
app = FastAPI(
    title="Market-Rover Core API",
    version="5.0.0-LangGraph",
    description="Institutional-grade agentic analysis powered by LangGraph."
)

# CORS Configuration
ALLOWED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the modular routes package
app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    return {
        "message": "Market-Rover Intelligence API Gateway",
        "status": "OPERATIONAL",
        "engine": "LangGraph v5.0",
        "python": "3.13",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Liveness probe including DB check."""
    db_status = "healthy"
    try:
        await db.connect()
        async with db.pool.acquire() as conn:
            await conn.execute("SELECT 1")
    except Exception as e:
        logger.error(f"Health check DB failure: {e}")
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "stable" if db_status == "healthy" else "degraded",
        "database": db_status,
        "engine": "LangGraph",
        "python_version": "3.13"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Potential integration with SRE Sentinel
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Agent Error", "detail": str(exc)}
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("src.server:app", host="0.0.0.0", port=port, reload=True)

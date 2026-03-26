import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from src.routes import api_router
# from src.config.database import connect_to_db, close_db_connection

import signal
from fastapi import Request
from fastapi.responses import JSONResponse
from src.utils.ops_support import analyze_error

# --- SIGNAL SHIELD: Prevent libraries from crashing threads ---
_original_signal = signal.signal
def _safe_signal(sig, handler):
    try:
        return _original_signal(sig, handler)
    except ValueError:
        return None
signal.signal = _safe_signal

app = FastAPI(
    title="Pledge Rover API",
    version="1.0.0",
    description="The signal institutions had. Now yours."
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global SRE Guardian for Pledge Rover.
    Captures crashes and provides AI diagnostics.
    """
    analysis = analyze_error(exc, context="pledge_rover_api")
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "sre_analysis": analysis or "SRE Agent unavailable"
        }
    )

# CORS Middleware (similar to InvestBrand)
ALLOWED_ORIGINS = os.getenv("FRONTEND_URL", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    print("--- PLEDGE ROVER BACKEND STARTING UP ---")
    # await connect_to_db()

@app.on_event("shutdown")
async def shutdown_event():
    print("--- PLEDGE ROVER BACKEND SHUTTING DOWN ---")
    # await close_db_connection()

app.include_router(api_router, prefix="/api")

# Serve React static assets in production if they exist
# In local development, Vite handles this on port 5173
dist_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "../frontend/dist")
if os.path.isdir(dist_folder):
    print(f"Mounting static frontend from {dist_folder}")
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_folder, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Fallback to index.html for client-side routing
        file_path = os.path.join(dist_folder, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(dist_folder, "index.html"))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    print(f"Pledge Rover API starting on port {port}")
    uvicorn.run("src.server:app", host="0.0.0.0", port=port, reload=True)

import os
import uvicorn
import signal
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from src.routes import api_router
from src.config.database import init_db, close_db
from src.utils.ops_support import analyze_error_async
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
    version="1.0.1-Hardened",
    description="The signal institutions had. Now yours."
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global SRE Guardian for Pledge Rover.
    Captures crashes and provides AI diagnostics asynchronously.
    """
    try:
        analysis = await analyze_error_async(exc, context="pledge_rover_api")
    except:
        analysis = None

    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "sre_analysis": analysis or "SRE Agent unavailable"
        }
    )

# CORS Middleware
ALLOWED_ORIGINS = os.getenv("FRONTEND_URL", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "Pledge Rover API"}

@app.on_event("startup")
async def startup_event():
    from dotenv import load_dotenv
    load_dotenv()
    print("--- PLEDGE ROVER BACKEND STARTING UP ---")
    try:
        await init_db()
        from src.data.seed import seed_data
        await seed_data()
    except Exception as e:
        print(f"DATABASE: FAILED to initialize. Error: {str(e)}")

    try:
        from src.data.scan_manager import ScanManager
        ScanManager.set_status("idle", "System ready.")
    except Exception as e:
        print(f"SCAN_MANAGER: Failed to initialize. Error: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    try:
        await close_db()
    except:
        pass

app.include_router(api_router, prefix="/api")

# Serve React static assets in production
dist_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "../frontend/dist")
assets_path = os.path.join(dist_folder, "assets")

if os.path.isdir(assets_path):
    print(f"Mounting static frontend from {dist_folder}")
    app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    # This catch-all route handles the React SPA routing with deep link support.
    file_path = os.path.join(dist_folder, full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)

    index_file = os.path.join(dist_folder, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"status": "Pledge Rover initializing... please refresh."}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("src.server:app", host="0.0.0.0", port=port, reload=False)

"""
Market-Rover Unified Entry Server
Consolidates all Market-Rover backend services:
- Market Rover Core API (/api/v1/market)
- Pledge Rover API (/api/v1/pledge)
- HIL Rover Mission Control API (/api/v1/hil)
- Ownerise API (/api/v1/ownerise)
- InvestBrand API (/api/v1/investbrand)

Also serves all frontend SPAs at:
- /             -> Market Rover UI
- /hil          -> HIL Rover HUD
- /investbrand  -> InvestBrand UI
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables immediately
load_dotenv()

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

REPO_ROOT = Path(__file__).resolve().parent

# Ensure repository root and market_rover backend are on sys.path
for p in [REPO_ROOT, REPO_ROOT / "market_rover" / "backend"]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

# 1. Import Market Rover Router
from src.routes import router as market_router

# 2. Import Pledge Rover Router
from pledge_rover.backend.src.routes import api_router as pledge_router

# 3. Import Ownerise Router
from ownerise.backend.router import router as ownerise_router

# Initialize main FastAPI application
app = FastAPI(
    title="Market-Rover Unified Intelligence Gateway",
    version="5.0.0-Monolith",
    description="Unified single-container deployment for all Market-Rover services."
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount satellite backend API sub-routers
app.include_router(market_router, prefix="/api/v1/market")
app.include_router(pledge_router, prefix="/api/v1/pledge")
app.include_router(ownerise_router, prefix="/api/v1/ownerise")

# --- Legacy & Root Route Compatibility ---
app.include_router(market_router, prefix="/api")

@app.get("/health")
async def health_check():
    """Unified health check endpoint."""
    return {
        "status": "healthy",
        "container": "market-rover-app",
        "architecture": "unified-monolith",
        "database": "Neon PostgreSQL"
    }

@app.get("/api/v1/health")
async def v1_health_check():
    return {
        "status": "healthy",
        "services": ["market_rover", "pledge_rover", "hil_rover", "ownerise", "investbrand"]
    }

# --- Static Frontend SPA Mounting ---
STATIC_ROOT = REPO_ROOT / "static"

for frontend_name, route_path in [
    ("market_rover", ""),
    ("hil_rover", "/hil"),
    ("investbrand", "/investbrand")
]:
    dist_dir = STATIC_ROOT / frontend_name
    assets_dir = dist_dir / "assets"
    if assets_dir.exists():
        mount_path = f"{route_path}/assets" if route_path else "/assets"
        app.mount(mount_path, StaticFiles(directory=str(assets_dir)), name=f"assets_{frontend_name}")

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Catch-all SPA router serving compiled React/Vite frontends."""
    if full_path.startswith("api/"):
        return JSONResponse(status_code=404, content={"error": "API route not found"})

    if full_path.startswith("hil"):
        frontend_dir = STATIC_ROOT / "hil_rover"
        sub_file = full_path.replace("hil/", "", 1).replace("hil", "", 1)
    elif full_path.startswith("investbrand"):
        frontend_dir = STATIC_ROOT / "investbrand"
        sub_file = full_path.replace("investbrand/", "", 1).replace("investbrand", "", 1)
    else:
        frontend_dir = STATIC_ROOT / "market_rover"
        sub_file = full_path

    target_file = frontend_dir / sub_file
    if sub_file and target_file.is_file():
        return FileResponse(target_file)

    index_file = frontend_dir / "index.html"
    if index_file.is_file():
        return FileResponse(index_file)

    return {
        "message": "Market-Rover Unified Gateway",
        "status": "OPERATIONAL",
        "docs": "/docs"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)

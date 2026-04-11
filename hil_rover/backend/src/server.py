from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import json
import os
import uuid
from datetime import datetime, timedelta

app = FastAPI(title="HIL Rover API")

# Path to built React frontend inside container structure
DIST_PATH = "../frontend/dist"

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
@app.get("/{path:path}")
async def serve_react(path: str = None):
    # If the path is for an API, health check, or static asset, skip catch-all
    if path and (path.startswith("api") or path.startswith("health") or path.startswith("assets")):
        return None

    # Otherwise, return the React index.html
    full_path = os.path.join(DIST_PATH, "index.html")
    if os.path.exists(full_path):
        return FileResponse(full_path)
    return {"status": "Frontend building... please refresh in 30s"}

# Mount the rest of the static assets (js, css, images)
if os.path.exists(os.path.join(DIST_PATH)):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST_PATH, "assets")), name="assets")

# Shared data path - use absolute path for container stability
DATA_FILE = os.environ.get("HIL_DATA_PATH", "/app/data/hil_requests.json")

def load_requests():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_requests(requests):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(requests, f, indent=4)

class HILDecision(BaseModel):
    decision: str
    comments: Optional[str] = None

@app.get("/api/health-stats")
async def get_health_stats():
    # In a real app, this would poll the JobManager or a metrics DB
    return {
        "api_latency": "142ms",
        "cache_hit_rate": "84.2%",
        "token_usage_total": "1.2M",
        "active_crews": 2,
        "error_rate": "0.04%"
    }

@app.get("/api/brain-manifest")
async def get_brain_manifest():
    return {
        "agents": [
            {"name": "Strategist", "role": "Macro Analysis", "max_iter": 3, "status": "Idling"},
            {"name": "Shadow Analyst", "role": "Technical Edge", "max_iter": 5, "status": "Analyzing NSE"},
            {"name": "SRE Support", "role": "Governance Gate", "max_iter": 3, "status": "Optimizing API"}
        ]
    }

@app.get("/api/requests")
async def get_all_requests():
    return load_requests()

@app.post("/api/requests/{request_id}/process")
async def process_request(request_id: str, decision: HILDecision):
    requests = load_requests()
    updated = False
    for r in requests:
        if r["id"] == request_id:
            r["status"] = decision.decision
            r["decision"] = decision.decision
            r["comments"] = decision.comments
            r["processed_at"] = datetime.now().isoformat()
            updated = True
            break

    if not updated:
        raise HTTPException(status_code=404, detail="Request not found")

    save_requests(requests)
    return {"status": "success"}

@app.get("/api/stats")
async def get_stats():
    requests = load_requests()
    total = len(requests)
    approved = len([r for r in requests if r["status"] == "APPROVED"])
    rejected = len([r for r in requests if r["status"] == "REJECTED"])
    pending = len([r for r in requests if r["status"] == "PENDING"])

    now = datetime.now()
    sla_breaches = 0
    for r in requests:
        if r["status"] == "PENDING":
            created_at = datetime.fromisoformat(r["created_at"])
            if now - created_at > timedelta(days=1):
                sla_breaches += 1

    return {
        "total": total,
        "approved": approved,
        "rejected": rejected,
        "pending": pending,
        "sla_breaches": sla_breaches,
        "approval_rate": (approved / (approved + rejected)) * 100 if (approved + rejected) > 0 else 0
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

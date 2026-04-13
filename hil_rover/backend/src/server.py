from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import aiofiles
import json
import os
import uuid
import time
from datetime import datetime, timezone, timedelta

# HIL-Rover Version: 4.2.2-Hardened (Deploy-Force: 2026-04-13 14:40 IST)
app = FastAPI(title="HIL Rover API")

# Path to built React frontend inside container
DIST_PATH = os.environ.get("HIL_FRONTEND_PATH", "../frontend/dist")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. ASYNC SHARED LOGIC
DATA_FILE = os.environ.get("HIL_DATA_PATH", "/app/data/hil_requests.json")

async def load_requests_async():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        async with aiofiles.open(DATA_FILE, "r") as f:
            content = await f.read()
            return json.loads(content)
    except Exception as e:
        print(f"SRE ERROR: Failed to load requests: {e}")
        return []

async def save_requests_async(requests):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    async with aiofiles.open(DATA_FILE, "w") as f:
        await f.write(json.dumps(requests, indent=4))

class HILDecision(BaseModel):
    decision: str
    comments: Optional[str] = None

# 2. CORE API ROUTES (PRIORITY)
from scripts.sre_sentinel import run_sre_sentinel

@app.post("/api/sre/audit")
async def trigger_sre_audit():
    try:
        run_sre_sentinel()
        return {"status": "Audit successful", "message": "SRE Support has scanned the infrastructure."}
    except Exception as e:
        return {"status": "Error", "message": str(e)}

@app.get("/api/health-stats")
async def get_health_stats():
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

@app.get("/api/kpi-leaderboard")
async def get_kpi_leaderboard():
    return [
        {"agent": "Strategist", "kpi": "Funnel Integrity", "score": 94, "target": 90, "status": "Above Target"},
        {"agent": "Shadow Analyst", "kpi": "Divergence Alpha", "score": 82, "target": 70, "status": "Above Target"},
        {"agent": "Market Context", "kpi": "Technical Precision", "score": 78, "target": 80, "status": "Near Target"},
        {"agent": "SRE Support", "kpi": "SLA Governance", "score": 98, "target": 95, "status": "Optimal"}
    ]

@app.get("/api/requests")
async def get_all_requests():
    return await load_requests_async()

@app.post("/api/requests/{request_id}/process")
async def process_request(request_id: str, decision: HILDecision):
    requests = await load_requests_async()
    updated = False
    for r in requests:
        if r["id"] == request_id:
            r["status"] = decision.decision
            r["decision"] = decision.decision
            r["comments"] = decision.comments
            r["processed_at"] = datetime.now(timezone.utc).isoformat()
            updated = True
            break

    if not updated:
        raise HTTPException(status_code=404, detail="Request not found")

    await save_requests_async(requests)
    return {"status": "success"}

@app.get("/api/stats")
async def get_stats():
    requests = await load_requests_async()
    total = len(requests)
    approved = len([r for r in requests if r.get("status") == "APPROVED"])
    rejected = len([r for r in requests if r.get("status") == "REJECTED"])
    pending = len([r for r in requests if r.get("status") == "PENDING"]) or 0

    now = datetime.now(timezone.utc)
    sla_breaches = 0
    for r in requests:
        if r.get("status") == "PENDING":
            try:
                created_at = datetime.fromisoformat(r["created_at"])
                if now - created_at > timedelta(hours=24):
                    sla_breaches += 1
            except:
                pass

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

@app.post("/api/requests")
async def create_request(request: Request):
    try:
        new_data = await request.json()
        if not new_data.get("agent_name") or not new_data.get("task_name"):
            return JSONResponse(status_code=400, content={"error": "Missing agent_name or task_name"})

        requests_list = await load_requests_async()
        if not new_data.get("id"):
            new_data["id"] = f"EXT-{int(time.time())}"
        if not new_data.get("status"):
            new_data["status"] = "PENDING"
        if not new_data.get("created_at"):
            new_data["created_at"] = datetime.now(timezone.utc).isoformat()

        requests_list.append(new_data)
        await save_requests_async(requests_list)
        return {"status": "success", "id": new_data["id"]}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# 3. STATIC ASSETS
if os.path.exists(os.path.join(DIST_PATH, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST_PATH, "assets")), name="assets")

# 4. CATCH-ALL FOR REACT SPA (LOWEST PRIORITY)
@app.get("/{path:path}")
async def catch_all(path: str):
    index_file = os.path.join(DIST_PATH, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"status": "Mission Control initializing... please refresh in 10s"}

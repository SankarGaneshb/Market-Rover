from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
import os
import uuid
from datetime import datetime, timedelta

app = FastAPI(title="HIL Rover API")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared data path (assuming it's in a persistent volume or handled via DB in prod)
DATA_FILE = os.environ.get("HIL_DATA_PATH", "../../data/hil_requests.json")

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

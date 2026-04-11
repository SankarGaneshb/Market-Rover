import json
import os
import uuid
from datetime import datetime, timedelta

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "hil_requests.json")

def _load_requests():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def _save_requests(requests):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(requests, f, indent=4)

def create_hil_request(agent_name, task_name, data, instructions=None):
    """
    Creates a new HIL request and saves it.
    """
    requests = _load_requests()

    # SLA: 1 day from now
    expires_at = (datetime.now() + timedelta(days=1)).isoformat()

    new_request = {
        "id": str(uuid.uuid4())[:8],
        "agent_name": agent_name,
        "task_name": task_name,
        "data": data,
        "instructions": instructions or "Please review this agent action and either Approve to proceed or Reject to halt.",
        "status": "PENDING",
        "created_at": datetime.now().isoformat(),
        "expires_at": expires_at,
        "decision": None,
        "comments": None,
        "processed_at": None
    }

    requests.append(new_request)
    _save_requests(requests)
    return new_request["id"]

def get_requests(status=None):
    """
    Returns filtered HIL requests.
    """
    requests = _load_requests()
    if status:
        return [r for r in requests if r["status"] == status]
    return requests

def process_request(request_id, status, comments=None):
    """
    Updates the status of a HIL request (APPROVED or REJECTED).
    """
    requests = _load_requests()
    for r in requests:
        if r["id"] == request_id:
            r["status"] = status
            r["decision"] = status
            r["comments"] = comments
            r["processed_at"] = datetime.now().isoformat()
            break
    _save_requests(requests)
    return True

def get_kpi_summary():
    """
    Calculates HIL-vouchsafed KPIs.
    """
    requests = _load_requests()
    total = len(requests)
    if total == 0:
        return {"total": 0, "approval_rate": 0, "pending": 0}

    approved = len([r for r in requests if r["status"] == "APPROVED"])
    rejected = len([r for r in requests if r["status"] == "REJECTED"])
    pending = len([r for r in requests if r["status"] == "PENDING"])

    # SLA check: How many pending are > 24h old?
    sla_breaches = 0
    now = datetime.now()
    for r in requests:
        if r["status"] == "PENDING":
            created_at = datetime.fromisoformat(r["created_at"])
            if now - created_at > timedelta(days=1):
                sla_breaches += 1

    approval_rate = (approved / (approved + rejected)) * 100 if (approved + rejected) > 0 else 0

    return {
        "total": total,
        "approved": approved,
        "rejected": rejected,
        "pending": pending,
        "approval_rate": approval_rate,
        "sla_breaches": sla_breaches
    }

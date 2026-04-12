import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

HIL_REQUESTS_FILE = Path("/app/data/hil_requests.json")

def propose_system_remediation(issue_description: str, suggested_fix: str, risk_level: str = "Medium"):
    """
    Called by the SRE Agent when a system bottleneck is detected.
    Creates a formal HIL Request for the human to approve a remediation action.
    """
    # Ensure directory exists (Production safe)
    HIL_REQUESTS_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Create the request payload
    request_id = str(uuid.uuid4())[:8]
    new_request = {
        "id": request_id,
        "agent_name": "SRE Support",
        "task_name": "System Self-Healing",
        "instructions": f"ISSUE: {issue_description}\nPROPOSED FIX: {suggested_fix}",
        "data": {
            "issue": issue_description,
            "remediation": suggested_fix,
            "risk_level": risk_level,
            "system_impact": "Requires service restart or config update"
        },
        "status": "PENDING",
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    # Atomic Write to File
    requests = []
    if HIL_REQUESTS_FILE.exists():
        try:
            with open(HIL_REQUESTS_FILE, 'r', encoding='utf-8') as f:
                requests = json.load(f)
        except:
            requests = []

    requests.append(new_request)

    with open(HIL_REQUESTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(requests, f, indent=2)

    return f"Governance Request {request_id} created. Awaiting human approval in Mission Control."

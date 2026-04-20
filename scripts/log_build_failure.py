import os
import json
import requests
import time
import sys
from datetime import datetime, timezone

HIL_API_URL = os.environ.get("HIL_API_URL", "https://hil-rover-9514347926.us-central1.run.app") # Default prod URL
GENERIC_HIL_KEY = os.environ.get("HIL_API_KEY") # If needed for future auth

def log_failure_to_hil(workflow_name: str, run_id: str, error_context: str = "Unknown error"):
    """
    Dispatches a build failure event to the HIL Mission Control for SRE Agent capture.
    """

    print(f"[SRE ACTION] Reporting build failure in {workflow_name} (Run: {run_id})...")

    # Payload matching hil_rover/backend/src/server.py schema
    payload = {
        "id": f"BUILD-FAIL-{run_id}",
        "agent_name": "SRE Support",
        "task_name": f"Build Failure: {workflow_name}",
        "instructions": (
            f"CI Pipeline '{workflow_name}' failed at {datetime.now(timezone.utc).isoformat()}.\n"
            f"CONTEXT: {error_context}\n"
            f"ACTION: Inspect build logs for Run ID {run_id} and trigger remediation."
        ),
        "status": "PENDING",
        "data": {
            "workflow": workflow_name,
            "run_id": run_id,
            "severity": "CRITICAL",
            "repo": os.environ.get("GITHUB_REPOSITORY", "Market-Rover"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }

    try:
        response = requests.post(
            f"{HIL_API_URL}/api/requests",
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            print(f"✅ SRE Alert dispatched to HIL Dashboard. Request ID: {payload['id']}")
        else:
            print(f"❌ Failed to dispatch SRE alert: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"❌ Network Error dispatching HIL alert: {e}")

if __name__ == "__main__":
    # Basic CLI usage for CI steps:
    # python scripts/log_build_failure.py "Market Rover Deploy" "123456" "Docker build timeout"
    workflow = sys.argv[1] if len(sys.argv) > 1 else "CI Workflow"
    rid = sys.argv[2] if len(sys.argv) > 2 else str(int(time.time()))
    ctx = sys.argv[3] if len(sys.argv) > 3 else "No specific error provided."

    log_failure_to_hil(workflow, rid, ctx)

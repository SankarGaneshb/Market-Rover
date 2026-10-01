import os
import json
import logging
from datetime import datetime
import urllib.request
import urllib.error

# Global HIL Configuration
HIL_ROVER_URL = os.environ.get("HIL_ROVER_URL", "https://hil-rover-9514347926.us-central1.run.app")

def notify_hil(agent_name, task_name, instructions, data=None, status="PENDING"):
    """
    Standardized hook to phone home to HIL-Rover Mission Control.
    Uses standard library urllib to avoid external dependency requirements.
    """
    url = f"{HIL_ROVER_URL}/api/requests"
    payload = {
        "agent_name": agent_name,
        "task_name": task_name,
        "instructions": instructions,
        "data": data or {},
        "status": status,
        "created_at": datetime.now().isoformat()
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            response_data = resp.read().decode("utf-8")
            logging.info(f"HIL_LINK: Successfully escalated '{task_name}' to Mission Control.")
            return json.loads(response_data) if response_data else {"status": "ok"}
    except Exception as e:
        logging.warning(f"HIL_LINK_FAILURE: Could not reach Mission Control for {task_name}: {e}")
        return None

if __name__ == "__main__":
    # Test call
    logging.basicConfig(level=logging.INFO)
    notify_hil("SRE Sentinel", "Self-Test", "Verifying the SRE connection to HIL-Rover.")

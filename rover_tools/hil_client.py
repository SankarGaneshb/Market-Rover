import requests
import os
import json
import logging
from datetime import datetime

# Global HIL Configuration
HIL_ROVER_URL = os.environ.get("HIL_ROVER_URL", "https://hil-rover-9514347926.us-central1.run.app")

def notify_hil(agent_name, task_name, instructions, data=None, status="PENDING"):
    """
    Standardized hook to phone home to HIL-Rover Mission Control.
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
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logging.info(f"HIL_LINK: Successfully escalated '{task_name}' to Mission Control.")
        return response.json()
    except Exception as e:
        logging.warning(f"HIL_LINK_FAILURE: Could not reach Mission Control for {task_name}: {e}")
        return None

if __name__ == "__main__":
    # Test call
    logging.basicConfig(level=logging.INFO)
    notify_hil("SRE Sentinel", "Self-Test", "Verifying the SRE connection to HIL-Rover.")

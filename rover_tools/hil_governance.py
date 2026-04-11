import requests
import os
import time
from utils.logger import get_logger

logger = get_logger(__name__)

HIL_URL = os.environ.get("HIL_ROVER_URL", "https://hil-rover-9514347926.us-central1.run.app")

class GovernanceError(Exception):
    """Raised when the HIL Governance system is unreachable or rejects an action."""
    pass

def verify_action_with_human(agent_name, task_name, payload, instructions=None):
    """
    The 'Guardian Gate' tool.
    Checks if HIL is healthy, submits a request, and waits for a decision.
    """
    # 1. Heartbeat Check
    try:
        health = requests.get(f"{HIL_URL}/health", timeout=5)
        if health.status_code != 200:
            raise GovernanceError("HIL Console is reporting unhealthy status.")
    except Exception as e:
        logger.error(f"CRITICAL: HIL Console is DOWN. Suspension initiated. {e}")
        # FAIL-SAFE: Raise error to stop the CrewAI task
        raise GovernanceError(f"HIL_OFFLINE: Cannot proceed without governance at {HIL_URL}")

    # 2. Submit Request
    try:
        req_data = {
            "agent_name": agent_name,
            "task_name": task_name,
            "data": payload,
            "instructions": instructions
        }
        # In a real microservice, this would be a POST to the HIL API
        # For now, we simulate the submission
        logger.info(f"HIL_SUBMITTED: Waiting for approval on {task_name}")

        # 3. Decision Loop (Wait for Approval)
        # Note: In a production CrewAI setup, we might use a callback or a web socket.
        # For this logic, we return the status to the agent to tell them it's PENDING.
        return "PENDING_HUMAN_REVIEW"
    except Exception as e:
        raise GovernanceError(f"FAILED_TO_LOG_REQUEST: {e}")

def check_decision_status(request_id):
    """
    Polling tool for agents to check if their request was approved.
    """
    try:
        res = requests.get(f"{HIL_URL}/api/requests/{request_id}", timeout=5)
        data = res.json()
        return data.get("status")
    except:
        return "UNKNOWN"

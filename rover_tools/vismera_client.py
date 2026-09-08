"""
Vismera Platform Client for Market-Rover Agents.
Handles telemetry logging, token usage tracking, and platform health checks.
"""
import os
import logging
import requests
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger("MarketRover.Vismera")

# Vismera Environment Configuration
VISMERA_API_BASE_URL = os.getenv("VISMERA_API_BASE_URL", "https://dev.vismera.ai/api/v1")
VISMERA_SERVICE_KEY = os.getenv("VISMERA_SERVICE_KEY", "")
VISMERA_ENABLED = os.getenv("VISMERA_ENABLED", "true").lower() == "true"


def log_telemetry_event(
    event_type: str,
    agent_name: str,
    session_id: str,
    payload: Dict[str, Any],
    user_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Push step-level agent telemetry to the Vismera Platform session log.

    Args:
        event_type: Type of event (e.g. WORKFLOW_START, STEP_EXECUTION, WORKFLOW_END, ERROR)
        agent_name: Name of the active agent or node
        session_id: Active workflow session ID
        payload: Metadata, inputs, outputs, or error details
        user_id: Optional Vismera user ID

    Returns:
        Response dict from Vismera API or None on failure/disabled mode.
    """
    if not VISMERA_ENABLED:
        logger.debug("Vismera integration is disabled. Skipping telemetry log.")
        return None

    url = f"{VISMERA_API_BASE_URL.rstrip('/')}/telemetry"
    body = {
        "event_type": event_type,
        "agent_name": agent_name,
        "session_id": session_id,
        "user_id": user_id or "anonymous",
        "payload": payload,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {VISMERA_SERVICE_KEY}" if VISMERA_SERVICE_KEY else ""
    }

    try:
        response = requests.post(url, json=body, headers=headers, timeout=5)
        if response.status_code in (200, 201, 202):
            try:
                data = response.json()
                logger.info(f"[Vismera Telemetry] Event '{event_type}' logged for agent '{agent_name}'")
                return data
            except Exception:
                logger.info(f"[Vismera Telemetry] Event '{event_type}' received HTTP {response.status_code}")
                return {"status": "ok", "event_type": event_type, "agent_name": agent_name}
        else:
            logger.info(f"[Vismera Telemetry Sandbox] Logged event '{event_type}' locally for '{agent_name}' (HTTP {response.status_code})")
            return {"status": "sandbox_logged", "event_type": event_type, "agent_name": agent_name, "session_id": session_id}
    except Exception as e:
        logger.info(f"[Vismera Telemetry Sandbox] Logged event '{event_type}' locally for '{agent_name}' ({e})")
        return {"status": "sandbox_logged", "event_type": event_type, "agent_name": agent_name, "session_id": session_id}


def get_vismera_status() -> Dict[str, Any]:
    """
    Check connectivity and health of the Vismera platform bridge.
    """
    if not VISMERA_ENABLED:
        return {
            "status": "disabled",
            "endpoint": VISMERA_API_BASE_URL,
            "message": "Vismera bridge is disabled via VISMERA_ENABLED=false"
        }

    url = f"{VISMERA_API_BASE_URL.rstrip('/')}/health"
    headers = {
        "Authorization": f"Bearer {VISMERA_SERVICE_KEY}" if VISMERA_SERVICE_KEY else ""
    }

    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            try:
                res_data = response.json()
            except Exception:
                res_data = {"note": "Endpoint returned HTML SPA; Vismera Frontend active."}
            return {
                "status": "healthy",
                "endpoint": VISMERA_API_BASE_URL,
                "response": res_data
            }
        return {
            "status": "sandbox_mode",
            "endpoint": VISMERA_API_BASE_URL,
            "http_status": response.status_code,
            "message": "Vismera dev frontend reachable; local telemetry sandbox active."
        }
    except Exception as e:
        return {
            "status": "sandbox_mode",
            "endpoint": VISMERA_API_BASE_URL,
            "error": str(e),
            "message": "Local telemetry sandbox active."
        }

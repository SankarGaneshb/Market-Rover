import json
import os
from datetime import datetime
from typing import Dict, Any

SCAN_STATE_FILE = os.path.join(os.path.dirname(__file__), "scan_state.json")

class ScanManager:
    """
    Manages the persistent state of the Pledge Rover Global Scan.
    Uses a local JSON file to ensure status survives page refreshes in Cloud Run.
    """
    
    @staticmethod
    def get_state() -> Dict[str, Any]:
        if not os.path.exists(SCAN_STATE_FILE):
            # Initial default state
            default_state = {
                "status": "idle",
                "last_scan_at": None,
                "message": "Ready for next scan."
            }
            ScanManager.save_state(default_state)
            return default_state
            
        try:
            with open(SCAN_STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {"status": "idle", "message": "State recovery mode."}

    @staticmethod
    def save_state(state: Dict[str, Any]):
        try:
            # Ensure last_scan_at is serializable
            if isinstance(state.get("last_scan_at"), datetime):
                state["last_scan_at"] = state["last_scan_at"].isoformat()
                
            with open(SCAN_STATE_FILE, "w") as f:
                json.dump(state, f, indent=4)
        except Exception as e:
            print(f"ScanManager Error: Failed to save state - {e}")

    @staticmethod
    def set_status(status: str, message: str = ""):
        state = ScanManager.get_state()
        state["status"] = status
        state["message"] = message
        if status == "scanning":
            state["last_scan_at"] = datetime.now().isoformat()
        ScanManager.save_state(state)

    @staticmethod
    def is_scanning() -> bool:
        return ScanManager.get_state().get("status") == "scanning"

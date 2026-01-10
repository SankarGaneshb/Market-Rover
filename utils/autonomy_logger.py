"""
Autonomy Logger - Tracks high-level agent decisions and state changes.
"""
import json
import os
import datetime
from utils.logger import get_logger

logger = get_logger(__name__)

EVENTS_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'autonomy_events.json')

def _ensure_events_file():
    """Ensure the events JSON file exists."""
    if not os.path.exists(EVENTS_FILE_PATH):
        try:
            os.makedirs(os.path.dirname(EVENTS_FILE_PATH), exist_ok=True)
            with open(EVENTS_FILE_PATH, 'w') as f:
                json.dump([], f)
        except Exception as e:
            logger.error(f"Failed to create events file: {e}")

def log_autonomy_event(role: str, event_type: str, details: str, related_ticker: str = None):
    """
    Log a distinct autonomy event.
    
    Args:
        role: The agent role (e.g. "Strategist")
        event_type: Category (e.g. "REGIME_CHANGE", "TOOL_PIVOT", "MEMORY_RECALL")
        details: Description of the event.
        related_ticker: Optional ticker symbol.
    """
    _ensure_events_file()
    
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "role": role,
        "type": event_type,
        "details": details,
        "ticker": related_ticker
    }
    
    try:
        with open(EVENTS_FILE_PATH, 'r+') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
                
            data.append(entry)
            # Keep last 200 events
            if len(data) > 200:
                data = data[-200:]
                
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
            
    except Exception as e:
        logger.error(f"Failed to log autonomy event: {e}")

def read_autonomy_events():
    """Read the autonomy event stream."""
    _ensure_events_file()
    try:
        with open(EVENTS_FILE_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to read events file: {e}")
        return []

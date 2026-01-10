"""
Memory Tool - Persistent Learning for Market Rover Agents
"""
import json
import os
import datetime
from utils.logger import get_logger
try:
    from crewai.tools import tool
except ImportError:
    def tool(name_or_func):
        def decorator(func):
            return func
        return decorator

logger = get_logger(__name__)

MEMORY_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'memory.json')

def _ensure_memory_file():
    """Ensure the memory JSON file exists."""
    if not os.path.exists(MEMORY_FILE_PATH):
        try:
            os.makedirs(os.path.dirname(MEMORY_FILE_PATH), exist_ok=True)
            with open(MEMORY_FILE_PATH, 'w') as f:
                json.dump([], f)
        except Exception as e:
            logger.error(f"Failed to create memory file: {e}")

def read_memory():
    """Read the entire memory ledger."""
    _ensure_memory_file()
    try:
        with open(MEMORY_FILE_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to read memory file: {e}")
        return []

def write_memory(data):
    """Write data to the memory ledger."""
    _ensure_memory_file()
    try:
        with open(MEMORY_FILE_PATH, 'w') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        logger.error(f"Failed to write memory file: {e}")
        return False

# ==============================================================================
# AGENT TOOLS
# ==============================================================================

@tool("Read Past Predictions")
def read_past_predictions_tool(ticker: str) -> str:
    """
    Retrieves the most recent prediction made for a specific ticker (within last 30 days).
    Useful for 'Self-Correction' and checking if the AI was wrong previously.
    
    Args:
        ticker: The stock symbol (e.g. INFY.NS)
    """
    memory = read_memory()
    if not memory:
        return "No past predictions found."
    
    # Filter for the specific ticker
    # Normalize ticker (remove .NS for flexible matching if needed, but strict is better)
    ticker = ticker.upper()
    relevant = [m for m in memory if m.get('ticker') == ticker]
    
    if not relevant:
        return f"No past history for {ticker}."
    
    # Sort by date descending
    relevant.sort(key=lambda x: x.get('date', ''), reverse=True)
    latest = relevant[0]
    
    return f"🧠 **Memory Recall**: On {latest['date']}, we predicted '{latest['signal']}' with {latest.get('confidence', 'N/A')} confidence."

@tool("Save New Prediction")
def save_prediction_tool(ticker: str, signal: str, confidence: str) -> str:
    """
    Saves a new prediction to the memory ledger for future learning.
    
    Args:
        ticker: The stock symbol.
        signal: The core signal (e.g. "Buy", "Sell", "Wait").
        confidence: Assessment of confidence (High/Medium/Low).
    """
    memory = read_memory()
    
    entry = {
        "date": datetime.date.today().isoformat(),
        "ticker": ticker.upper(),
        "signal": signal,
        "confidence": confidence,
        "outcome": "Pending" # To be updated by a future 'outcome checker'
    }
    
    memory.append(entry)
    # Keep only last 1000 entries to prevent bloat
    if len(memory) > 1000:
        memory = memory[-1000:]
        
    if write_memory(memory):
        return f"Saved prediction for {ticker}."
    return "Failed to save prediction."

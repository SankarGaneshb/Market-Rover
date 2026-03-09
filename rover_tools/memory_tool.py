"""
Memory Tool - Persistent Learning for Market Rover Agents
"""
import json
import os
import datetime
import yfinance as yf
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

def evaluate_pending_predictions():
    """
    Evaluates 'Pending' predictions in the memory against actual market movement
    if they are older than 3 days. Updates the outcome in the memory ledger.
    """
    memory = read_memory()
    updated = False
    today = datetime.date.today()
    
    for entry in memory:
        if entry.get("outcome") == "Pending":
            try:
                pred_date_str = entry.get("date")
                pred_date = datetime.datetime.strptime(pred_date_str, "%Y-%m-%d").date()
                
                # We need at least 3 days to judge a short term swing/prediction
                if (today - pred_date).days >= 3:
                    ticker = entry.get("ticker", "")
                    signal = str(entry.get("signal", "")).lower()
                    
                    # Fetch brief history
                    stock = yf.Ticker(ticker)
                    hist = stock.history(start=pred_date.isoformat(), end=today.isoformat())
                    
                    if not hist.empty and len(hist) > 1:
                        price_then = hist.iloc[0]['Close']
                        price_now = hist.iloc[-1]['Close']
                        price_diff = (price_now - price_then) / price_then
                        
                        logger.info(f"Evaluating {ticker}: Predicted {signal} on {pred_date_str}. Price moved {price_diff*100:.2f}%.")
                        
                        if any(s in signal for s in ["buy", "accumulate", "bullish"]):
                            entry["outcome"] = "Success" if price_diff > 0 else "Failed"
                        elif any(s in signal for s in ["sell", "trap", "bearish"]):
                            entry["outcome"] = "Success" if price_diff < 0 else "Failed"
                        else:
                            entry["outcome"] = "Neutral (No Direction)"
                            
                        updated = True
            except Exception as e:
                logger.error(f"Failed to evaluate prediction for {entry.get('ticker')}: {e}")
                
    if updated:
        write_memory(memory)
        logger.info("Memory ledger outcomes updated.")

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
    
    outcome_str = f" (Outcome: {latest.get('outcome', 'Pending')})"
    return f"🧠 **Memory Recall**: On {latest['date']}, we predicted '{latest['signal']}' with {latest.get('confidence', 'N/A')} confidence{outcome_str}."

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

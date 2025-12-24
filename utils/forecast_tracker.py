
import json
import os
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
FORECAST_FILE = DATA_DIR / "forecast_history.json"

def save_forecast(ticker, current_price, target_price, target_date, strategy_name, confidence, years_tested):
    """
    Saves a forecast record to JSON for future validation.
    """
    # Create directory if needed
    if not DATA_DIR.exists():
        DATA_DIR.mkdir()

    record = {
        "timestamp": datetime.now().isoformat(),
        "ticker": ticker,
        "current_price": float(current_price),
        "target_price": float(target_price),
        "target_date": target_date,
        "strategy": strategy_name,
        "confidence": confidence,
        "years_tested": years_tested,
        "status": "active"
    }

    history = []
    if FORECAST_FILE.exists():
        try:
            with open(FORECAST_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except json.JSONDecodeError:
            history = [] # Reset corrupt file

    history.append(record)

    with open(FORECAST_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2)

    return True

def get_forecast_history():
    """Retrieve all saved forecasts."""
    if not FORECAST_FILE.exists():
        return []
        
    try:
        with open(FORECAST_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def delete_forecasts(timestamps_to_delete):
    """
    Deletes forecasts with matching timestamps.
    """
    if not FORECAST_FILE.exists():
        return False
        
    try:
        with open(FORECAST_FILE, 'r', encoding='utf-8') as f:
            history = json.load(f)
            
        # Filter out the items to delete
        initial_len = len(history)
        history = [h for h in history if h['timestamp'] not in timestamps_to_delete]
        
        if len(history) == initial_len:
            return False # Nothing deleted
            
        with open(FORECAST_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2)
            
        return True
    except Exception as e:
        print(f"Error deleting forecasts: {e}")
        return False

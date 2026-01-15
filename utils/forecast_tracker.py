
import json
import os
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
FORECAST_FILE = DATA_DIR / "forecast_history.json"

def _load_db():
    """
    Loads the database, handling migration from legacy list format to user-dict format.
    Returns: {"users": { "username": [records...] }}
    """
    if not FORECAST_FILE.exists():
        return {"users": {}}
        
    try:
        with open(FORECAST_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # MIGRATION: If it's a list, it's the old format
        if isinstance(data, list):
            # Migrate legacy data to 'guest' or 'legacy'
            # We'll use 'guest' as the default bucket for untagged data
            return {"users": {"guest": data}}
            
        return data
        
    except Exception:
        return {"users": {}}

def _save_db(db):
    """Saves the database to disk."""
    with open(FORECAST_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2)

def save_forecast(ticker, current_price, target_price, target_date, strategy_name, confidence, years_tested, username="guest"):
    """
    Saves a forecast record to JSON for future validation.
    Now supports username isolation.
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

    db = _load_db()
    
    # Ensure users dict exists (double safety)
    if not isinstance(db, dict) or "users" not in db:
        if isinstance(db, list): db = {"users": {"guest": db}} # Should be caught by load_db but safety first
        else: db = {"users": {}}
        
    if username not in db["users"]:
        db["users"][username] = []
        
    db["users"][username].append(record)
    
    _save_db(db)
    return True

def get_forecast_history(username="guest"):
    """Retrieve all saved forecasts for a specific user."""
    db = _load_db()
    return db.get("users", {}).get(username, [])

def delete_forecasts(timestamps_to_delete, username="guest"):
    """
    Deletes forecasts with matching timestamps for a specific user.
    """
    if not FORECAST_FILE.exists():
        return False
        
    try:
        db = _load_db()
        users = db.get("users", {})
        
        if username not in users:
            return False
            
        history = users[username]
        initial_len = len(history)
        
        # Filter out the items to delete
        new_history = [h for h in history if h['timestamp'] not in timestamps_to_delete]
        
        if len(new_history) == initial_len:
            return False # Nothing deleted
            
        users[username] = new_history
        db["users"] = users
        
        _save_db(db)
            
        return True
    except Exception as e:
        print(f"Error deleting forecasts: {e}")
        return False

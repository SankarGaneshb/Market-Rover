import json
import os
import pandas as pd
from datetime import datetime

DATA_FILE = "data/saved_portfolios.json"

class PortfolioManager:
    """
    Manages saving and loading of user portfolios to a local JSON file.
    Enforces constraints: Max 3 portfolios per user (globally for this local instance).
    """
    def __init__(self):
        self._ensure_data_dir()
        
    def _ensure_data_dir(self):
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'w') as f:
                json.dump({"portfolios": {}}, f)
                
    def _load_db(self):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return {"portfolios": {}}
            
    def _save_db(self, db):
        with open(DATA_FILE, 'w') as f:
            json.dump(db, f, indent=4)
            
    def get_portfolio_names(self):
        """Returns list of saved portfolio names"""
        db = self._load_db()
        return list(db["portfolios"].keys())
        
    def get_portfolio(self, name):
        """Returns dataframe for a given portfolio name"""
        db = self._load_db()
        if name in db["portfolios"]:
            data = db["portfolios"][name]
            return pd.DataFrame(data)
        return None
        
    def save_portfolio(self, name, df):
        """
        Saves a dataframe as a portfolio.
        Returns (Success: bool, Message: str)
        """
        if not name or not name.strip():
            return False, "Portfolio name cannot be empty."
            
        if df.empty:
            return False, "Cannot save an empty portfolio."
            
        if len(df) > 5:
             return False, "Max 5 stocks allowed per portfolio."
             
        db = self._load_db()
        
        # Check constraints
        current_names = db["portfolios"].keys()
        if name not in current_names and len(current_names) >= 3:
            return False, "Storage limit reached (Max 3 portfolios). Delete one to save new."
            
        # Convert to records for storage
        db["portfolios"][name] = df.to_dict('records')
        self._save_db(db)
        
        return True, f"Portfolio '{name}' saved successfully!"
        
    def delete_portfolio(self, name):
        """Deletes a portfolio by name"""
        db = self._load_db()
        if name in db["portfolios"]:
            del db["portfolios"][name]
            self._save_db(db)
            return True, f"Deleted '{name}'"
        return False, "Portfolio not found"

import json
import os
import pandas as pd
from datetime import datetime
import config

DATA_FILE = "data/saved_portfolios.json"

class PortfolioManager:
    """
    Manages saving and loading of user portfolios to a local JSON file.
    Enforces constraints and ISOLATES data by username.
    """
    def __init__(self, username=None):
        self.username = username or "guest"
        self._ensure_data_dir()
        
    def _ensure_data_dir(self):
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(DATA_FILE):
            # New Schema: { "users": {} }
            with open(DATA_FILE, 'w') as f:
                json.dump({"users": {}}, f)
        else:
            # MIGRATION CHECK: If file exists but is old format (key "portfolios" at root)
            try:
                with open(DATA_FILE, 'r') as f:
                    db = json.load(f)
                
                if "portfolios" in db and "users" not in db:
                    print("Migrating legacy portfolios to admin user...")
                    # Default migration: Assign all existing to 'admin' (or a specific legacy account)
                    # We assume 'bsankarganesh' or common admin name, but let's use 'admin'
                    new_db = {
                        "users": {
                            "admin": {
                                "portfolios": db["portfolios"]
                            }
                        }
                    }
                    with open(DATA_FILE, 'w') as f:
                        json.dump(new_db, f, indent=4)
            except Exception as e:
                print(f"Error checking DB migration: {e}")

    def _load_db(self):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return {"users": {}}
            
    def _save_db(self, db):
        with open(DATA_FILE, 'w') as f:
            json.dump(db, f, indent=4)
    
    def _get_user_data(self, db):
        """Helper to get safe reference to user's data block"""
        if "users" not in db:
            db["users"] = {}
        
        if self.username not in db["users"]:
            db["users"][self.username] = {"portfolios": {}}
            
        return db["users"][self.username]

    def get_portfolio_names(self):
        """Returns list of saved portfolio names for CURRENT USER ONLY"""
        db = self._load_db()
        user_data = self._get_user_data(db)
        return list(user_data["portfolios"].keys())
        
    def get_portfolio(self, name):
        """Returns dataframe for a given portfolio name for CURRENT USER ONLY"""
        db = self._load_db()
        user_data = self._get_user_data(db)
        
        if name in user_data["portfolios"]:
            data = user_data["portfolios"][name]
            return pd.DataFrame(data)
        return None
        
    def save_portfolio(self, name, df):
        """
        Saves a dataframe as a portfolio for CURRENT USER.
        Returns (Success: bool, Message: str)
        """
        if not name or not name.strip():
            return False, "Portfolio name cannot be empty."
            
        if df.empty:
            return False, "Cannot save an empty portfolio."
            
        if len(df) > config.MAX_STOCKS_PER_PORTFOLIO:
             return False, f"Max {config.MAX_STOCKS_PER_PORTFOLIO} stocks allowed per portfolio."
             
        db = self._load_db()
        
        # Ensure user structure exists
        if "users" not in db: db["users"] = {}
        if self.username not in db["users"]: db["users"][self.username] = {"portfolios": {}}
        
        user_portfolios = db["users"][self.username]["portfolios"]
        
        # Check constraints
        current_names = user_portfolios.keys()
        if name not in current_names and len(current_names) >= config.MAX_PORTFOLIOS_PER_USER:
            return False, f"Storage limit reached (Max {config.MAX_PORTFOLIOS_PER_USER} portfolios). Delete one to save new."
            
        # Convert to records for storage
        db["users"][self.username]["portfolios"][name] = df.to_dict('records')
        self._save_db(db)
        
        return True, f"Portfolio '{name}' saved successfully!"
        
    def delete_portfolio(self, name):
        """Deletes a portfolio by name for CURRENT USER"""
        db = self._load_db()
        
        if "users" in db and self.username in db["users"]:
            if name in db["users"][self.username]["portfolios"]:
                del db["users"][self.username]["portfolios"][name]
                self._save_db(db)
                return True, f"Deleted '{name}'"
        
        return False, "Portfolio not found"

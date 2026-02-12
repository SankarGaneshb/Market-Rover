import json
import os
import pandas as pd
from utils.logger import logger
import config

DATA_FILE = "data/saved_portfolios.json"

class PortfolioManager:
    """
    Manages saving and loading of user portfolios to a local JSON file.
    Enforces constraints and ISOLATES data by username within the JSON structure.
    """
    def __init__(self, username=None):
        self.username = username or "guest"
        self._ensure_data_dir()
        self.data = self._load_data()
        
    def _ensure_data_dir(self):
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

    def _load_data(self) -> dict:
        """Loads data from the JSON file."""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading portfolios from JSON: {e}")
        return {"users": {}}

    def _save_data(self):
        """Saves the current state back to the JSON file."""
        try:
            with open(DATA_FILE, 'w') as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving portfolios to JSON: {e}")

    def get_portfolio_names(self):
        """Returns list of saved portfolio names for current user."""
        user_data = self.data.get("users", {}).get(self.username, {})
        portfolios = user_data.get("portfolios", {})
        return list(portfolios.keys())
        
    def get_portfolio(self, name):
        """Returns dataframe for a given portfolio name for current user."""
        user_data = self.data.get("users", {}).get(self.username, {})
        portfolios = user_data.get("portfolios", {})
        records = portfolios.get(name)
        if records:
            return pd.DataFrame(records)
        return None
        
    def save_portfolio(self, name, df):
        """
        Saves a dataframe as a portfolio for the current user.
        Returns (Success: bool, Message: str)
        """
        if not name or not name.strip():
            return False, "Portfolio name cannot be empty."
            
        if df.empty:
            return False, "Cannot save an empty portfolio."
            
        if len(df) > config.MAX_STOCKS_PER_PORTFOLIO:
             return False, f"Max {config.MAX_STOCKS_PER_PORTFOLIO} stocks allowed per portfolio."
             
        # Initialize user path if it doesn't exist
        if "users" not in self.data:
            self.data["users"] = {}
        if self.username not in self.data["users"]:
            self.data["users"][self.username] = {"portfolios": {}}
            
        user_portfolios = self.data["users"][self.username]["portfolios"]
        
        # Check storage limit
        if name not in user_portfolios and len(user_portfolios) >= config.MAX_PORTFOLIOS_PER_USER:
            return False, f"Storage limit reached (Max {config.MAX_PORTFOLIOS_PER_USER} portfolios). Delete one to save new."
            
        # Convert to records for storage
        user_portfolios[name] = df.to_dict('records')
        self._save_data()
        
        return True, f"Portfolio '{name}' saved successfully!"
        
    def delete_portfolio(self, name):
        """Deletes a portfolio by name for current user."""
        user_data = self.data.get("users", {}).get(self.username, {})
        portfolios = user_data.get("portfolios", {})
        
        if name in portfolios:
            del portfolios[name]
            self._save_data()
            return True, f"Deleted '{name}'"
        return False, "Portfolio not found"

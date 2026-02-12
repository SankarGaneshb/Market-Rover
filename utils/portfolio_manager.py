import json
import os
import pandas as pd
from utils.db_manager import DatabaseManager
from utils.logger import logger
import config

DATA_FILE = "data/saved_portfolios.json"

class PortfolioManager:
    """
    Manages saving and loading of user portfolios to SQLite.
    Enforces constraints and ISOLATES data by username.
    Includes fallback migration from legacy JSON file.
    """
    def __init__(self, username=None):
        self.username = username or "guest"
        self.db = DatabaseManager()
        self._migrate_from_json()
        
    def _migrate_from_json(self):
        """
        Migrates data from legacy JSON file to SQLite if it exists.
        Handles both old schema and new schema in the JSON file.
        """
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    db_json = json.load(f)
                
                # Handle Migration from "users" schema or legacy "portfolios" schema
                if "users" in db_json:
                    for username, user_data in db_json["users"].items():
                        portfolios = user_data.get("portfolios", {})
                        for name, records in portfolios.items():
                            if not self.db.get_portfolio(username, name):
                                self.db.save_portfolio(username, name, records)
                elif "portfolios" in db_json:
                    # Legacy schema: Assign to 'admin' as per previous code's intent
                    portfolios = db_json["portfolios"]
                    for name, records in portfolios.items():
                        if not self.db.get_portfolio("admin", name):
                            self.db.save_portfolio("admin", name, records)
                
                # Legacy schema: Assign to 'admin' as per previous code's intent
                os.rename(DATA_FILE, DATA_FILE + ".bak")
            except Exception as e:
                logger.error(f"Migration error for Portfolios: {e}")

    def get_portfolio_names(self):
        """Returns list of saved portfolio names for CURRENT USER ONLY"""
        return self.db.get_portfolio_names(self.username)
        
    def get_portfolio(self, name):
        """Returns dataframe for a given portfolio name for CURRENT USER ONLY"""
        records = self.db.get_portfolio(self.username, name)
        if records:
            return pd.DataFrame(records)
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
             
        # Check constraints
        current_names = self.get_portfolio_names()
        if name not in current_names and len(current_names) >= config.MAX_PORTFOLIOS_PER_USER:
            return False, f"Storage limit reached (Max {config.MAX_PORTFOLIOS_PER_USER} portfolios). Delete one to save new."
            
        # Convert to records for storage
        self.db.save_portfolio(self.username, name, df.to_dict('records'))
        
        return True, f"Portfolio '{name}' saved successfully!"
        
    def delete_portfolio(self, name):
        """Deletes a portfolio by name for CURRENT USER"""
        if self.db.delete_portfolio(self.username, name):
            return True, f"Deleted '{name}'"
        return False, "Portfolio not found"


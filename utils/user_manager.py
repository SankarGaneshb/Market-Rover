import json
import os
from datetime import datetime
from utils.db_manager import DatabaseManager
from utils.logger import logger

DATA_FILE = "data/user_profiles.json"

class UserProfileManager:
    """
    Manages user profile metadata to enforce flow.
    Tracks if a user has completed the Investor Profile and when.
    Uses SQLite for persistent storage with a fallback migration from JSON.
    """
    def __init__(self):
        self.db = DatabaseManager()
        self._migrate_from_json()
        
    def _migrate_from_json(self):
        """
        Migrates data from legacy JSON file to SQLite if it exists.
        Runs only once (as long as JSON file exists).
        """
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    db_json = json.load(f)
                
                profiles = db_json.get("profiles", {})
                for username, data in profiles.items():
                    # Check if profile already exists in DB to avoid duplicates/overwrite
                    if not self.db.get_user_profile(username):
                        persona = data.get('persona', "Unknown")
                        scores = data.get('scores', {})
                        brands = data.get('brands', [])
                        self.db.save_user_profile(username, persona, scores, brands)
                
                # Optional: Rename or delete JSON file after successful migration
                # For safety, we just rename it for now
                os.rename(DATA_FILE, DATA_FILE + ".bak")
            except Exception as e:
                logger.error(f"Migration error for User Profiles: {e}")

    def get_profile_status(self, username: str) -> dict:
        """
        Check if profile exists and is valid (recent).
        Returns: {'exists': bool, 'last_updated': datetime_obj, 'days_old': int, 'needs_update': bool}
        """
        profile = self.db.get_user_profile(username)
        
        if not profile:
            return {
                'exists': False,
                'last_updated': None,
                'days_old': 9999,
                'needs_update': True
            }
            
        last_updated_str = profile.get('last_updated')
        
        try:
            last_updated = datetime.fromisoformat(last_updated_str)
            days_old = (datetime.now() - last_updated).days
            needs_update = days_old > 365
            
            return {
                'exists': True,
                'last_updated': last_updated,
                'days_old': days_old,
                'needs_update': needs_update,
                'persona': profile.get('persona')
            }
        except Exception:
             return {
                'exists': True, 
                'last_updated': None,
                'days_old': 9999,
                'needs_update': True
            }

    def update_profile_timestamp(self, username: str):
        """
        Updates the last_updated timestamp for a user.
        """
        profile = self.db.get_user_profile(username)
        if profile:
            self.db.save_user_profile(
                username, 
                profile['persona'], 
                profile['scores'], 
                profile['brands']
            )
        else:
            self.db.save_user_profile(username, "New User", {}, [])

    def save_user_profile(self, username: str, persona_val: str, scores: dict, brands: list = None):
        """
        Saves the full Investor Profile to SQLite.
        """
        self.db.save_user_profile(username, persona_val, scores, brands)

    def get_user_profile(self, username: str) -> dict:
        """
        Retrieves the full profile data from SQLite.
        """
        return self.db.get_user_profile(username)


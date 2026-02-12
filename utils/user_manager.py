import json
import os
from datetime import datetime
from utils.logger import logger

DATA_FILE = "data/user_profiles.json"

class UserProfileManager:
    """
    Manages user profile metadata to enforce flow.
    Tracks if a user has completed the Investor Profile and when.
    Uses local JSON for storage.
    """
    def __init__(self):
        self._ensure_data_dir()
        self.profiles = self._load_profiles()

    def _ensure_data_dir(self):
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

    def _load_profiles(self) -> dict:
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)
                    return data.get("profiles", {})
            except Exception as e:
                logger.error(f"Error loading user profiles: {e}")
        return {}

    def _save_profiles(self):
        try:
            with open(DATA_FILE, 'w') as f:
                json.dump({"profiles": self.profiles}, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving user profiles: {e}")

    def get_profile_status(self, username: str) -> dict:
        """
        Check if profile exists and is valid (recent).
        Returns: {'exists': bool, 'last_updated': datetime_obj, 'days_old': int, 'needs_update': bool}
        """
        profile = self.profiles.get(username)
        
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
            needs_update = days_old > 365 # Force update once a year
            
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
        if username in self.profiles:
            self.profiles[username]['last_updated'] = datetime.now().isoformat()
            self._save_profiles()

    def save_user_profile(self, username: str, persona_val: str, scores: dict, brands: list = None):
        """
        Saves the full Investor Profile answers and results.
        """
        self.profiles[username] = {
            'persona': persona_val,
            'scores': scores,
            'brands': brands or [],
            'last_updated': datetime.now().isoformat()
        }
        self._save_profiles()

    def get_user_profile(self, username: str) -> dict:
        """
        Retrieves the full profile data.
        """
        return self.profiles.get(username)

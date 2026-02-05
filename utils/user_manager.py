import json
import os
from datetime import datetime

DATA_FILE = "data/user_profiles.json"

class UserProfileManager:
    """
    Manages user profile metadata to enforce flow.
    Tracks if a user has completed the Investor Profile and when.
    """
    def __init__(self):
        self._ensure_data_dir()
        
    def _ensure_data_dir(self):
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'w') as f:
                json.dump({"profiles": {}}, f)
                
    def _load_db(self):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return {"profiles": {}}
            
    def _save_db(self, db):
        with open(DATA_FILE, 'w') as f:
            json.dump(db, f, indent=4)

    def get_profile_status(self, username: str) -> dict:
        """
        Check if profile exists and is valid (recent).
        Returns: {'exists': bool, 'last_updated': datetime_obj, 'days_old': int, 'needs_update': bool}
        """
        db = self._load_db()
        profiles = db.get("profiles", {})
        
        if username not in profiles:
            return {
                'exists': False,
                'last_updated': None,
                'days_old': 9999,
                'needs_update': True
            }
            
        data = profiles[username]
        last_updated_str = data.get('last_updated')
        
        if not last_updated_str:
             return {
                'exists': False, 
                'last_updated': None, 
                'days_old': 9999,
                'needs_update': True
            }
            
        try:
            last_updated = datetime.fromisoformat(last_updated_str)
            days_old = (datetime.now() - last_updated).days
            needs_update = days_old > 365
            
            return {
                'exists': True,
                'last_updated': last_updated,
                'days_old': days_old,
                'needs_update': needs_update,
                'persona': data.get('persona')
            }
        except:
             return {
                'exists': True, # It exists but maybe corrupted, force update
                'last_updated': None,
                'days_old': 9999,
                'needs_update': True
            }

    def update_profile_timestamp(self, username: str):
        """
        Updates the last_updated timestamp for a user.
        DEPRECATED: Use save_user_profile instead for full data.
        Kept for backward compatibility or simple timestamp updates.
        """
        db = self._load_db()
        profiles = db.get("profiles", {})
        
        # Preserve existing data if any, just update timestamp
        if username in profiles:
            profiles[username]['last_updated'] = datetime.now().isoformat()
        else:
            profiles[username] = {
                'last_updated': datetime.now().isoformat()
            }
        
        db["profiles"] = profiles
        self._save_db(db)

    def save_user_profile(self, username: str, persona_val: str, scores: dict, brands: list = None):
        """
        Saves the full Investor Profile.
        
        Args:
            username: User ID
            persona_val: String value of InvestorPersona (e.g., "The Compounder")
            scores: Dict of quiz scores {'q1': 1, 'q2': 2, 'q3': 3}
            brands: List of selected brand tickers [Optional]
        """
        db = self._load_db()
        profiles = db.get("profiles", {})
        
        # Get existing or init new
        user_data = profiles.get(username, {})
        
        # Update fields
        user_data['last_updated'] = datetime.now().isoformat()
        user_data['persona'] = persona_val
        user_data['scores'] = scores
        if brands is not None:
             user_data['brands'] = brands
             
        profiles[username] = user_data
        db["profiles"] = profiles
        self._save_db(db)

    def get_user_profile(self, username: str) -> dict:
        """
        Retrieves the full profile data.
        Returns dict or None if not found/incomplete.
        """
        db = self._load_db()
        profiles = db.get("profiles", {})
        return profiles.get(username, None)

"""
Authentication utility for Market-Rover.
Handles user login, session management, and access control using streamlit-authenticator.
"""
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import time

class AuthManager:
    """Manages user authentication and session state."""
    
    def __init__(self):
        self._config = self._load_config()
        self.authenticator = self._init_authenticator()

    def _load_config(self):
        """Load configuration from secrets or local config."""
        # In a real scenario, we might fallback or check secrets
        # For this setup to work, secrets.toml must be populated correctly
        try:
            return st.secrets
        except FileNotFoundError:
            st.error("Secrets file not found. Please set up .streamlit/secrets.toml")
            return {}

    def _init_authenticator(self):
        """Initialize the Steamlit Authenticator."""
        if not self._config:
            return None
            
        try:
            # Reconstruct the config dictionary from secrets object
            # Streamlit secrets might need to be converted to a proper dict for the library
            credentials = {
                'usernames': {
                    self._config['credentials']['usernames'][i]: {
                        'email': self._config['credentials']['usernames'][i] + "@example.com", # Mock email if not in secrets
                        'name': self._config['credentials']['names'][i],
                        'password': self._config['credentials']['passwords'][i] # In real prod, this should be hashed
                    } for i in range(len(self._config['credentials']['usernames']))
                }
            }
            
            cookie = self._config['cookie']
            
            # Create authenticator object
            # Using 'unsafe' hasher for demo purposes as we are storing plain text in secrets for now.
            # In production, use stauth.Hasher to hash passwords and store hashes.
            return stauth.Authenticate(
                credentials,
                cookie['name'],
                cookie['key'],
                cookie['expiry_days']
            )
        except KeyError as e:
            st.error(f"⚠️ Configuration Error: Missing key {e} in secrets.")
            st.info("💡 **Tip:** If you just added `secrets.toml`, please **Stop** and **Restart** the terminal server (`Ctrl+C` then `streamlit run app.py`).")
            return None
        except Exception as e:
            st.error(f"Authentication setup failed: {e}")
            return None

    def check_authentication(self):
        """
        Main method to check and enforce authentication.
        Returns:
            bool: True if authenticated, False otherwise.
        """
        if not self.authenticator:
            st.warning("Authentication not configured.")
            return False

        # Check authentication status
        # login() returns tuple but also sets session state
        try:
            # Updated for streamlit-authenticator 0.4.x: login(location='main')
            # 'fields' argument can be used to customize input labels if needed
            name, authentication_status, username = self.authenticator.login(location='main')
        except Exception as e:
            st.error(f"Login widget error: {e}")
            return False

        if authentication_status:
            return True
        elif authentication_status is False:
            st.error('Username/password is incorrect')
            return False
        elif authentication_status is None:
            st.warning('Please enter your username and password')
            return False
            
        return False

    def logout_widget(self):
        """Display logout button in sidebar."""
        if st.session_state.get("authentication_status"):
            # Updated for streamlit-authenticator 0.4.x: logout(location='sidebar')
            self.authenticator.logout(location='sidebar')
            st.sidebar.write(f"Welcome *{st.session_state.get('name')}*")

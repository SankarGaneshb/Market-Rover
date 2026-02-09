"""
Authentication utility for Market-Rover.
Handles user login, session management, and access control using streamlit-authenticator.
"""
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import time

# Import Social Auth Manager
from utils.social_auth import SocialAuthManager

class AuthManager:
    """Manages user authentication and session state."""
    
    def __init__(self):
        self._config = self._load_config()
        self.authenticator = self._init_authenticator()
        # Initialize Social Auth
        self.social_auth = SocialAuthManager(self._config)

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
            # st.error(f"⚠️ Configuration Error: Missing key {e} in secrets.")
            # Suppress specific key error to allow partial config if only social auth is used?
            # For now keep existing behavior but maybe soft fail?
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
        
        # 1. Check Session State first (Fast Return)
        if st.session_state.get('authentication_status'):
            return True

        # 2. Render Traditional Login (if configured)
        if self.authenticator:
            try:
                # Logo for Login Screen
                try:
                    st.image("assets/login_logo.png", width=300)
                except:
                    pass # Fail silently if image missing
                
                result = self.authenticator.login(location='main')
                if st.session_state.get('authentication_status'):
                    return True
            except Exception as e:
                st.error(f"Login widget error: {e}")

        # 3. Render Social Login Buttons (Always render below traditional)
        # Pass control to Social Manager
        social_user = self.social_auth.render_social_login_buttons()
        
        if social_user:
            # Successful Social Login!
            st.session_state['authentication_status'] = True
            st.session_state['name'] = social_user['name']
            st.session_state['username'] = social_user['username']
            st.session_state['login_provider'] = social_user['provider']
            st.rerun() # Rerun to update UI state immediately
            return True

        # 4. Final Fallback Message
        if not st.session_state.get('authentication_status'):
            if self.authenticator:
                if st.session_state.get('authentication_status') is False:
                    st.error('Username/password is incorrect')
                elif st.session_state.get('authentication_status') is None:
                    st.warning('Please enter your username and password')
            else:
                 # If no traditional auth, imply social only or config missing
                 st.info("Please sign in.")
            return False
            
        return False

    def logout_widget(self):
        """Display logout button in sidebar."""
        if st.session_state.get("authentication_status"):
            # Updated for streamlit-authenticator 0.4.x: logout(location='sidebar')
            if self.authenticator:
                self.authenticator.logout(location='sidebar')
            elif st.sidebar.button("Logout"):
                # Manual logout for social users
                st.session_state['authentication_status'] = None
                st.session_state['name'] = None
                st.session_state['username'] = None
                st.rerun()
                
            st.sidebar.write(f"Welcome *{st.session_state.get('name')}*")

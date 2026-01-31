"""
Social Authentication Manager for Market-Rover.
Handles OAuth flows multiple providers (Google, Facebook, etc.) and enforces whitelist logic.
Requires 'streamlit-oauth' and keys in secrets.toml.
"""
import streamlit as st
import os
from streamlit_oauth import OAuth2Component
import httpx
import logging

logger = logging.getLogger(__name__)

class SocialAuthManager:
    """
    Manages social login buttons and authentication flows.
    """
    def __init__(self, config=None):
        self._config = config or st.secrets
        self.oauth_providers = self._load_providers()
        self.whitelist = self._load_whitelist()

    def _load_providers(self):
        """Load enabled OAuth providers from secrets."""
        providers = {}
        if 'oauth' in self._config:
            for provider_name, settings in self._config['oauth'].items():
                # Basic validation
                if 'client_id' in settings and 'client_secret' in settings:
                     providers[provider_name] = settings
        return providers

    def _load_whitelist(self):
        """Load whitelist if it exists."""
        # Top level key in secrets
        return self._config.get('approved_emails', None)

    def is_user_allowed(self, email):
        """
        Check if user is allowed to login.
        If whitelist is None/Empty -> OPEN ACCESS (Return True).
        If whitelist exists -> Check exact match.
        """
        if not self.whitelist:
            return True # Open Access
        
        return email in self.whitelist

    def render_social_login_buttons(self):
        """
        Renders buttons for all configured providers.
        Returns user_info dict if login successful, None otherwise.
        """
        if not self.oauth_providers:
            # DEBUG/HELP: Show message if no providers found (so user knows to configure secrets)
            # In production you might want to hide this, but for setup it's crucial.
            if st.secrets.get('show_auth_debug', True): 
                st.info("ℹ️ Social Login not configured. Add `[oauth]` section to `.streamlit/secrets.toml` to enable.")
            return None

        st.markdown("---")
        st.markdown("###### Or sign in with:")
        
        # Determine columns based on count (max 4 per row nicely)
        count = len(self.oauth_providers)
        cols = st.columns(count) if count > 0 else []
        
        user_data = None
        
        for idx, (name, settings) in enumerate(self.oauth_providers.items()):
            with cols[idx]:
                # Create OAuth2Component instance
                # Note: We create a unique key for each provider to prevent state collisions
                logger.info(f"Initializing OAuth via OAuth2Component for provider: {name} with revoke_token_endpoint=None")
                oauth2 = OAuth2Component(
                    settings.get('client_id'),
                    settings.get('client_secret'),
                    settings.get('authorize_endpoint'),
                    settings.get('token_endpoint'),
                    settings.get('token_endpoint'), # refresh token endpoint (often same)
                    None, # Revoke endpoint disabled to prevent MissingRevokeTokenAuthMethodError
                )

                # Render button
                # Label handling
                label = settings.get('label', f"Login with {name.title()}")
                icon = settings.get('icon', 'cloud') 
                
                # The result is the AUTHORIZATION CODE handling result
                result = oauth2.authorize_button(
                    name=label,
                    icon=icon,
                    redirect_uri=settings.get('redirect_uri'),
                    scope=settings.get('scope', 'openid email profile'),
                    key=f"oauth_btn_{name}",
                    extras_params=settings.get('extras_params', {}) # e.g. prompt=consent
                )

                if result:
                    # If we have a result, it means we got a token!
                    # "result" structure depends on the lib, usually contains 'token' dict
                    
                    if 'token' in result:
                        # Fetch user info
                        try:
                            token = result['token']
                            user_info_endpoint = settings.get('user_info_endpoint')
                            
                            if user_info_endpoint:
                                # Use httpx to fetch profile
                                headers = {'Authorization': f"Bearer {token.get('access_token')}"}
                                response = httpx.get(user_info_endpoint, headers=headers)
                                
                                if response.status_code == 200:
                                    profile = response.json()
                                    
                                    # Normalize profile data (differs by provider)
                                    email = profile.get('email')
                                    name_user = profile.get('name') or profile.get('given_name') or email
                                    
                                    # WHITELIST CHECK
                                    if self.is_user_allowed(email):
                                        st.success(f"Welcome, {name_user}!")
                                        user_data = {
                                            'name': name_user,
                                            'email': email,
                                            'username': email, # Use email as username
                                            'provider': name
                                        }
                                        return user_data # Return immediately on success
                                    else:
                                        st.error("⛔ Access Denied: Your email is not on the whitelist.")
                                        st.stop()
                                
                                else:
                                    st.error(f"Failed to fetch user info: {response.text}")
                        except Exception as e:
                            st.error(f"Login processing error: {e}")
        
        return None

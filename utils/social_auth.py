"""
Social Authentication Manager for Market-Rover.
Open Access implementation: Anyone with a social account can login instantly.
"""
import streamlit as st
import httpx
import logging
from streamlit_oauth import OAuth2Component

logger = logging.getLogger(__name__)

# THE DEFINITIVE HTML TRAY - Zero Indent for perfect rendering
LOGIN_HTML_TEMPLATE = '<div style="display:block;text-align:center;width:100%;font-family:sans-serif;margin:30px 0;"><div style="font-size:13px;font-weight:700;color:#888;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:25px;">Sign in with</div><div style="display:inline-flex;justify-content:center;align-items:center;">{icon_html}</div></div>'

class SocialAuthManager:
    def __init__(self, config=None):
        self._config = config or st.secrets
        self.oauth_providers = self._load_providers()

    def _load_providers(self):
        providers = {}
        if 'oauth' in self._config:
            for p_name, settings in self._config['oauth'].items():
                if 'client_id' in settings and 'client_secret' in settings:
                     providers[p_name] = settings
        return providers

    def is_user_allowed(self, email):
        """Check if email is in the approved list. Empty list means Open Access."""
        whitelist = self._config.get('approved_emails', [])
        if not whitelist: return True
        return email in whitelist

    def _normalize_profile(self, profile, provider):
        data = {'email': None, 'name': None, 'username': None, 'provider': provider}
        p = provider.lower()
        if p == 'google': data.update({'email': profile.get('email'), 'name': profile.get('name')})
        elif p == 'facebook': data.update({'email': profile.get('email'), 'name': profile.get('name')})
        elif p == 'linkedin':
            first = profile.get('localizedFirstName', profile.get('given_name', ''))
            last = profile.get('localizedLastName', profile.get('family_name', ''))
            data['name'] = f"{first} {last}".strip()
            data['email'] = profile.get('email') or profile.get('id')
        elif p in ['x', 'twitter']:
            inner = profile.get('data', profile)
            data.update({'name': inner.get('name'), 'username': inner.get('username'), 'email': inner.get('email') or inner.get('id')})

        if not data['email']: data['email'] = profile.get('email') or profile.get('sub') or profile.get('id')
        if not data['name']: data['name'] = profile.get('display_name') or data['username'] or data['email']
        if not data['username']: data['username'] = data['email']

        logger.info(f"✨ New Social Login: {data['name']} ({data['email']}) via {provider}")
        return data

    def render_social_login_buttons(self):
        # 1. Capture the Handshake Trigger
        active_provider = st.session_state.get('active_oauth_provider')

        # 2. Complete the handshake (Handshake Mode)
        if active_provider and active_provider in self.oauth_providers:
            settings = self.oauth_providers[active_provider]
            placeholder = st.empty()
            with placeholder.container():
                st.info(f"Connecting to {active_provider}...")
                try:
                    # Determine Redirect URI
                    redir = settings.get('redirect_uri', 'http://localhost:8501').rstrip("/")
                    if "/component/" not in redir:
                        redir += "/component/streamlit_oauth.authorize_button"

                    oauth2 = OAuth2Component(
                        client_id=settings.get('client_id'),
                        client_secret=settings.get('client_secret'),
                        authorize_endpoint=settings.get('authorize_endpoint'),
                        token_endpoint=settings.get('token_endpoint'),
                        refresh_token_endpoint=settings.get('token_endpoint', None)
                    )

                    result = oauth2.authorize_button(
                        name=f"Finalize {active_provider} Login",
                        redirect_uri=redir,
                        scope=settings.get('scope', 'openid email profile'),
                        key=f"round_trip_final_{active_provider}",
                        auto_click=True
                    )

                    if result and 'token' in result:
                        st.session_state.pop('active_oauth_provider', None)
                        placeholder.empty()
                        headers = {'Authorization': f"Bearer {result['token']['access_token']}"}
                        params = settings.get('user_info_params', {})
                        try:
                            response = httpx.get(settings.get('user_info_endpoint'), headers=headers, params=params, follow_redirects=True, timeout=15.0)
                            if response.is_success:
                                return self._normalize_profile(response.json(), active_provider)
                            else:
                                st.error(f"⚠️ {active_provider} API Error: {response.status_code}")
                        except Exception as req_err:
                            st.error(f"❌ Handshake Error: {str(req_err)}")
                except Exception as e:
                    st.error(f"Auth Hub Error: {e}")
                    st.session_state.pop('active_oauth_provider', None)
                    time.sleep(2)
                    st.rerun()

        # 3. Render Landing UI (The Icon Tray)
        # Check if we have any providers
        if not self.oauth_providers:
            st.warning("⚠️ No Social Providers configured in secrets.toml")
            return None

        # Custom CSS for the tray
        st.markdown("""
            <style>
            .social-header {
                text-align: center;
                font-size: 14px;
                font-weight: 700;
                color: #888;
                letter-spacing: 1.5px;
                text-transform: uppercase;
                margin: 20px 0 10px 0;
            }
            div[data-testid="column"] button {
                border-radius: 50% !important;
                width: 60px !important;
                height: 60px !important;
                display: flex !important;
                justify-content: center !important;
                align-items: center !important;
                padding: 0 !important;
                background-color: white !important;
                border: 1px solid #eee !important;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
                transition: all 0.2s ease !important;
            }
            div[data-testid="column"] button:hover {
                box-shadow: 0 6px 12px rgba(0,0,0,0.1) !important;
                transform: translateY(-2px) !important;
                border-color: #ddd !important;
            }
            </style>
            <div class="social-header">Secure Social Entry</div>
        """, unsafe_allow_html=True)

        # Logic for icons - Always show top 3 even if not fully configured to avoid "blank" look
        logos = {
            'google': 'https://img.icons8.com/color/96/google-logo.png',
            'facebook': 'https://img.icons8.com/color/96/facebook-new.png',
            'linkedin': 'https://img.icons8.com/color/96/linkedin.png'
        }

        # Select which ones to show (all available in secrets + some defaults if user wants to see them)
        display_providers = list(self.oauth_providers.keys())

        # Render icons in centered columns
        cols = st.columns([1, 1, 1, 1, 1])[1:-1] # Center indices
        for i, name in enumerate(display_providers[:3]):
            with cols[i]:
                # Use a button with an image inside? Streamlit buttons don't support images well.
                # So we use a button + an image display for the "WOW" effect
                st.image(logos.get(name.lower(), ""), width=32)
                if st.button(f" {name.title()} ", key=f"btn_{name}", use_container_width=True):
                    st.session_state['active_oauth_provider'] = name
                    st.rerun()

        return None

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
                # Store all providers, even if they have placeholder IDs
                providers[p_name] = settings
        return providers

    def is_user_allowed(self, email):
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
        elif p in ['github']:
            data.update({'name': profile.get('name'), 'username': profile.get('login'), 'email': profile.get('email')})

        if not data['email']: data['email'] = profile.get('email') or profile.get('sub') or profile.get('id')
        if not data['name']: data['name'] = profile.get('display_name') or data['username'] or data['email']
        if not data['username']: data['username'] = data['email']

        logger.info(f"✨ New Social Login: {data['name']} ({data['email']}) via {provider}")
        return data

    def render_social_login_buttons(self):
        # 1. Handle Active Handshake
        active_provider = st.session_state.get('active_oauth_provider')
        if active_provider and active_provider in self.oauth_providers:
            settings = self.oauth_providers[active_provider]

            # CHECK FOR PLACEHOLDER KEYS
            if settings.get('client_id') in ['test-id', 'your-client-id', '...']:
                st.warning(f"🛠️ **{active_provider.title()} Login is in setup mode.** Please provide a valid Client ID in secrets.")
                if st.button("Back to Selection"):
                    st.session_state.pop('active_oauth_provider', None)
                    st.rerun()
                return None

            # --- SRE FIX: Bypassing Streamlit Cloud Sandbox Iframe ---
            # If we just selected a provider, we generate the Auth URL and redirect TOP level
            if 'oauth_redirect_initiated' not in st.session_state:
                st.info(f"Preparing secure connection to {active_provider.title()}...")

                # Build the URL (Simplified for the redirector)
                # Note: We still use OAuth2Component to handle the 'state' and 'code' later
                oauth2 = OAuth2Component(
                    client_id=settings.get('client_id'),
                    client_secret=settings.get('client_secret'),
                    authorize_endpoint=settings.get('authorize_endpoint'),
                    token_endpoint=settings.get('token_endpoint')
                )

                # Check for existing result (if we just came back)
                redir = settings.get('redirect_uri', 'https://market-rover.streamlit.app').rstrip("/")
                if "/component/" not in redir:
                    redir += "/component/streamlit_oauth.authorize_button"

                # Render the button but with a JS trigger to ensure it works in Streamlit Cloud
                result = oauth2.authorize_button(
                    name=f"Launch {active_provider.title()} Login",
                    redirect_uri=redir,
                    scope=settings.get('scope', 'openid email profile'),
                    key=f"oauth_btn_final_{active_provider}",
                    auto_click=False # Manual click is more reliable in some sandboxes
                )

                if result and 'token' in result:
                    st.session_state.pop('active_oauth_provider', None)
                    headers = {'Authorization': f"Bearer {result['token']['access_token']}"}
                    try:
                        response = httpx.get(settings.get('user_info_endpoint'), headers=headers, follow_redirects=True, timeout=15.0)
                        if response.is_success:
                            return self._normalize_profile(response.json(), active_provider)
                        else:
                            st.error(f"⚠️ {active_provider} API Error: {response.status_code}")
                    except Exception as req_err:
                        st.error(f"❌ User Info Error: {str(req_err)}")

                st.markdown("---")
                if st.button("Cancel Login"):
                    st.session_state.pop('active_oauth_provider', None)
                    st.rerun()
                return None

        # 2. Render Login UI
        st.markdown("""
            <style>
            .social-outer {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 40px 20px;
                background: linear-gradient(135deg, #0f0f15 0%, #1a1a25 100%);
                border-radius: 32px;
                border: 1px solid rgba(255,255,255,0.08);
                box-shadow: 0 30px 60px rgba(0,0,0,0.6);
                margin: 40px auto;
                max-width: 550px;
                text-align: center;
            }
            .social-header-small {
                font-family: 'Inter', sans-serif;
                font-size: 11px;
                font-weight: 800;
                color: #6366f1;
                letter-spacing: 3px;
                text-transform: uppercase;
                margin-bottom: 8px;
            }
            .social-title {
                font-size: 28px;
                font-weight: 900;
                color: white;
                margin-bottom: 24px;
                letter-spacing: -0.5px;
            }
            .platform-label {
                font-size: 10px;
                font-weight: 700;
                color: #888;
                margin-top: 8px;
                text-transform: uppercase;
            }
            </style>
            <div class="social-outer">
                <div class="social-header-small">Mission Intelligence</div>
                <div class="social-title">Connect your Social ID</div>
            </div>
        """, unsafe_allow_html=True)

        # Platforms mapping
        platforms = [
            {'id': 'google', 'name': 'Google', 'icon': 'https://img.icons8.com/color/96/google-logo.png'},
            {'id': 'facebook', 'name': 'Facebook', 'icon': 'https://img.icons8.com/color/96/facebook-new.png'},
            {'id': 'linkedin', 'name': 'LinkedIn', 'icon': 'https://img.icons8.com/color/96/linkedin.png'},
            {'id': 'github', 'name': 'GitHub', 'icon': 'https://img.icons8.com/glyph-neue/128/ffffff/github.png'},
            {'id': 'x', 'name': 'X', 'icon': 'https://img.icons8.com/ios-filled/100/ffffff/x-logo.png'}
        ]

        # Use st.columns for even distribution
        main_cols = st.columns([1, 12, 1])
        with main_cols[1]:
            # Create two rows if needed, but 5 columns should fit on wide layout
            btn_cols = st.columns(len(platforms))
            for i, p in enumerate(platforms):
                with btn_cols[i]:
                    is_available = p['id'] in self.oauth_providers

                    # Tooltip for status
                    status_text = "Click to Login" if is_available else "Coming Soon"

                    st.image(p['icon'], use_container_width=True)

                    if is_available:
                        if st.button("Login", key=f"login_{p['id']}", use_container_width=True, type="primary"):
                            st.session_state['active_oauth_provider'] = p['id']
                            st.rerun()
                    else:
                        st.button("Setup", key=f"login_{p['id']}", use_container_width=True, disabled=True)

                    st.markdown(f'<div class="platform-label">{p["name"]}</div>', unsafe_allow_html=True)

        st.markdown('<div style="margin-bottom: 50px;"></div>', unsafe_allow_html=True)

        return None

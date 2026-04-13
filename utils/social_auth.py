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
        if not self.oauth_providers: return None

        # 1. Capture the Round-Trip or Trigger
        trigger = st.query_params.get("login_trigger")
        if trigger and trigger in self.oauth_providers:
            settings = self.oauth_providers[trigger]
            c_id = settings.get('client_id', '')

            # THE SAFETY SHIELD: Stop redirection if ID is still a test placeholder
            if "test-id" in c_id.lower():
                st.query_params.clear()
                st.warning(f"🛡️ **Governance Check**: Identity Verification is currently pending for **{trigger.upper()}**. Please use **Google** for now.")
                st.session_state.pop('active_oauth_provider', None)
            else:
                st.session_state['active_oauth_provider'] = trigger
                st.query_params.clear()
                st.rerun()

        active_provider = st.session_state.get('active_oauth_provider')

        # 2. Complete the handshake
        if active_provider and active_provider in self.oauth_providers:
            settings = self.oauth_providers[active_provider]
            placeholder = st.empty()
            with placeholder.container():
                try:
                    redir = settings.get('redirect_uri', 'http://localhost:8501').rstrip("/")
                    if "/component/" not in redir: redir += "/component/streamlit_oauth.authorize_button"

                    oauth2 = OAuth2Component(
                        client_id=settings.get('client_id'),
                        client_secret=settings.get('client_secret'),
                        authorize_endpoint=settings.get('authorize_endpoint'),
                        token_endpoint=settings.get('token_endpoint'),
                        refresh_token_endpoint=settings.get('token_endpoint', None)
                    )

                    result = oauth2.authorize_button(
                        name="Authorizing...",
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
                                st.error(f"⚠️ Provider API Error ({active_provider}): {response.status_code}")
                                logger.error(f"User Info Error: {response.status_code} - {response.text}")
                        except Exception as req_err:
                            st.error(f"❌ Handshake Read Error: {str(req_err)}")
                            logger.error(f"Request Exception: {req_err}")
                except Exception as e:
                    logger.error(f"Auth Loop Error: {e}")
                    placeholder.empty()

        # 3. Render Landing UI (only if not handshaking)
        if not active_provider:
             logos = {'google': 'https://img.icons8.com/color/96/google-logo.png', 'facebook': 'https://img.icons8.com/color/96/facebook-new.png', 'linkedin': 'https://img.icons8.com/color/96/linkedin.png', 'x': 'https://img.icons8.com/ios-filled/100/twitterx.png'}
             icon_html = ""
             for name in self.oauth_providers.keys():
                 icon_html += f'<a href="?login_trigger={name}" target="_top" style="text-decoration:none;margin:0 12px;width:58px;height:58px;border-radius:50%;background:white;display:inline-flex;justify-content:center;align-items:center;box-shadow:0 1px 12px rgba(0,0,0,0.1);border:1px solid #eee;"><img src="{logos.get(name.lower(), "")}" style="width:28px;height:28px;object-fit:contain;"></a>'
             st.markdown(LOGIN_HTML_TEMPLATE.format(icon_html=icon_html), unsafe_allow_html=True)

        return None

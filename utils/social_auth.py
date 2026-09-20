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
    DEFAULT_PROVIDER_CONFIGS = {
        'github': {
            'authorize_endpoint': 'https://github.com/login/oauth/authorize',
            'token_endpoint': 'https://github.com/login/oauth/access_token',
            'user_info_endpoint': 'https://api.github.com/user',
            'scope': 'read:user user:email',
        },
        'x': {
            'authorize_endpoint': 'https://twitter.com/i/oauth2/authorize',
            'token_endpoint': 'https://api.twitter.com/2/oauth2/token',
            'user_info_endpoint': 'https://api.twitter.com/2/users/me',
            'scope': 'users.read tweet.read openid email',
        },
        'twitter': {
            'authorize_endpoint': 'https://twitter.com/i/oauth2/authorize',
            'token_endpoint': 'https://api.twitter.com/2/oauth2/token',
            'user_info_endpoint': 'https://api.twitter.com/2/users/me',
            'scope': 'users.read tweet.read openid email',
        },
        'google': {
            'authorize_endpoint': 'https://accounts.google.com/o/oauth2/v2/auth',
            'token_endpoint': 'https://oauth2.googleapis.com/token',
            'user_info_endpoint': 'https://www.googleapis.com/oauth2/v3/userinfo',
            'scope': 'openid email profile',
        },
        'facebook': {
            'authorize_endpoint': 'https://www.facebook.com/v12.0/dialog/oauth',
            'token_endpoint': 'https://graph.facebook.com/v12.0/oauth/access_token',
            'user_info_endpoint': 'https://graph.facebook.com/me',
            'scope': 'email,public_profile',
        },
        'linkedin': {
            'authorize_endpoint': 'https://www.linkedin.com/oauth/v2/authorization',
            'token_endpoint': 'https://www.linkedin.com/oauth/v2/accessToken',
            'user_info_endpoint': 'https://api.linkedin.com/v2/userinfo',
            'scope': 'openid profile email',
        },
    }

    def __init__(self, config=None):
        self._config = config or st.secrets
        self.oauth_providers = self._load_providers()

    def _load_providers(self):
        providers = {}
        if 'oauth' in self._config:
            for p_name, user_settings in self._config['oauth'].items():
                p_key = p_name.lower()
                merged = dict(self.DEFAULT_PROVIDER_CONFIGS.get(p_key, {}))
                if isinstance(user_settings, dict):
                    merged.update(user_settings)
                else:
                    try:
                        merged.update(dict(user_settings))
                    except Exception:
                        pass
                providers[p_key] = merged
        return providers

    def is_user_allowed(self, email):
        whitelist = self._config.get('approved_emails', [])
        if not whitelist: return True
        return email in whitelist

    def _normalize_profile(self, profile, provider):
        data = {'email': None, 'name': None, 'username': None, 'provider': provider}
        p = provider.lower()
        if p == 'google':
            data.update({
                'email': profile.get('email'),
                'name': profile.get('name'),
                'username': profile.get('email')
            })
        elif p == 'facebook':
            data.update({
                'email': profile.get('email'),
                'name': profile.get('name'),
                'username': profile.get('id') or profile.get('email')
            })
        elif p == 'linkedin':
            first = profile.get('localizedFirstName', profile.get('given_name', ''))
            last = profile.get('localizedLastName', profile.get('family_name', ''))
            name = f"{first} {last}".strip() or profile.get('name')
            email = profile.get('email') or profile.get('id')
            data.update({
                'name': name,
                'email': email,
                'username': email
            })
        elif p in ['github']:
            uname = profile.get('login') or profile.get('username')
            name = profile.get('name') or uname
            email = profile.get('email') or (f"{uname}@users.noreply.github.com" if uname else None)
            data.update({
                'name': name,
                'username': uname,
                'email': email
            })
        elif p in ['x', 'twitter']:
            u_data = profile.get('data', profile) if isinstance(profile, dict) else {}
            uname = u_data.get('username') or profile.get('screen_name') or u_data.get('id')
            name = u_data.get('name') or profile.get('name') or uname
            email = profile.get('email') or (f"{uname}@x.com" if uname else None)
            data.update({
                'name': name,
                'username': uname,
                'email': email
            })

        if not data['email']:
            data['email'] = profile.get('email') or profile.get('sub') or profile.get('id')
        if not data['name']:
            data['name'] = profile.get('display_name') or data['username'] or data['email'] or 'Analyst'
        if not data['username']:
            data['username'] = data['email'] or data['name'] or 'user'

        logger.info(f"✨ New Social Login: {data['name']} ({data['email']}) via {provider}")
        return data

    def render_social_login_buttons(self):
        # 1. Handle Active Handshake
        active_provider = st.session_state.get('active_oauth_provider')
        if active_provider and active_provider in self.oauth_providers:
            settings = self.oauth_providers[active_provider]

            # CHECK FOR PLACEHOLDER KEYS
            if settings.get('client_id') in ['test-id', 'your-client-id', '...', '']:
                st.warning(f"🛠️ **{active_provider.title()} Login is in setup mode.** Please provide a valid Client ID in secrets.")
                if st.button("Back to Selection"):
                    st.session_state.pop('active_oauth_provider', None)
                    st.rerun()
                return None

            # --- SRE FIX: Bypassing Streamlit Cloud Sandbox Iframe ---
            if 'oauth_redirect_initiated' not in st.session_state:
                st.info(f"Preparing secure connection to {active_provider.title()}...")

                oauth2 = OAuth2Component(
                    client_id=settings.get('client_id'),
                    client_secret=settings.get('client_secret'),
                    authorize_endpoint=settings.get('authorize_endpoint'),
                    token_endpoint=settings.get('token_endpoint')
                )

                redir = settings.get('redirect_uri', 'https://market-rover.streamlit.app').rstrip("/")
                if "/component/" not in redir:
                    redir += "/component/streamlit_oauth.authorize_button"

                default_scope = self.DEFAULT_PROVIDER_CONFIGS.get(active_provider, {}).get('scope', 'openid email profile')
                result = oauth2.authorize_button(
                    name=f"Launch {active_provider.title()} Login",
                    redirect_uri=redir,
                    scope=settings.get('scope', default_scope),
                    key=f"oauth_btn_final_{active_provider}",
                    auto_click=False
                )

                if result and 'token' in result:
                    st.session_state.pop('active_oauth_provider', None)
                    headers = {
                        'Authorization': f"Bearer {result['token']['access_token']}",
                        'User-Agent': 'Market-Rover-App/1.0',
                        'Accept': 'application/json, application/vnd.github.v3+json'
                    }
                    try:
                        response = httpx.get(settings.get('user_info_endpoint'), headers=headers, follow_redirects=True, timeout=15.0)
                        if response.is_success:
                            user_info = response.json()
                            # Extra email lookup for GitHub if user email is hidden
                            if active_provider == 'github' and not user_info.get('email'):
                                try:
                                    email_res = httpx.get('https://api.github.com/user/emails', headers=headers, follow_redirects=True, timeout=5.0)
                                    if email_res.is_success:
                                        emails = email_res.json()
                                        for em in emails:
                                            if isinstance(em, dict) and em.get('primary'):
                                                user_info['email'] = em.get('email')
                                                break
                                        if not user_info.get('email') and emails and isinstance(emails[0], dict):
                                            user_info['email'] = emails[0].get('email')
                                except Exception as e_err:
                                    logger.debug(f"GitHub email lookup skipped: {e_err}")

                            return self._normalize_profile(user_info, active_provider)
                        else:
                            st.error(f"⚠️ {active_provider.title()} API Error: {response.status_code}")
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
                padding: 36px 20px;
                background: linear-gradient(135deg, #0f0f15 0%, #1a1a25 100%);
                border-radius: 28px;
                border: 1px solid rgba(255,255,255,0.1);
                box-shadow: 0 25px 50px rgba(0,0,0,0.5);
                margin: 30px auto;
                max-width: 580px;
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
                font-size: 26px;
                font-weight: 900;
                color: #ffffff;
                margin-bottom: 6px;
                letter-spacing: -0.5px;
            }
            .social-subtitle {
                font-size: 13px;
                color: #94a3b8;
                margin-bottom: 0;
            }
            .platform-label {
                font-size: 11px;
                font-weight: 700;
                color: #e2e8f0;
                margin-top: 6px;
                text-align: center;
                letter-spacing: 0.5px;
                text-transform: uppercase;
            }
            </style>
            <div class="social-outer">
                <div class="social-header-small">Mission Intelligence</div>
                <div class="social-title">Connect your Social ID</div>
                <div class="social-subtitle">Sign in instantly via OAuth to unlock multi-agent market analytics</div>
            </div>
        """, unsafe_allow_html=True)

        # Platforms mapping with high-contrast, universally visible colored icons (compatible with both Dark & Light modes)
        platforms = [
            {
                'id': 'google',
                'name': 'Google',
                'icon': 'https://img.icons8.com/color/96/google-logo.png'
            },
            {
                'id': 'github',
                'name': 'GitHub',
                'icon': 'https://img.icons8.com/color/96/github--v1.png'
            },
            {
                'id': 'x',
                'name': 'X (Twitter)',
                'icon': 'https://img.icons8.com/color/96/twitterx--v1.png'
            },
            {
                'id': 'linkedin',
                'name': 'LinkedIn',
                'icon': 'https://img.icons8.com/color/96/linkedin.png'
            },
            {
                'id': 'facebook',
                'name': 'Facebook',
                'icon': 'https://img.icons8.com/color/96/facebook-new.png'
            }
        ]

        # Use st.columns for even distribution across all platforms
        main_cols = st.columns([1, 10, 1])
        with main_cols[1]:
            btn_cols = st.columns(len(platforms))
            for i, p in enumerate(platforms):
                with btn_cols[i]:
                    is_available = p['id'] in self.oauth_providers or (p['id'] == 'x' and 'twitter' in self.oauth_providers)

                    st.image(p['icon'], use_container_width=True)

                    if is_available:
                        prov_key = p['id'] if p['id'] in self.oauth_providers else 'twitter'
                        if st.button("Login", key=f"login_{p['id']}", use_container_width=True, type="primary"):
                            st.session_state['active_oauth_provider'] = prov_key
                            st.rerun()
                    else:
                        st.button("Setup", key=f"login_{p['id']}", use_container_width=True, disabled=True, help=f"Configure [oauth.{p['id']}] in secrets.toml")

                    st.markdown(f'<div class="platform-label">{p["name"]}</div>', unsafe_allow_html=True)

        st.markdown('<div style="margin-bottom: 40px;"></div>', unsafe_allow_html=True)

        return None

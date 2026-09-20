import pytest
from unittest.mock import MagicMock, patch
from utils.auth import AuthManager

@pytest.fixture
def mock_streamlit():
    with patch('utils.auth.st') as mock_st, \
         patch('utils.auth.stauth') as mock_stauth, \
         patch('utils.social_auth.st') as mock_social_st:

        # Mock secrets dict
        mock_secrets = {
            'credentials': {
                'usernames': ['user1'],
                'names': ['User One'],
                'passwords': ['pass1']
            },
            'cookie': {
                'name': 'cookie_name',
                'key': 'cookie_key',
                'expiry_days': 1
            },
            'oauth': {},
            'show_auth_debug': False # Add this to avoid default lookup issues
        }

        # Patch st.secrets on all mock objects
        mock_st.secrets = mock_secrets
        mock_st.session_state = {}

        mock_social_st.secrets = mock_secrets
        mock_social_st.session_state = {}

        # Ensure Authenticator returns a Mock object
        mock_authenticator_instance = MagicMock()
        mock_stauth.Authenticate.return_value = mock_authenticator_instance

        # Global patch as safety net
        with patch('streamlit.secrets', new=mock_secrets):
             yield mock_st

@pytest.fixture
def auth_manager(mock_streamlit):
    return AuthManager()

def test_check_authentication_session_true(mock_streamlit, auth_manager):
    mock_streamlit.session_state['authentication_status'] = True
    assert auth_manager.check_authentication() is True

def test_check_authentication_login_success(mock_streamlit, auth_manager):
    # Mock return value of authenticator.login
    # It sends (name, status, username) usually, but we care about session state effect
    with patch.object(auth_manager.authenticator, 'login') as mock_login:
        # Simulate login success by setting session state
        mock_streamlit.session_state['authentication_status'] = True
        assert auth_manager.check_authentication() is True

def test_check_authentication_login_fail(mock_streamlit, auth_manager):
    # Mock return value of authenticator.login
    with patch.object(auth_manager.authenticator, 'login') as mock_login:
        # Simulate login failure
        mock_streamlit.session_state['authentication_status'] = False
        assert auth_manager.check_authentication() is False


def test_social_auth_normalize_github_public_email():
    from utils.social_auth import SocialAuthManager
    mgr = SocialAuthManager(config={'oauth': {}})
    profile = {
        'login': 'octocat',
        'name': 'The Octocat',
        'email': 'octocat@github.com'
    }
    normalized = mgr._normalize_profile(profile, 'github')
    assert normalized['username'] == 'octocat'
    assert normalized['name'] == 'The Octocat'
    assert normalized['email'] == 'octocat@github.com'
    assert normalized['provider'] == 'github'


def test_social_auth_normalize_github_private_email():
    from utils.social_auth import SocialAuthManager
    mgr = SocialAuthManager(config={'oauth': {}})
    profile = {
        'login': 'private_user',
        'name': 'Private User',
        'email': None
    }
    normalized = mgr._normalize_profile(profile, 'github')
    assert normalized['username'] == 'private_user'
    assert normalized['name'] == 'Private User'
    assert normalized['email'] == 'private_user@users.noreply.github.com'


def test_social_auth_normalize_x_twitter():
    from utils.social_auth import SocialAuthManager
    mgr = SocialAuthManager(config={'oauth': {}})
    # Twitter API v2 format
    profile = {
        'data': {
            'id': '12345678',
            'name': 'Market Rover AI',
            'username': 'market_rover'
        }
    }
    normalized = mgr._normalize_profile(profile, 'x')
    assert normalized['username'] == 'market_rover'
    assert normalized['name'] == 'Market Rover AI'
    assert normalized['email'] == 'market_rover@x.com'
    assert normalized['provider'] == 'x'


def test_social_auth_load_provider_defaults():
    from utils.social_auth import SocialAuthManager
    cfg = {
        'oauth': {
            'github': {'client_id': 'gh_123', 'client_secret': 'gh_sec'},
            'x': {'client_id': 'x_123', 'client_secret': 'x_sec'},
            'linkedin': {'client_id': 'li_123', 'client_secret': 'li_sec'},
            'facebook': {'client_id': 'fb_123', 'client_secret': 'fb_sec'},
            'google': {'client_id': 'gg_123', 'client_secret': 'gg_sec'},
        }
    }
    mgr = SocialAuthManager(config=cfg)
    assert 'github' in mgr.oauth_providers
    assert mgr.oauth_providers['github']['authorize_endpoint'] == 'https://github.com/login/oauth/authorize'
    assert mgr.oauth_providers['github']['scope'] == 'read:user user:email'

    assert 'x' in mgr.oauth_providers
    assert mgr.oauth_providers['x']['authorize_endpoint'] == 'https://twitter.com/i/oauth2/authorize'
    assert 'users.read' in mgr.oauth_providers['x']['scope']

    assert 'linkedin' in mgr.oauth_providers
    assert mgr.oauth_providers['linkedin']['authorize_endpoint'] == 'https://www.linkedin.com/oauth/v2/authorization'
    assert mgr.oauth_providers['linkedin']['scope'] == 'openid profile email'

    assert 'facebook' in mgr.oauth_providers
    assert mgr.oauth_providers['facebook']['authorize_endpoint'] == 'https://www.facebook.com/v12.0/dialog/oauth'
    assert mgr.oauth_providers['facebook']['scope'] == 'email,public_profile'

    assert 'google' in mgr.oauth_providers
    assert mgr.oauth_providers['google']['authorize_endpoint'] == 'https://accounts.google.com/o/oauth2/v2/auth'
    assert mgr.oauth_providers['google']['scope'] == 'openid email profile'


def test_social_auth_normalize_linkedin():
    from utils.social_auth import SocialAuthManager
    mgr = SocialAuthManager(config={'oauth': {}})
    profile = {
        'given_name': 'Jane',
        'family_name': 'Doe',
        'email': 'jane.doe@linkedin.com'
    }
    normalized = mgr._normalize_profile(profile, 'linkedin')
    assert normalized['name'] == 'Jane Doe'
    assert normalized['email'] == 'jane.doe@linkedin.com'
    assert normalized['username'] == 'jane.doe@linkedin.com'
    assert normalized['provider'] == 'linkedin'


def test_social_auth_normalize_facebook():
    from utils.social_auth import SocialAuthManager
    mgr = SocialAuthManager(config={'oauth': {}})
    profile = {
        'id': 'fb_123456',
        'name': 'Facebook Analyst',
        'email': 'analyst@meta.com'
    }
    normalized = mgr._normalize_profile(profile, 'facebook')
    assert normalized['name'] == 'Facebook Analyst'
    assert normalized['email'] == 'analyst@meta.com'
    assert normalized['username'] == 'fb_123456'
    assert normalized['provider'] == 'facebook'

import pytest
from unittest.mock import MagicMock, patch
from utils.auth import AuthManager

@pytest.fixture
def mock_streamlit():
    with patch('utils.auth.st') as mock_st, \
         patch('utils.auth.stauth') as mock_stauth:
        
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
            'oauth': {}
        }
        
        # Patch st.secrets on the mock object
        mock_st.secrets = mock_secrets
        mock_st.session_state = {}
        
        # Ensure Authenticator returns a Mock object
        mock_authenticator_instance = MagicMock()
        mock_stauth.Authenticate.return_value = mock_authenticator_instance
        
        # Also patch streamlit.secrets just in case utils.auth accesses it before patch?
        # But patching the imported module 'utils.auth.st' should handle usages in that module.
        # We can keep the global patch for extra safety if needed, but the stauth mock is the key.
        # Let's keep the global patch too to be safe.
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

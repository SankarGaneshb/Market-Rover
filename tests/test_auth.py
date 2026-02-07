import pytest
from unittest.mock import MagicMock, patch
from utils.auth import AuthManager

@pytest.fixture
def mock_streamlit():
    with patch('utils.auth.st') as mock:
        mock.secrets = {
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
        mock.session_state = {}
        yield mock

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

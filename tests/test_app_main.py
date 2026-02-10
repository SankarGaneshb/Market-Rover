import sys
import pytest
from unittest.mock import MagicMock, patch
import importlib

@pytest.fixture
def mock_modules():
    """Mock all external dependencies to prevent loading binary extensions and isolate app logic."""
    mock_st = MagicMock()
    # Ensure nested mocks return MagicMocks to prevent attribute errors
    mock_st.sidebar = MagicMock()
    mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
    
    # Custom Session State that supports both attribute and item access
    class MockSessionState(dict):
        def __getattr__(self, key):
            try:
                return self[key]
            except KeyError:
                raise AttributeError(key)
        def __setattr__(self, key, value):
            self[key] = value
            
    mock_st.session_state = MockSessionState({
        'job_manager': MagicMock(),
        'current_job_id': None, 
        'analysis_complete': False,
        'test_mode': False,
        'heatmap_limiter': MagicMock(),
        'portfolio_limiter': MagicMock(),
        'username': 'test_user',
        'show_balloons': False
    })
    
    # Mock mocks for all used modules
    mocks = {
        'streamlit': mock_st,
        'streamlit.components': MagicMock(),
        'streamlit.components.v1': MagicMock(),
        'streamlit.runtime': MagicMock(),
        'streamlit.runtime.scriptrunner': MagicMock(),
        'plotly': MagicMock(),
        'rover_tools': MagicMock(),
        'utils': MagicMock(),
        'utils.job_manager': MagicMock(),
        'utils.metrics': MagicMock(),
        'utils.security': MagicMock(),
        'utils.auth': MagicMock(),
        'utils.user_manager': MagicMock(),
        'utils.logger': MagicMock(),
        'tabs': MagicMock(),
        'tabs.portfolio_tab': MagicMock(),
        'tabs.market_analysis_tab': MagicMock(),
        'tabs.forecast_tab': MagicMock(),
        'tabs.shadow_tab': MagicMock(),
        'tabs.profiler_tab': MagicMock(),
        'tabs.system_health': MagicMock(),
        'tabs.brain_tab': MagicMock(),
        'tabs.trading_calendar_tab': MagicMock(),
    }
    
    # Apply patches
    with patch.dict(sys.modules, mocks):
        yield mocks

def test_app_main_logic(mock_modules):
    # Import app inside the patched context
    # We use importlib.reload to re-run the module body (if it was already imported)
    if 'app' in sys.modules:
        import app
        importlib.reload(app)
    else:
        import app
        
    mock_st = mock_modules['streamlit']
    
    # Test 1: Auth Fail
    # Setup AuthManager mock
    auth_mgr = mock_modules['utils.auth'].AuthManager.return_value
    auth_mgr.check_authentication.return_value = False
    
    app.main()
    
    mock_st.stop.assert_called()
    mock_st.stop.reset_mock()
    
    # Test 2: Auth Success + Market Analysis
    auth_mgr.check_authentication.return_value = True
    mock_st.radio.return_value = "🔍 Market Analysis"
    mock_st.session_state['nav_selection'] = "🔍 Market Analysis"
    
    app.main()
    
    mock_modules['tabs.market_analysis_tab'].show_market_analysis_tab.assert_called()
    
    # Test 3: Auth Success + Portfolio Analysis
    mock_st.radio.return_value = "📤 Portfolio Analysis"
    mock_st.session_state['nav_selection'] = "📤 Portfolio Analysis"
    
    app.main()
    
    mock_modules['tabs.portfolio_tab'].show_portfolio_analysis_tab.assert_called()
    
    # Test 4: Balloons
    mock_st.session_state['show_balloons'] = True
    app.main()
    mock_st.balloons.assert_called()

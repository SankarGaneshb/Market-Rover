import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from utils.analysis_runner import run_analysis
from config import PORTFOLIO_FILE

@pytest.fixture
def mock_streamlit():
    with patch('utils.analysis_runner.st') as mock:
        # Setup session state
        mock.session_state = MagicMock()
        mock.session_state.job_manager = MagicMock()
        mock.session_state.test_mode = False
        mock.session_state.username = 'test_user'
        yield mock

@pytest.fixture
def mock_crew():
    with patch('utils.analysis_runner.create_crew') as mock:
        crew_instance = MagicMock()
        crew_instance.run.return_value = "Analysis Report Content"
        mock.return_value = crew_instance
        yield mock

@pytest.fixture
def mock_thread():
    with patch('utils.analysis_runner.threading.Thread') as mock:
        # Execute the target function immediately in the main thread for testing
        def side_effect(target=None, **kwargs):
            target()
            return MagicMock()
        mock.side_effect = side_effect
        yield mock

@pytest.fixture
def sample_portfolio():
    return pd.DataFrame({
        'Symbol': ['RELIANCE.NS', 'TCS.NS'],
        'Company Name': ['Reliance', 'TCS'],
        'Quantity': [10, 5],
        'Average Price': [2500, 3500]
    })

def test_run_analysis_success(mock_streamlit, mock_crew, mock_thread, sample_portfolio):
    # Setup job manager mock
    job_id = "job_123"
    mock_streamlit.session_state.job_manager.create_job.return_value = job_id
    
    # Run analysis
    with patch('builtins.open', new_callable=MagicMock) as mock_open:
        run_analysis(sample_portfolio, "portfolio.csv", max_parallel=2)
    
    # Verify job creation and start
    mock_streamlit.session_state.job_manager.create_job.assert_called()
    mock_streamlit.session_state.job_manager.start_job.assert_called_with(job_id)
    
    # Verify crew execution
    mock_crew.assert_called()
    mock_crew.return_value.run.assert_called()
    
    # Verify job completion
    mock_streamlit.session_state.job_manager.complete_job.assert_called_with(job_id, "Analysis Report Content")
    
    # Verify success message
    mock_streamlit.success.assert_called()

def test_run_analysis_failure(mock_streamlit, mock_crew, mock_thread, sample_portfolio):
    # Setup crew to raise exception
    mock_crew.return_value.run.side_effect = Exception("API Error")
    
    job_id = "job_123"
    mock_streamlit.session_state.job_manager.create_job.return_value = job_id
    
    # Run analysis
    run_analysis(sample_portfolio, "portfolio.csv", max_parallel=2)
    
    # Verify job failure
    mock_streamlit.session_state.job_manager.fail_job.assert_called_with(job_id, "API Error")
    
    # Verify error message
    mock_streamlit.error.assert_called()

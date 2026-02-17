import streamlit as st
import pytest
from unittest.mock import MagicMock, patch, call
import pandas as pd
import threading
from utils.analysis_runner import run_analysis

@pytest.fixture(autouse=True)
def mock_sleep():
    with patch('utils.analysis_runner.time.sleep'):
        yield

@pytest.fixture
def mock_streamlit():
    with patch('utils.analysis_runner.st') as mock:
        # Setup basic session state
        mock.session_state = MagicMock()
        mock.session_state.get.return_value = 'test_user'
        mock.session_state.job_manager = MagicMock()
        mock.session_state.test_mode = False
        mock.session_state.username = 'test_user'
        
        # Setup UI elements
        mock.empty.return_value = MagicMock()
        mock.progress.return_value = MagicMock()
        mock.columns.return_value = [MagicMock(), MagicMock(), MagicMock(), MagicMock()] 
        
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
        # Create a mock thread instance
        thread_instance = MagicMock()
        mock.return_value = thread_instance
        
        # Define side effect for start(): run the target function
        def start_side_effect():
            # Retrieve target from constructor call
            if mock.call_args:
                args, kwargs = mock.call_args
                target = kwargs.get('target')
                if target:
                    target()
        
        thread_instance.start.side_effect = start_side_effect
        yield mock

@pytest.fixture
def mock_visualizer():
    with patch('utils.analysis_runner.ReportVisualizer') as mock:
        viz_instance = MagicMock()
        mock.return_value = viz_instance
        yield mock

@pytest.fixture
def mock_market_analyzer():
    with patch('rover_tools.market_analytics.MarketAnalyzer') as mock:
        ma_instance = MagicMock()
        # Mock correlation matrix
        ma_instance.calculate_correlation_matrix.return_value = pd.DataFrame()
        # Mock rebalance
        ma_instance.analyze_rebalance.return_value = (pd.DataFrame(), "analysis")
        mock.return_value = ma_instance
        yield mock

@pytest.fixture
def mock_shadow_tools():
    with patch('utils.analysis_runner.detect_silent_accumulation') as mock:
        mock.return_value = {'score': 50, 'signals': ['Test Signal']}
        yield mock

@pytest.fixture
def sample_portfolio():
    return pd.DataFrame({
        'Symbol': ['RELIANCE.NS', 'TCS.NS'],
        'Company Name': ['Reliance', 'TCS'],
        'Quantity': [10, 5],
        'Average Price': [2500, 3500]
    })

def test_run_analysis_success_real_mode(
    mock_streamlit, mock_crew, mock_thread, mock_visualizer, 
    mock_market_analyzer, mock_shadow_tools, sample_portfolio
):
    # Setup
    job_id = "job_123"
    mock_streamlit.session_state.job_manager.create_job.return_value = job_id
    mock_streamlit.session_state.test_mode = False
    
    # Run
    with patch('builtins.open', new_callable=MagicMock) as mock_open:
        with patch('utils.analysis_runner.logger'): # Suppress logs
            run_analysis(sample_portfolio, "portfolio.csv", max_parallel=2)
    
    # Verify Job Flow
    mock_streamlit.session_state.job_manager.create_job.assert_called()
    mock_streamlit.session_state.job_manager.start_job.assert_called_with(job_id)
    mock_streamlit.session_state.job_manager.complete_job.assert_called()
    
    # Verify Crew Execution
    mock_crew.assert_called()
    mock_crew.return_value.run.assert_called()
    
    # Verify UI Interaction (Progress, Success)
    mock_streamlit.progress.assert_called()
    mock_streamlit.success.assert_called()
    
    # Verify Visualization and Post-Processing
    mock_market_analyzer.assert_called() # Risk analysis init
    mock_visualizer.assert_called() # Visualizer init

def test_run_analysis_success_test_mode(
    mock_streamlit, mock_crew, mock_thread, mock_visualizer,
    mock_market_analyzer, mock_shadow_tools, sample_portfolio
):
    # Setup
    job_id = "job_123"
    mock_streamlit.session_state.job_manager.create_job.return_value = job_id
    mock_streamlit.session_state.test_mode = True
    
    # Mock mock_generator to avoid dependency on utils
    with patch('utils.analysis_runner.mock_generator') as mock_gen:
        mock_gen.generate_mock_report.return_value = "Mock Report"
        mock_gen.generate_sentiment_data.return_value = {'positive': 5}
        
        # Run
        with patch('builtins.open', new_callable=MagicMock):
             # Mock time.sleep to speed up test
            with patch('utils.analysis_runner.time.sleep'):
                run_analysis(sample_portfolio, "portfolio.csv", max_parallel=2)
                
    # Verify
    mock_streamlit.session_state.job_manager.complete_job.assert_called_with(job_id, "Mock Report")
    mock_crew.assert_not_called() # Should not create crew in test mode

def test_run_analysis_failure_crew_error(
    mock_streamlit, mock_crew, mock_thread, sample_portfolio
):
    # Setup
    mock_streamlit.session_state.test_mode = False
    job_id = "job_fail"
    mock_streamlit.session_state.job_manager.create_job.return_value = job_id
    
    # Make crew raise exception
    mock_crew.return_value.run.side_effect = Exception("API Connection Failed")
    
    # Run
    with patch('utils.analysis_runner.logger'):
        run_analysis(sample_portfolio, "portfolio.csv", max_parallel=2)
        
    # Verify
    mock_streamlit.session_state.job_manager.fail_job.assert_called_with(job_id, "API Connection Failed")
    mock_streamlit.error.assert_called()

def test_run_analysis_save_portfolio_error(
    mock_streamlit, mock_crew, mock_thread, sample_portfolio
):
    # Setup
    mock_streamlit.session_state.test_mode = False
    
    # Force error on to_csv
    # We need to mock to_csv on the dataframe, but since run_analysis calls to_csv on the passed df...
    # We can pass a mock object instead of a real dataframe if we are careful, 
    # OR we can patch pd.DataFrame.to_csv. Let's patch to_csv
    
    with patch.object(pd.DataFrame, 'to_csv', side_effect=Exception("Disk Full")):
        with patch('utils.analysis_runner.logger') as mock_logger:
            # Should still proceed, just log error
            run_analysis(sample_portfolio, "portfolio.csv", max_parallel=2)
            
            # Verify log
            mock_logger.error.assert_called()
            # Should still try to run crew
            mock_crew.assert_called()

def test_run_analysis_runtime_error_in_thread(
    mock_streamlit, mock_crew, mock_thread, sample_portfolio
):
    # Setup
    mock_streamlit.session_state.test_mode = False
    job_id = "job_runtime"
    mock_streamlit.session_state.job_manager.create_job.return_value = job_id
    
    # Simulate RuntimeError (e.g., cannot schedule new futures)
    mock_crew.return_value.run.side_effect = RuntimeError("cannot schedule new futures")
    
    # Run
    with patch('utils.analysis_runner.logger'):
        run_analysis(sample_portfolio, "portfolio.csv", max_parallel=2)
    
    # Verify it was caught and translated
    # The fail_job call should contain the friendly message
    args, _ = mock_streamlit.session_state.job_manager.fail_job.call_args
    assert args[0] == job_id
    assert "Model Overload/Timeout" in str(args[1])

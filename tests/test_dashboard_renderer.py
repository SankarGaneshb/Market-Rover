import pytest
import pandas as pd
import numpy as np
import io
from unittest.mock import MagicMock, patch
from rover_tools.dashboard_renderer import DashboardRenderer

@pytest.fixture
def renderer():
    return DashboardRenderer()

@pytest.fixture
def sample_data():
    # History DF
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    history_df = pd.DataFrame({'Close': np.linspace(100, 200, 100)}, index=dates)
    
    # OI Data
    oi_data = {
        'pcr': 1.5,
        'max_pain': 15000,
        'support_strike': 14000,
        'resistance_strike': 16000,
        'expiry': '29-Feb',
        'strikes': [14000, 15000, 16000],
        'ce_ois': [100, 200, 500],
        'pe_ois': [500, 200, 100]
    }
    
    # Scenarios
    scenarios = {
        'bull_target': 220,
        'bear_target': 180,
        'neutral_range': (190, 210),
        'expected_move': 10
    }
    
    # Returns Matrix
    returns_matrix = pd.DataFrame({
        'Jan': [1.0, 2.0],
        'Feb': [-1.0, 0.5]
    }, index=[2023, 2024])
    
    # Forecast 2026
    forecast_2026 = {
        'target_date': pd.Timestamp('2026-12-31'),
        'consensus_target': 300,
        'range_low': 280,
        'range_high': 320,
        'cagr_percent': 15.0,
        'models': {
            'Trend (Linear Reg)': 290,
            'CAGR (Growth)': 310
        }
    }
    
    return {
        'ticker': 'TEST',
        'history_df': history_df,
        'oi_data': oi_data,
        'scenarios': scenarios,
        'returns_matrix': returns_matrix,
        'forecast_2026': forecast_2026
    }

@patch('rover_tools.dashboard_renderer.plt')
def test_generate_dashboard_decorator_removed(renderer, sample_data): # Removing patch decorator
    pass

def test_generate_dashboard(renderer, sample_data):
    with patch('rover_tools.dashboard_renderer.plt') as mock_plt, \
         patch('rover_tools.dashboard_renderer.sns') as mock_sns:
        # Setup mocks
        mock_fig = MagicMock()
        mock_plt.figure.return_value = mock_fig
        
        # Run
        buf = renderer.generate_dashboard(
            sample_data['ticker'],
            sample_data['history_df'],
            sample_data['oi_data'],
            sample_data['scenarios'],
            sample_data['returns_matrix'],
            sample_data['forecast_2026']
        )
        
        # Verify
        assert isinstance(buf, io.BytesIO)
        mock_plt.switch_backend.assert_called_with('Agg')
        mock_plt.figure.assert_called()
        mock_plt.close.assert_called()
        
        # Verify subplots were created
        assert mock_fig.add_subplot.call_count >= 4
        
        # Verify sns calls
        mock_sns.heatmap.assert_called()

def test_generate_pdf_report(renderer, sample_data):
    with patch('rover_tools.dashboard_renderer.plt') as mock_plt, \
         patch('rover_tools.dashboard_renderer.PdfPages') as mock_pdf_pages, \
         patch('rover_tools.dashboard_renderer.sns') as mock_sns:
        
        # Setup mocks
        mock_pdf = MagicMock()
        mock_pdf_pages.return_value.__enter__.return_value = mock_pdf
        
        # Additional data for PDF
        seasonality_stats = pd.DataFrame({
            'Month_Name': ['Jan', 'Feb'],
            'Win_Rate': [60, 40],
            'Avg_Return': [2.5, -1.0]
        })
        
        mock_calendar_tool = MagicMock()
        mock_calendar_tool.plot_calendar.return_value = MagicMock() # The figure
        
        calendar_df = pd.DataFrame({
            'Month': ['January', 'February'],
            'Best_Buy_Day_Raw': [1, 5],
            'Best_Sell_Day_Raw': [10, 15],
            'Avg_Gain_Pct': [5.5, 2.3],
            'Avg_Annual_Gain': [10.2, 8.5]
        })
        
        # Run
        buf = renderer.generate_pdf_report(
            sample_data['ticker'],
            sample_data['history_df'],
            sample_data['scenarios'],
            sample_data['returns_matrix'],
            sample_data['forecast_2026'],
            seasonality_stats,
            mock_calendar_tool,
            calendar_df,
            calendar_df # reusing for muhurta for test
        )
        
        # Verify
        assert isinstance(buf, io.BytesIO)
        mock_pdf.savefig.assert_called()
        assert mock_pdf.savefig.call_count >= 1

def test_plot_price_chart_handles_empty_data(renderer):
    with patch('rover_tools.dashboard_renderer.plt') as mock_plt:
        # Test graceful handling of empty data
        mock_ax = MagicMock()
        renderer._plot_price_chart(mock_ax, "TEST", pd.DataFrame(), {})
        
        # Should write text on axes instead of failing
        mock_ax.text.assert_called()
        assert "No recent price data" in mock_ax.text.call_args[0]

def test_plot_oi_chart_handles_empty_data(renderer):
    with patch('rover_tools.dashboard_renderer.plt') as mock_plt:
        mock_ax = MagicMock()
        renderer._plot_oi_chart(mock_ax, {})
        
        mock_ax.text.assert_called()
        assert "No OI Data Available" in mock_ax.text.call_args[0]

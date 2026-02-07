
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from rover_tools.analytics.win_rate import get_performance_stars

# Mock yfinance data
@pytest.fixture
def mock_yf_data():
    dates = pd.date_range(start="2019-01-01", end="2025-01-01", freq="ME")
    
    # Stock A: Constant growth (Best)
    data_a = pd.Series(range(len(dates)), index=dates, name="STOCK_A.NS") * 10 
    
    # Stock B: Flat
    data_b = pd.Series([100]*len(dates), index=dates, name="STOCK_B.NS")
    
    # Stock C: Decline
    data_c = pd.Series(range(len(dates), 0, -1), index=dates, name="STOCK_C.NS") * 10
    
    # Stock D: Moderate growth
    data_d = pd.Series(range(len(dates)), index=dates, name="STOCK_D.NS") * 5

    df = pd.DataFrame({
        "STOCK_A.NS": data_a,
        "STOCK_B.NS": data_b,
        "STOCK_C.NS": data_c,
        "STOCK_D.NS": data_d
    })
    return df

@patch("rover_tools.analytics.win_rate.yf.download")
@patch("rover_tools.analytics.win_rate.get_common_tickers")
def test_get_performance_stars_1y(mock_get_tickers, mock_download, mock_yf_data):
    # Setup mocks
    mock_get_tickers.return_value = ["STOCK_A.NS", "STOCK_B.NS", "STOCK_C.NS", "STOCK_D.NS"]
    
    # Mock download to return data
    # yfinance download returns a DataFrame with MultiIndex columns if group_by='ticker' (default)
    # But usually 'Close' is accessed. Our function expects just a DataFrame of Close prices if we mock it right.
    # The actual code does: data = yf.download(...)['Close']
    
    # So we mock the return of download to be an object where ['Close'] returns our df
    mock_download_obj = MagicMock()
    mock_download_obj.__getitem__.return_value = mock_yf_data
    mock_download.return_value = {"Close": mock_yf_data} # simplified mock for dict access or adjust if needed
    
    # Actually yf.download returns a DF. The code does `yf.download(...)['Close']`. 
    # So valid mock is:
    mock_download.return_value = pd.concat([mock_yf_data], keys=['Close'], axis=1)

    # Test 5Y (Full range of mock data)
    stars = get_performance_stars(category="Test", period="5y", top_n=2)
    
    assert len(stars) == 2
    assert stars[0]['ticker'] == "STOCK_A.NS" # Highest growth
    assert stars[1]['ticker'] == "STOCK_D.NS" # Second highest
    
    # Verify return values are positive
    assert stars[0]['total_return'] > 0

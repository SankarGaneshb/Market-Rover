
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from rover_tools.market_data import MarketDataFetcher

@pytest.fixture
def fetcher():
    return MarketDataFetcher()

@pytest.fixture
def mock_yf():
    with patch('yfinance.Ticker') as mock:
        yield mock

def test_fetch_ltp_primary_success(fetcher, mock_yf):
    # Setup: .NS succeeds
    mock_instance = mock_yf.return_value
    mock_instance.fast_info = {'last_price': 100.0}
    
    price = fetcher.fetch_ltp("RELIANCE")
    assert price == 100.0
    # Should have called with .NS (default)
    mock_yf.assert_called_with("RELIANCE.NS")

def test_fetch_ltp_fallback_success(fetcher, mock_yf):
    # Setup: .NS fails, .BO succeeds
    
    # We need side_effect on the constructor to return different mocks or
    # side_effect on the mock instance methods/properties?
    # The code creates a NEW Ticker("...") each time.
    
    def side_effect(ticker):
        instance = MagicMock()
        if ticker.endswith(".NS"):
            # Simulate failure (fast_info dict access returns None or raises error?)
            # The code checks `price is None` or catches Exception.
            # _fetch_yf_price_unsafe raises ValueError if None.
            # Let's make it return None for fast_info['last_price']
            instance.fast_info = {'last_price': None}
        elif ticker.endswith(".BO"):
            instance.fast_info = {'last_price': 200.0}
        return instance

    mock_yf.side_effect = side_effect
    
    price = fetcher.fetch_ltp("RELIANCE")
    assert price == 200.0

def test_fetch_history_fallback_success(fetcher, mock_yf):
    # Setup: .NS empty, .BO has data
    def side_effect(ticker):
        instance = MagicMock()
        if ticker.endswith(".NS"):
            instance.history.return_value = pd.DataFrame()
        elif ticker.endswith(".BO"):
            instance.history.return_value = pd.DataFrame({'Close': [100]})
        return instance

    mock_yf.side_effect = side_effect
    
    hist = fetcher.fetch_historical_data("TCS")
    assert not hist.empty
    assert hist.iloc[0]['Close'] == 100

def test_fetch_all_fail(fetcher, mock_yf):
    # Setup: Both fail
    mock_instance = mock_yf.return_value
    mock_instance.fast_info = {'last_price': None}
    
    price = fetcher.fetch_ltp("FAIL")
    assert price is None

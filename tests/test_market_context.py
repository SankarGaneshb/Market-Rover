import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from rover_tools.market_context_tool import analyze_market_context

@pytest.fixture
def mock_yf_ticker():
    with patch('yfinance.Ticker') as mock:
        yield mock

def test_analyze_market_context_no_portfolio(mock_yf_ticker):
    # Setup mocks for Nifty 50 and Bank Nifty
    # Mock Nifty 50 (^NSEI)
    mock_nifty_hist = pd.DataFrame({'Close': [100, 101, 102, 103, 104, 105]}) # rising
    mock_bank_hist = pd.DataFrame({'Close': [200, 201, 202, 203, 204, 205]})
    
    # Configure mock side_effect based on ticker symbol
    def side_effect(symbol):
        ticker = MagicMock()
        if 'NSEI' in symbol:
            ticker.history.return_value = mock_nifty_hist
            ticker.info = {'name': 'Nifty 50'}
        elif 'NSEBANK' in symbol:
            ticker.history.return_value = mock_bank_hist
            ticker.info = {'name': 'Bank Nifty'}
        else:
            ticker.history.return_value = pd.DataFrame() # Default empty
        return ticker

    mock_yf_ticker.side_effect = side_effect
    
    result = analyze_market_context.run()
    assert "Nifty 50" in result
    assert "Bank Nifty" in result
    assert "Positive" in result
    assert "Market is showing" in result

def test_analyze_market_context_with_stocks(mock_yf_ticker):
    # Setup mocks for Ticker logic
    # We need to handle:
    # 1. Stock Info fetching (for sector detection)
    # 2. Index History fetching
    
    def side_effect(symbol):
        ticker = MagicMock()
        
        # Stock Logic
        if "TCS" in symbol:
            ticker.info = {'sector': 'Technology'}
        elif "TATAMOTORS" in symbol:
            ticker.info = {'sector': 'Automotive'}
            
        # Index Logic
        elif "NSEI" in symbol: # Nifty
             ticker.history.return_value = pd.DataFrame({'Close': [100]*10})
        elif "NSEBANK" in symbol: # Bank Nifty
             ticker.history.return_value = pd.DataFrame({'Close': [200]*10})
        elif "CNXIT" in symbol: # IT Sector
             ticker.history.return_value = pd.DataFrame({'Close': [300, 310, 320, 330, 340, 350]}) # Strong
        elif "CNXAUTO" in symbol: # Auto Sector
             ticker.history.return_value = pd.DataFrame({'Close': [400, 390, 380, 370, 360, 350]}) # Weak
        else:
             ticker.history.return_value = pd.DataFrame()
             ticker.info = {}
             
        return ticker

    mock_yf_ticker.side_effect = side_effect
    
    # Run with TCS (IT) and TATAMOTORS (Auto)
    result = analyze_market_context.run("TCS, TATAMOTORS")
    
    assert "Nifty 50" in result
    assert "Nifty IT (Portfolio Sector)" in result
    assert "Nifty Auto (Portfolio Sector)" in result
    # IT should be positive
    # Auto should be negative (implied by 400->350) 
    # Logic: week change uses -5 index. 
    # [400, 390, 380, 370, 360, 350] len 6. 
    # current=350. week_ago=390 (index -5 if available, else 0).
    # 350 < 390 -> Negative.
    
    assert "Analyzed sectors based on portfolio: Auto, IT" in result or "IT, Auto" in result

def test_analyze_market_context_error_handling(mock_yf_ticker):
    mock_yf_ticker.side_effect = Exception("API Down")
    
    result = analyze_market_context.run()
    assert "Error analyzing market context" in result

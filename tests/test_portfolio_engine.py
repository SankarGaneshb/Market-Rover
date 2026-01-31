
import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
from rover_tools.analytics.portfolio_engine import AnalyticsPortfolio

# Create a concrete class for testing that implements the missing mixin methods
class TestablePortfolio(AnalyticsPortfolio):
    def calculate_volatility(self, data):
        # Simple volatility mock: std dev of pct_change * sqrt(252)
        if isinstance(data, pd.DataFrame):
            rets = data.pct_change().dropna()
            return rets.std().iloc[0] * np.sqrt(252) if not rets.empty else 0.0
        return 0.15 # Default mock

    def _remove_outliers(self, series):
        # Pass-through for testing
        return series

@pytest.fixture
def portfolio():
    return TestablePortfolio()

@pytest.fixture
def mock_yf_download():
    with patch('yfinance.download') as mock:
        yield mock

@pytest.fixture
def mock_ticker():
    with patch('yfinance.Ticker') as mock:
        yield mock

def test_calculate_correlation_matrix_empty(portfolio):
    assert portfolio.calculate_correlation_matrix([]).empty
    assert portfolio.calculate_correlation_matrix(['AAPL']).empty

def test_calculate_correlation_matrix_success(portfolio, mock_yf_download):
    # Mock data for 2 tickers
    dates = pd.date_range(start='2023-01-01', periods=10)
    data = pd.DataFrame({
        'AAPL': np.random.uniform(100, 110, 10),
        'GOOG': np.random.uniform(200, 220, 10)
    }, index=dates)
    data.columns.name = 'Ticker'
    
    # Mocking the MultiIndex return structure often seen in yfinance
    # Or just flat if the code handles it. Code handles flat.
    mock_yf_download.return_value = data
    
    # Force 'Close' column check in code - the code checks for 'Close' or if columns intersect tickers
    # Let's provide a DataFrame that looks like Case 3 (columns are tickers)
    
    corr = portfolio.calculate_correlation_matrix(['AAPL', 'GOOG'])
    assert not corr.empty
    assert corr.shape == (2, 2)
    assert corr.iloc[0, 0] == 1.0

def test_analyze_rebalance_empty(portfolio):
    df, warnings = portfolio.analyze_rebalance([])
    assert df.empty
    assert warnings == []

def test_analyze_rebalance_safety(portfolio, mock_yf_download):
    portfolio_data = [
        {'symbol': 'AAPL', 'value': 1000},
        {'symbol': 'GOOG', 'value': 1000}
    ]
    
    # Mock market data
    dates = pd.date_range(start='2023-01-01', periods=50)
    # Low volatility for AAPL, High for GOOG
    aapl_prices = np.linspace(100, 105, 50) # Stable
    goog_prices = np.linspace(100, 150, 50) + np.random.normal(0, 5, 50) # Volatile
    
    data = pd.DataFrame({
        'AAPL': aapl_prices,
        'GOOG': goog_prices
    }, index=dates)
    
    mock_yf_download.return_value = data
    
    df, warnings = portfolio.analyze_rebalance(portfolio_data, mode="safety")
    
    assert not df.empty
    assert 'target_weight' in df.columns
    
    # Safety mode should weight lower volatility (AAPL) higher
    row_aapl = df[df['symbol'] == 'AAPL'].iloc[0]
    row_goog = df[df['symbol'] == 'GOOG'].iloc[0]
    
    assert row_aapl['volatility'] < row_goog['volatility']
    assert row_aapl['target_weight'] > row_goog['target_weight']
    assert row_aapl['action'] in ['Buy', 'Sell', 'Hold']

def test_analyze_rebalance_growth(portfolio, mock_yf_download):
    portfolio_data = [
        {'symbol': 'AAPL', 'value': 1000},
        {'symbol': 'GOOG', 'value': 1000}
    ]
    
    # Mock market data
    dates = pd.date_range(start='2023-01-01', periods=50)
    # High return for AAPL
    aapl_prices = np.linspace(100, 200, 50) 
    # Low return for GOOG
    goog_prices = np.linspace(100, 101, 50)
    
    data = pd.DataFrame({
        'AAPL': aapl_prices,
        'GOOG': goog_prices
    }, index=dates)
    mock_yf_download.return_value = data
    
    df, warnings = portfolio.analyze_rebalance(portfolio_data, mode="growth")
    
    # Growth mode (Sharpe) should favor higher return/volatility
    row_aapl = df[df['symbol'] == 'AAPL'].iloc[0]
    row_goog = df[df['symbol'] == 'GOOG'].iloc[0]
    
    # AAPL has massive return, should have higher weight
    assert row_aapl['return'] > row_goog['return']
    assert row_aapl['target_weight'] > row_goog['target_weight']

def test_calculate_risk_score(portfolio, mock_ticker):
    # Mock history
    mock_hist = pd.DataFrame({'Close': [100, 101, 102, 101, 100]})
    mock_ticker.return_value.history.return_value = mock_hist
    
    score = portfolio.calculate_risk_score("AAPL")
    assert 0 <= score <= 100
    
    # Test fallback
    mock_ticker.return_value.history.return_value = pd.DataFrame()
    assert portfolio.calculate_risk_score("INVALID") == 50

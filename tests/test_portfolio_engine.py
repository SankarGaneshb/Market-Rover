import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
from rover_tools.analytics.portfolio_engine import AnalyticsPortfolio

@pytest.fixture
def engine():
    return AnalyticsPortfolio()

@pytest.fixture
def mock_market_data():
    # Create sample price data for 2 tickers over 100 days
    dates = pd.date_range(start='2024-01-01', periods=100)
    data = pd.DataFrame({
        'T1': np.random.normal(100, 1, 100).cumsum() + 100,
        'T2': np.random.normal(100, 1, 100).cumsum() + 100
    }, index=dates)
    return data

def test_remove_outliers(engine):
    returns = pd.Series(np.random.normal(0, 0.01, 100))
    # Add outliers
    returns.iloc[0] = 10.0
    returns.iloc[1] = -10.0
    
    clean = engine._remove_outliers(returns)
    assert len(clean) < len(returns)
    assert 10.0 not in clean.values
    assert -10.0 not in clean.values

def test_calculate_volatility(engine):
    # Constant price -> 0 vol
    data = pd.DataFrame({'Close': [100, 100, 100, 100]})
    vol = engine.calculate_volatility(data)
    assert vol == 0.0
    
    # Volatile price
    data_vol = pd.DataFrame({'Close': [100, 105, 95, 110, 90]})
    vol_res = engine.calculate_volatility(data_vol)
    assert vol_res > 0.0

def test_calculate_correlation_matrix(engine, mock_market_data):
    with patch('rover_tools.analytics.portfolio_engine.yf.download') as mock_download:
        # yf.download returns DataFrame with columns as tickers (flat or MultiIndex)
        # Let's mock simple case
        mock_download.return_value = mock_market_data
        
        corr = engine.calculate_correlation_matrix(['T1', 'T2'])
        assert not corr.empty
        assert corr.shape == (2, 2)
        assert corr.iloc[0, 0] == 1.0 # Self correlation

def test_calculate_correlation_matrix_empty(engine):
    with patch('rover_tools.analytics.portfolio_engine.yf.download') as mock_download:
        mock_download.return_value = pd.DataFrame()
        corr = engine.calculate_correlation_matrix(['T1', 'T2'])
        assert corr.empty

def test_analyze_rebalance_safety(engine, mock_market_data):
    with patch('rover_tools.analytics.portfolio_engine.yf.download') as mock_download:
        mock_download.return_value = mock_market_data
        
        portfolio = [
            {'symbol': 'T1', 'value': 1000},
            {'symbol': 'T2', 'value': 1000}
        ]
        
        df, warnings = engine.analyze_rebalance(portfolio, mode="safety")
        
        assert not df.empty
        assert 'action' in df.columns
        assert 'comment' in df.columns
        assert df['current_weight'].sum() == pytest.approx(1.0)
        assert df['target_weight'].sum() == pytest.approx(1.0)

def test_analyze_rebalance_growth(engine, mock_market_data):
    with patch('rover_tools.analytics.portfolio_engine.yf.download') as mock_download:
        mock_download.return_value = mock_market_data
        
        portfolio = [
            {'symbol': 'T1', 'value': 500},
            {'symbol': 'T2', 'value': 1500} # Imbalanced
        ]
        
        df, warnings = engine.analyze_rebalance(portfolio, mode="growth")
        
        assert not df.empty
        assert isinstance(warnings, list)
        assert df['target_weight'].sum() == pytest.approx(1.0)
        
        # Check logic: diff should exist
        assert 'diff' not in df.columns # It is internal, but action reflects it
        assert df['action'].iloc[0] in ['Buy', 'Sell', 'Hold']

def test_calculate_risk_score(engine):
    with patch('rover_tools.analytics.portfolio_engine.yf.Ticker') as MockTicker:
        mock_hist = pd.DataFrame({'Close': [100, 101, 102, 99, 98]})
        MockTicker.return_value.history.return_value = mock_hist
        
        score = engine.calculate_risk_score("RELIANCE")
        assert 0 <= score <= 100

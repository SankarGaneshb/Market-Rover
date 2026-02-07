import pytest
import pandas as pd
import numpy as np
from rover_tools.derivative_analysis import DerivativeAnalyzer

@pytest.fixture
def analyzer():
    return DerivativeAnalyzer()

@pytest.fixture
def sample_history():
    dates = pd.date_range(start='2023-01-01', periods=365, freq='D')
    # Create a simple trend + noise
    # We use enough data to ensure monthly stats are possible
    np.random.seed(42)
    close = np.linspace(100, 200, 365) + np.random.normal(0, 5, 365)
    df = pd.DataFrame({'Close': close}, index=dates)
    return df

def test_calculate_seasonality(analyzer, sample_history):
    seasonality = analyzer.calculate_seasonality(sample_history)
    assert isinstance(seasonality, dict)
    # Check if we have months in the keys
    assert len(seasonality) > 0
    # Check structure of a month entry
    first_month = list(seasonality.values())[0]
    assert 'mean' in first_month
    assert 'std' in first_month

def test_calculate_seasonality_empty(analyzer):
    empty_df = pd.DataFrame()
    assert analyzer.calculate_seasonality(empty_df) == {}

def test_calculate_monthly_returns_matrix(analyzer, sample_history):
    matrix = analyzer.calculate_monthly_returns_matrix(sample_history)
    assert isinstance(matrix, pd.DataFrame)
    # Check if columns are month abbreviations (Jan, Feb...)
    import calendar
    assert 'Jan' in matrix.columns
    assert 'Dec' in matrix.columns

def test_calculate_volatility(analyzer, sample_history):
    vol = analyzer.calculate_volatility(sample_history)
    assert isinstance(vol, float)
    assert vol > 0

def test_calculate_volatility_empty(analyzer):
    assert analyzer.calculate_volatility(pd.DataFrame()) == 0.0

def test_model_scenarios(analyzer):
    # LTP=100, Vol=0.2 (20%), Exp=30 days
    # Expected move = 100 * 0.2 * sqrt(30/365) ~= 100 * 0.2 * 0.286 ~= 5.7
    result = analyzer.model_scenarios(ltp=100, volatility=0.2, max_pain=100, expiry_date=None)
    
    assert result['expected_move'] > 0
    assert result['bull_target'] > 100
    assert result['bear_target'] < 100
    assert result['neutral_range'][0] < 100
    assert result['neutral_range'][1] > 100

def test_analyze_oi_valid(analyzer):
    # Construct a minimal valid option chain structure
    # This structure must match what analyze_oi expects
    chain = {
        'records': {
            'expiryDates': ['29-Jun-2023'],
            'data': [
                {
                    'expiryDate': '29-Jun-2023',
                    'strikePrice': 18000,
                    'CE': {'openInterest': 1000, 'impliedVolatility': 15},
                    'PE': {'openInterest': 500, 'impliedVolatility': 14}
                },
                {
                    'expiryDate': '29-Jun-2023',
                    'strikePrice': 18100,  # ATM
                    'CE': {'openInterest': 2000, 'impliedVolatility': 16},
                    'PE': {'openInterest': 2000, 'impliedVolatility': 16}
                },
                {
                    'expiryDate': '29-Jun-2023',
                    'strikePrice': 18200,
                    'CE': {'openInterest': 500, 'impliedVolatility': 14},
                    'PE': {'openInterest': 1000, 'impliedVolatility': 15}
                }
            ]
        }
    }
    
    result = analyzer.analyze_oi(chain, ltp=18100)
    assert result is not None
    assert result['pcr'] > 0
    assert 'max_pain' in result
    assert result['atm_iv'] > 0
    assert result['support_strike'] == 18100 # Highest PE OI
    assert result['resistance_strike'] == 18100 # Highest CE OI

def test_analyze_oi_invalid(analyzer):
    assert analyzer.analyze_oi({}, 100) is None

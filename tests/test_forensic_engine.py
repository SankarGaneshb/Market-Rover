
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from rover_tools.analytics.forensic_engine import ForensicAnalyzer

@pytest.fixture
def mock_ticker():
    with patch('yfinance.Ticker') as mock:
        yield mock

@pytest.fixture
def analyzer(mock_ticker):
    return ForensicAnalyzer("TEST.NS")

def create_mock_df(data):
    return pd.DataFrame(data)

def test_load_data_success(analyzer, mock_ticker):
    instance = mock_ticker.return_value
    instance.balance_sheet = pd.DataFrame({'2023': [1]})
    instance.financials = pd.DataFrame({'2023': [1]})
    instance.cashflow = pd.DataFrame({'2023': [1]})
    
    assert analyzer.load_data() is True
    assert analyzer.data_loaded is True

def test_load_data_failure(analyzer, mock_ticker):
    instance = mock_ticker.return_value
    instance.balance_sheet = pd.DataFrame() # Empty
    
    assert analyzer.load_data() is False
    assert analyzer.data_loaded is False

# --- Check Tests ---

def test_satyam_check_pass(analyzer, mock_ticker):
    # Setup data for healthy interest income (e.g. 5% yield)
    # Cash = 1000, Interest = 50
    instance = mock_ticker.return_value
    instance.balance_sheet = pd.DataFrame(
        {'2023': [1000]}, index=["Cash And Cash Equivalents"]
    )
    instance.financials = pd.DataFrame(
        {'2023': [50]}, index=["Interest Income"]
    )
    
    result = analyzer.run_satyam_check()
    assert result['status'] == "PASS"
    assert result['metric'] == "Cash Yield"

def test_satyam_check_fail(analyzer, mock_ticker):
    # Setup data for suspicious interest income (e.g. 1% yield)
    # Cash = 1000, Interest = 10
    instance = mock_ticker.return_value
    instance.balance_sheet = pd.DataFrame(
        {'2023': [1000]}, index=["Cash And Cash Equivalents"]
    )
    instance.financials = pd.DataFrame(
        {'2023': [10]}, index=["Interest Income"]
    )
    
    result = analyzer.run_satyam_check()
    assert result['status'] == "FAIL"
    assert result['flag'] == "RED"

def test_cwip_check_pass(analyzer, mock_ticker):
    # CWIP = 10, PPE = 90 -> Ratio 10% (Safe)
    instance = mock_ticker.return_value
    instance.balance_sheet = pd.DataFrame(
        {'2023': [10, 90]}, 
        index=["Capital Work In Progress", "Gross PPE"]
    )
    
    result = analyzer.run_cwip_check()
    assert result['status'] == "PASS"

def test_cwip_check_fail(analyzer, mock_ticker):
    # CWIP = 40, PPE = 60 -> Ratio 40% (High risk)
    instance = mock_ticker.return_value
    instance.balance_sheet = pd.DataFrame(
        {'2023': [40, 60]}, 
        index=["Capital Work In Progress", "Gross PPE"]
    )
    
    result = analyzer.run_cwip_check()
    assert result['status'] == "FAIL"
    assert result['flag'] == "RED"

def test_revenue_quality_check_pass(analyzer, mock_ticker):
    # Sales grew 10%, Receivables grew 10% -> Delta 0 (Safe)
    instance = mock_ticker.return_value
    
    # Let's mock properly: Columns=Years
    
    # Let's mock properly: Columns=Years
    instance.financials = pd.DataFrame(
        {'2023': [110], '2022': [100]}, 
        index=["Total Revenue"]
    )
    instance.balance_sheet = pd.DataFrame(
        {'2023': [110], '2022': [100]}, 
        index=["Net Receivables"]
    )
    
    result = analyzer.run_revenue_quality_check()
    assert result['status'] == "PASS"

def test_revenue_quality_check_fail(analyzer, mock_ticker):
    # Sales grew 0%, Receivables grew 50% -> Delta 50 (Bad)
    instance = mock_ticker.return_value
    
    instance.financials = pd.DataFrame(
        {'2023': [100], '2022': [100]}, 
        index=["Total Revenue"]
    )
    
    instance.balance_sheet = pd.DataFrame(
        {'2023': [150], '2022': [100]}, 
        index=["Net Receivables"]
    )
    
    result = analyzer.run_revenue_quality_check()
    assert result['status'] == "FAIL"
    assert result['flag'] == "RED"

def test_generate_forensic_report(analyzer, mock_ticker):
    # Pass all
    instance = mock_ticker.return_value
    instance.balance_sheet = pd.DataFrame({
        '2023': [1000, 10, 90, 110],
        '2022': [1000, 10, 90, 100]
    }, index=["Cash And Cash Equivalents", "Capital Work In Progress", "Gross PPE", "Net Receivables"])
    
    instance.financials = pd.DataFrame({
        '2023': [50, 110],
        '2022': [50, 100]
    }, index=["Interest Income", "Total Revenue"])
    
    instance.cashflow = pd.DataFrame() 

    report = analyzer.generate_forensic_report()
    assert report['overall_status'] == "CLEAN"
    assert len(report['checks']) == 3

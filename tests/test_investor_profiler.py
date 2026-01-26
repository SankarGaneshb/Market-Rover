
import pytest
from unittest.mock import MagicMock, patch
from rover_tools.analytics.investor_profiler import InvestorProfiler, PortfolioValidator, InvestorPersona

@pytest.fixture
def profiler():
    return InvestorProfiler()

@pytest.fixture
def validator():
    return PortfolioValidator()

@pytest.fixture
def mock_forensic():
    with patch('rover_tools.analytics.investor_profiler.ForensicAnalyzer') as mock:
        yield mock

@pytest.fixture
def mock_shadow():
    with patch('rover_tools.analytics.investor_profiler.detect_silent_accumulation') as mock:
        yield mock

@pytest.fixture
def mock_portfolio_engine():
    with patch('rover_tools.analytics.investor_profiler.AnalyticsPortfolio') as mock:
        yield mock

# --- InvestorProfiler Tests ---

def test_get_profile(profiler):
    # Preserver (<= 4)
    assert profiler.get_profile(1, 1, 1) == InvestorPersona.PRESERVER
    # Defender (5-6)
    assert profiler.get_profile(2, 2, 1) == InvestorPersona.DEFENDER
    # Compounder (7)
    assert profiler.get_profile(3, 2, 2) == InvestorPersona.COMPOUNDER
    # Hunter (>7)
    assert profiler.get_profile(3, 3, 3) == InvestorPersona.HUNTER

def test_get_allocation_strategy(profiler):
    # Just check structure return types
    s_preserver = profiler.get_allocation_strategy(InvestorPersona.PRESERVER)
    assert s_preserver['risk_level'] == "Low"
    assert "Gold" in s_preserver['allocation']

    s_hunter = profiler.get_allocation_strategy(InvestorPersona.HUNTER)
    assert s_hunter['risk_level'] == "Aggressive"
    assert "Equity_Small" in s_hunter['allocation']

def test_generate_smart_portfolio_preserver(profiler):
    # Preserver logic
    persona = InvestorPersona.PRESERVER
    user_picks = ["TCS.NS"]
    
    holdings = profiler.generate_smart_portfolio(persona, user_picks)
    
    # Check if TCS is included
    tcs = next((h for h in holdings if h['Symbol'] == "TCS.NS"), None)
    assert tcs is not None
    assert tcs['Asset Class'] == "Equity_Core"
    
    # Check Gold (Safety_Gold)
    gold = next((h for h in holdings if h['Asset Class'] == "Safety_Gold"), None)
    assert gold is not None

def test_generate_smart_portfolio_hunter(profiler):
    # Hunter logic
    persona = InvestorPersona.HUNTER
    holdings = profiler.generate_smart_portfolio(persona, [])
    
    # Should include specific Hunter picks like TRENT, BEL etc.
    assert any(h['Symbol'] == "TRENT.NS" for h in holdings)
    assert any(h['Strategy'] == "Momentum/Shadow" for h in holdings)

# --- PortfolioValidator Tests ---

def test_validate_holdings_clean(validator, mock_forensic, mock_shadow, mock_portfolio_engine):
    # Setup clean mocks
    mock_instance = mock_forensic.return_value
    mock_instance.generate_forensic_report.return_value = {'overall_status': 'CLEAN', 'red_flags': 0}
    
    mock_shadow.return_value = {'score': 20} # Low score
    
    mock_portfolio_engine.return_value.calculate_correlation_matrix.return_value = pd.DataFrame()
    
    holdings = [{'Symbol': 'TCS.NS'}]
    flags = validator.validate_holdings(holdings)
    
    assert flags['TCS.NS']['status'] == 'GREEN'

def test_validate_holdings_forensic_fail(validator, mock_forensic, mock_shadow, mock_portfolio_engine):
    # Setup dirty mocks
    mock_instance = mock_forensic.return_value
    mock_instance.generate_forensic_report.return_value = {'overall_status': 'CRITICAL', 'red_flags': 3}
    
    holdings = [{'Symbol': 'BAD.NS'}]
    flags = validator.validate_holdings(holdings)
    
    assert flags['BAD.NS']['status'] == 'RED'
    assert 'Forensic Alert' in flags['BAD.NS']['reason']

def test_validate_holdings_shadow_alert(validator, mock_forensic, mock_shadow, mock_portfolio_engine):
    # Setup shadow alert
    mock_instance = mock_forensic.return_value
    mock_instance.generate_forensic_report.return_value = {'overall_status': 'CLEAN'}
    
    mock_shadow.return_value = {'score': 80} # High score
    
    holdings = [{'Symbol': 'PUMP.NS'}]
    flags = validator.validate_holdings(holdings)
    
    assert 'Shadow Score' in flags['PUMP.NS']['reason']


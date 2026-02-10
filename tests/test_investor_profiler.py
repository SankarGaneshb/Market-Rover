import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from rover_tools.analytics.investor_profiler import InvestorProfiler, PortfolioValidator, InvestorPersona

@pytest.fixture
def profiler():
    return InvestorProfiler()

@pytest.fixture
def validator():
    return PortfolioValidator()

def test_get_profile(profiler):
    # Preserver <= 4
    assert profiler.get_profile(1, 1, 1) == InvestorPersona.PRESERVER
    # Defender <= 6
    assert profiler.get_profile(2, 2, 2) == InvestorPersona.DEFENDER
    # Compounder <= 7
    assert profiler.get_profile(3, 2, 2) == InvestorPersona.COMPOUNDER
    # Hunter > 7
    assert profiler.get_profile(3, 3, 3) == InvestorPersona.HUNTER

def test_get_allocation_strategy(profiler):
    strat = profiler.get_allocation_strategy(InvestorPersona.PRESERVER)
    assert strat['risk_level'] == "Low"
    assert strat['max_tickers'] == 3
    
    strat = profiler.get_allocation_strategy(InvestorPersona.HUNTER)
    assert strat['risk_level'] == "Aggressive"
    assert strat['max_tickers'] == 6

def test_generate_smart_portfolio_preserver(profiler):
    # Should generate 3 bluechips
    holdings = profiler.generate_smart_portfolio(InvestorPersona.PRESERVER, user_picked_brands=[])
    assert len(holdings) == 3
    assert holdings[0]['Asset Class'] == 'Equity_Core'
    assert sum(h['Weight (%)'] for h in holdings) == pytest.approx(100.0, abs=0.5)

def test_generate_smart_portfolio_defender(profiler):
    # Should generate 2 Bluechips + 1 Dividend
    holdings = profiler.generate_smart_portfolio(InvestorPersona.DEFENDER, user_picked_brands=[])
    assert len(holdings) == 3
    # Check for dividend stock
    curr_syms = [h['Symbol'] for h in holdings]
    has_div = any(s in profiler.DIVIDEND_STOCKS for s in curr_syms)
    assert has_div
    assert sum(h['Weight (%)'] for h in holdings) == pytest.approx(100.0, abs=0.5)

def test_generate_smart_portfolio_compounder(profiler):
    holdings = profiler.generate_smart_portfolio(InvestorPersona.COMPOUNDER, user_picked_brands=['RELIANCE.NS'])
    print(f"\nCompounder Holdings: {holdings}")
    # Should fill remaining slots (total 4)
    assert len(holdings) == 4
    assert holdings[0]['Symbol'] == 'RELIANCE.NS'
    # Rounding errors can cause sum to be slightly off 100
    assert sum(h['Weight (%)'] for h in holdings) == pytest.approx(100.0, abs=0.5)

def test_generate_smart_portfolio_hunter(profiler):
    holdings = profiler.generate_smart_portfolio(InvestorPersona.HUNTER, user_picked_brands=[])
    print(f"\nHunter Holdings: {holdings}")
    # Target 6
    assert len(holdings) <= 6
    assert len(holdings) >= 4 # Should have some
    assert sum(h['Weight (%)'] for h in holdings) == pytest.approx(100.0, abs=0.5)

def test_validate_holdings(validator):
    # Mock all dependencies
    with patch('rover_tools.analytics.investor_profiler.ForensicAnalyzer') as MockForensic, \
         patch('rover_tools.analytics.investor_profiler.detect_silent_accumulation') as mock_shadow, \
         patch('rover_tools.analytics.investor_profiler.AnalyticsPortfolio') as MockPortfolio:
        
        # Setup Forensic - USE SAFE so we can see other flags if logic allows, 
        # OH WAIT, logic only adds shadow if > 60.
        # But validator logic: if score > 60, append msg IF status != RED.
        
        # Scenario 1: Red Flag (Forensic) -> Shadow suppressed
        mock_analyzer = MagicMock()
        MockForensic.return_value = mock_analyzer
        mock_analyzer.generate_forensic_report.return_value = {'overall_status': 'CRITICAL', 'red_flags': 5}
        
        mock_shadow.return_value = {'score': 80}
        
        mock_pf_engine = MockPortfolio.return_value
        mock_pf_engine.calculate_correlation_matrix.return_value = pd.DataFrame()
        validator.pf_engine = mock_pf_engine
        
        holdings = [{'Symbol': 'T1'}]
        flags = validator.validate_holdings(holdings)
        
        assert flags['T1']['status'] == 'RED'
        # Shadow reason NOT added because status is RED
        assert "Shadow Score" not in flags['T1']['reason']

def test_validate_holdings_shadow_alert(validator):
    # Scenario 2: Green Forensic -> Shadow Alert appears
    with patch('rover_tools.analytics.investor_profiler.ForensicAnalyzer') as MockForensic, \
         patch('rover_tools.analytics.investor_profiler.detect_silent_accumulation') as mock_shadow, \
         patch('rover_tools.analytics.investor_profiler.AnalyticsPortfolio') as MockPortfolio:
        
        mock_analyzer = MagicMock()
        MockForensic.return_value = mock_analyzer
        mock_analyzer.generate_forensic_report.return_value = {'overall_status': 'SAFE', 'red_flags': 0}
        
        mock_shadow.return_value = {'score': 80} # High shadow score
        
        mock_pf_engine = MockPortfolio.return_value
        mock_pf_engine.calculate_correlation_matrix.return_value = pd.DataFrame()
        validator.pf_engine = mock_pf_engine
        
        holdings = [{'Symbol': 'T1'}]
        flags = validator.validate_holdings(holdings)
        
        # Shadow should add warning, likely keeping Green or changing to Amber?
        # Logic: flags['ticker'] = {status: GREEN...}
        # if score > 60: flags['ticker']['reason'] += ...
        # It doesn't change status to AMBER in current logic unless correlation does.
        # Wait, if status is GREEN, it appends.
        
        assert "Shadow Score" in flags['T1']['reason']

def test_validate_holdings_clean(validator):
    with patch('rover_tools.analytics.investor_profiler.ForensicAnalyzer') as MockForensic, \
         patch('rover_tools.analytics.investor_profiler.detect_silent_accumulation') as mock_shadow, \
         patch('rover_tools.analytics.investor_profiler.AnalyticsPortfolio') as MockPortfolio:
        
        mock_analyzer = MagicMock()
        MockForensic.return_value = mock_analyzer
        mock_analyzer.generate_forensic_report.return_value = {'overall_status': 'SAFE', 'red_flags': 0}
        
        mock_shadow.return_value = {'score': 20}
        
        mock_pf_engine = MockPortfolio.return_value
        mock_pf_engine.calculate_correlation_matrix.return_value = pd.DataFrame()
        validator.pf_engine = mock_pf_engine # Inject
        
        holdings = [{'Symbol': 'T1'}]
        flags = validator.validate_holdings(holdings)
        
        assert flags['T1']['status'] == 'GREEN'

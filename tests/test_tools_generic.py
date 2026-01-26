
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch, AsyncMock
from rover_tools.stock_data_tool import get_stock_data
from rover_tools.news_scraper_tool import scrape_stock_news
from rover_tools.visualizer_tool import generate_market_snapshot

# Mocking decorators if they exist (assuming similar to market_context)
# For now assuming functions are importable or standard.

@pytest.fixture
def mock_yf():
    with patch('yfinance.Ticker') as mock:
        yield mock



def test_get_stock_data_success(mock_yf):
    mock_ticker = mock_yf.return_value
    mock_ticker.history.return_value = pd.DataFrame({'Close': [100]})
    mock_ticker.info = {'shortName': 'Test Corp'}
    
    # Assuming get_stock_data returns a string or dict
    # We need to check if get_stock_data is a Tool object or function
    # Importing it directly.
    # If it is a Tool, we use .run().
    
    try:
        if hasattr(get_stock_data, 'run'):
            result = get_stock_data.run("TEST")
        else:
            result = get_stock_data("TEST")
    except Exception as e:
        pytest.fail(f"Execution failed: {e}")

    assert result is not None

def test_scrape_news_mocked():
    with patch('rover_tools.news_scraper_tool.extract_links_from_search', new_callable=AsyncMock) as mock_links, \
         patch('rover_tools.news_scraper_tool.process_article', new_callable=AsyncMock) as mock_process:
         
        mock_links.return_value = ["http://test.com"]
        mock_process.return_value = {
            'title': 'Test News',
            'summary': 'Summary',
            'date': '2023-01-01'
        }

        try:
             if hasattr(scrape_stock_news, 'run'):
                 result = scrape_stock_news.run("TCS")
             else:
                 result = scrape_stock_news("TCS")
        except Exception as e:
            pytest.fail(f"Scrape failed: {e}")
            
        assert "Test News" in result 

def test_visualizer_tool(mock_yf):
    # Mock dependencies for generate_market_snapshot
    with patch('rover_tools.visualizer_tool.MarketDataFetcher') as mock_fetcher_cls, \
         patch('rover_tools.visualizer_tool.MarketAnalyzer') as mock_analyzer_cls, \
         patch('rover_tools.visualizer_tool.DashboardRenderer') as mock_renderer_cls, \
         patch('rover_tools.visualizer_tool.SeasonalityCalendar') as mock_cal_cls:
         
        mock_fetcher = mock_fetcher_cls.return_value
        mock_fetcher.fetch_ltp.return_value = 100.0
        mock_fetcher.fetch_full_history.return_value = pd.DataFrame({'Close': [100]})
        
        mock_analyzer = mock_analyzer_cls.return_value
        mock_analyzer.calculate_volatility.return_value = 0.2
        mock_analyzer.calculate_monthly_returns_matrix.return_value = pd.DataFrame()
        mock_analyzer.model_scenarios.return_value = {
            'neutral_range': [90, 110], 'bull_target': 120, 'bear_target': 80
        }
        mock_analyzer.calculate_seasonality.return_value = {}
        mock_analyzer.calculate_2026_forecast.return_value = {
            'consensus_target': 150, 'range_low': 140, 'range_high': 160, 'cagr_percent': 10
        }
        
        mock_renderer = mock_renderer_cls.return_value
        mock_bb = MagicMock()
        mock_bb.getbuffer.return_value = b"PDF"
        mock_renderer.generate_pdf_report.return_value = mock_bb

        try:
             # generate_market_snapshot is a Tool object
             if hasattr(generate_market_snapshot, 'run'):
                 result = generate_market_snapshot.run("TCS")
             else:
                 result = generate_market_snapshot("TCS")
        except Exception as e:
            pytest.fail(f"Snapshot failed: {e}")

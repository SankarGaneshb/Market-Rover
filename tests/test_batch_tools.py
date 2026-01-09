import pytest
from unittest.mock import MagicMock, patch
from rover_tools.batch_tools import batch_get_stock_data, batch_scrape_news, batch_detect_accumulation

class TestBatchTools:
    
    @patch('rover_tools.batch_tools.yf.Ticker')
    def test_batch_get_stock_data_success(self, mock_ticker):
        # Setup mock return values
        mock_instance = MagicMock()
        mock_instance.fast_info.last_price = 2500.0
        mock_instance.fast_info.previous_close = 2400.0
        mock_ticker.return_value = mock_instance
        
        tickers = "RELIANCE.NS, TCS.NS"
        result = batch_get_stock_data.run(tickers)
        
        # Verify output formatting
        assert "Batch Stock Market Data" in result
        assert "RELIANCE.NS" in result
        assert "2500.00" in result
        assert "+4.17%" in result # (2500-2400)/2400 * 100

    @patch('rover_tools.batch_tools.yf.Ticker')
    def test_batch_get_stock_data_fallback(self, mock_ticker):
        # Test fallback when fast_info is None
        mock_instance = MagicMock()
        mock_instance.fast_info.last_price = None
        
        # Mock history fallback
        mock_hist = MagicMock()
        mock_hist.empty = False
        mock_hist.__getitem__.return_value.iloc = [2300.0, 2350.0] # Prev, Close
        mock_hist.__len__.return_value = 2
        mock_instance.history.return_value = mock_hist
        
        mock_ticker.return_value = mock_instance
        
        result = batch_get_stock_data.run("INFY.NS")
        assert "INFY.NS" in result
        
    @patch('rover_tools.batch_tools.scrape_stock_news')
    def test_batch_scrape_news(self, mock_tool):
        mock_tool.run.return_value = "Mock news content for stock"
        
        tickers = "RELIANCE.NS, TCS.NS"
        result = batch_scrape_news.run(tickers)
        
        assert "Batch News Report" in result
        assert "RELIANCE.NS" in result
        assert "Mock news content" in result
        assert mock_tool.run.call_count == 2 # Called for each ticker

    @patch('rover_tools.batch_tools.detect_silent_accumulation')
    def test_batch_shadow_scan(self, mock_detect):
        mock_detect.return_value = {'score': 85, 'signals': ['Volume Spike']}
        
        tickers = "RELIANCE.NS"
        result = batch_detect_accumulation.run(tickers)
        
        assert "Batch Institutional Shadow Scan" in result
        assert "RELIANCE.NS" in result
        assert "Score: 85/100" in result
        assert "Volume Spike" in result

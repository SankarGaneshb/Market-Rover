import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import MagicMock, patch
import time
from utils.parallel_processor import ParallelStockProcessor

def test_initialization():
    processor = ParallelStockProcessor(max_workers=10, rate_limit_delay=0.1)
    assert processor.max_workers == 10
    assert processor.rate_limit_delay == 0.1
    # Check initial progress state
    assert processor.progress_data['total'] == 0

def test_process_stocks_success():
    # Mock processing function
    def mock_process(stock):
        return f"Processed {stock['Symbol']}"
    
    stocks = [
        {'Symbol': 'AAPL'},
        {'Symbol': 'GOOG'}
    ]
    
    processor = ParallelStockProcessor(max_workers=2, rate_limit_delay=0.01)
    
    # We mock time.sleep to run fast
    with patch('time.sleep'):
        results = processor.process_stocks(stocks, mock_process)
        
    assert results['summary']['total'] == 2
    assert results['summary']['successful'] == 2
    assert results['summary']['failed'] == 0
    assert len(results['results']) == 2
    
    # Check result content
    res_map = {r['stock']['Symbol']: r['result'] for r in results['results']}
    assert res_map['AAPL'] == "Processed AAPL"
    assert res_map['GOOG'] == "Processed GOOG"

def test_process_stocks_partial_failure():
    # Function that fails for one stock
    def mock_process_fail_some(stock):
        if stock['Symbol'] == 'BAD':
            raise ValueError("Bad Stock")
        return "OK"
    
    stocks = [
        {'Symbol': 'GOOD'},
        {'Symbol': 'BAD'}
    ]
    
    processor = ParallelStockProcessor(max_workers=2, rate_limit_delay=0.01)
    
    with patch('time.sleep'):
        results = processor.process_stocks(stocks, mock_process_fail_some)
        
    assert results['summary']['successful'] == 1
    assert results['summary']['failed'] == 1
    assert len(results['errors']) == 1
    
    error_entry = results['errors'][0]
    assert error_entry['stock']['Symbol'] == 'BAD'
    assert "Bad Stock" in error_entry['error']

def test_progress_tracking_and_callback():
    callback_mock = MagicMock()
    
    def mock_process(stock):
        return "OK"
        
    stocks = [{'Symbol': 'A'}, {'Symbol': 'B'}]
    processor = ParallelStockProcessor(max_workers=1, rate_limit_delay=0.01)
    
    with patch('time.sleep'):
        processor.process_stocks(stocks, mock_process, progress_callback=callback_mock)
        
    # Callback should be called twice (once for each stock completion)
    assert callback_mock.call_count == 2
    
    # Check progress method
    progress = processor.get_progress()
    assert progress['total'] == 2
    assert progress['completed'] == 2
    assert progress['percentage'] == 100.0

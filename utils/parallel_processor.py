"""
Parallel stock analysis processor for Market-Rover 2.0
Handles concurrent processing of multiple stocks using ThreadPoolExecutor
"""
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Callable, Optional
from threading import Lock


class ParallelStockProcessor:
    """
    Orchestrates parallel analysis of stocks in a portfolio.
    Uses ThreadPoolExecutor to process multiple stocks concurrently.
    """
    
    def __init__(self, max_workers: int = 5, rate_limit_delay: float = 1.0):
        """
        Initialize the parallel processor.
        
        Args:
            max_workers: Maximum number of concurrent stock analyses (default: 5)
            rate_limit_delay: Delay in seconds between API calls per thread (default: 1.0)
        """
        self.max_workers = max_workers
        self.rate_limit_delay = rate_limit_delay
        self.progress_lock = Lock()
        self.progress_data = {
            'total': 0,
            'completed': 0,
            'failed': 0,
            'current_stocks': set()
        }
    
    def process_stocks(
        self, 
        stocks: List[Dict], 
        process_func: Callable,
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """
        Process multiple stocks in parallel.
        
        Args:
            stocks: List of stock dictionaries with 'Symbol' and 'Company Name'
            process_func: Function to process each stock (takes stock dict, returns result)
            progress_callback: Optional callback for progress updates (percentage, stock_name)
        
        Returns:
            Dictionary with results and errors
        """
        self.progress_data['total'] = len(stocks)
        self.progress_data['completed'] = 0
        self.progress_data['failed'] = 0
        self.progress_data['current_stocks'] = set()
        
        results = []
        errors = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all stock processing jobs
            future_to_stock = {
                executor.submit(self._process_single_stock, stock, process_func): stock 
                for stock in stocks
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_stock):
                stock = future_to_stock[future]
                stock_symbol = stock.get('Symbol', 'Unknown')
                
                try:
                    result = future.result()
                    results.append({
                        'stock': stock,
                        'result': result,
                        'success': True
                    })
                    
                    with self.progress_lock:
                        self.progress_data['completed'] += 1
                        self.progress_data['current_stocks'].discard(stock_symbol)
                        
                    if progress_callback:
                        progress_pct = (self.progress_data['completed'] / self.progress_data['total']) * 100
                        progress_callback(progress_pct, stock_symbol, 'completed')
                        
                except Exception as e:
                    errors.append({
                        'stock': stock,
                        'error': str(e),
                        'success': False
                    })
                    
                    with self.progress_lock:
                        self.progress_data['failed'] += 1
                        self.progress_data['current_stocks'].discard(stock_symbol)
                    
                    if progress_callback:
                        progress_pct = (self.progress_data['completed'] / self.progress_data['total']) * 100
                        progress_callback(progress_pct, stock_symbol, 'failed')
        
        return {
            'results': results,
            'errors': errors,
            'summary': {
                'total': len(stocks),
                'successful': len(results),
                'failed': len(errors)
            }
        }
    
    def _process_single_stock(self, stock: Dict, process_func: Callable):
        """
        Process a single stock with rate limiting.
        
        Args:
            stock: Stock dictionary
            process_func: Function to process the stock
            
        Returns:
            Result from process_func
        """
        stock_symbol = stock.get('Symbol', 'Unknown')
        
        # Track current stock being processed
        with self.progress_lock:
            self.progress_data['current_stocks'].add(stock_symbol)
        
        # Rate limiting - sleep before making API calls
        time.sleep(self.rate_limit_delay)
        
        # Execute the processing function
        result = process_func(stock)
        
        return result
    
    def get_progress(self) -> Dict:
        """
        Get current progress information.
        
        Returns:
            Dictionary with progress data
        """
        with self.progress_lock:
            return {
                'total': self.progress_data['total'],
                'completed': self.progress_data['completed'],
                'failed': self.progress_data['failed'],
                'in_progress': len(self.progress_data['current_stocks']),
                'current_stocks': list(self.progress_data['current_stocks']),
                'percentage': (self.progress_data['completed'] / self.progress_data['total'] * 100) 
                              if self.progress_data['total'] > 0 else 0
            }

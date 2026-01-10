import time
import functools
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any, Callable

# Configure dedicated performance logger
logger = logging.getLogger("performance")
logger.setLevel(logging.INFO)

# File handler for tracking metrics
file_handler = logging.FileHandler("logs/performance.log")
formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

class PerformanceMonitor:
    """
    Singleton class to track and log performance metrics for the application.
    Supports both decorator and context manager usage.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PerformanceMonitor, cls).__new__(cls)
        return cls._instance

    def log_metric(self, name: str, duration_sec: float, metadata: Optional[Dict[str, Any]] = None):
        """
        Log a specific performance metric.
        
        Args:
            name: The name of the operation being measured (e.g., 'news_fetch')
            duration_sec: Duration in seconds
            metadata: Optional dictionary of extra context (e.g., {'stock_count': 5})
        """
        meta_str = f" | {metadata}" if metadata else ""
        log_msg = f"METRIC: {name} completed in {duration_sec:.4f}s{meta_str}"
        logger.info(log_msg)
        # We could also push to a dashboard or DB here in the future
    
    @contextmanager
    def measure(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Context manager to measure execution time of a block.
        
        Usage:
            with PerformanceMonitor().measure("complex_calc", {"items": 10}):
                do_work()
        """
        start_time = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start_time
            self.log_metric(name, duration, metadata)

def track_performance(name_override: Optional[str] = None):
    """
    Decorator to measure execution time of a function.
    
    Usage:
        @track_performance(name_override="custom_name")
        def my_func(): ...
    """
    def decorator(func: Callable):
        metric_name = name_override or func.__name__
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            monitor = PerformanceMonitor()
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.perf_counter() - start_time
                # Attempt to extract relevant metadata if possible, else keep it simple
                monitor.log_metric(metric_name, duration)
        return wrapper
    return decorator

def track_error_detail(error_type: str, error_message: str, context: Optional[Dict[str, Any]] = None):
    """
    Log detailed error information.
    Restored to fix ImportError in news_scraper_tool.py.
    """
    logger.error(f"ERROR: {error_type} - {error_message} | Context: {context}")


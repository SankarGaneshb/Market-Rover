import time
import functools
import logging
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Dict, Any, Callable

# Configure dedicated performance logger
logger = logging.getLogger("performance")
logger.setLevel(logging.INFO)

# Create logs directory
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# File handler for tracking metrics
file_handler = logging.FileHandler(LOG_DIR / "performance.log")
formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Metric files configuration
METRICS_DIR = Path("metrics")
METRICS_DIR.mkdir(exist_ok=True)

def _get_metric_file(prefix: str) -> Path:
    today = datetime.now(timezone.utc).date().isoformat()
    return METRICS_DIR / f"{prefix}_{today}.jsonl"

def _append_to_jsonl(file_path: Path, data: Dict[str, Any]):
    try:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")
    except Exception as e:
        logger.error(f"Failed to write to metrics file {file_path}: {e}")

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
    Log detailed error information to both logger and JSONL metrics.
    """
    # Log to standard logger
    logger.error(f"ERROR: {error_type} - {error_message} | Context: {context}")
    
    # Log to JSONL
    data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": error_type,
        "message": error_message,
        "context": context or {}
    }
    _append_to_jsonl(_get_metric_file("errors"), data)

def track_workflow_start(workflow_name: str) -> str:
    """Start tracking a workflow session."""
    session_id = str(uuid.uuid4())
    data = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "type": "start",
        "session_id": session_id,
        "workflow": workflow_name
    }
    _append_to_jsonl(_get_metric_file("workflow_events"), data)
    return session_id

def track_workflow_end(session_id: str, status: str):
    """End tracking a workflow session."""
    data = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "type": "end",
        "session_id": session_id,
        "status": status
    }
    _append_to_jsonl(_get_metric_file("workflow_events"), data)

def track_workflow_event(event_name: str, description: str, session_id: Optional[str] = None):
    """Track a specific event within a workflow."""
    data = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "type": "event",
        "event_name": event_name,
        "description": description,
        "session_id": session_id
    }
    _append_to_jsonl(_get_metric_file("workflow_events"), data)

def track_error(error_type: str, message: str = "Unspecified error", context: Optional[Dict[str, Any]] = None):
    """Alias/Compatibility wrapper for track_error_detail"""
    track_error_detail(error_type, message, context)

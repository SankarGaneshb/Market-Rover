"""
Metrics tracking for Market-Rover 2.0
Tracks API usage, performance, cache stats, and errors
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any
import threading

# Create metrics directory
METRICS_DIR = Path("metrics")
METRICS_DIR.mkdir(exist_ok=True)

# Thread-safe metrics storage
_metrics_lock = threading.Lock()


class MetricsTracker:
    """Track application metrics in-memory and persist daily"""
    
    def __init__(self):
        self.metrics = {
            "api_calls": {
                "today": 0,
                "total": 0,
                "limit": 20,  # Gemini free tier daily limit
                "last_reset": datetime.now().date().isoformat()
            },
            "performance": {
                "total_analyses": 0,
                "total_duration": 0.0,
                "avg_duration": 0.0,
                "min_duration": float('inf'),
                "max_duration": 0.0
            },
            "cache": {
                "hits": 0,
                "misses": 0,
                "hit_rate": 0.0
            },
            "errors": {
                "total": 0,
                "by_type": {}
            }
        }
        self._load_today_metrics()
    
    def _load_today_metrics(self):
        """Load metrics from today's file if exists"""
        today = datetime.now().date().isoformat()
        metrics_file = METRICS_DIR / f"metrics_{today}.json"
        
        if metrics_file.exists():
            try:
                with open(metrics_file, 'r') as f:
                    saved_metrics = json.load(f)
                    self.metrics.update(saved_metrics)
            except Exception:
                pass  # If file is corrupted, start fresh
    
    def _save_metrics(self):
        """Save current metrics to today's file"""
        today = datetime.now().date().isoformat()
        metrics_file = METRICS_DIR / f"metrics_{today}.json"
        
        try:
            with open(metrics_file, 'w') as f:
                json.dump(self.metrics, f, indent=2)
        except Exception:
            pass  # Silently fail if can't save
    
    def _check_daily_reset(self):
        """Reset daily counters if it's a new day"""
        today = datetime.now().date().isoformat()
        if self.metrics["api_calls"]["last_reset"] != today:
            self.metrics["api_calls"]["today"] = 0
            self.metrics["api_calls"]["last_reset"] = today
            self._save_metrics()
    
    def track_api_call(self, service: str = "gemini", operation: str = "generate"):
        """Track an API call"""
        with _metrics_lock:
            self._check_daily_reset()
            self.metrics["api_calls"]["today"] += 1
            self.metrics["api_calls"]["total"] += 1
            self._save_metrics()
    
    def track_performance(self, duration: float):
        """Track analysis duration"""
        with _metrics_lock:
            perf = self.metrics["performance"]
            perf["total_analyses"] += 1
            perf["total_duration"] += duration
            perf["avg_duration"] = perf["total_duration"] / perf["total_analyses"]
            perf["min_duration"] = min(perf["min_duration"], duration)
            perf["max_duration"] = max(perf["max_duration"], duration)
            self._save_metrics()
    
    def track_cache(self, hit: bool):
        """Track cache hit or miss"""
        with _metrics_lock:
            cache = self.metrics["cache"]
            if hit:
                cache["hits"] += 1
            else:
                cache["misses"] += 1
            
            total = cache["hits"] + cache["misses"]
            cache["hit_rate"] = (cache["hits"] / total * 100) if total > 0 else 0.0
            self._save_metrics()
    
    def track_error(self, error_type: str):
        """Track an error by type"""
        with _metrics_lock:
            errors = self.metrics["errors"]
            errors["total"] += 1
            errors["by_type"][error_type] = errors["by_type"].get(error_type, 0) + 1
            self._save_metrics()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot"""
        with _metrics_lock:
            self._check_daily_reset()
            return self.metrics.copy()
    
    def get_api_usage(self) -> Dict[str, int]:
        """Get API usage stats"""
        return {
            "today": self.metrics["api_calls"]["today"],
            "total": self.metrics["api_calls"]["total"],
            "limit": self.metrics["api_calls"]["limit"],
            "remaining": max(0, self.metrics["api_calls"]["limit"] - self.metrics["api_calls"]["today"])
        }
    
    def get_performance_stats(self) -> Dict[str, float]:
        """Get performance statistics"""
        perf = self.metrics["performance"]
        return {
            "total_analyses": perf["total_analyses"],
            "avg_duration": perf["avg_duration"],
            "min_duration": perf["min_duration"] if perf["min_duration"] != float('inf') else 0.0,
            "max_duration": perf["max_duration"]
        }
    
    def get_cache_stats(self) -> Dict[str, any]:
        """Get cache statistics"""
        return self.metrics["cache"].copy()
    
    def get_error_stats(self) -> Dict[str, any]:
        """Get error statistics"""
        return self.metrics["errors"].copy()


# Global metrics tracker instance
metrics_tracker = MetricsTracker()


# Convenience functions
def track_api_call(service: str = "gemini", operation: str = "generate"):
    """Track an API call"""
    metrics_tracker.track_api_call(service, operation)


def track_performance(duration: float):
    """Track analysis performance"""
    metrics_tracker.track_performance(duration)


def track_cache_hit():
    """Track cache hit"""
    metrics_tracker.track_cache(hit=True)


def track_cache_miss():
    """Track cache miss"""
    metrics_tracker.track_cache(hit=False)


def track_error(error_type: str):
    """Track an error"""
    metrics_tracker.track_error(error_type)


def get_metrics() -> Dict[str, Any]:
    """Get all metrics"""
    return metrics_tracker.get_metrics()


def get_api_usage() -> Dict[str, int]:
    """Get API usage stats"""
    return metrics_tracker.get_api_usage()


def get_performance_stats() -> Dict[str, float]:
    """Get performance stats"""
    return metrics_tracker.get_performance_stats()


def get_cache_stats() -> Dict[str, any]:
    """Get cache stats"""
    return metrics_tracker.get_cache_stats()


def get_error_stats() -> Dict[str, any]:
    """Get error stats"""
    return metrics_tracker.get_error_stats()

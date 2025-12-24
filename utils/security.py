"""
Security utilities for Market-Rover
Handles input validation and sanitization
"""
import re
from typing import Optional


def sanitize_ticker(ticker: str) -> Optional[str]:
    """
    Sanitize and validate stock ticker input.
    Prevents injection attacks and ensures valid format.
    
    Args:
        ticker: Raw ticker input from user
        
    Returns:
        Sanitized ticker or None if invalid
        
    Examples:
        >>> sanitize_ticker("SBIN")
        'SBIN'
        >>> sanitize_ticker("TCS.NS")
        'TCS.NS'
        >>> sanitize_ticker("'; DROP TABLE--")
        None
        >>> sanitize_ticker("<script>alert('xss')</script>")
        None
    """
    if not ticker:
        return None
    
    # Remove leading/trailing whitespace
    ticker = ticker.strip().upper()
    
    # Valid ticker pattern: alphanumeric + optional .NS/.BO suffix
    # Max length: 20 characters
    # Updated to allow ^ prefix for indices (e.g. ^NSEI)
    ticker_pattern = r'^\^?[A-Z0-9]{1,15}(?:\.[A-Z]{1,3})?$'
    
    if re.match(ticker_pattern, ticker):
        return ticker
    
    return None


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file operations.
    
    Args:
        filename: Raw filename
        
    Returns:
        Sanitized filename safe for file system
    """
    if not filename:
        return "unnamed_file"
    
    # Remove path traversal attempts
    filename = filename.replace('../', '').replace('..\\', '')
    
    # Keep only safe characters
    safe_chars = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', filename)
    
    # Limit length
    return safe_chars[:100]


def validate_csv_content(content: bytes, max_size_mb: int = 5) -> tuple[bool, str]:
    """
    Validate CSV file content before processing.
    
    Args:
        content: File content in bytes
        max_size_mb: Maximum allowed file size in MB
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check file size
    size_mb = len(content) / (1024 * 1024)
    if size_mb > max_size_mb:
        return False, f"File too large ({size_mb:.1f}MB). Maximum allowed: {max_size_mb}MB"
    
    # Check if content is not empty
    if len(content) == 0:
        return False, "File is empty"
    
    # Try to decode as UTF-8
    try:
        content.decode('utf-8')
    except UnicodeDecodeError:
        return False, "File encoding not supported. Please use UTF-8 encoded CSV"
    
    return True, ""


def sanitize_llm_input(user_input: str, max_length: int = 200) -> str:
    """
    Sanitize user input before sending to LLM.
    Prevents prompt injection attacks.
    
    Args:
        user_input: Raw user input
        max_length: Maximum allowed length
        
    Returns:
        Sanitized input safe for LLM
    """
    if not user_input:
        return ""
    
    # Remove potential injection patterns
    dangerous_patterns = [
        r'ignore\s+previous\s+instructions',
        r'you\s+are\s+now',
        r'system\s*:',
        r'<\s*script',
        r'javascript\s*:',
    ]
    
    sanitized = user_input
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
    
    # Truncate to max length
    sanitized = sanitized[:max_length]
    
    # Remove control characters
    sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\n\r\t')
    
    return sanitized.strip()


class RateLimiter:
    """
    Simple rate limiter for API calls.
    Prevents abuse and manages quota.
    """
    
    def __init__(self, max_requests: int = 30, time_window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed in time window
            time_window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window_seconds
        self.requests = []  # List of timestamps
    
    def is_allowed(self) -> tuple[bool, str]:
        """
        Check if request is allowed under rate limit.
        
        Returns:
            Tuple of (is_allowed, message)
        """
        import time
        
        current_time = time.time()
        
        # Remove old requests outside time window
        self.requests = [req_time for req_time in self.requests 
                        if current_time - req_time < self.time_window]
        
        if len(self.requests) >= self.max_requests:
            oldest_request = min(self.requests)
            wait_time = int(self.time_window - (current_time - oldest_request))
            return False, f"Rate limit exceeded. Please wait {wait_time} seconds."
        
        # Add current request
        self.requests.append(current_time)
        return True, ""
    
    def get_remaining(self) -> int:
        """Get number of remaining requests in current window."""
        import time
        current_time = time.time()
        
        # Clean up old requests
        self.requests = [req_time for req_time in self.requests 
                        if current_time - req_time < self.time_window]
        
        return max(0, self.max_requests - len(self.requests))

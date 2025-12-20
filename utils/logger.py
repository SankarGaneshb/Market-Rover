"""
Logging infrastructure for Market-Rover 2.0
Provides structured logging with rotation and multiple log levels
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Create logs directory
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Log configuration
LOG_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FILE = LOG_DIR / "market_rover.log"
MAX_BYTES = 10 * 1024 * 1024  # 10MB per file
BACKUP_COUNT = 7  # Keep 7 days of logs


def get_logger(name: str = "market_rover") -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (usually __name__ from calling module)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler with rotation
        try:
            file_handler = RotatingFileHandler(
                LOG_FILE,
                maxBytes=MAX_BYTES,
                backupCount=BACKUP_COUNT,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            # If file logging fails (e.g., permissions), continue with console only
            logger.warning(f"Could not create file handler: {e}")
        
        # Prevent propagation to root logger
        logger.propagate = False
    
    return logger


# Create default logger
logger = get_logger()


def log_analysis_start(job_id: str, num_stocks: int, test_mode: bool = False):
    """Log the start of a portfolio analysis"""
    logger.info(
        f"Analysis started | job_id={job_id} | stocks={num_stocks} | test_mode={test_mode}"
    )


def log_analysis_complete(job_id: str, duration: float, success: bool = True):
    """Log the completion of a portfolio analysis"""
    status = "SUCCESS" if success else "FAILED"
    logger.info(
        f"Analysis complete | job_id={job_id} | duration={duration:.2f}s | status={status}"
    )


def log_api_call(service: str, operation: str, success: bool = True):
    """Log an API call"""
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"API call | service={service} | operation={operation} | status={status}")


def log_error(error_type: str, message: str, details: str = None):
    """Log an error with details"""
    error_msg = f"ERROR | type={error_type} | message={message}"
    if details:
        error_msg += f" | details={details}"
    logger.error(error_msg)


def log_cache_operation(operation: str, hit: bool = None):
    """Log cache operations"""
    if hit is not None:
        result = "HIT" if hit else "MISS"
        logger.debug(f"Cache {operation} | result={result}")
    else:
        logger.debug(f"Cache {operation}")


import time
import functools
from typing import Type, Tuple, Union, Callable
from utils.logger import logger

def retry_operation(
    max_retries: int = 3,
    delay: float = 2.0,
    backoff: float = 2.0,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = (Exception,)
):
    """
    Decorator to retry a function call with exponential backoff.
    
    Args:
        max_retries: Maximum number of retries before giving up.
        delay: Initial delay between retries in seconds.
        backoff: Multiplier for delay after each failure.
        exceptions: Exception type(s) to catch and retry on.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            m_retries, m_delay = max_retries, delay
            
            while m_retries > 0:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    m_retries -= 1
                    if m_retries == 0:
                        logger.error(f"❌ Operation failed after {max_retries} retries: {str(e)}")
                        raise e
                    
                    logger.warning(
                        f"⚠️ Operation failed: {str(e)}. Retrying in {m_delay:.1f}s... ({m_retries} attempts left)"
                    )
                    time.sleep(m_delay)
                    m_delay *= backoff
            
            return func(*args, **kwargs) # Should be unreachable
        return wrapper
    return decorator

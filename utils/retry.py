
import time
import random
import functools
from typing import Type, Tuple, Union, Callable, Any
from utils.logger import logger

def retry_operation(
    max_retries: int = 3,
    delay: float = 2.0,
    backoff: float = 2.0,
    jitter: bool = True,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = (Exception,)
):
    """
    Decorator to retry a function call with exponential backoff and random full jitter.

    Args:
        max_retries: Maximum number of retries before giving up.
        delay: Initial delay between retries in seconds.
        backoff: Multiplier for delay after each failure.
        jitter: If True, adds full random jitter to delay.
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

                    sleep_time = random.uniform(0, m_delay) if jitter else m_delay
                    logger.warning(
                        f"⚠️ Operation failed: {str(e)}. Retrying in {sleep_time:.1f}s... ({m_retries} attempts left)"
                    )
                    time.sleep(sleep_time)
                    m_delay *= backoff

            return func(*args, **kwargs)
        return wrapper
    return decorator


def retry_with_fallback(
    primary_func: Callable[[], Any],
    fallback_func: Callable[[], Any],
    max_retries: int = 2
) -> Any:
    """
    Attempt primary_func with retries; if it fails across all retries, execute fallback_func.
    """
    try:
        decorated_primary = retry_operation(max_retries=max_retries, delay=1.5, backoff=2.0)(primary_func)
        return decorated_primary()
    except Exception as primary_err:
        logger.warning(f"⚠️ Primary LLM/Service failed ({primary_err}). Invoking Fallback engine...")
        try:
            return fallback_func()
        except Exception as fallback_err:
            logger.error(f"❌ Fallback engine also failed: {fallback_err}")
            raise fallback_err

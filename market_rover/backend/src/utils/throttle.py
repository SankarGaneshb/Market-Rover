import asyncio
from typing import TypeVar, Callable, Any
import functools

T = TypeVar("T")

# Standard concurrency limit for Market-Rover data/API calls
# Prevents 'Rate Exceeded' errors from yfinance and Gemini
CONCURRENCY_LIMIT = 5
_semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

def throttled(func: Callable[..., Any]):
    """Decorator to limit concurrency and automatically retry on rate limits."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        max_retries = 3
        base_delay = 1.0 # seconds

        async with _semaphore:
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    error_msg = str(e).lower()
                    # Catch 'Rate Limit', 'Too Many Requests', '429', 'Quota'
                    if any(x in error_msg for x in ["rate limit", "too many", "429", "quota"]):
                        if attempt == max_retries - 1:
                            raise # Last attempt failed

                        wait_time = base_delay * (2 ** attempt) # Exponential backoff
                        import random
                        wait_time += random.uniform(0, 0.5) # Add jitter

                        print(f"⚠️ Rate limit hit. Retrying in {wait_time:.2f}s... (Attempt {attempt+1}/{max_retries})")
                        await asyncio.sleep(wait_time)
                    else:
                        raise # Not a rate limit error, re-raise
    return wrapper

async def gather_with_concurrency(n: int, *tasks):
    """Executes tasks with a limited number of concurrent runs."""
    semaphore = asyncio.Semaphore(n)

    async def sem_task(task):
        async with semaphore:
            return await task

    return await asyncio.gather(*(sem_task(task) for task in tasks))

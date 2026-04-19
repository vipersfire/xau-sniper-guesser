import time
import logging
from functools import wraps
from typing import Callable, Type

logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_attempts: int = 4,
    base_delay: float = 2.0,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
):
    """Exponential backoff decorator: 2s, 4s, 8s, 16s."""
    def decorator(fn: Callable):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            delay = base_delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        raise
                    logger.warning(
                        "Attempt %d/%d failed for %s: %s. Retrying in %.1fs",
                        attempt, max_attempts, fn.__name__, e, delay,
                    )
                    time.sleep(delay)
                    delay *= 2
        return wrapper
    return decorator


async def async_retry_with_backoff(
    fn: Callable,
    *args,
    max_attempts: int = 4,
    base_delay: float = 2.0,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
    **kwargs,
):
    import asyncio
    delay = base_delay
    for attempt in range(1, max_attempts + 1):
        try:
            return await fn(*args, **kwargs)
        except exceptions as e:
            if attempt == max_attempts:
                raise
            logger.warning(
                "Async attempt %d/%d failed: %s. Retrying in %.1fs",
                attempt, max_attempts, e, delay,
            )
            await asyncio.sleep(delay)
            delay *= 2

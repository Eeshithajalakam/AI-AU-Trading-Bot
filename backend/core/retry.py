"""Retry helper for flaky external calls."""

import asyncio
import logging
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)
T = TypeVar("T")


async def async_retry(
    func: Callable[[], T],
    max_attempts: int = 3,
    delay: float = 1.0,
    exceptions: tuple = (Exception,),
) -> T:
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func()
            return await asyncio.to_thread(func)
        except exceptions as e:
            last_error = e
            logger.warning("Attempt %d/%d failed: %s", attempt, max_attempts, e)
            if attempt < max_attempts:
                await asyncio.sleep(delay * attempt)
    raise last_error  # type: ignore[misc]

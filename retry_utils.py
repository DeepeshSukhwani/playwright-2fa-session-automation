
"""Helpers for retrying transient automation failures."""

import logging
import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")
logger = logging.getLogger("github_automation")


def retry_transient(
        operation: Callable[[], T],
        retryable_exceptions: tuple[type[Exception], ...],
        max_attempts: int = 3,
        base_delay_seconds: float = 1.0,
) -> T:
    """Retry specified transient failures with bounded exponential backoff."""
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    if base_delay_seconds < 0:
        raise ValueError("base_delay_seconds cannot be negative")
    if not retryable_exceptions:
        raise ValueError("Specify at least one retryable exception")

    for attempt in range(1, max_attempts + 1):
        try:
            return operation()
        except retryable_exceptions:
            if attempt == max_attempts:
                logger.error("Operation failed after %s attempts", attempt)
                raise

            delay = base_delay_seconds * (2 ** (attempt - 1))
            logger.warning(
                "Transient failure on attempt %s/%s; retrying in %.1f seconds",
                attempt,
                max_attempts,
                delay,
            )
            time.sleep(delay)

    raise RuntimeError("Unreachable retry state")

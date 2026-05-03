from __future__ import annotations

import functools
import logging
import time
from typing import Any, Callable


def log_call(func: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        logging.info("Calling %s", func.__name__)
        result = func(*args, **kwargs)
        logging.info("%s completed", func.__name__)
        return result

    return wrapper


def retry(times: int = 3, delay: int = 1) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    logging.warning(
                        "Attempt %s/%s failed for %s: %s", attempt, times, func.__name__, exc
                    )
                    if attempt == times:
                        raise
                    time.sleep(delay)

        return wrapper

    return decorator

import functools
import time
from collections.abc import Callable
from typing import Any, TypeVar

from .logger import logger

F = TypeVar("F", bound=Callable[..., Any])


def trace_performance(func: F) -> F:
    """
    记录函数执行时间的简单装饰器。
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            duration = time.perf_counter() - start_time
            logger.debug(
                "Function {} executed in {:.4f} seconds",
                func.__name__,
                duration,
            )

    return wrapper  # type: ignore


def log_exceptions(func: F) -> F:
    """
    捕获并记录函数异常的装饰器。
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception("Exception in {}: {}", func.__name__, e)
            raise

    return wrapper  # type: ignore

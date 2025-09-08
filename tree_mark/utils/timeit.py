# === FILE: tree_mark/utils/timeit.py ===
import time
from typing import Callable, TypeVar, Any, Coroutine, ParamSpec
from tree_mark.core.models.usecase_result import UseCaseResult

P = ParamSpec('P')
R = TypeVar('R')

def timeit_async(func: Callable[P, Coroutine[Any, Any, R]]) -> Callable[P, Coroutine[Any, Any, UseCaseResult]]:
    """
    Decorator for async functions: measure elapsed time and return a UseCaseResult.
    If the wrapped function already returns a UseCaseResult, we only update its elapsed time.
    """
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> UseCaseResult:
        start = time.monotonic()
        result = await func(*args, **kwargs)
        duration = time.monotonic() - start

        # If the inner function already returned UseCaseResult, just update elapsed and return it.
        if isinstance(result, UseCaseResult):
            result.elapsed = duration
            return result

        # Otherwise, wrap into UseCaseResult (expecting result is a dict-like results payload)
        return UseCaseResult(results=result if (result is not None) else {}, elapsed=duration)

    return wrapper
"""Function decorator patterns."""

from __future__ import annotations

from functools import wraps
from typing import Callable, TypeVar

F = TypeVar("F", bound=Callable[..., object])


def log_call(func: F) -> F:
    @wraps(func)
    def wrapper(*args: object, **kwargs: object) -> object:
        print(f"Calling {func.__name__} with {args} {kwargs}")
        return func(*args, **kwargs)

    return wrapper  # type: ignore[return-value]


@log_call
def add(a: int, b: int) -> int:
    return a + b


def main() -> None:
    print(add(2, 3))


if __name__ == "__main__":
    main()

"""Itertools and functools usage examples."""

from __future__ import annotations

from functools import lru_cache, reduce
from itertools import chain, islice


def take(values: list[int], count: int) -> list[int]:
    return list(islice(values, count))


def flatten(nested: list[list[int]]) -> list[int]:
    return list(chain.from_iterable(nested))


def sum_all(values: list[int]) -> int:
    return reduce(lambda a, b: a + b, values, 0)


@lru_cache(maxsize=8)
def fib(n: int) -> int:
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)


def main() -> None:
    print(take([1, 2, 3, 4], 2))
    print(flatten([[1, 2], [3, 4]]))
    print(sum_all([1, 2, 3]))
    print(fib(6))


if __name__ == "__main__":
    main()

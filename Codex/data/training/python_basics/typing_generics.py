"""Generic functions and type variables."""

from __future__ import annotations

from typing import TypeVar

T = TypeVar("T")


def first(items: list[T]) -> T:
    if not items:
        raise ValueError("items must not be empty")
    return items[0]


def pair(a: T, b: T) -> tuple[T, T]:
    return (a, b)


def main() -> None:
    print(first(["a", "b"]))
    print(pair(1, 2))


if __name__ == "__main__":
    main()

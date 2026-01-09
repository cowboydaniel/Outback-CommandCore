"""Iterator and generator patterns."""

from __future__ import annotations

from collections.abc import Iterator


def count_up_to(limit: int) -> Iterator[int]:
    current = 1
    while current <= limit:
        yield current
        current += 1


def chunked(values: list[int], size: int) -> list[list[int]]:
    return [values[i : i + size] for i in range(0, len(values), size)]


def main() -> None:
    print(list(count_up_to(3)))
    print(chunked([1, 2, 3, 4, 5], 2))


if __name__ == "__main__":
    main()

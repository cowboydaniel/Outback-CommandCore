"""Multiprocessing basics with a worker pool."""

from __future__ import annotations

import multiprocessing as mp


def square(value: int) -> int:
    return value * value


def main() -> None:
    with mp.Pool(processes=2) as pool:
        results = pool.map(square, [1, 2, 3])
    print(results)


if __name__ == "__main__":
    main()

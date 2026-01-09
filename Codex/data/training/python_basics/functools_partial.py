"""functools.partial usage."""

from __future__ import annotations

from functools import partial


def power(base: int, exponent: int) -> int:
    return base ** exponent


def main() -> None:
    square = partial(power, exponent=2)
    print(square(5))


if __name__ == "__main__":
    main()

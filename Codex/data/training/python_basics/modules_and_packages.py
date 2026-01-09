"""Module import patterns and __all__ usage."""

from __future__ import annotations

import math

__all__ = ["circle_area", "circle_circumference"]


def circle_area(radius: float) -> float:
    return math.pi * radius ** 2


def circle_circumference(radius: float) -> float:
    return 2 * math.pi * radius


def main() -> None:
    print(circle_area(3.0))
    print(circle_circumference(3.0))


if __name__ == "__main__":
    main()

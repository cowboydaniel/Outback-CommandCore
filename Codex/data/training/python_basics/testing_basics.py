"""Basic testing patterns using assert statements."""

from __future__ import annotations

from functions import average, clamp


def test_average() -> None:
    assert average([1.0, 2.0, 3.0]) == 2.0


def test_clamp() -> None:
    assert clamp(1.5) == 1.0
    assert clamp(-1.0) == 0.0


def main() -> None:
    test_average()
    test_clamp()
    print("All tests passed")


if __name__ == "__main__":
    main()

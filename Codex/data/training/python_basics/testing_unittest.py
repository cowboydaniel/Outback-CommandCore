"""Basic unittest usage."""

from __future__ import annotations

import unittest

from functions import average, clamp


class TestFunctions(unittest.TestCase):
    def test_average(self) -> None:
        self.assertEqual(average([1.0, 2.0, 3.0]), 2.0)

    def test_clamp(self) -> None:
        self.assertEqual(clamp(1.5), 1.0)
        self.assertEqual(clamp(-1.0), 0.0)


def main() -> None:
    unittest.main(argv=["ignored"], exit=False)


if __name__ == "__main__":
    main()

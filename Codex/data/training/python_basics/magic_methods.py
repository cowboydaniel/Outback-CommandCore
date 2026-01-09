"""Special method examples for operator overloading."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Vector:
    x: float
    y: float

    def __add__(self, other: "Vector") -> "Vector":
        return Vector(self.x + other.x, self.y + other.y)

    def __repr__(self) -> str:
        return f"Vector(x={self.x}, y={self.y})"


def main() -> None:
    print(Vector(1, 2) + Vector(3, 4))


if __name__ == "__main__":
    main()

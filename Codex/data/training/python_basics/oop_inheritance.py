"""Inheritance and method overriding examples."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Vehicle:
    name: str
    speed: float

    def describe(self) -> str:
        return f"{self.name} traveling at {self.speed} km/h"


@dataclass
class Rover(Vehicle):
    terrain: str

    def describe(self) -> str:
        base = super().describe()
        return f"{base} on {self.terrain} terrain"


def main() -> None:
    rover = Rover("Scout", 12.5, "rocky")
    print(rover.describe())


if __name__ == "__main__":
    main()

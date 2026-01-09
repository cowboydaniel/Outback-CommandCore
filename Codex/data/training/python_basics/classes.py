"""Basic class and dataclass examples."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Coordinates:
    x: float
    y: float

    def distance_from_origin(self) -> float:
        return (self.x ** 2 + self.y ** 2) ** 0.5


@dataclass
class Rover:
    name: str
    location: Coordinates

    def move(self, dx: float, dy: float) -> None:
        self.location = Coordinates(self.location.x + dx, self.location.y + dy)


class Battery:
    def __init__(self, capacity: float) -> None:
        self.capacity = capacity
        self.charge = capacity

    def drain(self, amount: float) -> None:
        self.charge = max(0.0, self.charge - amount)

    def percent(self) -> float:
        return (self.charge / self.capacity) * 100


def main() -> None:
    rover = Rover("Echo", Coordinates(3.0, 4.0))
    print("Distance:", rover.location.distance_from_origin())
    rover.move(1.0, -2.0)
    print("Moved:", rover.location)

    battery = Battery(100.0)
    battery.drain(27.5)
    print("Battery:", battery.percent())


if __name__ == "__main__":
    main()

"""Dataclasses with slots and defaults."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Telemetry:
    source: str
    readings: list[float] = field(default_factory=list)

    def add(self, value: float) -> None:
        self.readings.append(value)

    def average(self) -> float:
        return sum(self.readings) / len(self.readings) if self.readings else 0.0


def main() -> None:
    telemetry = Telemetry("sensor-a")
    telemetry.add(1.2)
    telemetry.add(1.8)
    print(telemetry.average())


if __name__ == "__main__":
    main()

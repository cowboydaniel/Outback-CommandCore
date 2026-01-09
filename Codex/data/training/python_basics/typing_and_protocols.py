"""Type hinting and protocol-like patterns."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class SupportsReport(Protocol):
    def report(self) -> str:
        """Return a human-readable report."""


@dataclass
class Sensor:
    name: str
    reading: float

    def report(self) -> str:
        return f"{self.name}: {self.reading:.2f}"


def render_reports(items: list[SupportsReport]) -> str:
    return "\n".join(item.report() for item in items)


def main() -> None:
    sensors = [Sensor("temp", 21.5), Sensor("pressure", 101.3)]
    print(render_reports(sensors))


if __name__ == "__main__":
    main()

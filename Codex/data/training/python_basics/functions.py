"""Simple functions with type hints, defaults, and keyword-only arguments."""

from __future__ import annotations

from typing import Iterable


def average(values: Iterable[float]) -> float:
    """Compute the average of numeric values."""
    values_list = list(values)
    if not values_list:
        raise ValueError("values must not be empty")
    return sum(values_list) / len(values_list)


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    """Clamp a value between minimum and maximum."""
    return max(minimum, min(value, maximum))


def format_report(title: str, *lines: str, width: int = 40) -> str:
    """Format a report with a title and a list of lines."""
    header = f"{title:^{width}}"
    body = "\n".join(f"- {line}" for line in lines)
    return f"{header}\n{body}"


def scale_readings(readings: Iterable[float], *, factor: float) -> list[float]:
    """Scale readings by a keyword-only factor."""
    return [reading * factor for reading in readings]


def main() -> None:
    readings = [0.2, 0.5, 0.9]
    print("Average:", average(readings))
    print("Clamped:", clamp(1.2))
    print(format_report("Sensors", "A-OK", "Nominal"))
    print(scale_readings(readings, factor=100))


if __name__ == "__main__":
    main()

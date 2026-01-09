"""Error handling and context manager examples."""

from __future__ import annotations

from pathlib import Path


def safe_divide(numerator: float, denominator: float) -> float | None:
    try:
        return numerator / denominator
    except ZeroDivisionError:
        return None


def read_optional(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def parse_int(value: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"Invalid integer: {value}") from exc


def main() -> None:
    print(safe_divide(10, 0))
    print(read_optional(Path("missing.txt")))
    try:
        parse_int("not-a-number")
    except ValueError as exc:
        print("Error:", exc)


if __name__ == "__main__":
    main()

"""Basic data validation and normalization patterns."""

from __future__ import annotations


def validate_range(value: float, *, minimum: float, maximum: float) -> float:
    if not minimum <= value <= maximum:
        raise ValueError(f"Value {value} out of range")
    return value


def normalize_name(name: str) -> str:
    return " ".join(part.capitalize() for part in name.strip().split())


def main() -> None:
    print(validate_range(5, minimum=0, maximum=10))
    print(normalize_name("  jane   DOE "))


if __name__ == "__main__":
    main()

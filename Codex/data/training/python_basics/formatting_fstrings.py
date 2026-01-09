"""String formatting patterns."""

from __future__ import annotations


def format_status(name: str, value: float) -> str:
    return f"{name:>8}: {value:06.2f}"


def main() -> None:
    print(format_status("temp", 3.5))


if __name__ == "__main__":
    main()

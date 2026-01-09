"""Datetime and timezone handling."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


def in_one_hour() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=1)


def format_local(dt: datetime) -> str:
    return dt.astimezone().strftime("%Y-%m-%d %H:%M")


def main() -> None:
    print(in_one_hour())
    print(format_local(datetime.now(timezone.utc)))


if __name__ == "__main__":
    main()

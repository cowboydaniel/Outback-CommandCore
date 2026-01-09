"""Enum and constant patterns."""

from __future__ import annotations

from enum import Enum


class Status(Enum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"


DEFAULT_TIMEOUT = 5.0


def main() -> None:
    status = Status.OK
    print(status.value, DEFAULT_TIMEOUT)


if __name__ == "__main__":
    main()

"""Standard library usage samples."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from statistics import mean


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def average_latency(values: list[float]) -> float:
    return mean(values)


def ensure_log_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def main() -> None:
    print(timestamp())
    print(average_latency([1.1, 1.3, 0.9]))
    print(ensure_log_dir(Path("logs")))


if __name__ == "__main__":
    main()

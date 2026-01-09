"""Custom context manager examples."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path


@contextmanager
def temporary_file(path: Path, content: str) -> str:
    path.write_text(content, encoding="utf-8")
    try:
        yield path.read_text(encoding="utf-8")
    finally:
        path.unlink(missing_ok=True)


def main() -> None:
    with temporary_file(Path("temp.txt"), "hello") as text:
        print(text)


if __name__ == "__main__":
    main()

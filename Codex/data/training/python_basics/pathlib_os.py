"""Pathlib and os module patterns."""

from __future__ import annotations

import os
from pathlib import Path


def list_py_files(path: Path) -> list[str]:
    return [item.name for item in path.iterdir() if item.suffix == ".py"]


def current_working_dir() -> str:
    return os.getcwd()


def main() -> None:
    print(current_working_dir())
    print(list_py_files(Path(".")))


if __name__ == "__main__":
    main()

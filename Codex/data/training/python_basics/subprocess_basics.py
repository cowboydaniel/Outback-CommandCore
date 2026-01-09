"""Subprocess invocation patterns."""

from __future__ import annotations

import subprocess


def run_echo(message: str) -> str:
    result = subprocess.run(["echo", message], check=True, text=True, capture_output=True)
    return result.stdout.strip()


def main() -> None:
    print(run_echo("hello"))


if __name__ == "__main__":
    main()

"""Regular expression examples."""

from __future__ import annotations

import re


def extract_ids(text: str) -> list[str]:
    pattern = re.compile(r"ID-(\d+)")
    return pattern.findall(text)


def main() -> None:
    print(extract_ids("ID-12 and ID-98"))


if __name__ == "__main__":
    main()

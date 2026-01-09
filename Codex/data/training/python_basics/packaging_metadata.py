"""Simple package metadata patterns."""

from __future__ import annotations

from importlib import metadata


def version_for(package: str) -> str | None:
    try:
        return metadata.version(package)
    except metadata.PackageNotFoundError:
        return None


def main() -> None:
    print(version_for("pip"))


if __name__ == "__main__":
    main()

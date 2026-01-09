"""Logging configuration and usage."""

from __future__ import annotations

import logging


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(message)s")


def main() -> None:
    configure_logging()
    logging.info("System ready")
    logging.warning("Low power")


if __name__ == "__main__":
    main()

from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app import config
from ui.window import IOSToolsModule


def configure_logging() -> None:
    logging.basicConfig(
        level=config.LOG_LEVEL,
        format=config.LOG_FORMAT,
        handlers=[logging.StreamHandler()],
    )


def main() -> int:
    configure_logging()
    app = QApplication(sys.argv)
    app.setApplicationVersion(config.APP_VERSION)

    window = IOSToolsModule()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

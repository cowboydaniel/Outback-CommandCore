"""Application entry point for CommandCoreCodex."""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from Codex.app.config import DEFAULT_CONFIG
from Codex.app.gui import CommandCoreGUI


def create_app() -> QApplication:
    """Create the Qt application instance."""
    return QApplication(sys.argv)


def main() -> int:
    """Run the CommandCoreCodex GUI."""
    app = create_app()
    window = CommandCoreGUI(config=DEFAULT_CONFIG)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

"""Application entry point for CommandCoreCodex."""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

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

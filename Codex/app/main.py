"""Application entry point for CommandCoreCodex."""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from Codex.app.config import DEFAULT_CONFIG
from Codex.app.gui import CommandCoreGUI
from Codex.ui.splash_screen import show_splash_screen


def create_app() -> QApplication:
    """Create the Qt application instance."""
    return QApplication(sys.argv)


def main() -> int:
    """Run the CommandCoreCodex GUI."""
    app = create_app()

    # Show splash screen
    splash = show_splash_screen()
    app.processEvents()

    # Create main window while splash is showing
    splash.update_status("Loading AI models...")
    app.processEvents()

    window = CommandCoreGUI(config=DEFAULT_CONFIG)

    splash.update_status("Ready!")
    app.processEvents()

    # Close splash and show main window after animation completes
    def show_main():
        splash.close()
        window.show()

    QTimer.singleShot(5900, show_main)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

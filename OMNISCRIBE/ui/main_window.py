"""Main window for OMNISCRIBE."""
from __future__ import annotations

import os

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMainWindow, QStatusBar, QTabWidget

from OMNISCRIBE.app.config import ICON_RELATIVE_PATH, MIN_WINDOW_SIZE, WINDOW_TITLE
from OMNISCRIBE.tabs.script_tab import ScriptTab


class OmniscribeMainWindow(QMainWindow):
    def __init__(self, omniscribe) -> None:
        super().__init__()
        self.omniscribe = omniscribe
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.script_tab = ScriptTab(self.omniscribe, status_bar=self.status_bar)
        self._build_tabs()
        self._setup_toolbar()
        self._apply_window_settings()

    def _build_tabs(self) -> None:
        tabs = QTabWidget()
        tabs.addTab(self.script_tab, "Scripts")
        self.setCentralWidget(tabs)

    def _setup_toolbar(self) -> None:
        toolbar = self.addToolBar("Tools")

        new_action = QAction("New Script", self)
        new_action.triggered.connect(self.script_tab.new_script)
        toolbar.addAction(new_action)

        save_action = QAction("Save", self)
        save_action.triggered.connect(self.script_tab.save_script)
        toolbar.addAction(save_action)

        run_action = QAction("Run", self)
        run_action.triggered.connect(self.script_tab.run_current_script)
        toolbar.addAction(run_action)

        toolbar.addSeparator()

        import_action = QAction("Import Script", self)
        import_action.triggered.connect(self.script_tab.import_script)
        toolbar.addAction(import_action)

        export_action = QAction("Export Script", self)
        export_action.triggered.connect(self.script_tab.export_script)
        toolbar.addAction(export_action)

    def _apply_window_settings(self) -> None:
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(*MIN_WINDOW_SIZE)

        icon_path = os.path.join(self._project_root(), ICON_RELATIVE_PATH)
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    @staticmethod
    def _project_root() -> str:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

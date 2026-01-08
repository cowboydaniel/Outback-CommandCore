"""UI builder for the Validation tab."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTabWidget,
    QPlainTextEdit,
)


def setup_validation_tab(gui) -> None:
    """Set up the Validation tab."""
    tab = QWidget()
    layout = QVBoxLayout(tab)

    btn_layout = QHBoxLayout()
    lint_btn = QPushButton("Run Linter")
    run_btn = QPushButton("Run in Sandbox")

    lint_btn.clicked.connect(gui.run_linter)
    run_btn.clicked.connect(gui.run_in_sandbox)

    btn_layout.addWidget(lint_btn)
    btn_layout.addWidget(run_btn)

    output_tabs = QTabWidget()

    gui.linter_output = QPlainTextEdit()
    gui.linter_output.setReadOnly(True)
    gui.linter_output.setPlaceholderText("Linter output will appear here...")

    gui.sandbox_output = QPlainTextEdit()
    gui.sandbox_output.setReadOnly(True)
    gui.sandbox_output.setPlaceholderText("Sandbox output will appear here...")

    output_tabs.addTab(gui.linter_output, "Linter Output")
    output_tabs.addTab(gui.sandbox_output, "Sandbox Output")

    layout.addLayout(btn_layout)
    layout.addWidget(output_tabs)

    gui.tab_widget.addTab(tab, "Validation")

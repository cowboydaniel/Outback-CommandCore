"""UI builder for the Code Generation tab."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QDoubleSpinBox,
    QPushButton,
    QPlainTextEdit,
    QLabel,
)
from PySide6.QtGui import QFont


def setup_generation_tab(gui) -> None:
    """Set up the Code Generation tab."""
    tab = QWidget()
    layout = QVBoxLayout(tab)

    params_group = QGroupBox("Generation Parameters")
    params_layout = QFormLayout()

    gui.prompt_edit = QLineEdit()
    gui.prompt_edit.setPlaceholderText("Enter your prompt here...")

    gui.max_length = QSpinBox()
    gui.max_length.setRange(10, 2048)
    gui.max_length.setValue(100)

    gui.temperature = QDoubleSpinBox()
    gui.temperature.setRange(0.1, 2.0)
    gui.temperature.setValue(0.7)
    gui.temperature.setSingleStep(0.1)

    params_layout.addRow("Prompt:", gui.prompt_edit)
    params_layout.addRow("Max Length:", gui.max_length)
    params_layout.addRow("Temperature:", gui.temperature)

    generate_btn = QPushButton("Generate Code")
    generate_btn.clicked.connect(gui.generate_code)

    gui.generated_code = QPlainTextEdit()
    gui.generated_code.setReadOnly(True)
    gui.generated_code.setPlaceholderText("Generated code will appear here...")
    font = QFont("Monospace")
    font.setStyleHint(QFont.TypeWriter)
    gui.generated_code.setFont(font)

    params_group.setLayout(params_layout)

    layout.addWidget(params_group)
    layout.addWidget(generate_btn)
    layout.addWidget(QLabel("Generated Code:"))
    layout.addWidget(gui.generated_code)

    gui.tab_widget.addTab(tab, "Code Generation")

"""UI builder for the Training Control tab."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QFormLayout,
    QSpinBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QPushButton,
    QProgressBar,
    QPlainTextEdit,
    QLabel,
)


def setup_training_tab(gui) -> None:
    """Set up the Training Control tab."""
    tab = QWidget()
    layout = QVBoxLayout(tab)

    params_group = QGroupBox("Training Parameters")
    params_layout = QFormLayout()

    gui.batch_size = QSpinBox()
    gui.batch_size.setRange(1, 256)
    gui.batch_size.setValue(32)

    gui.learning_rate = QDoubleSpinBox()
    gui.learning_rate.setRange(1e-6, 1.0)
    gui.learning_rate.setValue(1e-4)
    gui.learning_rate.setDecimals(6)

    gui.num_epochs = QSpinBox()
    gui.num_epochs.setRange(1, 1000)
    gui.num_epochs.setValue(10)

    params_layout.addRow("Batch Size:", gui.batch_size)
    params_layout.addRow("Learning Rate:", gui.learning_rate)
    params_layout.addRow("Number of Epochs:", gui.num_epochs)

    controls_layout = QHBoxLayout()
    gui.start_training_btn = QPushButton("Start Training")
    gui.stop_training_btn = QPushButton("Stop Training")
    gui.stop_training_btn.setEnabled(False)

    controls_layout.addWidget(gui.start_training_btn)
    controls_layout.addWidget(gui.stop_training_btn)

    gui.training_progress = QProgressBar()
    gui.training_progress.setRange(0, 100)

    gui.training_status = QPlainTextEdit()
    gui.training_status.setReadOnly(True)
    gui.training_status.setPlaceholderText("Training status will appear here...")

    params_group.setLayout(params_layout)

    layout.addWidget(params_group)
    layout.addLayout(controls_layout)
    layout.addWidget(QLabel("Progress:"))
    layout.addWidget(gui.training_progress)
    layout.addWidget(QLabel("Status:"))
    layout.addWidget(gui.training_status)

    gui.tab_widget.addTab(tab, "Training Control")

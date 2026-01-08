"""UI builder for the Data Preparation tab."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QPlainTextEdit,
    QLabel,
)


def setup_data_prep_tab(gui) -> None:
    """Set up the Data Preparation tab."""
    tab = QWidget()
    layout = QVBoxLayout(tab)

    dataset_group = QGroupBox("Dataset Selection")
    dataset_layout = QVBoxLayout()

    dir_layout = QHBoxLayout()
    gui.dataset_path_edit = QLineEdit()
    gui.dataset_path_edit.setPlaceholderText("Select dataset directory...")
    gui.dataset_path_edit.setReadOnly(True)

    browse_btn = QPushButton("Browse...")
    browse_btn.clicked.connect(gui.browse_dataset_dir)

    dir_layout.addWidget(gui.dataset_path_edit)
    dir_layout.addWidget(browse_btn)

    prepare_btn = QPushButton("Prepare Dataset")
    prepare_btn.clicked.connect(gui.prepare_dataset)

    gui.data_prep_status = QPlainTextEdit()
    gui.data_prep_status.setReadOnly(True)
    gui.data_prep_status.setPlaceholderText("Status messages will appear here...")

    dataset_layout.addLayout(dir_layout)
    dataset_layout.addWidget(prepare_btn)
    dataset_group.setLayout(dataset_layout)

    layout.addWidget(dataset_group)
    layout.addWidget(QLabel("Status:"))
    layout.addWidget(gui.data_prep_status)

    gui.tab_widget.addTab(tab, "Data Preparation")

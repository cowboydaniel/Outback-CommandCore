"""Alerts tab layout for NIGHTFIRE."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QHeaderView


def setup_alerts_tab(ui) -> QWidget:
    """Set up the alerts tab."""
    alerts_tab = QWidget()
    layout = QVBoxLayout(alerts_tab)

    # Alerts table
    ui.alerts_table = QTableWidget(0, 4)
    ui.alerts_table.setHorizontalHeaderLabels(["Time", "Type", "Severity", "Message"])
    ui.alerts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    ui.alerts_table.setEditTriggers(QTableWidget.NoEditTriggers)

    layout.addWidget(ui.alerts_table)

    # Alert controls
    controls = QHBoxLayout()
    btn_clear = QPushButton("Clear All Alerts")
    btn_clear.clicked.connect(ui.clear_alerts)
    controls.addWidget(btn_clear)
    controls.addStretch()

    layout.addLayout(controls)

    return alerts_tab

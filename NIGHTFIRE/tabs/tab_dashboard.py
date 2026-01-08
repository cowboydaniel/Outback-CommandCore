"""Dashboard tab layout for NIGHTFIRE."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton

from NIGHTFIRE.ui.styles import app_styles


def setup_dashboard_tab(ui) -> QWidget:
    """Set up the dashboard tab."""
    dashboard_tab = QWidget()
    layout = QVBoxLayout(dashboard_tab)

    # Status overview
    status_group = QWidget()
    status_layout = QHBoxLayout(status_group)

    # System status
    sys_status = QWidget()
    sys_layout = QVBoxLayout(sys_status)
    sys_layout.addWidget(QLabel("<h3>System Status</h3>"))
    ui.status_indicator = QLabel("OPERATIONAL")
    ui.status_indicator.setStyleSheet(app_styles.STATUS_OK_STYLE)
    sys_layout.addWidget(ui.status_indicator)
    status_layout.addWidget(sys_status)

    # Threat level
    threat_status = QWidget()
    threat_layout = QVBoxLayout(threat_status)
    threat_layout.addWidget(QLabel("<h3>Threat Level</h3>"))
    ui.threat_level = QLabel("LOW")
    ui.threat_level.setStyleSheet(app_styles.THREAT_LOW_STYLE)
    threat_layout.addWidget(ui.threat_level)
    status_layout.addWidget(threat_status)

    layout.addWidget(status_group)

    # Quick actions
    actions_group = QWidget()
    actions_layout = QHBoxLayout(actions_group)

    ui.btn_start = QPushButton("Start Monitoring")
    ui.btn_stop = QPushButton("Stop Monitoring")
    ui.btn_stop.setEnabled(False)

    actions_layout.addWidget(ui.btn_start)
    actions_layout.addWidget(ui.btn_stop)
    actions_layout.addStretch()

    layout.addWidget(actions_group)
    layout.addStretch()

    return dashboard_tab

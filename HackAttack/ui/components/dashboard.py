"""Dashboard widget for the HackAttack GUI."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
)

from HackAttack.ui.styles import (
    DASHBOARD_HEADER_TITLE_STYLE,
    DASHBOARD_REFRESH_BUTTON_STYLE,
    DASHBOARD_CARD_STYLE,
    DASHBOARD_VALUE_STYLE,
    DASHBOARD_NAME_STYLE,
    DASHBOARD_DETAIL_STYLE,
    DASHBOARD_STATUS_CARD_TEMPLATE,
    DASHBOARD_STATUS_TITLE_STYLE,
    DASHBOARD_STATUS_NAME_STYLE,
    DASHBOARD_STATUS_STATE_STYLE,
    DASHBOARD_ACTIVITY_LIST_STYLE,
)


class DashboardWidget(QWidget):
    """Interactive dashboard widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.dashboard_metrics = []
        self.metric_cards = []
        self.status_tiles = []
        self.status_tile_labels = []
        self.activity_entries = []
        self.activity_feed = None
        self._build_ui()

    def _build_ui(self) -> None:
        container_layout = QVBoxLayout(self)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(16)

        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_title = QLabel("Security Operations Snapshot")
        header_title.setStyleSheet(DASHBOARD_HEADER_TITLE_STYLE)
        header_layout.addWidget(header_title)
        header_layout.addStretch()

        refresh_button = QPushButton("Run Quick Health Check")
        refresh_button.setStyleSheet(DASHBOARD_REFRESH_BUTTON_STYLE)
        header_layout.addWidget(refresh_button)
        container_layout.addWidget(header)

        metrics_row = QWidget()
        metrics_layout = QHBoxLayout(metrics_row)
        metrics_layout.setContentsMargins(0, 0, 0, 0)
        metrics_layout.setSpacing(12)

        self.dashboard_metrics = [
            {"label": "Active Targets", "value": 12, "detail": "3 new today"},
            {"label": "Open Findings", "value": 7, "detail": "2 critical"},
            {"label": "Sensors Online", "value": 18, "detail": "100% operational"},
            {"label": "Automations Running", "value": 5, "detail": "Next run in 15m"},
        ]

        self.metric_cards = []
        for metric in self.dashboard_metrics:
            card = QWidget()
            card.setStyleSheet(DASHBOARD_CARD_STYLE)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 12, 12, 12)
            card_layout.setSpacing(6)

            value_label = QLabel(str(metric["value"]))
            value_label.setStyleSheet(DASHBOARD_VALUE_STYLE)
            name_label = QLabel(metric["label"])
            name_label.setStyleSheet(DASHBOARD_NAME_STYLE)
            detail_label = QLabel(metric["detail"])
            detail_label.setStyleSheet(DASHBOARD_DETAIL_STYLE)

            card_layout.addWidget(value_label)
            card_layout.addWidget(name_label)
            card_layout.addWidget(detail_label)
            metrics_layout.addWidget(card)
            self.metric_cards.append((value_label, detail_label))

        container_layout.addWidget(metrics_row)

        status_and_activity = QWidget()
        status_layout = QHBoxLayout(status_and_activity)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(12)

        status_column = QWidget()
        status_column_layout = QVBoxLayout(status_column)
        status_column_layout.setContentsMargins(0, 0, 0, 0)
        status_column_layout.setSpacing(10)

        status_title = QLabel("Live Status")
        status_title.setStyleSheet(DASHBOARD_STATUS_TITLE_STYLE)
        status_column_layout.addWidget(status_title)

        self.status_tiles = [
            {"name": "Threat Intel Feed", "state": "Streaming", "accent": "#a6e3a1"},
            {"name": "Credential Watch", "state": "2 alerts", "accent": "#f38ba8"},
            {"name": "Patch Compliance", "state": "92% ready", "accent": "#f9e2af"},
        ]

        self.status_tile_labels = []
        for tile in self.status_tiles:
            tile_card = QWidget()
            tile_card.setStyleSheet(
                DASHBOARD_STATUS_CARD_TEMPLATE.format(accent=tile["accent"])
            )
            tile_layout = QVBoxLayout(tile_card)
            tile_layout.setContentsMargins(10, 10, 10, 10)
            tile_layout.setSpacing(4)
            name_label = QLabel(tile["name"])
            name_label.setStyleSheet(DASHBOARD_STATUS_NAME_STYLE)
            state_label = QLabel(tile["state"])
            state_label.setStyleSheet(DASHBOARD_STATUS_STATE_STYLE)
            tile_layout.addWidget(name_label)
            tile_layout.addWidget(state_label)
            status_column_layout.addWidget(tile_card)
            self.status_tile_labels.append(state_label)

        status_layout.addWidget(status_column, 1)

        activity_column = QWidget()
        activity_layout = QVBoxLayout(activity_column)
        activity_layout.setContentsMargins(0, 0, 0, 0)
        activity_layout.setSpacing(8)
        activity_title = QLabel("Recent Activity")
        activity_title.setStyleSheet(DASHBOARD_STATUS_TITLE_STYLE)
        activity_layout.addWidget(activity_title)

        self.activity_feed = QListWidget()
        self.activity_feed.setStyleSheet(DASHBOARD_ACTIVITY_LIST_STYLE)

        self.activity_entries = [
            "09:12 - Firmware scan completed on 4 devices.",
            "09:05 - New vulnerability advisory synced.",
            "08:58 - Network sweep queued (segment 10.0.4.0/24).",
            "08:47 - MFA audit report exported.",
        ]
        for entry in self.activity_entries:
            self.activity_feed.addItem(entry)

        activity_layout.addWidget(self.activity_feed)
        status_layout.addWidget(activity_column, 2)

        container_layout.addWidget(status_and_activity)

        refresh_button.clicked.connect(self.refresh_dashboard)

    def refresh_dashboard(self) -> None:
        """Simulate a dashboard refresh."""
        self.dashboard_metrics[0]["value"] += 1
        self.dashboard_metrics[1]["value"] = max(0, self.dashboard_metrics[1]["value"] - 1)
        self.dashboard_metrics[2]["value"] = 18
        self.dashboard_metrics[3]["value"] = 5

        for metric, labels in zip(self.dashboard_metrics, self.metric_cards):
            value_label, detail_label = labels
            value_label.setText(str(metric["value"]))
            detail_label.setText(metric["detail"])

        self.status_tiles[1]["state"] = "1 alert"
        self.status_tiles[2]["state"] = "93% ready"
        for tile, label in zip(self.status_tiles, self.status_tile_labels):
            label.setText(tile["state"])

        self.activity_entries.insert(0, "09:18 - Health check completed with 0 errors.")
        self.activity_feed.clear()
        for entry in self.activity_entries[:6]:
            self.activity_feed.addItem(entry)

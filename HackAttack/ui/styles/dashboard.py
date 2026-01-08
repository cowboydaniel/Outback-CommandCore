"""Styles for dashboard widgets."""

DASHBOARD_HEADER_TITLE_STYLE = "font-size: 20px; font-weight: bold; color: #cdd6f4;"

DASHBOARD_REFRESH_BUTTON_STYLE = """
    QPushButton {
        background-color: #89b4fa;
        color: #1e1e2e;
        padding: 8px 14px;
        border-radius: 6px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #b4befe;
    }
"""

DASHBOARD_CARD_STYLE = """
    background-color: #313244;
    border-radius: 10px;
    padding: 14px;
    border: 1px solid #45475a;
"""

DASHBOARD_VALUE_STYLE = "font-size: 26px; font-weight: bold; color: #a6e3a1;"
DASHBOARD_NAME_STYLE = "font-size: 13px; color: #cdd6f4;"
DASHBOARD_DETAIL_STYLE = "font-size: 12px; color: #a6adc8;"

DASHBOARD_STATUS_CARD_TEMPLATE = """
    background-color: #313244;
    border-radius: 10px;
    padding: 12px;
    border-left: 4px solid {accent};
    border-top: 1px solid #45475a;
    border-right: 1px solid #45475a;
    border-bottom: 1px solid #45475a;
"""

DASHBOARD_STATUS_TITLE_STYLE = "font-size: 16px; font-weight: bold; color: #cdd6f4;"
DASHBOARD_STATUS_NAME_STYLE = "font-size: 13px; color: #cdd6f4;"
DASHBOARD_STATUS_STATE_STYLE = "font-size: 14px; font-weight: bold; color: #cdd6f4;"

DASHBOARD_ACTIVITY_LIST_STYLE = """
    QListWidget {
        background-color: #313244;
        border-radius: 10px;
        padding: 6px;
        border: 1px solid #45475a;
        color: #cdd6f4;
        font-size: 13px;
    }
    QListWidget::item {
        padding: 8px;
        border-bottom: 1px solid rgba(205, 214, 244, 0.1);
    }
"""

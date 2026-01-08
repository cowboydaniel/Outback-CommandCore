"""Dashboard tab."""

from HackAttack.tabs.tab_base import build_tab
from HackAttack.ui.components import DashboardWidget


def build_dashboard_tab(title: str, description: str, icon_name: str):
    dashboard_widget = DashboardWidget()
    return build_tab(title, description, icon_name, dashboard_widget, show_description=False)

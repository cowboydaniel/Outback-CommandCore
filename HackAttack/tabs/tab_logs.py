"""Logs tab."""

from HackAttack.modules.logs import LogsGUI
from HackAttack.tabs.tab_base import build_tab


def build_logs_tab(title: str, description: str, icon_name: str):
    widget = LogsGUI()
    return build_tab(title, description, icon_name, widget)

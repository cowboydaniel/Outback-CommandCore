"""Automation tab."""

from HackAttack.modules.automation import AutomationGUI
from HackAttack.tabs.tab_base import build_tab


def build_automation_tab(title: str, description: str, icon_name: str):
    widget = AutomationGUI()
    return build_tab(title, description, icon_name, widget)

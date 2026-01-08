"""Settings & reports tab."""

from HackAttack.modules.settings_reports import SettingsReportsGUI
from HackAttack.tabs.tab_base import build_tab


def build_settings_tab(title: str, description: str, icon_name: str):
    widget = SettingsReportsGUI()
    return build_tab(title, description, icon_name, widget)

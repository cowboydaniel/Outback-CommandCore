"""Forensics tab."""

from HackAttack.modules.forensics import ForensicsGUI
from HackAttack.tabs.tab_base import build_tab


def build_forensics_tab(title: str, description: str, icon_name: str):
    widget = ForensicsGUI()
    return build_tab(title, description, icon_name, widget)

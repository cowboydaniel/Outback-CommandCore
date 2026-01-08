"""Firmware analysis tab."""

from HackAttack.modules.firmware_analysis import FirmwareAnalysisGUI
from HackAttack.tabs.tab_base import build_tab


def build_firmware_analysis_tab(title: str, description: str, icon_name: str):
    widget = FirmwareAnalysisGUI()
    return build_tab(title, description, icon_name, widget)

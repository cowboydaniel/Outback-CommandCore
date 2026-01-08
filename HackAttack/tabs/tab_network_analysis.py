"""Network analysis tab."""

from HackAttack.modules.network_analysis import NetworkAnalysisGUI
from HackAttack.tabs.tab_base import build_tab


def build_network_analysis_tab(title: str, description: str, icon_name: str):
    widget = NetworkAnalysisGUI()
    return build_tab(title, description, icon_name, widget)

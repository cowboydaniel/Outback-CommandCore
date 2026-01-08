"""Help & documentation tab."""

from HackAttack.modules.help_docs import HelpDocsGUI
from HackAttack.tabs.tab_base import build_tab


def build_help_tab(title: str, description: str, icon_name: str):
    widget = HelpDocsGUI()
    return build_tab(title, description, icon_name, widget)

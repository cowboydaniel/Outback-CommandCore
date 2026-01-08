"""Mobile & embedded tools tab."""

from HackAttack.modules.mobile_embedded_tools import MobileEmbeddedToolsGUI
from HackAttack.tabs.tab_base import build_tab


def build_mobile_embedded_tab(title: str, description: str, icon_name: str):
    widget = MobileEmbeddedToolsGUI()
    return build_tab(title, description, icon_name, widget)

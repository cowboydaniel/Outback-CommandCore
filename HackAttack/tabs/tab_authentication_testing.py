"""Authentication testing tab."""

from HackAttack.modules.authentication_testing import AuthenticationTestingGUI
from HackAttack.tabs.tab_base import build_tab


def build_authentication_tab(title: str, description: str, icon_name: str):
    widget = AuthenticationTestingGUI()
    return build_tab(title, description, icon_name, widget)

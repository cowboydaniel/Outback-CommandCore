"""Device discovery tab."""

from HackAttack.modules.device_discovery import DeviceDiscoveryGUI
from HackAttack.tabs.tab_base import build_tab


def build_device_discovery_tab(title: str, description: str, icon_name: str):
    widget = DeviceDiscoveryGUI()
    return build_tab(title, description, icon_name, widget)

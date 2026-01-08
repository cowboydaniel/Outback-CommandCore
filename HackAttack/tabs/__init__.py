"""Tab definitions for the HackAttack GUI."""

from HackAttack.core import TabDefinition
from HackAttack.tabs import (
    tab_dashboard,
    tab_device_discovery,
    tab_network_analysis,
    tab_firmware_analysis,
    tab_authentication_testing,
    tab_exploitation,
    tab_mobile_embedded,
    tab_forensics,
    tab_settings_reports,
    tab_automation,
    tab_logs,
    tab_help_docs,
)

TAB_DEFINITIONS = [
    TabDefinition(
        "Dashboard",
        "Monitor your security assessment activities, view system status, and access quick actions.",
        "📊",
        tab_dashboard.build_dashboard_tab,
    ),
    TabDefinition(
        "Device Discovery & Info",
        "Scan and analyze connected devices on your network, including detailed hardware and software information.",
        "🔍",
        tab_device_discovery.build_device_discovery_tab,
    ),
    TabDefinition(
        "Network & Protocol Analysis",
        "Analyze network traffic, perform protocol analysis, and identify vulnerabilities.",
        "🌐",
        tab_network_analysis.build_network_analysis_tab,
    ),
    TabDefinition(
        "Firmware & OS Analysis",
        "Inspect firmware images, analyze operating systems, and identify potential security issues.",
        "💾",
        tab_firmware_analysis.build_firmware_analysis_tab,
    ),
    TabDefinition(
        "Authentication & Password Testing",
        "Test authentication mechanisms and perform password security assessments.",
        "🔑",
        tab_authentication_testing.build_authentication_tab,
    ),
    TabDefinition(
        "Exploitation & Payloads",
        "Develop and manage exploits and payloads for security testing purposes.",
        "⚡",
        tab_exploitation.build_exploitation_tab,
    ),
    TabDefinition(
        "Mobile & Embedded Tools",
        "Specialized tools for testing mobile and embedded device security.",
        "📱",
        tab_mobile_embedded.build_mobile_embedded_tab,
    ),
    TabDefinition(
        "Forensics & Incident Response",
        "Investigate security incidents and perform digital forensics.",
        "🔍",
        tab_forensics.build_forensics_tab,
    ),
    TabDefinition(
        "Settings & Reports",
        "Configure application settings and generate detailed security reports.",
        "⚙️",
        tab_settings_reports.build_settings_tab,
    ),
    TabDefinition(
        "Automation & Scripting",
        "Create and manage automated security testing workflows.",
        "🤖",
        tab_automation.build_automation_tab,
    ),
    TabDefinition(
        "Logs & History",
        "View detailed logs and history of all security testing activities.",
        "📝",
        tab_logs.build_logs_tab,
    ),
    TabDefinition(
        "Help & Documentation",
        "Access user guides, tutorials, and API documentation.",
        "❓",
        tab_help_docs.build_help_tab,
    ),
]


def get_tab_definitions():
    """Return a copy of the tab definitions."""
    return list(TAB_DEFINITIONS)

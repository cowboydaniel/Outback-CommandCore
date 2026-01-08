import pytest


pytest.importorskip("PySide6")


def test_tab_imports():
    from BLACKSTORM.tabs import (
        advanced_tab,
        bulk_operations_tab,
        dashboard_tab,
        device_management_tab,
        forensic_tools_tab,
        security_compliance_tab,
        settings_tab,
        wipe_operations_tab,
    )

    assert hasattr(advanced_tab, "AdvancedTab")
    assert hasattr(bulk_operations_tab, "BulkOperationsTab")
    assert hasattr(dashboard_tab, "DashboardTab")
    assert hasattr(device_management_tab, "DeviceManagementTab")
    assert hasattr(forensic_tools_tab, "ForensicToolsTab")
    assert hasattr(security_compliance_tab, "SecurityComplianceTab")
    assert hasattr(settings_tab, "SettingsTab")
    assert hasattr(wipe_operations_tab, "WipeOperationsTab")

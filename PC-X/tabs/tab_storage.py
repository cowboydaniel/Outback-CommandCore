"""Storage tab layout for PC-X."""

import json
import logging
import subprocess

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSplitter,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)
from PySide6.QtGui import QFont


def setup_storage_tab(module) -> None:
    """Set up the Storage tab with disk and partition information."""
    storage_tab = module.device_tabs["storage"]

    splitter = QSplitter(Qt.Vertical)

    partitions_group = QGroupBox("Disk Partitions")
    partitions_layout = QVBoxLayout(partitions_group)

    module.partition_tree = QTreeWidget()
    module.partition_tree.setHeaderLabels(["Device", "Size", "Type", "Mount Point", "File System"])
    module.partition_tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)

    try:
        result = subprocess.run(
            ["lsblk", "-o", "NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE", "--json"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)

            for device in data.get("blockdevices", []):
                device_item = QTreeWidgetItem(
                    [
                        f"/dev/{device['name']}",
                        device.get("size", ""),
                        device.get("type", ""),
                        device.get("mountpoint", "") or "",
                        device.get("fstype", "") or "",
                    ]
                )
                module.partition_tree.addTopLevelItem(device_item)

                for child in device.get("children", []):
                    child_item = QTreeWidgetItem(
                        [
                            f"/dev/{child['name']}",
                            child.get("size", ""),
                            child.get("type", ""),
                            child.get("mountpoint", "") or "",
                            child.get("fstype", "") or "",
                        ]
                    )
                    device_item.addChild(child_item)

                device_item.setExpanded(True)
    except Exception as exc:
        logging.error("Error getting partition info: %s", exc)

    partitions_layout.addWidget(module.partition_tree)

    scheme_btn = QPushButton("Check Partition Scheme")
    scheme_btn.clicked.connect(lambda: module.check_partition_scheme())
    partitions_layout.addWidget(scheme_btn)

    splitter.addWidget(partitions_group)

    smart_group = QGroupBox("SMART Data")
    smart_layout = QVBoxLayout(smart_group)

    drive_frame = QFrame()
    drive_layout = QHBoxLayout(drive_frame)
    drive_layout.setContentsMargins(0, 0, 0, 0)

    drive_label = QLabel("Select Drive:")
    drive_label.setFont(QFont("Arial", 10, QFont.Bold))
    drive_layout.addWidget(drive_label)

    module.drive_combo = QComboBox()
    drives = module.list_block_devices()
    module.drive_combo.addItems(drives)
    if drives:
        module.selected_drive = drives[0]
    module.drive_combo.currentTextChanged.connect(module.on_drive_selected)
    drive_layout.addWidget(module.drive_combo)

    drive_layout.addStretch()

    refresh_btn = QPushButton("Refresh")
    refresh_btn.clicked.connect(module.refresh_smart_info)
    drive_layout.addWidget(refresh_btn)

    smart_layout.addWidget(drive_frame)

    module.smart_info_text = QTextEdit()
    module.smart_info_text.setReadOnly(True)
    module.smart_info_text.setFont(QFont("Courier", 9))
    smart_layout.addWidget(module.smart_info_text)

    splitter.addWidget(smart_group)

    splitter.setSizes([300, 400])

    tab_layout = QVBoxLayout(storage_tab)
    tab_layout.setContentsMargins(5, 5, 5, 5)
    tab_layout.addWidget(splitter)

    if drives:
        module.refresh_smart_info()

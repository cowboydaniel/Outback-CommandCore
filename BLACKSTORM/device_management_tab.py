"""
Device Management tab for BLACKSTORM - Manage storage devices.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QGroupBox, QTextEdit,
    QFormLayout, QLineEdit, QFileDialog, QTabWidget, QProgressBar,
    QMessageBox, QComboBox, QCheckBox, QSplitter, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor
import psutil

class DeviceManagementTab(QWidget):
    """Tab for managing storage devices."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.refresh_devices()
        
        # Set up auto-refresh
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_devices)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Refresh button
        btn_refresh = QPushButton("Refresh")
        btn_refresh.setStyleSheet("""
            QPushButton {
                background: #3498DB;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background: #2980B9;
            }
        """)
        btn_refresh.clicked.connect(self.refresh_devices)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(btn_refresh)
        
        # Devices table
        self.device_table = QTableWidget()
        self.device_table.setColumnCount(7)
        self.device_table.setHorizontalHeaderLabels([
            "Device", "Model", "Size", "Type", "Filesystem", "Mounted", "Health"
        ])
        
        # Style the table
        self.device_table.setStyleSheet("""
            QTableWidget {
                background: #2A2D2E;
                color: #E0E0E0;
                border: 1px solid #3E3E3E;
                border-radius: 4px;
                gridline-color: #3E3E3E;
            }
            QHeaderView::section {
                background: #2A2D2E;
                color: #B0B0B0;
                padding: 5px;
                border: none;
                border-right: 1px solid #3E3E3E;
                border-bottom: 1px solid #3E3E3E;
            }
            QTableWidget::item {
                padding: 5px;
                border-bottom: 1px solid #3E3E3E;
            }
            QTableWidget::item:selected {
                background: #3E3E3E;
                color: white;
            }
        """)
        
        # Configure table properties
        self.device_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.device_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.device_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.device_table.setSortingEnabled(True)
        
        # Set header resize modes
        header = self.device_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Device
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Model
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Size
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Type
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Filesystem
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Mounted
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Health
        
        # Device details
        details_group = QGroupBox("Device Details")
        details_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #3E3E3E;
                border-radius: 4px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        details_layout = QFormLayout()
        
        self.details_name = QLabel("-")
        self.details_model = QLabel("-")
        self.details_size = QLabel("-")
        self.details_type = QLabel("-")
        self.details_fs = QLabel("-")
        self.details_mount = QLabel("-")
        self.details_health = QLabel("-")
        
        details_layout.addRow("Device:", self.details_name)
        details_layout.addRow("Model:", self.details_model)
        details_layout.addRow("Size:", self.details_size)
        details_layout.addRow("Type:", self.details_type)
        details_layout.addRow("Filesystem:", self.details_fs)
        details_layout.addRow("Mounted at:", self.details_mount)
        details_layout.addRow("Health:", self.details_health)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        
        self.btn_mount = QPushButton("Mount")
        self.btn_unmount = QPushButton("Unmount")
        self.btn_format = QPushButton("Format...")
        self.btn_smart = QPushButton("S.M.A.R.T. Info")
        self.btn_benchmark = QPushButton("Benchmark")
        
        # Style buttons
        for btn in [self.btn_mount, self.btn_unmount, self.btn_format, 
                   self.btn_smart, self.btn_benchmark]:
            btn.setStyleSheet("""
                QPushButton {
                    padding: 5px 10px;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                    background: #2A2D2E;
                    color: #E0E0E0;
                }
                QPushButton:disabled {
                    color: #666666;
                }
                QPushButton:hover:!disabled {
                    background: #3E3E3E;
                }
            """)
        
        btn_layout.addWidget(self.btn_mount)
        btn_layout.addWidget(self.btn_unmount)
        btn_layout.addWidget(self.btn_format)
        btn_layout.addWidget(self.btn_smart)
        btn_layout.addWidget(self.btn_benchmark)
        
        details_layout.addRow(btn_layout)
        details_group.setLayout(details_layout)
        
        # Add widgets to main layout
        layout.addLayout(button_layout)
        layout.addWidget(self.device_table)
        layout.addWidget(details_group)
        
        # Connect signals
        self.device_table.itemSelectionChanged.connect(self.update_device_details)
        
        # Disable buttons initially
        self.update_button_states()
    
    def refresh_devices(self):
        """Refresh the list of storage devices."""
        # Save selection
        current_row = self.device_table.currentRow()
        current_device = None
        if current_row >= 0:
            current_device = self.device_table.item(current_row, 0).text()
        
        # Clear table
        self.device_table.setRowCount(0)
        
        # Get disk partitions
        try:
            partitions = psutil.disk_partitions(all=True)
            devices = {}
            
            # Get disk usage for each partition
            for part in partitions:
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                except Exception:
                    usage = None
                
                device = part.device.split('/')[-1]
                if device not in devices:
                    devices[device] = {
                        'model': 'Unknown',
                        'size': 'Unknown',
                        'type': part.fstype or 'Unknown',
                        'mountpoint': part.mountpoint,
                        'usage': usage
                    }
            
            # Add devices to table
            for i, (device, info) in enumerate(devices.items()):
                self.device_table.insertRow(i)
                
                # Device
                item = QTableWidgetItem(device)
                self.device_table.setItem(i, 0, item)
                
                # Model (placeholder)
                self.device_table.setItem(i, 1, QTableWidgetItem("Unknown"))
                
                # Size
                size = "Unknown"
                if info['usage']:
                    size = f"{info['usage'].total / (1024**3):.1f} GB"
                self.device_table.setItem(i, 2, QTableWidgetItem(size))
                
                # Type
                self.device_table.setItem(i, 3, QTableWidgetItem(info['type']))
                
                # Filesystem
                self.device_table.setItem(i, 4, QTableWidgetItem(info['type']))
                
                # Mounted
                mounted = "Yes" if info['mountpoint'] else "No"
                self.device_table.setItem(i, 5, QTableWidgetItem(mounted))
                
                # Health (placeholder)
                health_item = QTableWidgetItem("Good")
                health_item.setForeground(QColor("#2ECC71"))  # Green
                self.device_table.setItem(i, 6, health_item)
                
                # Restore selection if possible
                if device == current_device:
                    self.device_table.selectRow(i)
            
            # If no selection, select first row if available
            if self.device_table.rowCount() > 0 and not current_device:
                self.device_table.selectRow(0)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh devices: {str(e)}")
    
    def update_device_details(self):
        """Update the device details panel with the selected device."""
        selected = self.device_table.selectedItems()
        if not selected:
            self.clear_device_details()
            return
        
        row = selected[0].row()
        
        # Update details
        self.details_name.setText(self.device_table.item(row, 0).text())
        self.details_model.setText(self.device_table.item(row, 1).text())
        self.details_size.setText(self.device_table.item(row, 2).text())
        self.details_type.setText(self.device_table.item(row, 3).text())
        self.details_fs.setText(self.device_table.item(row, 4).text())
        self.details_mount.setText(self.device_table.item(row, 5).text())
        
        # Update health status
        health = self.device_table.item(row, 6).text()
        health_item = self.device_table.item(row, 6)
        self.details_health.setText(health)
        self.details_health.setStyleSheet(f"color: {health_item.foreground().color().name()}")
        
        # Update button states
        self.update_button_states()
    
    def clear_device_details(self):
        """Clear the device details panel."""
        self.details_name.setText("-")
        self.details_model.setText("-")
        self.details_size.setText("-")
        self.details_type.setText("-")
        self.details_fs.setText("-")
        self.details_mount.setText("-")
        self.details_health.setText("-")
        self.details_health.setStyleSheet("")
        
        self.update_button_states()
    
    def update_button_states(self):
        """Update the enabled/disabled state of action buttons."""
        has_selection = bool(self.device_table.selectedItems())
        is_mounted = self.details_mount.text() not in ("-", "No")
        
        self.btn_mount.setEnabled(has_selection and not is_mounted)
        self.btn_unmount.setEnabled(has_selection and is_mounted)
        self.btn_format.setEnabled(has_selection)
        self.btn_smart.setEnabled(has_selection)
        self.btn_benchmark.setEnabled(has_selection)

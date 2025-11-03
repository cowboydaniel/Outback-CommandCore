from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView

class DevicesTab(QWidget):
    """Devices tab that displays a list of connected devices."""
    
    def __init__(self, parent=None):
        """Initialize the devices tab."""
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface for the devices tab."""
        layout = QVBoxLayout(self)
        
        # Add a title label
        title_label = QLabel("Connected Devices")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; margin: 15px 0;")
        
        # Create a table to display devices
        self.devices_table = QTableWidget()
        self.devices_table.setColumnCount(3)
        self.devices_table.setHorizontalHeaderLabels(["Device ID", "Status", "Last Seen"])
        
        # Configure table properties
        self.devices_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.devices_table.verticalHeader().setVisible(False)
        
        # Add widgets to layout
        layout.addWidget(title_label)
        layout.addWidget(self.devices_table)
        
        # Add some sample data (in a real app, this would come from a device manager)
        self.add_sample_data()
        
        self.setLayout(layout)
    
    def add_sample_data(self):
        """Add sample data to the devices table."""
        sample_devices = [
            ("Device 001", "Online", "Just now"),
            ("Device 002", "Offline", "5 mins ago"),
            ("Device 003", "Online", "1 min ago")
        ]
        
        self.devices_table.setRowCount(len(sample_devices))
        for row, (device_id, status, last_seen) in enumerate(sample_devices):
            self.devices_table.setItem(row, 0, QTableWidgetItem(device_id))
            self.devices_table.setItem(row, 1, QTableWidgetItem(status))
            self.devices_table.setItem(row, 2, QTableWidgetItem(last_seen))
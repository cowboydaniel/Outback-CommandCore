import os
import time
from datetime import datetime, timedelta
from collections import deque
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGroupBox, QScrollArea, QStatusBar, QDialog,
    QDialogButtonBox, QApplication, QMessageBox
)
from PySide6.QtGui import QFont, QIcon, QPainterPath, QPen, QBrush, QColor
from PySide6.QtCore import QTimer, Qt, Signal
from typing import Tuple, List, Dict

from BLACKSTORM.ui.components.system_monitor import SystemMonitor

class DashboardTab(QWidget):
    def __init__(self, parent=None, tab_widget=None):
        """Initialize the Dashboard tab with a reference to the parent and tab widget."""
        super().__init__(parent)
        print("Initializing DashboardTab...")
        self.parent = parent
        self.monitor_timer = QTimer(self)
        self._initialized = False
        self.system_monitor = SystemMonitor()
        
        # Create the main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create a container widget for the dashboard content
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)
        
        # Create and add the status bar
        self.status_bar = QStatusBar()
        self.status_bar.setSizeGripEnabled(False)
        
        # Add widgets to main layout
        self.main_layout.addWidget(self.container)
        self.main_layout.addWidget(self.status_bar)
        
        # Set the layout
        self.setLayout(self.main_layout)
        
        # Initialize the UI
        self._init_ui()
        
        # Start system monitoring
        self.start_monitoring()
        
        # Perform initial updates
        self.update_system_stats()
        self.update_activities()
        
        print("DashboardTab initialization complete")
        
    def _init_ui(self):
        """Initialize the dashboard UI components."""
        print("Initializing dashboard UI...")
        
        # Create the main content
        self.create_dashboard_tab()
        
        # Set up the auto-refresh timer for activities
        self.activities_timer = QTimer(self)
        self.activities_timer.timeout.connect(self.update_activities)
        self.activities_timer.start(10000)  # Update every 10 seconds
        
        print("Dashboard UI initialization complete")
        
    def start_monitoring(self):
        """Start the system monitoring timer."""
        if not self.monitor_timer.isActive():
            self.monitor_timer.timeout.connect(self.update_system_stats)
            self.monitor_timer.start(1000)  # Update every second
    
    def stop_monitoring(self):
        """Stop the system monitoring timer."""
        if self.monitor_timer.isActive():
            self.monitor_timer.stop()
            self.monitor_timer.timeout.disconnect()
    
    def update_activities(self):
        """Update activity-related UI elements in the dashboard."""
        try:
            # Update the status bar with current time and system status
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if hasattr(self, 'status_bar'):
                self.status_bar.showMessage(f"Last updated: {current_time} | System monitoring active")
        except Exception as e:
            print(f"Error updating activities: {e}")
            import traceback
            traceback.print_exc()
    
    def update_system_stats(self):
        """Update system statistics in the status bar."""
        try:
            # Update activities (status bar, etc.)
            self.update_activities()
            
            # Update system stats
            if hasattr(self, 'system_monitor') and self.system_monitor is not None:
                cpu_usage = self.system_monitor.get_cpu_usage()
                mem_usage, mem_total, mem_percent = self.system_monitor.get_memory_usage()
                status_msg = f"CPU: {cpu_usage:.1f}% | Memory: {mem_percent:.1f}% ({mem_usage/1024/1024/1024:.1f}GB / {mem_total/1024/1024/1024:.1f}GB)"
                self.status_bar.showMessage(status_msg)
        except Exception as e:
            print(f"Error updating system stats: {e}")
        
    def refresh(self):
        """Refresh the dashboard tab content."""
        if hasattr(self, 'update_activities'):
            self.update_activities()
        if hasattr(self, 'update_system_stats'):
            self.update_system_stats()
    
    def update_activities(self):
        """Update the Recent Activities section with latest system and application events."""
        try:
            # Skip if the activities layout doesn't exist yet
            if not hasattr(self, 'activities_layout') or not self.activities_layout:
                return
                
            # Store current filter states if they exist
            current_filters = {}
            if hasattr(self, 'filter_buttons'):
                for category, btn in list(self.filter_buttons.items()):  # Create a copy with list()
                    try:
                        if self._is_widget_valid(btn):
                            current_filters[category] = btn.isChecked()
                    except Exception as e:
                        print(f"Error getting filter state for {category}: {e}")
                        continue
            
            # Clear existing activities if layout exists and is valid
            if hasattr(self, 'activities_layout') and self.activities_layout:
                try:
                    # Store the layout in a local variable before clearing
                    layout = self.activities_layout
                    if self._is_widget_valid(layout):
                        # Clear the layout
                        while layout.count() > 0:
                            item = layout.takeAt(0)
                            if item is None:
                                continue
                                
                            widget = item.widget()
                            if widget is not None and self._is_widget_valid(widget):
                                try:
                                    widget.deleteLater()
                                except RuntimeError:
                                    pass  # Widget already deleted
                except Exception as e:
                    print(f"Error clearing activities layout: {e}")
            
            # Initialize activity items list if it doesn't exist
            if not hasattr(self, 'all_activity_items'):
                self.all_activity_items = []
            else:
                # Clear existing items safely
                try:
                    self.all_activity_items.clear()
                except (AttributeError, RuntimeError) as e:
                    print(f"Error clearing activity items: {e}")
                    self.all_activity_items = []
                
            # Reapply filter states if they existed
            if hasattr(self, 'filter_buttons'):
                for category, btn in list(self.filter_buttons.items()):  # Create a copy with list()
                    try:
                        if category in current_filters and self._is_widget_valid(btn):
                            btn.setChecked(current_filters[category])
                    except Exception as e:
                        print(f"Error setting filter state for {category}: {e}")
                        continue
                
                # Apply filters if we have any
                try:
                    if hasattr(self, 'filter_buttons') and self.filter_buttons:
                        self._apply_filters()
                except Exception as e:
                    print(f"Error applying filters: {e}")
            
            # Define log directory in user's config folder
            log_dir = os.path.expanduser('~/.config/blackstorm/logs')
            app_log = os.path.join(log_dir, 'blackstorm.log')
            
            # Create log directory if it doesn't exist
            try:
                os.makedirs(log_dir, exist_ok=True)
                os.chmod(log_dir, 0o755)  # Ensure it's readable
            except Exception as e:
                print(f"Error creating log directory {log_dir}: {e}")
            
            # Get system logs and application logs
            log_files = [
                ('/var/log/syslog', 'system'),  # System logs
                (app_log, 'app')  # Application logs
            ]
            
            # Check if log files exist and are readable
            for log_file, source in log_files[:]:
                if not os.path.exists(log_file):
                    print(f"Log file not found: {log_file}")
                    if source == 'app':
                        # Create an empty log file if it doesn't exist
                        try:
                            with open(log_file, 'a'):
                                os.utime(log_file, None)
                            os.chmod(log_file, 0o644)
                            print(f"Created empty log file: {log_file}")
                        except Exception as e:
                            print(f"Error creating log file {log_file}: {e}")
                            log_files.remove((log_file, source))
            
            all_events = []
            for log_file, source in log_files:
                try:
                    if not os.path.exists(log_file):
                        print(f"Log file not found: {log_file}")
                        continue
                        
                    print(f"Reading log file: {log_file} (exists: {os.path.exists(log_file)})")
                    logs = self._read_log_file(log_file, max_lines=50)
                    print(f"Found {len(logs)} log entries in {log_file}")
                    
                    if source == 'system':
                        all_events.extend(self._parse_system_logs(logs))
                    else:
                        all_events.extend(self._parse_app_logs(logs))
                        
                except Exception as e:
                    print(f"Error processing {log_file}: {e}")
            
            # If no events found, add a helpful message
            if not all_events:
                self._add_activity_item(
                    "Info",
                    "No recent activities found in logs. This could be because log files are empty or not accessible.",
                    datetime.now().strftime("%H:%M"),
                    "app"
                )
                return
            
            # Sort events by timestamp (newest first)
            all_events.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            # Get active filters
            active_filters = {}
            if hasattr(self, 'filter_buttons'):
                active_filters = {cat: btn.isChecked() for cat, btn in self.filter_buttons.items()}
            
            # Add filtered events to the layout
            for event in all_events:
                category = event.get('category', 'Info')
                # If no filters are active or the event's category is checked, show it
                if not active_filters or active_filters.get(category, True):
                    self._add_activity_item(
                        category,
                        event.get('message', 'No message'),
                        event.get('timestamp', datetime.now().strftime("%H:%M")),
                        event.get('source', 'app')
                    )
                
            # Create button container
            button_container = QWidget()
            button_layout = QHBoxLayout(button_container)
            button_layout.setContentsMargins(0, 10, 0, 0)
            button_layout.setSpacing(5)
            
            # Add refresh button
            refresh_btn = QPushButton("Refresh")
            refresh_btn.setStyleSheet("""
                QPushButton {
                    background: #2d3436;
                    color: #b1b1b1;
                    border: 1px solid #3c3f41;
                    border-radius: 3px;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    background: #3c3f41;
                }
            """)
            refresh_btn.clicked.connect(self.update_activities)
            
            # Add delete logs button
            delete_btn = QPushButton("Delete Logs")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background: #6c2e2e;
                    color: #ff9999;
                    border: 1px solid #8b3a3a;
                    border-radius: 3px;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    background: #8b3a3a;
                }
            """)
            delete_btn.clicked.connect(self._delete_all_logs)
            
            # Add buttons to layout
            button_layout.addWidget(refresh_btn)
            button_layout.addWidget(delete_btn)
            button_layout.addStretch()
            
            # Get the button widget and clear existing buttons
            button_widget = self.activities_button_container.findChild(QWidget)
            if button_widget:
                button_layout = button_widget.layout()
                # Clear existing buttons
                while button_layout.count() > 0:
                    item = button_layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()
                
                # Create new buttons
                refresh_btn = QPushButton("Refresh")
                refresh_btn.setStyleSheet("""
                    QPushButton {
                        background: #2d3436;
                        color: #b1b1b1;
                        border: 1px solid #3c3f41;
                        border-radius: 3px;
                        padding: 5px 10px;
                    }
                    QPushButton:hover {
                        border: 1px solid #5d6062;
                    }
                """)
                refresh_btn.clicked.connect(self.update_activities)
                
                delete_btn = QPushButton("Delete Logs")
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background: #6d2727;
                        color: #ffb3b3;
                        border: 1px solid #8b3a3a;
                        border-radius: 3px;
                        padding: 5px 10px;
                    }
                    QPushButton:hover {
                        background: #8b3a3a;
                    }
                """)
                delete_btn.clicked.connect(self._delete_all_logs)
                
                # Add buttons to the layout
                button_layout.addWidget(refresh_btn)
                button_layout.addWidget(delete_btn)
                
        except Exception as e:
            print(f"Error updating activities: {e}")
            error_label = QLabel("Error loading activities")
            error_label.setStyleSheet("color: #e74c3c; font-style: italic;")
            self.activities_layout.addWidget(error_label)
    
    def _parse_system_logs(self, logs):
        """Parse system log entries."""
        events = []
        for log in logs:
            try:
                # Example syslog format: "Jan  1 12:34:56 hostname process[pid]: message"
                parts = log.split(maxsplit=5)
                if len(parts) >= 6:
                    timestamp = ' '.join(parts[:3])
                    process = parts[4].split('[')[0]
                    message = parts[5]
                    
                    # Categorize by process
                    category = "System"
                    if 'blackstorm' in process.lower():
                        category = "Application"
                    elif 'kernel' in process.lower():
                        category = "Kernel"
                    elif 'dbus' in process.lower() or 'systemd' in process.lower():
                        category = "System"
                    
                    events.append({
                        'timestamp': timestamp,
                        'category': category,
                        'message': message,
                        'raw': log,
                        'source': 'system'
                    })
            except Exception as e:
                print(f"Error parsing system log entry: {e}")
        return events
    
    def _parse_app_logs(self, logs):
        """Parse application log entries."""
        events = []
        for log in logs:
            try:
                if not log.strip():
                    continue
                    
                # Try to parse as [timestamp] [LEVEL] message
                if log.startswith('[') and ']' in log:
                    timestamp_end = log.find(']')
                    level_end = log.find(']', timestamp_end + 1)
                    
                    if level_end > timestamp_end:
                        timestamp = log[1:timestamp_end].strip()
                        level = log[timestamp_end+2:level_end].strip()
                        message = log[level_end+2:].strip()
                        
                        # Map log levels to categories
                        category = "Info"
                        if 'ERROR' in level:
                            category = "Error"
                        elif 'WARN' in level:
                            category = "Warning"
                        
                        events.append({
                            'timestamp': timestamp,
                            'category': category,
                            'message': message,
                            'raw': log,
                            'source': 'app'
                        })
                else:
                    # Fallback: treat as a simple message
                    events.append({
                        'timestamp': datetime.now().strftime("%H:%M"),
                        'category': "Info",
                        'message': log,
                        'raw': log,
                        'source': 'app'
                    })
            except Exception as e:
                print(f"Error parsing application log entry: {e}")
                continue
                
        return events
    
    def _create_filter_buttons(self):
        """Create filter buttons for the activity log."""
        # Create a container for filter buttons
        filter_container = QWidget()
        filter_layout = QHBoxLayout(filter_container)
        filter_layout.setContentsMargins(0, 0, 0, 10)
        filter_layout.setSpacing(5)
        
        # Define categories and their display names
        self.categories = {
            'System': '🔧 System',
            'Application': '💻 App',
            'Kernel': '⚙️ Kernel',
            'Error': '❌ Error',
            'Warning': '⚠️ Warning',
            'Info': 'ℹ️ Info'
        }
        
        # Create a button for each category
        self.filter_buttons = {}
        for category, display_name in self.categories.items():
            btn = QPushButton(display_name)
            btn.setCheckable(True)
            btn.setChecked(True)  # All categories visible by default
            btn.setStyleSheet("""
                QPushButton {
                    background: #2c3e50;
                    color: #ecf0f1;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 4px;
                    font-size: 11px;
                }
                QPushButton:checked {
                    background: #3498db;
                }
                QPushButton:hover {
                    background: #3e5770;
                }
            """)
            btn.clicked.connect(self._apply_filters)
            self.filter_buttons[category] = btn
            filter_layout.addWidget(btn)
        
        # Add a clear filters button
        clear_btn = QPushButton('Clear All')
        clear_btn.clicked.connect(self._clear_filters)
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #7f8c8d;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #95a5a6;
            }
        """)
        filter_layout.addWidget(clear_btn)
        filter_layout.addStretch()
        
        # Store all activity items for filtering
        self.all_activity_items = []
        
        return filter_container
    
    def _apply_filters(self):
        """Apply the selected filters to show/hide activity items safely."""
        try:
            # Get checked categories safely
            visible_categories = []
            if hasattr(self, 'filter_buttons'):
                for category, btn in list(self.filter_buttons.items()):
                    try:
                        if btn and hasattr(btn, 'isChecked') and btn.isChecked():
                            visible_categories.append(category)
                    except Exception as e:
                        print(f"Error checking filter button {category}: {e}")
                        continue
                        
            # If no filters are checked, show all
            if not visible_categories and hasattr(self, 'filter_buttons'):
                visible_categories = list(self.filter_buttons.keys())
                
            # Apply visibility
            if not hasattr(self, 'all_activity_items'):
                return
                
            for item, category in list(self.all_activity_items):
                try:
                    if item and hasattr(item, 'setVisible'):
                        item.setVisible(category in visible_categories)
                except Exception as e:
                    print(f"Error applying filter to item {category}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error in _apply_filters: {e}")
    
    def _clear_filters(self):
        """Clear all filters and show all categories safely."""
        try:
            # Check if we have a valid tab widget
            if not hasattr(self, 'tab_widget') or not self._is_widget_valid(self.tab_widget):
                return
                
            # Clear all filters safely
            if hasattr(self, 'filter_buttons'):
                for category, btn in list(self.filter_buttons.items()):  # Create a copy with list()
                    try:
                        if self._is_widget_valid(btn):
                            btn.setChecked(True)
                    except Exception as e:
                        print(f"Error clearing filter for {category}: {e}")
                        continue
                        
            # Force refresh of the display
            self._apply_filters()
            
        except Exception as e:
            print(f"Error in _clear_filters: {e}")
    
    def _delete_all_logs(self):
        """
        Delete all log files from the log directory and clear in-memory activities.
        Note: System logs in /var/log/syslog cannot be deleted without root permissions.
        """
        # Clear in-memory activities first
        if hasattr(self, 'all_activity_items'):
            self.all_activity_items.clear()
        
        # Clear the activities layout
        while self.activities_layout.count() > 0:
            item = self.activities_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Delete log files from the application log directory
        log_dir = '/var/log/blackstorm'
        deleted_count = 0
        syslog_cleared = False
        
        try:
            # Delete application log files
            if os.path.exists(log_dir):
                for filename in os.listdir(log_dir):
                    file_path = os.path.join(log_dir, filename)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                            deleted_count += 1
                    except Exception as e:
                        print(f"Error deleting log file {file_path}: {e}")
            
            # Try to clear system logs (this will only work with root permissions)
            try:
                with open('/var/log/syslog', 'w') as f:
                    f.write('')
                syslog_cleared = True
            except PermissionError:
                print("Insufficient permissions to clear system logs")
            except Exception as e:
                print(f"Error clearing system logs: {e}")
            
            # Show appropriate message based on what was cleared
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Information)
            
            if deleted_count > 0 or syslog_cleared:
                message = []
                if deleted_count > 0:
                    message.append(f"Deleted {deleted_count} application log file{'s' if deleted_count != 1 else ''}")
                if syslog_cleared:
                    message.append("System logs have been cleared")
                elif not syslog_cleared and deleted_count == 0:
                    message.append("Could not clear system logs (requires root permissions)")
                
                msg.setText("\n".join(message))
            else:
                msg.setText("No log files were deleted")
                
            msg.setWindowTitle("Logs Cleared")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
            
            # Refresh the activities to show empty state or remaining logs
            self.update_activities()
            
        except Exception as e:
            print(f"Error deleting logs: {e}")
            QMessageBox.critical(
                None,
                "Error",
                f"Failed to delete log files: {str(e)}"
            )

    def _add_activity_item(self, category, message, timestamp, source):
        """Add a single activity item to the layout."""
        # Create the activity item widget
        item = QWidget()
        item.setStyleSheet("""
            QWidget {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 6px;
                padding: 8px;
            }
            QWidget:hover {
                background: rgba(255, 255, 255, 0.08);
            }
        """)
        
        layout = QHBoxLayout(item)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(10)
        
        # Category icon
        icon_map = {
            'System': '🔧',
            'Application': '💻',
            'Kernel': '⚙️',
            'Error': '❌',
            'Warning': '⚠️',
            'Info': 'ℹ️'
        }
        icon = QLabel(icon_map.get(category, '🔹'))
        icon.setStyleSheet("font-size: 16px;")
        
        # Content
        content = QLabel(f"<b>{category}:</b> {message}")
        content.setWordWrap(True)
        content.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        content.setStyleSheet("""
            QLabel {
                color: #e0e0e0;
                font-size: 12px;
                padding: 0;
                margin: 0;
            }
        """)
        
        # Timestamp
        time_label = QLabel(timestamp)
        time_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 10px;
                padding: 2px 6px;
                background: rgba(0, 0, 0, 0.2);
                border-radius: 3px;
                min-width: 70px;
                text-align: center;
            }
        """)
        
        # Add widgets to layout
        layout.addWidget(icon, 0, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(content, 1)
        layout.addWidget(time_label, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        
        # Add to activities layout and track for filtering
        self.activities_layout.addWidget(item)
        
        # Track this item for filtering if we have the filter system initialized
        if hasattr(self, 'all_activity_items'):
            self.all_activity_items.append((item, category))
    
    def _read_log_file(self, file_path, max_lines=50):
        """Read the last n lines from a log file."""
        try:
            if not os.path.exists(file_path):
                return []
                
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Read last max_lines from file efficiently
                lines = deque(f, max_lines)
                return [line.strip() for line in lines if line.strip()]
        except Exception as e:
            print(f"Error reading log file {file_path}: {e}")
            return []
    
    def _is_widget_valid(self, widget):
        """Check if a widget is still valid (not deleted)."""
        try:
            # This will raise a RuntimeError if the C++ object has been deleted
            if widget is None:
                return False
            # Access a property to check if the widget is still valid
            widget.objectName()
            return True
        except (RuntimeError, AttributeError):
            return False
            
    def update_system_stats(self):
        """Update the system statistics in the dashboard."""
        try:
            # Check if we have valid status cards
            if not hasattr(self, 'status_cards') or not isinstance(self.status_cards, dict):
                return
                
            # Get CPU usage
            cpu_percent = SystemMonitor.get_cpu_usage()
            
            # Get memory usage
            used_gb, total_gb, mem_percent = SystemMonitor.get_memory_usage()
            
            # Update CPU card
            if 'cpu' in self.status_cards and self._is_widget_valid(self.status_cards['cpu']):
                value_label = self.status_cards['cpu'].findChild(QLabel, 'value')
                if value_label and self._is_widget_valid(value_label):
                    value_label.setText(f"{cpu_percent:.1f}%")
            
            # Update memory card
            if 'memory' in self.status_cards and self._is_widget_valid(self.status_cards['memory']):
                value_label = self.status_cards['memory'].findChild(QLabel, 'value')
                if value_label and self._is_widget_valid(value_label):
                    value_label.setText(f"{used_gb:.1f}/{total_gb:.1f}GB")
            
            # Update system status card with uptime and current time
            if hasattr(self, 'system_status_card') and self._is_widget_valid(self.system_status_card):
                try:
                    # Get system uptime
                    with open('/proc/uptime', 'r') as f:
                        uptime_seconds = float(f.readline().split()[0])
                    
                    # Format uptime
                    uptime = str(timedelta(seconds=int(uptime_seconds)))
                    
                    # Get current time
                    current_time = datetime.now().strftime("%H:%M:%S")
                    
                    # Update card
                    status_text = f"Uptime: {uptime}<br>Time: {current_time}"
                    value_label = self.system_status_card.findChild(QLabel, 'value')
                    if value_label and self._is_widget_valid(value_label):
                        value_label.setText(status_text)
                except Exception as e:
                    print(f"Error updating system status: {e}")
                
            # Update connected devices count (only update every 5 seconds to reduce system load)
            current_time = time.time()
            if not hasattr(self, '_last_device_update') or (current_time - self._last_device_update) > 5:
                try:
                    device_count = SystemMonitor.get_connected_devices_count()
                    if 'devices' in self.status_cards and self._is_widget_valid(self.status_cards['devices']):
                        value_label = self.status_cards['devices'].findChild(QLabel, 'value')
                        if value_label and self._is_widget_valid(value_label):
                            value_label.setText(f"{device_count}")
                    self._last_device_update = current_time
                except Exception as e:
                    print(f"Error updating device count: {e}")
            
        except Exception as e:
            print(f"Error updating system stats: {e}")
            import traceback
            traceback.print_exc()
    
    def closeEvent(self, event):
        """Clean up resources when closing the application."""
        try:
            if hasattr(self, 'monitor_timer') and self.monitor_timer.isActive():
                self.monitor_timer.stop()
                
            # Clean up any other resources if needed
            if hasattr(self, 'status_cards'):
                self.status_cards.clear()
                
            # Clear references to prevent memory leaks
            if hasattr(self, 'tab_widget'):
                self.tab_widget = None
                
            if hasattr(self, 'parent'):
                self.parent = None
                
        except Exception as e:
            print(f"Error during cleanup: {e}")
            
        event.accept()
    
    def create_dashboard_tab(self):
        """Create the Dashboard tab with modern UI components."""
        tab = QWidget()
        self.tab = tab  # Store reference to the tab
        
        # Apply status bar styling when dashboard tab is shown
        def on_tab_changed(index):
            if self.tab_widget.currentWidget() == tab:
                self.parent.statusBar().setStyleSheet("""
                    QStatusBar {
                        background-color: #2d3436;
                        color: #b1b1b1;
                        border-top: 1px solid #3c3f41;
                        padding: 2px;
                    }
                    QStatusBar::item {
                        border: none;
                    }
                """)
                # Refresh the dashboard when this tab is selected
                try:
                    if hasattr(self, 'refresh') and callable(self.refresh):
                        self.refresh()
                except Exception as e:
                    print(f"Error refreshing dashboard: {e}")
        
        # Connect tab changed signal
        if hasattr(self, 'tab_widget') and self.tab_widget:
            self.tab_widget.currentChanged.connect(on_tab_changed)
        
        # Initial setup if this is the first tab
        if hasattr(self, 'tab_widget') and self.tab_widget and self.tab_widget.currentWidget() == tab:
            on_tab_changed(self.tab_widget.currentIndex())
        
        # Mark as initialized
        self._initialized = True
        
        # Set up the timer to update system stats every second
        self.monitor_timer.timeout.connect(self.update_system_stats)
        self.monitor_timer.start(1000)  # Update every second
        
        # Initial update
        self.update_system_stats()
            
        main_layout = QVBoxLayout(tab)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(20)
        
        # Stats Cards Row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(15)
        
        def create_stat_card(title, value, icon_name, color):
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: #2d3436;
                    border-radius: 8px;
                    padding: 15px;
                    border: 1px solid #3c3f41;
                }}
                QLabel#title {{ color: #b1b1b1; font-size: 12px; }}
                QLabel#value {{ 
                    color: {color}; 
                    font-size: 24px; 
                    font-weight: bold;
                    margin: 5px 0;
                }}
                QLabel#icon {{
                    font-size: 18px;
                    color: #b1b1b1;
                }}
                QLabel#icon:hover {{
                    font-size: 20px;
                    color: #ffffff;
                }}
            """)
            layout = QVBoxLayout(card)
            
            # Header with icon
            header = QHBoxLayout()
            title_label = QLabel(title.upper())
            title_label.setObjectName("title")
            
            # Using text as icon for simplicity
            icon = QLabel(icon_name)
            icon.setObjectName("icon")
            icon_font = QFont("Segoe UI Emoji", 14)
            icon.setFont(icon_font)
            
            # Make icon clickable only for devices card
            if title == "Connected Devices":
                def show_devices_dialog(event=None):
                    try:
                        devices = SystemMonitor.get_connected_devices()
                        dialog = QDialog(card)
                        dialog.setWindowTitle("Connected Storage Devices")
                        # Set fixed square size (width x height)
                        dialog.setFixedSize(800, 800)
                        # Center the dialog on the screen
                        screen = QApplication.primaryScreen().geometry()
                        dialog.move(
                            (screen.width() - dialog.width()) // 2,
                            (screen.height() - dialog.height()) // 2
                        )
                        # Apply dark theme
                        dialog.setStyleSheet("""
                            QDialog {
                                background-color: #2d2d2d;
                                border: 1px solid #444;
                                border-radius: 8px;
                                color: #e0e0e0;
                            }
                            QLabel {
                                color: #e0e0e0;
                            }
                            QPushButton {
                                background-color: #3a3a3a;
                                color: #e0e0e0;
                                border: 1px solid #555;
                                padding: 5px 15px;
                                border-radius: 4px;
                            }
                            QPushButton:hover {
                                background-color: #4a4a4a;
                                border-color: #666;
                            }
                            QScrollArea {
                                border: none;
                                background: transparent;
                            }
                            QWidget#scrollAreaWidgetContents {
                                background: transparent;
                            }
                        """)
                        
                        layout = QVBoxLayout(dialog)
                        
                        if not devices:
                            layout.addWidget(QLabel("No storage devices found."))
                        else:
                            scroll = QScrollArea()
                            scroll.setWidgetResizable(True)
                            content = QWidget()
                            content_layout = QVBoxLayout(content)
                            
                            for device in devices:
                                # Create device frame
                                device_frame = QFrame()
                                device_frame.setFrameShape(QFrame.Shape.StyledPanel)
                                device_frame.setStyleSheet("""
                                    QFrame {
                                        border: 1px solid #444;
                                        border-radius: 6px;
                                        padding: 12px;
                                        margin: 6px 0;
                                        background-color: #383838;
                                    }
                                    QFrame:hover {
                                        border-color: #5a9cf8;
                                        background-color: #404040;
                                    }
                                    .device-header {
                                        font-weight: bold;
                                        font-size: 14px;
                                        color: #e0e0e0;
                                        margin-bottom: 8px;
                                    }
                                    .partition-info {
                                        margin-left: 16px;
                                        color: #aaa;
                                        font-size: 13px;
                                    }
                                """)
                                
                                device_layout = QVBoxLayout(device_frame)
                                
                                # Device header with model/vendor
                                device_header = QLabel()
                                device_header.setProperty("class", "device-header")
                                
                                # Format: Vendor Model (size) [Removable] if applicable
                                device_text = []
                                if device.get('vendor'):
                                    device_text.append(device['vendor'])
                                if device.get('model'):
                                    device_text.append(device['model'])
                                    
                                device_name = ' '.join(device_text) if device_text else os.path.basename(device['device'])
                                size_text = f"{device.get('size_gb', 0):.1f} GB"
                                
                                device_header.setText(f"{device_name} ({size_text})")
                                if device.get('removable'):
                                    device_header.setText(device_header.text() + " [Removable]")
                                
                                device_layout.addWidget(device_header)
                                
                                # Add device path
                                device_path = QLabel(f"Device: {device['device']}")
                                device_path.setStyleSheet("color: #666;")
                                device_layout.addWidget(device_path)
                                
                                # Add partitions if any
                                if device.get('partitions'):
                                    part_label = QLabel("Partitions:")
                                    part_label.setStyleSheet("font-weight: bold; margin-top: 5px;")
                                    device_layout.addWidget(part_label)
                                    
                                    for part in device['partitions']:
                                        part_frame = QFrame()
                                        part_frame.setStyleSheet("""
                                            QFrame {
                                                border: 1px solid #444;
                                                border-radius: 4px;
                                                padding: 6px 8px;
                                                margin: 4px 0 4px 16px;
                                                background-color: #2d2d2d;
                                            }
                                            QFrame:hover {
                                                background-color: #333;
                                                border-color: #555;
                                            }
                                            QLabel {
                                                color: #ccc;
                                            }
                                        """)
                                        
                                        part_layout = QVBoxLayout(part_frame)
                                        
                                        # Partition device name and size
                                        part_header = QLabel(f"{os.path.basename(part['device'])} ({part.get('size', 0):.1f} GB)")
                                        part_header.setStyleSheet("font-weight: bold;")
                                        part_layout.addWidget(part_header)
                                        
                                        # Filesystem and mount point if available
                                        part_info = []
                                        if part.get('fstype'):
                                            part_info.append(f"Filesystem: {part['fstype']}")
                                        if part.get('mountpoint'):
                                            part_info.append(f"Mounted at: {part['mountpoint']}")
                                            
                                        if part_info:
                                            part_info_label = QLabel(" • ".join(part_info))
                                            part_layout.addWidget(part_info_label)
                                        
                                        device_layout.addWidget(part_frame)
                                else:
                                    no_parts = QLabel("No partitions found")
                                    no_parts.setStyleSheet("color: #888; font-style: italic; margin-left: 10px;")
                                    device_layout.addWidget(no_parts)
                                
                                device_layout.addStretch()
                                content_layout.addWidget(device_frame)
                            
                            content_layout.addStretch()
                            scroll.setWidget(content)
                            layout.addWidget(scroll)
                        
                        # Add close button
                        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
                        button_box.rejected.connect(dialog.reject)
                        layout.addWidget(button_box)
                        
                        dialog.exec()
                    except Exception as e:
                        print(f"Error showing devices dialog: {e}")
                
                # Set cursor and connect click event
                icon.setCursor(Qt.CursorShape.PointingHandCursor)
                icon.mousePressEvent = show_devices_dialog
        
            header.addWidget(title_label)
            header.addStretch()
            header.addWidget(icon)
            
            # Value
            value_label = QLabel(value)
            value_label.setObjectName("value")
            
            layout.addLayout(header)
            layout.addWidget(value_label)
            layout.addStretch()
            
            # Store the value label for updates
            card.value_label = value_label
            
            return card
        
        # System Status card with CPU and Memory info
        self.system_status_card = create_stat_card("System", "Loading...", "💻", "#27ae60")
        stats_row.addWidget(self.system_status_card)
        
        # System status card is not clickable
        self.system_status_card.setCursor(Qt.CursorShape.ArrowCursor)
        
        # Connected Devices card
        device_count = SystemMonitor.get_connected_devices_count()
        self.devices_card = create_stat_card("Connected Devices", str(device_count), "💾", "#3498db")
        stats_row.addWidget(self.devices_card)
        
        # CPU card with clickable lightning bolt
        self.cpu_card = create_stat_card("CPU Usage", "Loading...", "⚡", "#e74c3c")
        # Make only the icon clickable
        def cpu_clicked(event):
            if event.button() == Qt.MouseButton.LeftButton:
                # Check if click was on the icon (last widget in the header)
                header = self.cpu_card.layout().itemAt(0).layout()
                icon = header.itemAt(header.count() - 1).widget()
                if icon.underMouse():
                    event.accept()
                    SystemMonitor.show_cpu_monitor(self.parent)
                    return
            event.ignore()
        self.cpu_card.mousePressEvent = cpu_clicked
        # Set cursor for the icon
        cpu_header = self.cpu_card.layout().itemAt(0).layout()
        cpu_icon = cpu_header.itemAt(cpu_header.count() - 1).widget()
        cpu_icon.setCursor(Qt.CursorShape.PointingHandCursor)

        # Memory card with clickable brain icon
        self.memory_card = create_stat_card("Memory", "Loading...", "🧠", "#9b59b6")
        # Make only the icon clickable
        def memory_clicked(event):
            if event.button() == Qt.MouseButton.LeftButton:
                # Check if click was on the icon (last widget in the header)
                header = self.memory_card.layout().itemAt(0).layout()
                icon = header.itemAt(header.count() - 1).widget()
                if icon.underMouse():
                    event.accept()
                    SystemMonitor.show_memory_monitor(self.parent)
                    return
            event.ignore()
        self.memory_card.mousePressEvent = memory_clicked
        # Set cursor for the icon
        mem_header = self.memory_card.layout().itemAt(0).layout()
        mem_icon = mem_header.itemAt(mem_header.count() - 1).widget()
        mem_icon.setCursor(Qt.CursorShape.PointingHandCursor)

        # Add to layout
        stats_row.addWidget(self.cpu_card)
        stats_row.addWidget(self.memory_card)
        
        main_layout.addLayout(stats_row)
        
        # Main Content Row
        content_row = QHBoxLayout()
        content_row.setSpacing(20)
        
        # Left Column - Quick Actions
        actions_group = QGroupBox("Quick Actions")
        actions_group.setStyleSheet("""
            QGroupBox {
                background: #2d3436;
                border: 1px solid #3c3f41;
                border-radius: 8px;
                margin-top: 20px;
                padding-top: 15px;
                color: #b1b1b1;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #b1b1b1;
            }
        """)
        actions_layout = QVBoxLayout(actions_group)
        
        def create_action_button(text, icon, color):
            btn = QPushButton(text)
            btn.setIcon(QIcon.fromTheme(icon))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {color};
                    color: white;
                    border: none;
                    padding: 12px;
                    border-radius: 6px;
                    text-align: left;
                    font-weight: 500;
                    margin: 5px 0;
                }}
                QPushButton:hover {{
                    background: {color};
                    opacity: 0.9;
                }}
            """)
            return btn
        
        actions_layout.addWidget(create_action_button("Quick Wipe", "edit-delete", "#e74c3c"))
        actions_layout.addWidget(create_action_button("Quick Image", "document-save", "#3498db"))
        actions_layout.addWidget(create_action_button("Quick Scan", "system-search", "#2ecc71"))
        actions_layout.addStretch()
        
        # Right Column - Recent Activities
        activities_group = QGroupBox("Recent Activities")
        activities_group.setStyleSheet(actions_group.styleSheet())
        activities_layout = QVBoxLayout(activities_group)
        
        # Add filter buttons above the activities
        filter_container = QWidget()
        filter_layout = QHBoxLayout(filter_container)
        filter_layout.setContentsMargins(0, 0, 0, 10)  # Add some bottom margin
        filter_layout.setSpacing(5)
        
        # Create filter buttons
        self.filter_buttons = {}
        categories = ['System', 'Application', 'Kernel', 'Error', 'Warning', 'Info']
        
        for category in categories:
            btn = QPushButton(category)
            btn.setCheckable(True)
            btn.setChecked(True)
            btn.setStyleSheet("""
                QPushButton {
                    background: #2d3436;
                    color: #b1b1b1;
                    border: 1px solid #3c3f41;
                    border-radius: 3px;
                    padding: 3px 8px;
                    font-size: 11px;
                }
                QPushButton:checked {
                    background: #3498db;
                    color: white;
                }
                QPushButton:hover {
                    border: 1px solid #5d6062;
                }
            """)
            btn.clicked.connect(self._apply_filters)
            self.filter_buttons[category] = btn
            filter_layout.addWidget(btn)
        
        # Add clear filters button
        clear_btn = QPushButton("Clear All")
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #7f8c8d;
                color: white;
                border: 1px solid #95a5a6;
                border-radius: 3px;
                padding: 3px 8px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #95a5a6;
            }
        """)
        clear_btn.clicked.connect(self._clear_filters)
        filter_layout.addWidget(clear_btn)
        
        # Add filter container to layout
        activities_layout.addWidget(filter_container)
        
        # Create scroll area for activities
        activities_scroll = QScrollArea()
        activities_scroll.setWidgetResizable(True)
        activities_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QWidget#activities_content {
                background: transparent;
            }
        """)
        
        # Container widget for activities
        activities_content = QWidget()
        activities_content.setObjectName("activities_content")
        self.activities_layout = QVBoxLayout(activities_content)
        self.activities_layout.setContentsMargins(0, 0, 0, 0)
        self.activities_layout.setSpacing(8)
        
        # Add loading message
        loading = QLabel("Loading activities...")
        loading.setStyleSheet("color: #7f8c8d; font-style: italic;")
        self.activities_layout.addWidget(loading)
        
        activities_scroll.setWidget(activities_content)
        activities_layout.addWidget(activities_scroll, 1)  # Add stretch factor to make it take available space
        
        # Create a container for the buttons with centered layout
        self.activities_button_container = QWidget()
        button_outer_layout = QHBoxLayout(self.activities_button_container)
        button_outer_layout.setContentsMargins(0, 5, 0, 0)
        
        # Add stretch to center the buttons
        button_outer_layout.addStretch()
        
        # Create a widget to hold the buttons
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)  # Add some spacing between buttons
        
        # Add the button widget to the outer layout
        button_outer_layout.addWidget(button_widget)
        button_outer_layout.addStretch()
        
        # Add the container to the activities layout
        activities_layout.addWidget(self.activities_button_container)
        
        # Initialize activities list and timer
        self.recent_activities = []
        self.last_activity_update = 0
        
        # Update activities immediately and then every 10 seconds
        self.update_activities()
        self.activities_timer = QTimer()
        self.activities_timer.timeout.connect(self.update_activities)
        self.activities_timer.start(10000)  # Update every 10 seconds
        
        activities_layout.addStretch()
        
        # Configure content row proportions
        content_row.addWidget(actions_group, 1)
        content_row.addWidget(activities_group, 2)
        
        # Set stretch factors for the layout
        content_row.setStretch(0, 1)  # Actions group
        content_row.setStretch(1, 2)  # Activities group
        
        main_layout.addLayout(content_row, 1)
        
        # Status bar at bottom
        status_bar = QStatusBar()
        status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #2d3436;
                color: #b1b1b1;
                padding: 5px 10px;
                border-top: 1px solid #3c3f41;
                font-size: 11px;
            }
        """)
        status_bar.showMessage("BLACKSTORM v1.0.0 | System Ready")
        
        main_layout.addWidget(status_bar)
        
        # Store references for updates with proper indexing
        self.status_cards = {
            'system': stats_row.itemAt(0).widget(),
            'devices': stats_row.itemAt(1).widget(),
            'cpu': self.cpu_card,
            'memory': self.memory_card
        }
        
        # Add main layout to the container
        if hasattr(self, 'main_widget'):
            # Remove existing widget if it exists
            old_widget = self.layout.takeAt(0).widget()
            if old_widget:
                old_widget.deleteLater()
        
        # Create a new widget to hold the main layout
        self.main_widget = QWidget()
        self.main_widget.setLayout(main_layout)
        
        # Add the main widget to the container
        self.layout.addWidget(self.main_widget)
        
        return tab

"""
Application Manager Tab

This module provides a tab for managing all CommandCore applications.
"""

import os
import re
import sys
import importlib.util
import subprocess
from subprocess import Popen, PIPE, TimeoutExpired, CalledProcessError
import psutil
from psutil import Process, NoSuchProcess, AccessDenied
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import git
import signal

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QListWidget, 
                             QHBoxLayout, QPushButton, QMessageBox, QFrame, 
                             QGridLayout, QSizePolicy, QScrollArea, QSpacerItem)
from PySide6.QtCore import Qt, QSize, Signal, QThread, QTimer, QProcess, QObject, QMutex
from PySide6.QtGui import QIcon, QFont, QPixmap, QColor, QPainter, QLinearGradient


def get_version_from_module(module_path: str) -> Optional[str]:
    """Extract version from a Python module."""
    try:
        spec = importlib.util.spec_from_file_location("module.name", module_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Check common version attributes
            for attr in ['__version__', 'version', 'VERSION', 'app']:
                if hasattr(module, attr):
                    version_obj = getattr(module, attr)
                    # Handle QApplication version
                    if attr == 'app' and hasattr(version_obj, 'applicationVersion'):
                        version = version_obj.applicationVersion()
                        if version and version != 'unknown':
                            return version
                    # Handle direct version strings
                    elif isinstance(version_obj, str):
                        return version_obj
                    # Handle version objects with __str__
                    elif hasattr(version_obj, '__str__'):
                        version = str(version_obj)
                        if version and version != 'unknown':
                            return version
    except Exception as e:
        print(f"Error getting version from module {module_path}: {e}")
    return None


def get_version_from_git(repo_path: str) -> Optional[str]:
    """Get version from git tags."""
    try:
        result = subprocess.run(
            ['git', 'describe', '--tags', '--always'],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def get_version_from_file(file_path: str, custom_patterns: Optional[list] = None) -> Optional[str]:
    """Extract version from a file by looking for version-like strings.
    
    Args:
        file_path: Path to the file to search in
        custom_patterns: Optional list of regex patterns to try first
        
    Returns:
        The first matched version string, or None if no version found
    """
    # Default patterns to try if no custom patterns provided
    default_patterns = [
        r'__version__\s*=\s*["\']([^"\']+)["\']',
        r'version\s*=\s*["\']([^"\']+)["\']',
        r'VERSION\s*=\s*["\']([^"\']+)["\']',
        r'app\.setApplicationVersion\(["\']([^"\']+)["\']\)',
        r'root\.option_add\(\s*[\'\"]\*?applicationVersion[\'\"]\s*,\s*[\'\"]([^\'\"]+)[\'\"]\)',
        r'version\s*=\s*["\']([\d.]+)["\']',
        r'Version:\s*([\d.]+)',
        r'([0-9]+\.[0-9]+\.[0-9]+)',  # X.Y.Z format
        r'v([0-9]+\.[0-9]+(?:\.[0-9]+)?)'  # vX.Y or vX.Y.Z format
    ]
    
    # Use custom patterns if provided, otherwise use default patterns
    version_patterns = custom_patterns if custom_patterns is not None else default_patterns
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            import re
            patterns_tried = set()  # Track patterns we've already tried to avoid duplicates
            
            # First try exact matches with the patterns
            for pattern in version_patterns:
                if pattern in patterns_tried:
                    continue
                    
                patterns_tried.add(pattern)
                matches = list(re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE))
                
                for match in matches:
                    # Check each group in the match (some patterns have multiple capture groups)
                    for i in range(1, len(match.groups()) + 1):
                        try:
                            if match.group(i):
                                version = match.group(i).strip("'\"")
                                # Basic validation - should contain at least one digit and one dot
                                if any(c.isdigit() for c in version) and '.' in version:
                                    return version
                        except IndexError:
                            continue
            
            # If no matches found, try a more aggressive search for version-like strings
            if not custom_patterns:  # Only do this for the initial call, not recursive ones
                version_regex = re.compile(r'([0-9]+\.[0-9]+(?:\.[0-9]+(?:-[a-zA-Z0-9]+)?)?)')
                matches = version_regex.findall(content)
                if matches:
                    return max(matches, key=len)  # Return the most specific version found
                    
    except Exception as e:
        print(f"Error reading version from file {file_path}: {e}")
    return None


def detect_version(app_path: str) -> str:
    """Detect version of an application using multiple methods."""
    if not os.path.exists(app_path):
        return "not installed"
        
    app_dir = os.path.dirname(app_path)
    app_name = os.path.basename(app_path).lower()
    
    # Special handling for specific applications
    if 'ares-i' in app_name or 'ares_i' in app_name:
        # ARES-i has version in main function
        version = get_version_from_file(app_path, [r'app\.setApplicationVersion\(["\']([^"\']+)["\']\)'])
        if version:
            return version
    elif 'droidcom' in app_name:
        # DROIDCOM stores version via applicationVersion metadata
        version = get_version_from_file(app_path, [r'root\.option_add\(\s*[\'\"]\*?applicationVersion[\'\"]\s*,\s*[\'\"]([^\'\"]+)[\'\"]\)'])
        if version:
            return version
    elif 'pc_tools_linux' in app_name:
        # PC-X tools module might have version in a different format
        version = get_version_from_file(app_path, [r'__version__\s*=\s*["\']([^"\']+)["\']',
                                                 r'Version\s*=\s*["\']([^"\']+)["\']'])
        if version:
            return version
    elif 'launch_vantage' in app_name:
        # VANTAGE has version in app/config.py
        config_py = os.path.join(os.path.dirname(app_path), 'app', 'config.py')
        if os.path.exists(config_py):
            version = get_version_from_file(config_py, [r'VERSION\s*=\s*["\']([^"\']+)["\']'])
            if version:
                return version
    
    # Try to get version from the main module
    if app_path.endswith('.py'):
        # First try direct file content search (faster)
        version = get_version_from_file(app_path)
        if version:
            return version
            
        # Then try module import (slower but more thorough)
        version = get_version_from_module(app_path)
        if version:
            return version
    
    # Check for version in __init__.py in the same directory
    init_py = os.path.join(os.path.dirname(app_path), '__init__.py')
    if os.path.exists(init_py):
        version = get_version_from_file(init_py) or get_version_from_module(init_py)
        if version:
            return version
            
    # Check for setup.py in parent directory
    setup_py = os.path.join(os.path.dirname(app_path), 'setup.py')
    if os.path.exists(setup_py):
        version = get_version_from_file(setup_py)
        if version:
            return version
            
    # Last resort: check for any version-like string in the file
    if os.path.isfile(app_path):
        version = get_version_from_file(app_path, [r'([0-9]+\.[0-9]+\.[0-9]+)', r'v([0-9]+\.[0-9]+)'])
        if version:
            return version
    
    # Try to get version from git
    version = get_version_from_git(os.path.dirname(app_path))
    if version:
        return version
    
    # Fallback to modification time
    try:
        mtime = os.path.getmtime(app_path)
        from datetime import datetime
        return f"dev-{datetime.fromtimestamp(mtime).strftime('%Y%m%d%H%M')}"
    except Exception:
        return "unknown"


class ProcessMonitor(QThread):
    """Monitors processes and emits signals when they exit."""
    process_exited = Signal(str, int)  # app_id, returncode
    
    def __init__(self):
        super().__init__()
        self.processes = {}  # app_id -> (process, callback)
        self.running = True
        self.mutex = QMutex()
    
    def add_process(self, app_id, process, callback):
        """Add a process to monitor."""
        self.mutex.lock()
        try:
            self.processes[app_id] = (process, callback)
        finally:
            self.mutex.unlock()
    
    def remove_process(self, app_id):
        """Remove a process from monitoring."""
        self.mutex.lock()
        try:
            if app_id in self.processes:
                del self.processes[app_id]
        finally:
            self.mutex.unlock()
    
    def stop(self):
        """Stop the monitor thread."""
        self.running = False
        self.wait()
    
    def run(self):
        """Main monitoring loop."""
        while self.running:
            self.mutex.lock()
            try:
                to_remove = []
                for app_id, (process, callback) in self.processes.items():
                    returncode = process.poll()
                    if returncode is not None:
                        # Process has exited
                        to_remove.append(app_id)
                        self.process_exited.emit(app_id, returncode)
                
                # Remove exited processes
                for app_id in to_remove:
                    if app_id in self.processes:
                        del self.processes[app_id]
            finally:
                self.mutex.unlock()
            
            # Sleep a bit to avoid busy-waiting
            self.msleep(1000)  # Check every second


class AppCard(QFrame):
    """Widget representing an application card in the Application Manager."""
    
    def __init__(self, app_data, app_manager, parent=None):
        """Initialize the app card.
        
        Args:
            app_data (dict): Dictionary containing app information
            app_manager (ApplicationManagerTab): Reference to the app manager
            parent (QWidget, optional): Parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.app_data = app_data
        self.app_manager = app_manager
        self.process = None
        
        # Set up the card
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(120)
        self.setMaximumWidth(300)
        self.setObjectName("appCard")
        
        # Set up the UI
        self._setup_ui()
        
        # Connect to the app manager's process monitor
        if hasattr(self.app_manager, 'process_monitor'):
            self.app_manager.process_monitor.process_exited.connect(self._on_process_exited)
    
    def _setup_ui(self):
        """Set up the user interface for the app card."""
        # Style - using QPalette for background color
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor(45, 45, 45))  # #2D2D2D
        self.setPalette(palette)
        
        # Set border and border radius
        self.setStyleSheet("""
            QFrame#appCard {
                border: 1px solid #3E3E3E;
                border-radius: 8px;
                background-color: #2D2D2D;
            }
            
            QFrame#appCard:hover {
                border: 1px solid #00a8ff;
            }
            
            QLabel#titleLabel {
                font-size: 14px;
                font-weight: bold;
                color: #FFFFFF;
                margin: 0px;
                padding: 0px;
            }
            
            QLabel#descriptionLabel {
                font-size: 12px;
                color: #B0B0B0;
                margin: 0px;
                padding: 0px;
            }
            
            QLabel#versionLabel {
                font-size: 11px;
                color: #808080;
                margin: 0px;
                padding: 0px;
            }
            
            QLabel#statusLabel {
                font-size: 11px;
                padding: 2px 6px;
                border-radius: 4px;
                margin: 0px;
            }
            
            QPushButton#actionButton {
                padding: 4px 12px;
                border-radius: 4px;
                font-weight: 500;
                font-size: 12px;
                min-width: 80px;
            }
            
            QPushButton#actionButton:disabled {
                opacity: 0.6;
            }
        """)
        
        # Create main layout if it doesn't exist
        if not hasattr(self, '_main_layout'):
            self._main_layout = QVBoxLayout(self)
            self._main_layout.setContentsMargins(12, 12, 12, 12)
            self._main_layout.setSpacing(8)
        else:
            # Clear existing widgets if reinitializing
            while self._main_layout.count() > 0:
                item = self._main_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        
        # App title
        self.title_label = QLabel(self.app_data['name'])
        self.title_label.setObjectName("titleLabel")
        self._main_layout.addWidget(self.title_label)
        
        # App description
        if 'description' in self.app_data:
            self.desc_label = QLabel(self.app_data['description'])
            self.desc_label.setObjectName("descriptionLabel")
            self.desc_label.setWordWrap(True)
            self._main_layout.addWidget(self.desc_label)
        
        # Version and status
        info_layout = QHBoxLayout()
        
        # Version
        if 'version' in self.app_data and self.app_data['version'] != 'unknown':
            self.version_label = QLabel(f"v{self.app_data['version']}")
            self.version_label.setObjectName("versionLabel")
            info_layout.addWidget(self.version_label)
        
        info_layout.addStretch()
        
        # Status
        self.status_label = QLabel(self.app_data.get('status', 'stopped').capitalize())
        self.status_label.setObjectName("statusLabel")
        
        # Update status style
        self._update_status_style()
                
        info_layout.addWidget(self.status_label)
        self._main_layout.addLayout(info_layout)
        
        # Action button
        self.action_btn = QPushButton("Start" if self.app_data.get('status') != 'running' else "Stop")
        self.action_btn.setObjectName("actionButton")
        self.action_btn.clicked.connect(self.toggle_app_status)
        
        # Update button style
        self._update_button_style()
        
        self._main_layout.addWidget(self.action_btn)
        
    def _update_status_style(self):
        """Update the status label style based on current status."""
        status_style = """
            QLabel#statusLabel {
                font-size: 11px;
                padding: 2px 6px;
                border-radius: 4px;
                margin: 0px;
                background-color: %s;
                color: %s;
            }
        """
        
        if self.app_data.get('status') == 'running':
            self.status_label.setStyleSheet(status_style % 
                ("rgba(0, 200, 83, 0.2)", "#4CAF50"))
        else:
            self.status_label.setStyleSheet(status_style % 
                ("rgba(244, 67, 54, 0.2)", "#F44336"))
    
    def _update_button_style(self):
        """Update the button style based on current status."""
        if not hasattr(self, 'action_btn') or not self.action_btn:
            return
            
        if self.app_data.get('status') == 'running':
            style = """
                QPushButton#actionButton {
                    background-color: #00a8ff;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 12px;
                    min-width: 80px;
                }
                QPushButton#actionButton:hover {
                    background-color: #0095e0;
                }
            """
        else:
            style = """
                QPushButton#actionButton {
                    background-color: #3A3A3A;
                    color: #B0B0B0;
                    border: 1px solid #4A4A4A;
                    border-radius: 4px;
                    padding: 4px 12px;
                    min-width: 80px;
                }
                QPushButton#actionButton:hover {
                    background-color: #444444;
                }
            """
        self.action_btn.setStyleSheet(style)
        self.action_btn.setText("Stop" if self.app_data.get('status') == 'running' else "Start")
    
    def toggle_app_status(self):
        """Toggle the application status between running and stopped."""
        if self.app_data['status'] == 'running':
            self.stop_app()
        else:
            self.start_app()
    
    def _on_process_exited(self, app_id, returncode):
        """Called when a monitored process exits."""
        if app_id == self.app_data['id']:
            self.app_data['status'] = 'stopped'
            self._update_ui_state()
            
            # Update status in the app manager
            if hasattr(self.app_manager, 'update_status'):
                self.app_manager.update_status(self.app_data['id'], 'stopped')
    
    def _update_ui_state(self):
        """Update all UI elements to reflect current state."""
        self.action_btn.setText("Stop" if self.app_data.get('status') == 'running' else "Start")
        self._update_button_style()
        self._update_status_style()
        
        # Update the status label text
        if hasattr(self, 'status_label'):
            self.status_label.setText(self.app_data.get('status', 'stopped').capitalize())
    
    def start_app(self):
        """Start the application with better error handling."""
        try:
            # Disable button to prevent multiple clicks
            self.action_btn.setEnabled(False)
            self.action_btn.setText("Starting...")
            
            # Get the full path to the Python interpreter
            python_exec = sys.executable
            script_path = self.app_data['path']
            
            # Verify the script exists
            if not os.path.exists(script_path):
                raise FileNotFoundError(f"Script not found: {script_path}")
            
            # Special handling for specific applications
            if 'vantage' in self.app_data['id']:
                # For VANTAGE, we need to run it from its directory
                script_dir = os.path.dirname(script_path)
                cmd = [python_exec, 'launch_vantage.py']
                cwd = script_dir
            else:
                # For other apps, just run the script directly
                if not os.access(script_path, os.R_OK):
                    raise PermissionError(f"Cannot read script: {script_path}")
                cmd = [python_exec, script_path]
                cwd = os.path.dirname(script_path)
            
            print(f"Starting command: {' '.join(cmd)} in {cwd}")
            
            # Create log directory if it doesn't exist
            log_dir = os.path.join(cwd, 'logs')
            os.makedirs(log_dir, exist_ok=True)
            
            # Create log files for stdout and stderr
            stdout_log_path = os.path.join(log_dir, f"{self.app_data['id']}_stdout.log")
            stderr_log_path = os.path.join(log_dir, f"{self.app_data['id']}_stderr.log")
            
            stdout_log = open(stdout_log_path, 'w')
            stderr_log = open(stderr_log_path, 'w')
            
            # Start the process with output redirection
            self.process = subprocess.Popen(
                cmd,
                stdout=stdout_log,
                stderr=stderr_log,
                cwd=cwd,
                start_new_session=True,
                shell=False,
                text=True
            )
            
            # Store file handles and process info
            self.app_data['log_files'] = (stdout_log, stderr_log)
            self.app_data['pid'] = self.process.pid
            
            # Add to process monitor
            if hasattr(self.app_manager, 'process_monitor') and self.app_manager.process_monitor:
                self.app_manager.process_monitor.add_process(
                    self.app_data['id'],
                    self.process,
                    lambda rc: self._on_process_exited(self.app_data['id'], rc)
                )
            
            # Update the status
            self.app_data['status'] = 'running'
            self._update_ui_state()
            
            # Notify the app manager
            if hasattr(self.app_manager, 'update_status'):
                self.app_manager.update_status(self.app_data['id'], 'running')
            
            print(f"Successfully started {self.app_data['name']} with PID {self.process.pid}")
            
            # Print process info for debugging
            self.print_process_info_by_pid(self.process.pid)
                
        except Exception as e:
            print(f"Error starting application {self.app_data['name']}: {e}")
            import traceback
            traceback.print_exc()
            
            # Clean up on error
            if 'log_files' in self.app_data and self.app_data['log_files']:
                try:
                    stdout_log, stderr_log = self.app_data['log_files']
                    if stdout_log and not stdout_log.closed:
                        stdout_log.close()
                    if stderr_log and not stderr_log.closed:
                        stderr_log.close()
                except:
                    pass
                finally:
                    self.app_data['log_files'] = None
            
            # Reset UI state
            self.app_data['status'] = 'stopped'
            self._update_ui_state()
            
            # Show error message
            QMessageBox.warning(self, "Error", f"Failed to start {self.app_data['name']}: {str(e)}")
        
        finally:
            # Re-enable button
            self.action_btn.setEnabled(True)

    def print_process_info_by_pid(self, pid):
        """Print the command line and name of a process by PID for debugging."""
        try:
            proc = psutil.Process(pid)
            print(f"Process PID: {pid}")
            print(f"Name: {proc.name()}")
            print(f"Cmdline: {proc.cmdline()}")
        except psutil.NoSuchProcess:
            print(f"No process found with PID {pid}")
        except Exception as e:
            print(f"Error retrieving process info for PID {pid}: {e}")

    def stop_app(self):
        """Stop the application."""
        try:
            # If we have a direct process handle, use it
            if self.process is not None:
                self._stop_process_handle()
            # Otherwise try to find and stop the process by name
            elif 'pid' in self.app_data and self.app_data['pid']:
                self._stop_process_by_pid(self.app_data['pid'])
            else:
                self._stop_process_by_name()
                
            # Update the UI
            self.app_data['status'] = 'stopped'
            self._update_ui_state()
            
            # Notify the app manager
            if hasattr(self, 'app_manager') and hasattr(self.app_manager, 'update_status'):
                self.app_manager.update_status(self.app_data['id'], 'stopped')
                
        except Exception as e:
            print(f"Error stopping application {self.app_data['name']}: {e}")
            import traceback
            traceback.print_exc()
    
    def _stop_process_handle(self):
        """Stop a process using its process handle."""
        try:
            # Close log files if they exist
            if 'log_files' in self.app_data and self.app_data['log_files']:
                try:
                    stdout_log, stderr_log = self.app_data['log_files']
                    if stdout_log and not stdout_log.closed:
                        stdout_log.close()
                    if stderr_log and not stderr_log.closed:
                        stderr_log.close()
                except Exception as e:
                    print(f"Error closing log files: {e}")
                finally:
                    self.app_data['log_files'] = None
            
            # Remove from process monitor first
            if hasattr(self.app_manager, 'process_monitor') and self.app_data['id']:
                self.app_manager.process_monitor.remove_process(self.app_data['id'])
            
            # Get the process ID before we lose it
            pid = self.process.pid if self.process else None
            
            if pid is not None:
                self._terminate_process_tree(pid)
                
                # Clean up the subprocess.Popen object
                try:
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=1)
                    except (subprocess.TimeoutExpired, TimeoutExpired):
                        self.process.kill()
                        self.process.wait()
                except (ProcessLookupError, psutil.NoSuchProcess):
                    pass
            
        finally:
            self.process = None
    
    def _stop_process_by_pid(self, pid):
        """Stop a process by its PID."""
        try:
            process = psutil.Process(pid)
            self._terminate_process_tree(pid)
        except psutil.NoSuchProcess:
            pass
    
    def _stop_process_by_name(self):
        """Stop a process by its name."""
        app_name = os.path.basename(self.app_data['path'])
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if (proc.info['cmdline'] and 
                    any(app_name.lower() in cmd.lower() for cmd in proc.info['cmdline'])):
                    self._terminate_process_tree(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    
    def _terminate_process_tree(self, pid):
        """Terminate a process and all its children."""
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            
            # Terminate children first
            for child in children:
                try:
                    child.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Wait for children to terminate
            gone, still_alive = psutil.wait_procs(children, timeout=3)
            
            # Kill any remaining children
            for child in still_alive:
                try:
                    child.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Terminate the parent
            try:
                parent.terminate()
                parent.wait(timeout=3)
            except psutil.TimeoutExpired:
                try:
                    parent.kill()
                    parent.wait()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                    
        except psutil.NoSuchProcess:
            pass

class ApplicationManagerTab(QWidget):
    """Tab for managing all CommandCore applications."""
    
    def __init__(self, parent=None):
        """Initialize the Application Manager tab."""
        super().__init__(parent)
        
        # Initialize process monitor FIRST
        self.process_monitor = ProcessMonitor()
        self.process_monitor.start()
        
        # Then initialize apps and UI
        self.apps = self._get_installed_apps()
        self.init_ui()
    
    def closeEvent(self, event):
        """Clean up when the tab is closed."""
        if hasattr(self, 'process_monitor'):
            self.process_monitor.stop()
        super().closeEvent(event)
    
    def _is_process_running(self, process_name):
        """Check if a process is running by name or module path for specific apps, with result output."""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    pname = proc.info['name'].lower() if proc.info['name'] else ''
                    cmdline = proc.info['cmdline']
                    # Check for specific process names and command line matches
                    cmdline_str = ' '.join(cmdline).lower() if cmdline else ''
                    if process_name == 'ares_i_process':
                        if 'ares_i.ares_i' in cmdline_str:
                            return True
                    elif process_name == 'blackstorm_launcher_process':
                        if 'blackstorm.app.main' in cmdline_str or 'blackstorm/app/main.py' in cmdline_str:
                            return True
                    elif process_name == 'commandcore_launcher_process':
                        if 'commandcore.app.main' in cmdline_str:
                            return True
                    elif process_name == 'commandcorecodex_process':
                        if 'codex.gui' in cmdline_str:
                            return True
                    elif process_name == 'droidcom_process':
                        if 'android_tools_linux.android_tools_linux' in cmdline_str:
                            return True
                    elif process_name == 'hackattack_process':
                        if 'hackattack.launch' in cmdline_str:
                            return True
                    elif process_name == 'nightfire_process':
                        if 'nightfire.nightfire' in cmdline_str:
                            return True
                    elif process_name == 'omniscribe_process':
                        if 'omniscribe.omniscribe' in cmdline_str:
                            return True
                    elif process_name == 'pc_tools_linux_process':
                        if 'pc.pc_tools_linux' in cmdline_str:
                            return True
                    elif process_name == 'vantage_process':
                        if 'vantage.launch_vantage' in cmdline_str:
                            return True
                    # Otherwise, check if process name or command line contains process_name
                    elif (process_name.lower() in pname or
                          (cmdline and any(process_name.lower() in cmd.lower() for cmd in cmdline))):
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            return False
        except Exception as e:
            print(f"Error checking process {process_name}: {e}")
            return False
            
    def _get_process_pid(self, process_name):
        """Get PID of a running process by name."""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if (process_name.lower() in proc.info['name'].lower() or 
                        (proc.info['cmdline'] and 
                         any(process_name.lower() in cmd.lower() for cmd in proc.info['cmdline']))):
                        return proc.info['pid']
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            return None
        except Exception as e:
            print(f"Error getting PID for {process_name}: {e}")
            return None
    
    def _get_installed_apps(self):
        """Get the list of installed CommandCore applications with detected versions."""
        # Navigate from CommandCore/tabs/ up to project root (Outback-CommandCore)
        # __file__ is in CommandCore/tabs/, so go up 3 levels to reach project root
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        apps = [
            {
                "id": "ares_i",
                "name": "ARES-I",
                "description": "AI-powered research and analysis tool.",
                "path": os.path.join(base_dir, "ARES-i/app/main.py"),
                'version': None,
                'status': 'stopped',
                'process_name': 'ares_i_process'
            },
            {
                "id": "blackstorm_launcher",
                "name": "Blackstorm Launcher",
                "description": "Launcher for the Blackstorm suite of applications.",
                "path": os.path.join(base_dir, "BLACKSTORM/app/main.py"),
                'version': None,
                'status': 'stopped',
                'process_name': 'blackstorm_launcher_process'
            },
            {
                "id": "commandcore_launcher",
                "name": "CommandCore Launcher",
                "description": "Central hub for launching and managing CommandCore applications.",
                "path": os.path.join(base_dir, "CommandCore/app/main.py"),
                'version': None,
                'status': 'stopped',
                'process_name': 'commandcore_launcher_process'
            },
            {
                "id": "commandcorecodex",
                "name": "CommandCoreCodex",
                "description": "AI-powered code generation and analysis tool.",
                "path": os.path.join(base_dir, "Codex/app/gui.py"),
                'version': None,
                'status': 'stopped',
                'process_name': 'commandcorecodex_process'
            },
            {
                "id": "droidcom",
                "name": "DROIDCOM",
                "description": "Android device management and debugging toolkit.",
                "path": os.path.join(base_dir, "DROIDCOM/main.py"),
                'version': None,
                'status': 'stopped',
                'process_name': 'droidcom_process'
            },
            {
                "id": "hackattack",
                "name": "HackAttack",
                "description": "Penetration testing and vulnerability assessment framework.",
                "path": os.path.join(base_dir, "HackAttack/launch.py"),
                'version': None,
                'status': 'stopped',
                'process_name': 'hackattack_process'
            },
            {
                "id": "nightfire",
                "name": "Nightfire",
                "description": "Nightfire system monitor and controller.",
                "path": os.path.join(base_dir, "NIGHTFIRE/nightfire.py"),
                'version': None,
                'status': 'stopped',
                'process_name': 'nightfire_process'
            },
            {
                "id": "omniscribe",
                "name": "Omniscribe",
                "description": "Omniscribe transcription and analysis tool.",
                "path": os.path.join(base_dir, "OMNISCRIBE/app/main.py"),
                'version': None,
                'status': 'stopped',
                'process_name': 'omniscribe_process'
            },
            {
                "id": "pc_tools_linux",
                "name": "PC Tools Linux",
                "description": "PC tools for Linux system management.",
                "path": os.path.join(base_dir, "PC-X/pc_tools_linux.py"),
                'version': None,
                'status': 'stopped',
                'process_name': 'pc_tools_linux_process'
            },
            {
                "id": "vantage",
                "name": "VANTAGE",
                "description": "Advanced system monitoring and performance analysis.",
                "path": os.path.join(base_dir, "VANTAGE/launch_vantage.py"),
                'version': None,
                'status': 'stopped',
                'process_name': 'vantage_process'
            },
        ]
        
        # Sort apps alphabetically by name
        apps.sort(key=lambda app: app['name'])
        
        # Detect versions and check if running
        for app in apps:
            if os.path.exists(app['path']):
                # Detect version
                app['version'] = detect_version(app['path'])
                
                # Check if process is already running
                app_name = app['process_name']
                app['status'] = 'running' if self._is_process_running(app_name) else 'stopped'
                
                # If running, store the PID
                if app['status'] == 'running' and 'process_name' in app:
                    pid = self._get_process_pid(app_name)
                    if pid:
                        app['pid'] = pid
            else:
                app['version'] = 'not installed'
                app['status'] = 'not installed'
        
        return apps
    
    def init_ui(self):
        """Initialize the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)
        
        # Header
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Application Manager")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #ECF0F1;
            margin-bottom: 4px;
        """)
        
        description = QLabel("Manage all CommandCore applications from one central location.")
        description.setStyleSheet("color: #B0B0B0; font-size: 14px; margin-bottom: 8px;")
        
        # Stats bar
        stats = QWidget()
        stats_layout = QHBoxLayout(stats)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(16)
        
        total_label = QLabel(f"Total Apps: {len(self.apps)}")
        running_count = len([app for app in self.apps if app['status'] == 'running'])
        running_label = QLabel(f"Running: {running_count}")
        stopped_label = QLabel(f"Stopped: {len(self.apps) - running_count}")
        
        for label in [total_label, running_label, stopped_label]:
            label.setStyleSheet("color: #B0B0B0; font-size: 13px;")
            stats_layout.addWidget(label)
        
        stats_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setFixedSize(100, 32)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3A3A3A;
                color: #ECF0F1;
                border: 1px solid #4A4A4A;
                border-radius: 4px;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background-color: #4A4A4A;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_apps)
        
        # Auto refresh every 5 seconds (reduced frequency to prevent UI issues)
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self.refresh_apps)
        self._refresh_timer.start(5000)  # 5000 ms = 5 seconds

        header_layout.addWidget(title)
        header_layout.addWidget(description)
        header_layout.addWidget(stats)
        
        # Cards container
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        container = QWidget()
        self.cards_layout = QGridLayout(container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(16)
        
        self.update_app_cards()
        
        scroll.setWidget(container)
        
        # Add widgets to main layout
        main_layout.addWidget(header)
        main_layout.addWidget(refresh_btn, alignment=Qt.AlignRight)
        main_layout.addWidget(scroll, 1)
    
    def update_app_cards(self):
        """Update the application cards in the grid."""
        # Clear existing cards
        for i in reversed(range(self.cards_layout.count())): 
            self.cards_layout.itemAt(i).widget().setParent(None)
        
        # Add cards in a grid (3 columns)
        for i, app in enumerate(self.apps):
            row = i // 3
            col = i % 3
            card = AppCard(app, self)
            self.cards_layout.addWidget(card, row, col)
    
    def update_status(self, app_id, status):
        """Update the status of an application."""
        try:
            # Update the app status in our list
            app_updated = False
            for app in self.apps:
                if app['id'] == app_id:
                    app['status'] = status
                    app_updated = True
                    break
                    
            if app_updated:
                # Update the UI
                for i in range(self.cards_layout.count()):
                    widget = self.cards_layout.itemAt(i).widget()
                    if hasattr(widget, 'app_data') and widget.app_data['id'] == app_id:
                        # Update the status label
                        for child in widget.findChildren(QLabel):
                            if child.property('class') and 'app-status' in child.property('class'):
                                child.setText(status.capitalize())
                                child.setProperty('class', f'app-status status-{status}')
                                child.style().unpolish(child)
                                child.style().polish(child)
                        # Update the button
                        for child in widget.findChildren(QPushButton):
                            if child.property('class') and 'app-button' in child.property('class'):
                                child.setText("Stop" if status == 'running' else "Start")
                                child.setStyleSheet("""
                                    background-color: #00a8ff;
                                    color: white;
                                    border: none;
                                    border-radius: 4px;
                                    padding: 4px 12px;
                                """ if status == 'running' else """
                                    background-color: #3A3A3A;
                                    color: #B0B0B0;
                                    border: 1px solid #4A4A4A;
                                    border-radius: 4px;
                                    padding: 4px 12px;
                                """)
                                break
                        break
        except Exception as e:
            print(f"Error updating status for {app_id}: {e}")
            import traceback
            traceback.print_exc()
    
    def refresh_apps(self):
        """Refresh the status of all apps independently without linking."""
        status_changed = False
        for app in self.apps:
            app_name = app['process_name']
            new_status = 'running' if self._is_process_running(app_name) else 'stopped'
            if app['status'] != new_status:
                app['status'] = new_status
                status_changed = True

        # Only rebuild UI if status actually changed
        if status_changed:
            self.update_app_cards()

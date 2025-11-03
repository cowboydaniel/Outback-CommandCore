"""
Advanced tab for BLACKSTORM - Advanced settings and tools.
"""
import os
import platform
import subprocess
import sys
import psutil
import time
import re
import json
import select
import threading
import traceback
from datetime import datetime

from PySide6.QtCore import Qt, QProcess, QTimer, Signal, QThread
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGroupBox, QFormLayout, QLineEdit, QComboBox, QCheckBox,
    QSpinBox, QFileDialog, QMessageBox, QTextEdit, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar,
    QApplication, QMainWindow, QStatusBar, QSizePolicy
)
from PySide6.QtGui import QTextCursor, QFont, QIcon

class AdvancedTab(QWidget):
    """Tab for advanced settings and tools."""
    
    def __init__(self, parent=None):
        try:
            print("Initializing AdvancedTab...")
            super().__init__(parent)
            
            # Initialize attributes
            self.sys_info_labels = []
            self.terminal_output = None
            self.cmd_input = None
            self.auto_refresh_timer = QTimer(self)
            self.auto_refresh_timer.timeout.connect(self.refresh_system_info)
            
            # Set up the UI
            self.setup_ui()
            
            # Start auto-refresh for system info
            self.auto_refresh_timer.start(1000)  # Update every second
            
            print("AdvancedTab initialized successfully")
            
        except Exception as e:
            print(f"Error initializing AdvancedTab: {e}")
            import traceback
            traceback.print_exc()
            raise  # Re-raise to let the parent handle the error
    
    def setup_ui(self):
        """Set up the user interface."""
        try:
            print("Setting up AdvancedTab UI...")
            layout = QVBoxLayout(self)
            layout.setContentsMargins(5, 5, 5, 5)
            
            # Create tab widget
            tabs = QTabWidget()
            
            # System Information tab
            print("Creating System Information tab...")
            sysinfo_tab = self.create_system_info_tab()
            tabs.addTab(sysinfo_tab, "System Information")
            
            # Terminal tab
            print("Creating Terminal tab...")
            terminal_tab = self.create_terminal_tab()
            tabs.addTab(terminal_tab, "Terminal")
            
            # Add tabs to layout
            layout.addWidget(tabs)
            
            print("AdvancedTab UI setup complete")
            
        except Exception as e:
            print(f"Error in AdvancedTab.setup_ui: {e}")
            import traceback
            traceback.print_exc()
            raise  # Re-raise to let the parent handle the error
    
    def get_system_info(self):
        """Gather system information dynamically."""
        import socket
        import psutil
        import platform
        from datetime import datetime
        
        # Get system information
        system_info = []
        
        # BLACKSTORM Version (you might want to get this from a version file or package)
        try:
            with open(os.path.join(os.path.dirname(__file__), 'VERSION'), 'r') as f:
                storm_version = f.read().strip()
        except:
            storm_version = "1.0.0"  # Fallback version
            
        system_info.append(("BLACKSTORM Version:", storm_version))
        
        # Python Version
        system_info.append(("Python Version:", platform.python_version()))
        
        # OS Information
        os_info = f"{platform.system()} {platform.release()} ({platform.version()})"
        system_info.append(("Operating System:", os_info))
        
        # Hostname
        system_info.append(("Hostname:", socket.gethostname()))
        
        # CPU Information
        system_info.append(("CPU Cores (Physical):", str(psutil.cpu_count(logical=False))))
        system_info.append(("CPU Cores (Logical):", str(psutil.cpu_count(logical=True))))
        system_info.append(("CPU Usage:", f"{psutil.cpu_percent()}%"))
        
        # Memory Information
        mem = psutil.virtual_memory()
        system_info.append(("Total Memory:", f"{self._format_bytes(mem.total)}"))
        system_info.append(("Available Memory:", f"{self._format_bytes(mem.available)} ({mem.percent}% used)"))
        
        # Disk Information
        try:
            disk = psutil.disk_usage('/')
            system_info.append(("Disk Usage (Root):", 
                             f"{self._format_bytes(disk.used)} / {self._format_bytes(disk.total)} ({disk.percent}% used)"))
        except Exception as e:
            system_info.append(("Disk Usage:", f"Error: {str(e)}"))
        
        # Boot Time
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        system_info.append(("System Boot Time:", boot_time.strftime("%Y-%m-%d %H:%M:%S")))
        
        # Network Information
        net_io = psutil.net_io_counters()
        system_info.append(("Network (Sent/Received):", 
                         f"{self._format_bytes(net_io.bytes_sent)} / {self._format_bytes(net_io.bytes_recv)}"))
        
        return system_info
    
    def _format_bytes(self, bytes):
        """Format bytes to human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.2f} PB"
    
    def refresh_system_info(self):
        """Refresh the system information display."""
        if not hasattr(self, 'sys_info_labels'):
            return
            
        system_info = self.get_system_info()
        for i, (label, value) in enumerate(system_info):
            if i < len(self.sys_info_labels):
                self.sys_info_labels[i].setText(value)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sys_info_labels = []
        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.timeout.connect(self.refresh_system_info)
        self.setup_ui()
        # Start auto-refresh immediately
        self.auto_refresh_timer.start(1000)  # Update every 1000ms (1 second)
        
    def create_system_info_tab(self):
        """Create the System Information tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # System info group - no title needed as it's in the tab
        sys_group = QGroupBox()
        sys_group.setStyleSheet("QGroupBox { border: 0; margin-top: 0px; padding-top: 0px; }")
        sys_layout = QFormLayout()
        
        # Get system info
        system_info = self.get_system_info()
        self.sys_info_labels = []
        
        # Create labels for each piece of information
        for label, value in system_info:
            value_label = QLabel(value)
            value_label.setStyleSheet("""
                color: #E0E0E0;
                padding: 2px 0;
            """)
            sys_layout.addRow(QLabel(f"<b>{label}</b>"), value_label)
            self.sys_info_labels.append(value_label)
        
        sys_group.setLayout(sys_layout)
        
        # Add to layout with some spacing
        layout.addWidget(sys_group)
        layout.addStretch()
        
        # Set a minimum width for better appearance
        tab.setMinimumWidth(500)
        
        # Initial refresh
        self.refresh_system_info()
        
        return tab
            
    def closeEvent(self, event):
        """Ensure timer is stopped when tab is closed."""
        self.auto_refresh_timer.stop()
        super().closeEvent(event)
    
    def create_terminal_tab(self):
        """Create the Terminal tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Command input
        cmd_layout = QHBoxLayout()
        
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("Enter command...")
        
        btn_send = QPushButton("Send")
        btn_send.setStyleSheet("""
            QPushButton {
                background: #2ECC71;
                color: white;
                padding: 5px 15px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #27AE60;
            }
        """)
        
        cmd_layout.addWidget(self.cmd_input)
        cmd_layout.addWidget(btn_send)
        
        # Terminal output
        self.terminal_output = QTextEdit()
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setStyleSheet("""
            QTextEdit {
                background: #000000;
                color: #00FF00;
                font-family: monospace;
                border: 1px solid #3E3E3E;
                border-radius: 3px;
                padding: 5px;
            }
        """)
        
        # Add welcome message
        welcome_msg = """BLACKSTORM Terminal v1.0.0
Type 'help' for available commands

>"""
        self.terminal_output.setPlainText(welcome_msg)
        
        # Add to layout
        layout.addLayout(cmd_layout)
        layout.addWidget(self.terminal_output)
        
        # Connect signals
        btn_send.clicked.connect(self.execute_command)
        self.cmd_input.returnPressed.connect(self.execute_command)
        
        return tab
    
    def refresh_logs(self):
        """Refresh the log display."""
        # In a real app, this would reload logs from file
        QMessageBox.information(self, "Logs", "Logs refreshed.")
    
    def clear_logs(self):
        """Clear the log display."""
        reply = QMessageBox.question(
            self,
            "Clear Logs",
            "Are you sure you want to clear all logs?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.log_display.clear()
    
    def _restart_application(self, parent_window):
        """Restart the application."""
        try:
            # Get the current Python interpreter and script path
            import sys
            import os
            
            # Get the current Python executable
            python = sys.executable
            
            # Get the path to the main script
            script_path = os.path.abspath(sys.argv[0])
            
            # Prepare the command
            cmd = [python, script_path]
            
            # Add any command line arguments except the script name
            cmd.extend(sys.argv[1:])
            
            # Start a new instance
            QProcess.startDetached(python, cmd[1:])
            
            # Close the current instance
            parent_window.close()
            
        except Exception as e:
            self.terminal_output.append(f"Error restarting application: {str(e)}")
            
    def _is_smart_capable(self, device):
        """Check if a device supports SMART."""
        try:
            # First check if smartctl is installed
            subprocess.run(['which', 'smartctl'], check=True, 
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Get device info
            result = subprocess.run(
                ['smartctl', '-i', device],
                capture_output=True, text=True
            )
            
            # Check for both traditional SMART and NVMe devices
            return ('SMART support is:' in result.stdout or 
                   'NVME' in result.stdout.upper() or
                   'NVMe' in result.stdout or
                   'SMART/Health' in result.stdout)
                    
        except subprocess.CalledProcessError as e:
            self.terminal_output.append(f"  Warning: smartctl command failed: {e.stderr.strip()}")
            return False
        except Exception as e:
            self.terminal_output.append(f"  Warning: {str(e)}")
            return False
    
    def _get_device_info(self, device):
        """Get detailed information about a device or partition."""
        info = {
            'model': 'Unknown',
            'size': 'Unknown',
            'type': 'partition' if any(c.isdigit() for c in device) else 'disk',
            'mounted': False,
            'mount_points': [],
            'table_type': None,
            'filesystem': None
        }
        
        try:
            # Get udev information
            udev_info = subprocess.run(
                ['udevadm', 'info', '--query=property', '--name=' + device],
                capture_output=True, text=True
            )
            
            if udev_info.returncode == 0:
                for line in udev_info.stdout.split('\n'):
                    if 'ID_MODEL=' in line:
                        info['model'] = line.split('=')[1].replace('_', ' ').strip('"')
                    elif 'ID_PART_TABLE_TYPE=' in line:
                        info['table_type'] = line.split('=')[1].strip('"')
            
            # Get size
            try:
                size_bytes = int(subprocess.check_output(
                    ['blockdev', '--getsize64', device]
                ).decode().strip())
                info['size'] = f"{size_bytes / (1024**3):.2f} GB"
            except:
                pass
                
            # Check mount status
            mount_check = subprocess.run(
                ['findmnt', '--source', device, '-n', '-o', 'TARGET'],
                capture_output=True, text=True
            )
            
            if mount_check.returncode == 0 and mount_check.stdout.strip():
                info['mounted'] = True
                info['mount_points'] = [mp for mp in mount_check.stdout.strip().split('\n') if mp]
                
            # Check filesystem
            blkid = subprocess.run(
                ['blkid', '-o', 'value', '-s', 'TYPE', device],
                capture_output=True, text=True
            )
            if blkid.returncode == 0 and blkid.stdout.strip():
                info['filesystem'] = blkid.stdout.strip()
                
        except Exception as e:
            self.terminal_output.append(f"  Warning: Could not get all device info: {str(e)}")
            
        return info
        
    def _run_quick_test(self, device):
        """Run basic device checks."""
        self.terminal_output.append("\n[1/3] Running quick checks...")
        
        # Get device information
        info = self._get_device_info(device)
        
        # Display basic info
        self.terminal_output.append(f"  Device: {os.path.basename(device)}")
        self.terminal_output.append(f"  Type:   {info['type'].capitalize()}")
        self.terminal_output.append(f"  Model:  {info['model']}")
        self.terminal_output.append(f"  Size:   {info['size']}")
        
        if info['table_type']:
            self.terminal_output.append(f"  Table:  {info['table_type']}")
            
        # Mount status
        if info['mounted']:
            self.terminal_output.append("  Status: Mounted (some tests may be limited)")
            for mp in info['mount_points']:
                self.terminal_output.append(f"    - {mp}")
            self.terminal_output.append("  Note: Some tests may be limited on mounted filesystems")
        else:
            self.terminal_output.append("  Status: Not mounted")
        
        # Check filesystem
        try:
            blkid = subprocess.run(
                ['blkid', '-o', 'value', '-s', 'TYPE', device],
                capture_output=True, text=True
            )
            if blkid.returncode == 0 and blkid.stdout.strip():
                fs_type = blkid.stdout.strip()
                self.terminal_output.append(f"  Filesystem: {fs_type}")
                
                # Check filesystem health if not mounted
                if 'mount_check' in locals() and mount_check.returncode != 0:
                    fsck_cmd = f'pkexec fsck -n {shlex.quote(device)}'
                    fsck = subprocess.run(
                        fsck_cmd,
                        shell=True,
                        capture_output=True,
                        text=True
                    )
                    if 'clean' in fsck.stdout or 'clean' in fsck.stderr:
                        self.terminal_output.append("  Filesystem status: Clean")
                    else:
                        self.terminal_output.append("  Filesystem status: Issues found")
                        self.terminal_output.append("    Run 'fsck' to repair")
            else:
                self.terminal_output.append("  Filesystem: None detected")
        except Exception as e:
            self.terminal_output.append(f"  Could not check filesystem: {str(e)}")
    
    def _run_smart_test(self, device, test_type='smart'):
        """Run SMART self-test on the device."""
        self.terminal_output.append("\n[2/3] Running SMART self-test...")
        
        try:
            # First determine if this is an NVMe device
            is_nvme = False
            try:
                info = subprocess.run(
                    ['smartctl', '-i', device],
                    capture_output=True, text=True
                )
                is_nvme = 'NVME' in info.stdout.upper() or 'NVMe' in info.stdout
            except:
                pass
                
            # Get and display SMART information
            self.terminal_output.append("\n=== NVMe Drive Information ===")
            
            # Get detailed SMART information with sudo
            cmd = ['pkexec', 'smartctl', '-a', device]
            
            try:
                # First try with -d nvme for NVMe devices
                smart_info = subprocess.run(
                    cmd + ['-d', 'nvme'],
                    capture_output=True, 
                    text=True,
                    timeout=10
                )
                
                # If that fails, try without the -d flag
                if smart_info.returncode != 0:
                    smart_info = subprocess.run(
                        cmd,
                        capture_output=True, 
                        text=True,
                        timeout=10
                    )
                
                # Process the output regardless of return code
                if smart_info.stdout.strip():
                    # Display the raw output for now
                    self.terminal_output.append("")
                    for line in smart_info.stdout.split('\n'):
                        if line.strip():
                            self.terminal_output.append(line)
                
                # Show any errors
                if smart_info.stderr.strip():
                    self.terminal_output.append("\nError output:")
                    for line in smart_info.stderr.split('\n'):
                        if line.strip():
                            self.terminal_output.append(f"  {line}")
                
                # If we got no output at all, show a message
                if not smart_info.stdout.strip() and not smart_info.stderr.strip():
                    self.terminal_output.append("  No output received from smartctl")
                    
            except subprocess.TimeoutExpired:
                self.terminal_output.append("  Error: Command timed out after 10 seconds")
            except Exception as e:
                self.terminal_output.append(f"  Error running command: {str(e)}")
            
            # Only run self-test if explicitly requested
            if test_type in ['smart', 'full']:
                self.terminal_output.append("\n=== Running Self-Test ===")
                try:
                    # Try to run short self-test (non-blocking)
                    result = subprocess.run(
                        ['pkexec', 'smartctl', '-t', 'short', device],
                        capture_output=True, text=True, timeout=5
                    )
                    
                    if result.returncode == 0:
                        self.terminal_output.append("  NVMe short self-test started successfully")
                        # Show when the test will complete
                        for line in result.stdout.split('\n'):
                            line = line.strip()
                            if line and ('test will complete after' in line or 'progress' in line.lower()):
                                self.terminal_output.append(f"    {line}")
                                break
                    else:
                        if result.stderr.strip():
                            self.terminal_output.append(f"  Note: {result.stderr.strip()}")
                except subprocess.TimeoutExpired:
                    self.terminal_output.append("  Note: Background self-test is running")
                except Exception as e:
                    self.terminal_output.append(f"  Error: {str(e)}")
                
                # Add note about self-test results
                self.terminal_output.append("\n  Note: Some NVMe drives may not support all self-tests")
                self.terminal_output.append("  For complete information, run:")
                self.terminal_output.append(f"    smartctl -a {device}")
            elif not is_nvme:
                # For traditional SATA devices
                result = subprocess.run(
                    ['pkexec', 'smartctl', '-t', 'short', device],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    self.terminal_output.append("  SMART short self-test started successfully")
                    # Get and display test progress
                    for line in result.stdout.split('\n'):
                        if 'test will complete after' in line:
                            self.terminal_output.append(f"  {line.strip()}")
                            break
                else:
                    self.terminal_output.append(f"  Error running SMART test: {result.stderr.strip()}")
            
            self.terminal_output.append(f"  Run 'smartctl -a {device}' to view detailed results")
            
        except Exception as e:
            self.terminal_output.append(f"  Error: {str(e)}")
    
    def _run_benchmark(self, device):
        """Run storage benchmark on the specified device in a separate thread."""
        # Check if benchmark is already running
        if hasattr(self, '_benchmark_thread') and self._benchmark_thread.is_alive():
            self.terminal_output.append("Benchmark is already running. Please wait...")
            return
            
        # Create a thread to run the benchmark
        self._benchmark_thread = threading.Thread(
            target=self._run_benchmark_thread,
            args=(device,),
            daemon=True
        )
        self._benchmark_thread.start()
    
    def _verify_device(self, device):
        """Run device verification (read-only badblocks check)."""
        # Check if verification is already running
        if hasattr(self, '_verify_thread') and self._verify_thread.is_alive():
            self.terminal_output.append("Verification is already running. Use 'stop' to cancel.")
            return
            
        # Create a thread to run the verification
        self._verify_thread = threading.Thread(
            target=self._verify_device_thread,
            args=(device,),
            daemon=True
        )
        self._verify_thread.start()
    
    def stop_verification(self):
        """Stop the currently running verification."""
        try:
            if not hasattr(self, '_verify_process') or not self._verify_process:
                return False
                
            if self._verify_process.poll() is not None:  # Process already finished
                return False
                
            # Try to terminate gracefully first
            self._verify_process.terminate()
            try:
                self._verify_process.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                try:
                    self._verify_process.kill()
                    self._verify_process.wait()
                except:
                    pass
                    
            self.terminal_output.append("\nVerification stopped by user.")
            return True
            
        except Exception as e:
            self.terminal_output.append(f"\nError stopping verification: {str(e)}")
            return False
        finally:
            # Clean up process resources
            if hasattr(self, '_verify_process'):
                try:
                    if self._verify_process.stdout:
                        self._verify_process.stdout.close()
                    if self._verify_process.stderr:
                        self._verify_process.stderr.close()
                    self._verify_process = None
                except:
                    pass
    
    def _verify_device_thread(self, device):
        """Thread function to verify device integrity."""
        def append_output(text):
            # Helper to safely update the UI from the thread
            self.terminal_output.append(text)
            
        try:
            append_output(f"\n=== Starting device verification for {device} ===")
            append_output("  Type 'stop' to cancel the verification at any time.")
            
            # Check if device is mounted
            mounts = psutil.disk_partitions()
            device_mounted = any(mount.device == device for mount in mounts)
            
            if device_mounted:
                append_output(f"  Warning: {device} is currently mounted. It's recommended to unmount it first.")
                append_output("  Continuing with read-only verification...")
            
            # Check if badblocks is installed
            try:
                subprocess.run(['which', 'badblocks'], check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError:
                append_output("  Error: 'badblocks' is required but not installed.")
                append_output("  Install it with: sudo apt-get install e2fsprogs")
                return
            
            # Run badblocks in read-only mode using pkexec for GUI password prompt
            append_output("  Running read-only verification (this may take a while)...")
            append_output("  A password prompt will appear for elevated privileges...")
            
            try:
                # Use pkexec to get GUI password prompt
                cmd = ['pkexec', 'badblocks', '-v', '-s', '-e', '1', device]
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,  # Line buffered
                    universal_newlines=True
                )
            except Exception as e:
                append_output(f"  Error starting verification: {str(e)}")
                append_output("  Make sure 'pkexec' is installed and properly configured.")
                return
            
            # Store process reference for potential stop
            self._verify_process = process
            
            # Read output in real-time
            while True:
                # Check if process has finished
                if process.poll() is not None:
                    break
                
                # Check for output in both stdout and stderr
                for stream in [process.stdout, process.stderr]:
                    if stream is None:
                        continue
                    
                    # Try to read a line
                    output = stream.readline()
                    if output:
                        append_output(f"  {output.strip()}")
                
                # Small sleep to prevent high CPU usage
                time.sleep(0.1)
            
            # Get any remaining output with a timeout
            try:
                remaining_stdout, remaining_stderr = process.communicate(timeout=5.0)
                if remaining_stdout:
                    for line in remaining_stdout.splitlines():
                        if line.strip():
                            append_output(f"  {line.strip()}")
                if remaining_stderr:
                    for line in remaining_stderr.splitlines():
                        if line.strip():
                            append_output(f"  [stderr] {line.strip()}")
            except subprocess.TimeoutExpired:
                append_output("  Warning: Timeout while waiting for final output")
            
            # Check for errors
            if process.returncode != 0 and process.returncode != -15:  # -15 is SIGTERM
                if stderr:
                    if "permission denied" in stderr.lower():
                        append_output("  Error: Permission denied. Try running with sudo or as root.")
                    else:
                        append_output(f"  Error: {stderr.strip()}")
            elif process.returncode == 0:
                append_output("\n=== Verification completed successfully! ===")
                append_output("  No bad blocks found." if not stderr else f"  Issues found: {stderr.strip()}")
                
        except subprocess.TimeoutExpired:
            append_output("\nVerification timed out.")
        except Exception as e:
            append_output(f"\nError during verification: {str(e)}")
        finally:
            # Clean up process resources
            if hasattr(self, '_verify_process') and self._verify_process:
                try:
                    if self._verify_process.poll() is None:
                        self._verify_process.terminate()
                        try:
                            self._verify_process.wait(timeout=1.0)
                        except (subprocess.TimeoutExpired, OSError):
                            pass
                    if self._verify_process.stdout:
                        self._verify_process.stdout.close()
                    if self._verify_process.stderr:
                        self._verify_process.stderr.close()
                    self._verify_process = None
                except Exception as e:
                    append_output(f"\nError during cleanup: {str(e)}")
                    
            append_output("\nVerification completed.")
    
    def _run_benchmark_thread(self, device):
        """Thread function to run the benchmark."""
        def append_output(text):
            # Helper to safely update the UI from the thread
            self.terminal_output.append(text)
            
        append_output("\n=== Starting Storage Benchmark ===")
        
        # Check if fio is installed
        try:
            subprocess.run(['which', 'fio'], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            append_output("  Error: 'fio' (Flexible I/O Tester) is required but not installed.")
            append_output("  Install it with: sudo apt-get install fio")
            return
        
        # Create a temporary file for testing
        test_file = f"/tmp/blackstorm_benchmark_{os.getpid()}.tmp"
        test_size = "256M"  # Test with 256MB file
        
        try:
            # Sequential Read Test
            append_output("\n[1/4] Sequential Read Test (30s)...")
            result = subprocess.run(
                ['fio', '--name=seqread', f'--filename={test_file}',
                 '--rw=read', '--bs=1M', '--direct=1', '--ioengine=libaio',
                 '--numjobs=1', '--time_based', '--runtime=30s',
                 '--size=256M', '--group_reporting', '--output-format=json'],
                capture_output=True, text=True, check=True
            )
            read_speed = self._parse_fio_output(result.stdout)
            append_output(f"  Sequential Read: {read_speed} MB/s")
            
            # Sequential Write Test
            append_output("\n[2/4] Sequential Write Test (30s)...")
            result = subprocess.run(
                ['fio', '--name=seqwrite', f'--filename={test_file}',
                 '--rw=write', '--bs=1M', '--direct=1', '--ioengine=libaio',
                 '--numjobs=1', '--time_based', '--runtime=30s',
                 '--size=256M', '--group_reporting', '--output-format=json'],
                capture_output=True, text=True, check=True
            )
            write_speed = self._parse_fio_output(result.stdout)
            append_output(f"  Sequential Write: {write_speed} MB/s")
            
            # Random Read Test
            append_output("\n[3/4] Random 4K Read Test (30s)...")
            result = subprocess.run(
                ['fio', '--name=randread', f'--filename={test_file}',
                 '--rw=randread', '--bs=4k', '--direct=1', '--ioengine=libaio',
                 '--iodepth=64', '--numjobs=1', '--time_based', '--runtime=30s',
                 '--size=256M', '--group_reporting', '--output-format=json'],
                capture_output=True, text=True, check=True
            )
            rand_read_iops = self._parse_fio_output(result.stdout, iops=True)
            append_output(f"  Random 4K Read: {rand_read_iops} IOPS")
            
            # Random Write Test
            append_output("\n[4/4] Random 4K Write Test (30s)...")
            result = subprocess.run(
                ['fio', '--name=randwrite', f'--filename={test_file}',
                 '--rw=randwrite', '--bs=4k', '--direct=1', '--ioengine=libaio',
                 '--iodepth=64', '--numjobs=1', '--time_based', '--runtime=30s',
                 '--size=256M', '--group_reporting', '--output-format=json'],
                capture_output=True, text=True, check=True
            )
            rand_write_iops = self._parse_fio_output(result.stdout, iops=True)
            append_output(f"  Random 4K Write: {rand_write_iops} IOPS")
            
            # Summary
            append_output("\n=== Benchmark Summary ===")
            append_output(f"  Sequential Read:  {read_speed} MB/s")
            append_output(f"  Sequential Write: {write_speed} MB/s")
            append_output(f"  Random 4K Read:   {rand_read_iops} IOPS")
            append_output(f"  Random 4K Write:  {rand_write_iops} IOPS")
            append_output("\nBenchmark completed!")
            
        except subprocess.CalledProcessError as e:
            append_output(f"  Error running benchmark: {e.stderr}")
        except Exception as e:
            append_output(f"  Unexpected error: {str(e)}")
        finally:
            # Clean up
            if os.path.exists(test_file):
                try:
                    os.remove(test_file)
                except Exception as e:
                    append_output(f"  Warning: Could not remove temporary file: {str(e)}")
    
    def _append_to_terminal(self, text):
        """Thread-safe method to append text to terminal."""
        self.terminal_output.append(text)
        
    def _resolve_device(self, device_name):
        """Resolve a device name to its full path."""
        # If it's already a full path, return as is
        if device_name.startswith('/dev/'):
            return device_name if os.path.exists(device_name) else None
            
        # Try with /dev/ prefix
        device_path = f"/dev/{device_name}"
        if os.path.exists(device_path):
            return device_path
            
        # For NVMe devices which might have 'p' before partition number
        if device_name.startswith('nvme'):
            if 'p' not in device_name and any(c.isdigit() for c in device_name):
                base = re.sub(r'\d+$', '', device_name)
                part_num = device_name[len(base):]
                device_path = f"/dev/{base}p{part_num}"
                if os.path.exists(device_path):
                    return device_path
        
        return None
        
    def _parse_fio_output(self, json_output, iops=False):
        """Parse fio JSON output to extract speed or IOPS."""
        try:
            data = json.loads(json_output)
            job = data['jobs'][0]
            if iops:
                return int(job['read']['iops'] + job['write']['iops'])
            else:
                # Convert from bytes to MB/s
                return round((job['read']['bw'] + job['write']['bw']) / 1024, 2)
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            self.terminal_output.append(f"  Error parsing benchmark results: {str(e)}")
            return "N/A"
    
    def _run_badblocks_test(self, device, read_only=True):
        """Check for bad blocks on the device."""
        try:
            # Check if badblocks is installed
            try:
                subprocess.run(['which', 'badblocks'], check=True, 
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except subprocess.CalledProcessError:
                self.terminal_output.append("  Error: 'badblocks' command not found. Please install e2fsprogs package.")
                return
                
            # Get device info
            info = self._get_device_info(device)
            
            # Check if device exists
            if info['size'] == 'Unknown':
                self.terminal_output.append(f"  Error: Could not access {device}")
                return
                
            # Warn if mounted read-write
            if info['mounted'] and not read_only:
                self.terminal_output.append("  Warning: Device is mounted. Badblocks test in read-write mode may cause data loss!")
                self.terminal_output.append("  Consider unmounting first or using read-only mode (-n)")
                
            # Get device size in blocks
            try:
                block_size = 4096  # 4K blocks
                size_bytes = int(subprocess.check_output(
                    ['blockdev', '--getsize64', device]
                ).decode().strip())
                num_blocks = size_bytes // block_size
                
                if num_blocks == 0:
                    self.terminal_output.append("  Error: Could not determine device size")
                    return
                    
                self.terminal_output.append(f"  Device size: {size_bytes / (1024**3):.2f} GB")
                self.terminal_output.append(f"  Scanning {num_blocks} blocks (may take a while)...")
                
                # Run badblocks in read-only mode by default
                badblocks_cmd = ['badblocks', '-v', '-b', str(block_size), '-s']
                if read_only:
                    badblocks_cmd.append('-n')
                badblocks_cmd.extend(['-c', '1024', device, str(num_blocks)])
                
                self.terminal_output.append(f"  Command: {' '.join(badblocks_cmd)}")
                
                process = subprocess.Popen(
                    ['pkexec'] + badblocks_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                
                # Monitor progress
                bad_blocks = 0
                last_progress = ""
                
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        output = output.strip()
                        if '%' in output or 'pass' in output.lower() or 'done' in output.lower():
                            if output != last_progress:  # Avoid duplicate progress messages
                                self.terminal_output.append(f"  {output}")
                                last_progress = output
                    
                # Get any remaining output
                stdout, stderr = process.communicate()
                
                # Check for bad blocks in the output
                for line in (stdout + stderr).split('\n'):
                    if 'bad blocks' in line.lower():
                        try:
                            bad_blocks = int(line.split(':')[-1].strip())
                        except (ValueError, IndexError):
                            pass
                
                if process.returncode == 0:
                    if bad_blocks > 0:
                        self.terminal_output.append(f"  Found {bad_blocks} bad blocks")
                        self.terminal_output.append("  Warning: Consider replacing this device soon")
                    else:
                        self.terminal_output.append("  No bad blocks found")
                else:
                    self.terminal_output.append(f"  Badblocks failed with return code {process.returncode}")
                    if stderr.strip():
                        self.terminal_output.append(f"  Error: {stderr.strip()}")
                    
            except subprocess.CalledProcessError as e:
                self.terminal_output.append(f"  Error getting device info: {str(e)}")
                if e.stderr:
                    self.terminal_output.append(f"  {e.stderr.strip()}")
                    
        except Exception as e:
            self.terminal_output.append(f"  Unexpected error in badblocks test: {str(e)}")
            import traceback
            self.terminal_output.append(f"  {traceback.format_exc().splitlines()[-1]}")
    
    def execute_command(self):
        """Execute the command entered in the terminal."""
        import platform
        import os
        import subprocess
        import psutil
        from datetime import datetime
        
        command = self.cmd_input.text().strip()
        
        if not command:
            return
        
        # Add command to terminal
        current_text = self.terminal_output.toPlainText()
        self.terminal_output.setPlainText(f"{current_text} {command}\n")
        
        try:
            # Process commands
            if command.lower() == "help":
                help_text = """Available commands:
  help       - Show this help
  clear      - Clear the terminal
  version    - Show version information
  devices    - List connected devices and storage
  status     - Show current system status and resource usage
  update     - Check for and install updates
  restart    - Restart the application
  shutdown   - Safely shut down the application
  
Storage Management:
  mount <device>    - Mount a specific storage device
  unmount <device>  - Safely unmount a device
  format <device>   - Format a storage device
  scan              - Scan for new storage devices
  usage             - Show storage usage statistics
  backup <src> <dst>- Create a backup
  restore <src> <dst> - Restore from backup

Diagnostics & Maintenance:
  test <device>     - Run diagnostics on a device
  benchmark <device> - Benchmark a device's performance
  verify <device>   - Verify integrity of a device
  recover <device>  - Attempt data recovery
  logs              - View application logs

Security & Automation:
  encrypt <device> <pwd> - Encrypt a device
  decrypt <device> <pwd> - Decrypt a device
  schedule <cmd> <time> - Schedule a command to run later
  script <filename>     - Run a script file
  export <data> <file>  - Export system data to a file
  import <file>         - Import settings or data
  config                - View or modify configuration settings"""
                self.terminal_output.append(help_text)
            
            elif command.lower() == "clear":
                self.terminal_output.clear()
                self.terminal_output.setPlainText("Terminal cleared\n>")
                return
                
            elif command.lower().startswith("verify "):
                # Format: verify <device>
                parts = command.split()
                if len(parts) < 2:
                    self.terminal_output.append("Usage: verify <device>")
                    return
                    
                device = self._resolve_device(parts[1])
                if not device:
                    self.terminal_output.append(f"Error: Device {parts[1]} not found")
                    return
                    
                self._verify_device(device)
                return
                
            elif command.lower() == "stop":
                if hasattr(self, '_verify_process') and self._verify_process and self._verify_process.poll() is None:
                    self.terminal_output.append("Stopping verification...")
                    self.stop_verification()
                else:
                    self.terminal_output.append("No active verification to stop.")
                return
                
            elif command.lower() == "version":
                version_info = f"""BLACKSTORM System Information:
  Version: 1.0.0
  Python: {platform.python_version()}
  OS: {platform.system()} {platform.release()} {platform.machine()}
  Hostname: {platform.node()}
  Uptime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
                self.terminal_output.append(version_info)
                
            elif command.lower() == "devices":
                try:
                    # Get disk partitions
                    partitions = psutil.disk_partitions()
                    devices_info = ["Connected Storage Devices:"]
                    
                    for partition in partitions:
                        try:
                            usage = psutil.disk_usage(partition.mountpoint)
                            total_gb = usage.total / (1024**3)
                            used_gb = usage.used / (1024**3)
                            free_gb = usage.free / (1024**3)
                            percent_used = usage.percent
                            
                            device_info = f"""  {partition.device} ({partition.fstype}):
    Mount: {partition.mountpoint}
    Size: {total_gb:.1f}GB (Used: {used_gb:.1f}GB, Free: {free_gb:.1f}GB, {percent_used}% used)"""
                            devices_info.append(device_info)
                        except Exception as e:
                            devices_info.append(f"  {partition.device}: Error reading device info")
                    
                    # Get USB devices
                    try:
                        lsusb = subprocess.run(['lsusb'], capture_output=True, text=True)
                        if lsusb.returncode == 0 and lsusb.stdout.strip():
                            devices_info.append("\nUSB Devices:" + "\n  " + "\n  ".join(lsusb.stdout.strip().split('\n')))
                    except:
                        pass
                        
                    self.terminal_output.append("\n".join(devices_info))
                    
                except Exception as e:
                    self.terminal_output.append(f"Error getting device information: {str(e)}")
            
            elif command.lower() == "status":
                try:
                    # CPU Usage
                    cpu_percent = psutil.cpu_percent(interval=1)
                    cpu_count = psutil.cpu_count()
                    cpu_freq = psutil.cpu_freq()
                    
                    # Memory Usage
                    memory = psutil.virtual_memory()
                    swap = psutil.swap_memory()
                    
                    # Disk I/O
                    disk_io = psutil.disk_io_counters()
                    
                    # Network
                    net_io = psutil.net_io_counters()
                    net_ifs = psutil.net_if_addrs()
                    
                    # System Load
                    load_avg = ' '.join([f"{x:.2f}" for x in os.getloadavg()])
                    
                    # Create status string
                    status_info = f"""=== SYSTEM STATUS ===

CPU:
  Usage: {cpu_percent}% of {cpu_count} cores
  Frequency: {cpu_freq.current/1000:.2f} GHz (Min: {cpu_freq.min/1000:.2f} GHz, Max: {cpu_freq.max/1000:.2f} GHz)

Memory:
  RAM: {memory.percent}% used ({memory.used/1024**3:.1f} GB / {memory.total/1024**3:.1f} GB)
  Swap: {swap.percent}% used ({swap.used/1024**3:.1f} GB / {swap.total/1024**3:.1f} GB)

Disk I/O:
  Read: {disk_io.read_bytes/1024**2:.1f} MB
  Write: {disk_io.write_bytes/1024**2:.1f} MB

Network:
  Bytes Sent: {net_io.bytes_sent/1024**2:.1f} MB
  Bytes Received: {net_io.bytes_recv/1024**2:.1f} MB
  Interfaces: {len(net_ifs)} active

System Load:
  Load Average (1, 5, 15 min): {load_avg}"""
                    
                    self.terminal_output.append(status_info)
                except Exception as e:
                    self.terminal_output.append(f"Error getting system status: {str(e)}")
                    
            elif command.lower() == "restart":
                # Get the parent window (BlackStormLauncher)
                parent = self.parent()
                while parent is not None and not isinstance(parent, QMainWindow):
                    parent = parent.parent()
                
                if parent is not None:
                    reply = QMessageBox.question(
                        self,
                        'Confirm Restart',
                        'Are you sure you want to restart BLACKSTORM?',
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )
                    
                    if reply == QMessageBox.StandardButton.Yes:
                        self.terminal_output.append("Restarting BLACKSTORM...")
                        # Use QProcess to restart the application
                        app = QApplication.instance()
                        if app:
                            QTimer.singleShot(1000, lambda: self._restart_application(parent))
                        return
                else:
                    self.terminal_output.append("Error: Could not find main application window")
                    
            elif command.lower() == "shutdown":
                self.terminal_output.append("Shutting down...")
                QApplication.quit()
                
            elif command.lower() == "scan":
                try:
                    self.terminal_output.append("Scanning for storage devices...")
                    
                    # Get all block devices
                    try:
                        # Use lsblk to get detailed block device information
                        lsblk = subprocess.run(
                            ['lsblk', '-o', 'NAME,SIZE,TYPE,MOUNTPOINT,MODEL,VENDOR,TRAN,LABEL', '-d', '-e7,11,1'],
                            capture_output=True, text=True
                        )
                        
                        if lsblk.returncode == 0:
                            self.terminal_output.append("\nBlock Devices:")
                            self.terminal_output.append("-" * 80)
                            self.terminal_output.append(lsblk.stdout.strip())
                        else:
                            self.terminal_output.append("Error: Could not list block devices")
                            
                    except Exception as e:
                        self.terminal_output.append(f"Error running lsblk: {str(e)}")
                    
                    # Get USB devices specifically
                    try:
                        usb_devs = []
                        usb_info = subprocess.run(
                            ['lsusb'],
                            capture_output=True, text=True
                        )
                        
                        if usb_info.returncode == 0 and usb_info.stdout.strip():
                            self.terminal_output.append("\nUSB Devices:")
                            self.terminal_output.append("-" * 80)
                            self.terminal_output.append(usb_info.stdout.strip())
                        
                    except Exception as e:
                        self.terminal_output.append(f"Error getting USB info: {str(e)}")
                    
                    # Get disk space information
                    try:
                        df = subprocess.run(
                            ['df', '-h', '--output=source,fstype,size,used,avail,pcent,target'],
                            capture_output=True, text=True
                        )
                        
                        if df.returncode == 0:
                            self.terminal_output.append("\nMounted Filesystems:")
                            self.terminal_output.append("-" * 80)
                            self.terminal_output.append(df.stdout.strip())
                            
                    except Exception as e:
                        self.terminal_output.append(f"Error getting disk usage: {str(e)}")
                    
                    # Check for SMART data if available
                    try:
                        smartctl = subprocess.run(
                            ['which', 'smartctl'],
                            capture_output=True, text=True
                        )
                        
                        if smartctl.returncode == 0:
                            self.terminal_output.append("\nNote: For detailed drive health information, use: sudo smartctl -a /dev/sdX")
                            
                    except:
                        pass
                        
                except Exception as e:
                    self.terminal_output.append(f"Error during scan: {str(e)}")
                    
            elif command.lower().startswith("mount "):
                try:
                    args = command.split()
                    if len(args) < 2:
                        self.terminal_output.append("Usage: mount <device> [options]")
                        self.terminal_output.append("Example: mount sda1")
                        self.terminal_output.append("Example: mount /dev/sdb1")
                        return
                        
                    # Handle device name (prepend /dev/ if not already a full path)
                    device = args[1] if args[1].startswith('/') else f"/dev/{args[1]}"
                    # Create mount point name from device name (without /dev/)
                    mount_point = f"/mnt/{os.path.basename(device).replace('/', '_')}"
                    
                    # Check if device exists
                    if not os.path.exists(device):
                        self.terminal_output.append(f"Error: Device {device} does not exist")
                        return
                        
                    # Note: Mount point creation is now handled in the script below
                    # to avoid multiple pkexec prompts
                    
                    # Check if already mounted
                    mount_check = subprocess.run(
                        ['findmnt', '--source', device],
                        capture_output=True, text=True
                    )
                    
                    if mount_check.returncode == 0:
                        self.terminal_output.append(f"Device {device} is already mounted at:")
                        self.terminal_output.append(mount_check.stdout.strip())
                        return
                    
                    # Try to determine filesystem type
                    fs_type = None
                    blkid = subprocess.run(
                        ['blkid', '-s', 'TYPE', '-o', 'value', device],
                        capture_output=True, text=True
                    )
                    
                    if blkid.returncode == 0 and blkid.stdout.strip():
                        fs_type = blkid.stdout.strip()
                        self.terminal_output.append(f"Detected filesystem: {fs_type}")
                    
                    # Build a single command that does everything with one pkexec prompt
                    script = f'''
                    #!/bin/bash
                    set -e  # Exit on any error
                    
                    # Create mount point if it doesn't exist
                    if [ ! -d "{mount_point}" ]; then
                        mkdir -p "{mount_point}" || exit 1
                        chmod 777 "{mount_point}" || exit 1
                        echo "Created mount point: {mount_point}" >&2
                    fi
                    
                    # Build mount command
                    mount_cmd=("mount")
                    
                    # Add filesystem type if detected
                    if [ -n "{fs_type}" ]; then
                        mount_cmd+=("-t" "{fs_type}")
                    fi
                    
                    # Add any additional options
                    additional_args=({' '.join(f'"{arg}"' for arg in args[2:] if arg != '--fstab')})
                    if [ "${{#additional_args[@]}}" -gt 0 ]; then
                        mount_cmd+=("${{additional_args[@]}}")
                    fi
                    
                    # Add device and mount point
                    mount_cmd+=("{device}" "{mount_point}")
                    
                    # Execute mount
                    "${{mount_cmd[@]}}" || exit $?
                    
                    # Add to fstab if requested
                    if [[ " {' '.join(args)} " == *' --fstab '* ]]; then
                        echo -e "\n# Added by BLACKSTORM on $(date)" | tee -a /etc/fstab >/dev/null
                        echo -e "{device}\t{mount_point}\t{fs_type or 'auto'}\tdefaults\t0 2" | tee -a /etc/fstab >/dev/null
                        echo "Added entry to /etc/fstab for persistent mounting" >&2
                    fi
                    
                    # Show mount information
                    echo "\nMount information:" >&2
                    df -h "{mount_point}" >&2
                    '''
                    
                    # Execute the combined command with a single pkexec
                    self.terminal_output.append(f"Mounting {device} to {mount_point}...")
                    result = subprocess.run(
                        ['pkexec', 'bash', '-c', script],
                        capture_output=True,
                        text=True
                    )
                    
                    # Process the output
                    if result.returncode == 0:
                        self.terminal_output.append(f"Successfully mounted {device} at {mount_point}")
                        # Add any output from the script
                        if result.stdout.strip():
                            self.terminal_output.append(result.stdout.strip())
                        if result.stderr.strip():
                            self.terminal_output.append(result.stderr.strip())
                    else:
                        error_msg = result.stderr.strip() or result.stdout.strip()
                        self.terminal_output.append(f"Failed to mount {device}:")
                        self.terminal_output.append(error_msg if error_msg else "Unknown error")
                        
                except Exception as e:
                    self.terminal_output.append(f"Error mounting device: {str(e)}")
                    
            elif command.lower().startswith("unmount "):
                try:
                    args = command.split()
                    if len(args) < 2:
                        self.terminal_output.append("Usage: unmount <device> [options]")
                        self.terminal_output.append("Example: unmount sda1")
                        self.terminal_output.append("Example: unmount /dev/sdb1")
                        return
                        
                    # Handle device name (prepend /dev/ if not already a full path)
                    device = args[1] if args[1].startswith('/') else f"/dev/{args[1]}"
                    
                    # Find the mount point for the device
                    findmnt = subprocess.run(
                        ['findmnt', '-n', '-o', 'TARGET', '--source', device],
                        capture_output=True, text=True
                    )
                    
                    if findmnt.returncode != 0 or not findmnt.stdout.strip():
                        # If not mounted by device, try to find by mount point
                        mount_point = device if device.startswith('/mnt/') else f"/mnt/{os.path.basename(device)}"
                        if os.path.ismount(mount_point):
                            mount_point_to_unmount = mount_point
                        else:
                            self.terminal_output.append(f"Error: {device} is not mounted")
                            return
                    else:
                        mount_point_to_unmount = findmnt.stdout.strip()
                    
                    # Build a single command that does both unmount and directory removal
                    # This way we only need one pkexec prompt
                    script = f'''
                    #!/bin/bash
                    # Unmount the device
                    umount "{mount_point_to_unmount}" || exit $?
                    
                    # Only try to remove if it's in /mnt/ and exists
                    if [[ "{mount_point_to_unmount}" == /mnt/* ]] && [ -d "{mount_point_to_unmount}" ]; then
                        rmdir "{mount_point_to_unmount}" || echo "Note: Could not remove mount point: $?" >&2
                    fi
                    '''
                    
                    # Execute the combined command with a single pkexec
                    self.terminal_output.append(f"Unmounting {mount_point_to_unmount}...")
                    result = subprocess.run(
                        ['pkexec', 'bash', '-c', script],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode == 0:
                        self.terminal_output.append(f"Successfully unmounted {mount_point_to_unmount}")
                        # Check if mount point was removed
                        if not os.path.exists(mount_point_to_unmount):
                            self.terminal_output.append(f"Removed mount point: {mount_point_to_unmount}")
                    else:
                        error_msg = result.stderr.strip() or result.stdout.strip()
                        self.terminal_output.append(f"Failed to unmount {mount_point_to_unmount}: {error_msg}")
                        
                except Exception as e:
                    self.terminal_output.append(f"Error unmounting device: {str(e)}")
                    
            elif command.lower().startswith("format "):
                try:
                    args = command.split()
                    if len(args) < 2:
                        self.terminal_output.append("Usage: format <device> [filesystem] [label]")
                        self.terminal_output.append("Example: format sdb1")
                        self.terminal_output.append("Example: format /dev/sdb1 ext4 MY_DRIVE")
                        self.terminal_output.append("\nAvailable filesystems: ext4, ext3, ext2, ntfs, fat32, exfat, btrfs, xfs")
                        return
                    
                    # Handle device name (prepend /dev/ if not already a full path)
                    device = args[1] if args[1].startswith('/') else f"/dev/{args[1]}"
                    
                    # Default filesystem is ext4 if not specified
                    filesystem = args[2].lower() if len(args) > 2 else 'ext4'
                    
                    # Get label if provided
                    label = args[3] if len(args) > 3 else ''
                    
                    # Validate filesystem type
                    valid_filesystems = {
                        'ext4': 'ext4',
                        'ext3': 'ext3',
                        'ext2': 'ext2',
                        'ntfs': 'ntfs',
                        'fat32': 'vfat',  # vfat is used for fat32 in mkfs
                        'exfat': 'exfat',
                        'btrfs': 'btrfs',
                        'xfs': 'xfs'
                    }
                    
                    if filesystem not in valid_filesystems:
                        self.terminal_output.append(f"Error: Unsupported filesystem '{filesystem}'")
                        self.terminal_output.append("Available filesystems: " + ", ".join(valid_filesystems.keys()))
                        return
                    
                    # Get fsck and mkfs commands based on filesystem
                    fs_type = valid_filesystems[filesystem]
                    
                    # Check if device exists and is not mounted
                    if not os.path.exists(device):
                        self.terminal_output.append(f"Error: Device {device} does not exist")
                        return
                    
                    # Show warning and get confirmation
                    self.terminal_output.append("\n=== WARNING: This will ERASE ALL DATA on the device! ===\n")
                    self.terminal_output.append(f"Device: {device}")
                    self.terminal_output.append(f"Filesystem: {filesystem.upper()}")
                    if label:
                        self.terminal_output.append(f"Label: {label}")
                    self.terminal_output.append("\nDevice information:")
                    self.terminal_output.append(lsblk.stdout.strip())
                    
                    # Ask for confirmation
                    confirm = input("\nAre you sure you want to format this device? (yes/NO): ")
                    if confirm.lower() != 'yes':
                        self.terminal_output.append("Format operation cancelled.")
                        return
                    
                    # Build format command
                    script = f'''
                    #!/bin/bash
                    set -e  # Exit on any error
                    
                    # Unmount the device if mounted
                    umount "{device}" 2>/dev/null || true
                    
                    # Wipe filesystem signatures
                    wipefs -a "{device}" || exit $?
                    
                    # Create new filesystem
                    case "{fs_type}" in
                        ext4|ext3|ext2)
                            mkfs_cmd=("mkfs.{fs_type}" "-F")
                            if [ -n "{label}" ]; then
                                mkfs_cmd+=("-L" "{label}")
                            fi
                            "${{mkfs_cmd[@]}}" "{device}" || exit $?
                            ;;
                        vfat|fat32)
                            mkfs_cmd=("mkfs.vfat" "-F" "32")
                            if [ -n "{label}" ]; then
                                mkfs_cmd+=("-n" "{label}")
                            fi
                            "${{mkfs_cmd[@]}}" "{device}" || exit $?
                            ;;
                        ntfs)
                            mkfs_cmd=("mkfs.ntfs" "-f")
                            if [ -n "{label}" ]; then
                                mkfs_cmd+=("-L" "{label}")
                            fi
                            "${{mkfs_cmd[@]}}" "{device}" || exit $?
                            ;;
                        exfat)
                            mkfs_cmd=("mkfs.exfat")
                            if [ -n "{label}" ]; then
                                mkfs_cmd+=("-n" "{label}")
                            fi
                            "${{mkfs_cmd[@]}}" "{device}" || exit $?
                            ;;
                        btrfs)
                            mkfs_cmd=("mkfs.btrfs" "-f")
                            if [ -n "{label}" ]; then
                                mkfs_cmd+=("-L" "{label}")
                            fi
                            "${{mkfs_cmd[@]}}" "{device}" || exit $?
                            ;;
                        xfs)
                            mkfs_cmd=("mkfs.xfs" "-f")
                            if [ -n "{label}" ]; then
                                mkfs_cmd+=("-L" "{label}")
                            fi
                            "${{mkfs_cmd[@]}}" "{device}" || exit $?
                            ;;
                        *)
                            echo "Unsupported filesystem: {fs_type}" >&2
                            exit 1
                            ;;
                    esac
                    
                    # Set permissions (for non-Windows filesystems)
                    if [[ "{fs_type}" != @(ntfs|vfat|fat32|exfat) ]]; then
                        # Create a temporary mount point
                        temp_mount=$(mktemp -d)
                        
                        # Mount the new filesystem
                        mount "{device}" "$temp_mount" || exit $?
                        
                        # Set permissions
                        chmod -R 777 "$temp_mount" || true
                        chown -R $SUDO_UID:$SUDO_GID "$temp_mount" || true
                        
                        # Unmount
                        umount "$temp_mount"
                        rmdir "$temp_mount"
                    fi
                    
                    echo "Successfully formatted {device} with {filesystem.upper()}"
                    '''
                    
                    # Execute the format command with pkexec
                    self.terminal_output.append(f"\nFormatting {device} with {filesystem.upper()} filesystem...")
                    result = subprocess.run(
                        ['pkexec', 'bash', '-c', script],
                        capture_output=True,
                        text=True
                    )
                    
                    # Process the output
                    if result.returncode == 0:
                        self.terminal_output.append(f"Successfully formatted {device} with {filesystem.upper()}")
                        if result.stdout.strip():
                            self.terminal_output.append(result.stdout.strip())
                    else:
                        error_msg = result.stderr.strip() or result.stdout.strip()
                        self.terminal_output.append(f"Failed to format {device}:")
                        self.terminal_output.append(error_msg if error_msg else "Unknown error")
                    
                except Exception as e:
                    self.terminal_output.append(f"Error formatting device: {str(e)}")
                    
            elif command.lower().startswith("backup "):
                try:
                    args = command.split()
                    if len(args) < 3:
                        self.terminal_output.append("Usage: backup <source> <destination.iso> [options]")
                        self.terminal_output.append("Example: backup /home/user/Documents /backups/documents_backup.iso")
                        self.terminal_output.append("\nOptions:")
                        self.terminal_output.append("  --exclude=PATTERN  Exclude files matching PATTERN (can be used multiple times)")
                        self.terminal_output.append("  --volid=NAME       Set the volume ID (default: backup_YYYYMMDD)")
                        return
                    
                    source = os.path.abspath(args[1])
                    destination = os.path.abspath(args[2])
                    
                    # Check if source exists
                    if not os.path.exists(source):
                        self.terminal_output.append(f"Error: Source '{source}' does not exist")
                        return
                        
                    # Check if destination directory exists and is writable
                    dest_dir = os.path.dirname(destination)
                    if not os.path.exists(dest_dir):
                        try:
                            os.makedirs(dest_dir, exist_ok=True)
                        except Exception as e:
                            self.terminal_output.append(f"Error creating destination directory: {str(e)}")
                            return
                    
                    if not os.access(dest_dir, os.W_OK):
                        self.terminal_output.append(f"Error: No write permission in destination directory: {dest_dir}")
                        return
                    
                    # Parse options
                    exclude_patterns = []
                    volid = f"backup_{datetime.now().strftime('%Y%m%d')}"
                    
                    for arg in args[3:]:
                        if arg.startswith('--exclude='):
                            exclude_patterns.append(arg.split('=', 1)[1])
                        elif arg.startswith('--volid='):
                            volid = arg.split('=', 1)[1]
                    
                    # Show backup summary
                    self.terminal_output.append("\n=== Backup Summary ===")
                    self.terminal_output.append(f"Source:      {source}")
                    self.terminal_output.append(f"Destination: {destination}")
                    self.terminal_output.append(f"Volume ID:   {volid}")
                    if exclude_patterns:
                        self.terminal_output.append("Excluding:   " + ", ".join(exclude_patterns))
                    
                    # Calculate source size for progress
                    try:
                        du = subprocess.run(
                            ['du', '-sh', source],
                            capture_output=True, text=True
                        )
                        size_info = du.stdout.strip().split('\t')[0]
                        self.terminal_output.append(f"Source size: {size_info}")
                    except:
                        pass
                    
                    # Get free space in destination
                    try:
                        statvfs = os.statvfs(dest_dir)
                        free_space = statvfs.f_frsize * statvfs.f_bavail
                        free_space_gb = free_space / (1024**3)
                        self.terminal_output.append(f"Free space:  {free_space_gb:.2f} GB available")
                    except:
                        pass
                    
                    # Ask for confirmation
                    confirm = input("\nStart backup? (yes/NO): ")
                    if confirm.lower() != 'yes':
                        self.terminal_output.append("Backup cancelled.")
                        return
                    
                    # Build mkisofs command
                    mkisofs_cmd = [
                        'pkexec',
                        'mkisofs',
                        '-iso-level', '4',
                        '-l',  # Allow full 31-character filenames
                        '-r',  # Rock Ridge (Unix permissions)
                        '-J',  # Joliet (Windows compatibility)
                        '-joliet-long',  # Allow long Joliet filenames
                        '-V', volid,  # Volume ID
                        '-o', destination
                    ]
                    
                    # Add exclude patterns
                    for pattern in exclude_patterns:
                        mkisofs_cmd.extend(['-m', pattern])
                    
                    # Add source directory
                    mkisofs_cmd.append(source)
                    
                    # Show command for debugging
                    self.terminal_output.append("\nExecuting: " + " ".join(mkisofs_cmd[:5] + ['...'] + mkisofs_cmd[-3:]))
                    self.terminal_output.append("Creating ISO backup. This may take a while...")
                    
                    # Start the backup process
                    start_time = time.time()
                    process = subprocess.Popen(
                        mkisofs_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        universal_newlines=True
                    )
                    
                    # Monitor progress
                    while True:
                        output = process.stderr.readline()
                        if output == '' and process.poll() is not None:
                            break
                        if output:
                            # Show progress (filter out common mkisofs messages)
                            if 'done, estimate' in output or '%' in output:
                                self.terminal_output.append(output.strip())
                    
                    # Get return code and output
                    return_code = process.poll()
                    
                    if return_code == 0:
                        # Calculate backup size and time
                        duration = time.time() - start_time
                        try:
                            size_bytes = os.path.getsize(destination)
                            size_mb = size_bytes / (1024 * 1024)
                            speed = size_mb / duration if duration > 0 else 0
                            
                            self.terminal_output.append("\n✓ Backup completed successfully!")
                            self.terminal_output.append(f"Backup size: {size_mb:.2f} MB")
                            self.terminal_output.append(f"Time taken: {duration:.1f} seconds")
                            self.terminal_output.append(f"Average speed: {speed:.1f} MB/s")
                            self.terminal_output.append(f"Backup saved to: {destination}")
                        except Exception as e:
                            self.terminal_output.append(f"\n✓ Backup completed! (Could not get stats: {str(e)})")
                    else:
                        error = process.stderr.read().strip()
                        self.terminal_output.append(f"\n✗ Backup failed with error code {return_code}:")
                        if error:
                            self.terminal_output.append(error)
                    
                except Exception as e:
                    self.terminal_output.append(f"Error during backup: {str(e)}")
                    
            elif command.lower().startswith("restore "):
                try:
                    args = command.split()
                    if len(args) != 3:
                        self.terminal_output.append("Usage: restore <source.iso> <device>")
                        self.terminal_output.append("Example: restore backup.iso sda1")
                        self.terminal_output.append("Example: restore /path/to/backup.iso /dev/sdb")
                        return
                    
                    source = os.path.abspath(args[1])
                    device = args[2] if args[2].startswith('/dev/') else f"/dev/{args[2]}"
                    
                    # Check if source exists and is an ISO file
                    if not os.path.isfile(source):
                        self.terminal_output.append(f"Error: Source file '{source}' does not exist")
                        return
                        
                    if not source.lower().endswith(('.iso', '.ISO')):
                        self.terminal_output.append("Warning: Source file does not have an .iso extension")
                    
                    # Check if target device exists
                    if not os.path.exists(device):
                        self.terminal_output.append(f"Error: Device '{device}' does not exist")
                        return
                    
                    # Get device information
                    try:
                        lsblk = subprocess.run(
                            ['lsblk', '-o', 'NAME,SIZE,TYPE,MOUNTPOINT', device],
                            capture_output=True, text=True
                        )
                        if lsblk.returncode != 0:
                            self.terminal_output.append(f"Error getting device information for {device}")
                            return
                            
                        self.terminal_output.append("\n=== Restore Summary ===")
                        self.terminal_output.append(f"Source:      {source}")
                        self.terminal_output.append(f"Target:      {device}")
                        self.terminal_output.append("\nDevice information:")
                        self.terminal_output.append(lsblk.stdout.strip())
                        
                        # Check if device is mounted
                        findmnt = subprocess.run(
                            ['findmnt', '--source', device],
                            capture_output=True, text=True
                        )
                        
                        if findmnt.returncode == 0:
                            self.terminal_output.append("\n⚠️  WARNING: Device is currently mounted!")
                            self.terminal_output.append(findmnt.stdout.strip())
                            self.terminal_output.append("\nPlease unmount all partitions on this device before proceeding.")
                            return
                        
                    except Exception as e:
                        self.terminal_output.append(f"Error checking device: {str(e)}")
                        return
                    
                    # Show final warning and get confirmation
                    self.terminal_output.append("\n⚠️  WARNING: This will completely ERASE ALL DATA on the target device!")
                    confirm = input("\nAre you sure you want to continue? (type 'yes' to confirm): ")
                    if confirm.lower() != 'yes':
                        self.terminal_output.append("Restore cancelled.")
                        return
                    
                    # Build and execute the dd command
                    self.terminal_output.append("\nStarting restore operation. This may take a while...")
                    self.terminal_output.append(f"Writing {source} to {device}")
                    self.terminal_output.append("DO NOT INTERRUPT THIS PROCESS!")
                    
                    start_time = time.time()
                    
                    # Use pv if available for progress, fall back to dd
                    try:
                        # Try using pv for progress
                        pv_check = subprocess.run(['which', 'pv'], capture_output=True)
                        if pv_check.returncode == 0:
                            cmd = f'pkexec bash -c "pv -n {shlex.quote(source)} | dd of={shlex.quote(device)} bs=4M oflag=sync status=none"'
                            process = subprocess.Popen(
                                cmd,
                                shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                universal_newlines=True
                            )
                            
                            # Monitor progress
                            while True:
                                output = process.stderr.readline()
                                if output == '' and process.poll() is not None:
                                    break
                                if output.strip():
                                    self.terminal_output.append(f"Progress: {output.strip()}%")
                        else:
                            # Fall back to dd with status=progress
                            cmd = f'pkexec dd if={shlex.quote(source)} of={shlex.quote(device)} bs=4M status=progress oflag=sync'
                            process = subprocess.Popen(
                                cmd,
                                shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                universal_newlines=True
                            )
                            
                            # Output progress
                            for line in process.stdout:
                                if line.strip():
                                    self.terminal_output.append(f"Progress: {line.strip()}")
                    
                    except Exception as e:
                        self.terminal_output.append(f"Error during restore: {str(e)}")
                        return
                    
                    # Wait for completion
                    return_code = process.wait()
                    
                    if return_code == 0:
                        duration = time.time() - start_time
                        self.terminal_output.append("\n✓ Restore completed successfully!")
                        
                        # Get size of written data
                        try:
                            iso_size = os.path.getsize(source)
                            iso_size_gb = iso_size / (1024**3)
                            speed = iso_size_gb / (duration / 3600)  # GB/h
                            
                            self.terminal_output.append(f"Wrote:       {iso_size_gb:.2f} GB")
                            self.terminal_output.append(f"Time taken:  {duration:.1f} seconds")
                            self.terminal_output.append(f"Avg. speed:  {speed:.1f} GB/h")
                            
                            # Run partprobe to update partition table
                            subprocess.run(['pkexec', 'partprobe', device], capture_output=True)
                            
                        except Exception as e:
                            self.terminal_output.append(f"\n✓ Restore completed! (Could not get stats: {str(e)})")
                        
                        self.terminal_output.append("\nYou may need to run 'partprobe' or reboot for changes to take effect.")
                    else:
                        error = process.stderr.read().strip() if process.stderr else "Unknown error"
                        self.terminal_output.append(f"\n✗ Restore failed with error code {return_code}:")
                        if error:
                            self.terminal_output.append(error)
                    
                except Exception as e:
                    self.terminal_output.append(f"Error during restore: {str(e)}")
                    
            elif command.lower().startswith("benchmark "):
                # Format: benchmark <device>
                parts = command.split()
                if len(parts) < 2:
                    self.terminal_output.append("Usage: benchmark <device>")
                    return
                    
                device = self._resolve_device(parts[1])
                if not device:
                    self.terminal_output.append(f"Error: Device {parts[1]} not found")
                    return
                    
                self._run_benchmark(device)
                
            elif command.lower().startswith("test "):
                try:
                    parts = command.split()
                    if len(parts) < 2:
                        self.terminal_output.append("Error: Missing device. Usage: test <device> [test_type]")
                        self.terminal_output.append("Test types: quick, smart, badblocks, full (default: full)")
                        return
                        
                    device = parts[1] if parts[1].startswith('/dev/') else f"/dev/{parts[1]}"
                    test_type = parts[2].lower() if len(parts) > 2 else 'full'
                    
                    # Validate test type
                    valid_tests = ['quick', 'smart', 'badblocks', 'full']
                    if test_type not in valid_tests:
                        self.terminal_output.append(f"Error: Invalid test type '{test_type}'")
                        self.terminal_output.append("Available tests: " + ", ".join(valid_tests))
                        return
                    
                    # Check if device/partition exists
                    if not os.path.exists(device):
                        self.terminal_output.append(f"Error: Device/partition '{device}' does not exist")
                        return
                    
                    # Check if it's a block device or partition
                    dev_name = os.path.basename(device)
                    sys_block_path = "/sys/block"
                    
                    # Check if it's a whole disk (e.g., /dev/sda, /dev/nvme0n1)
                    is_whole_disk = os.path.exists(f"{sys_block_path}/{dev_name}")
                    
                    # Check if it's a partition (e.g., /dev/sda1, /dev/nvme0n1p1)
                    is_partition = False
                    
                    # Handle NVMe partitions (nvme0n1p1)
                    if 'nvme' in dev_name and 'p' in dev_name:
                        # For NVMe partitions (nvme0n1p1)
                        base_device = dev_name.rsplit('p', 1)[0]  # Get nvme0n1 from nvme0n1p1
                        is_partition = os.path.exists(f"{sys_block_path}/{base_device}")
                    # Handle regular partitions (sda1, vda1, etc.)
                    elif dev_name[-1].isdigit():
                        # For regular partitions (sda1 -> sda, vda1 -> vda)
                        base_device = dev_name.rstrip('0123456789')
                        is_partition = os.path.exists(f"{sys_block_path}/{base_device}")
                    
                    if not (is_whole_disk or is_partition):
                        self.terminal_output.append(f"Error: '{device}' is not a valid block device or partition")
                        self.terminal_output.append("  Make sure the device exists and you have permission to access it")
                        return
                    
                    # If it's a partition, check if it's mounted
                    if is_partition:
                        mount_check = subprocess.run(
                            ['findmnt', '--source', device, '-n', '--output=TARGET', '--noheadings'],
                            capture_output=True, text=True
                        )
                        if mount_check.returncode == 0 and mount_check.stdout.strip():
                            mount_points = [mp for mp in mount_check.stdout.strip().split('\n') if mp]
                            if mount_points:
                                self.terminal_output.append(f"Warning: {device} is currently mounted. Some tests may be affected.")
                                for mp in mount_points:
                                    self.terminal_output.append(f"  - Mounted at: {mp}")
                                self.terminal_output.append("  Note: It's recommended to unmount the filesystem before running tests.")
                    
                    # Get device information
                    self.terminal_output.append(f"\n=== Running {test_type.upper()} diagnostics on {device} ===\n")
                    
                    # Track which tests will run
                    total_tests = 3  # We always have 3 possible tests
                    test_count = 1
                    
                    # Run quick test
                    if test_type in ['quick', 'full']:
                        self.terminal_output.append(f"\n[{test_count}/{total_tests}] Quick Checks...")
                        self._run_quick_test(device)
                    else:
                        self.terminal_output.append(f"\n[{test_count}/{total_tests}] Quick Checks: Skipped")
                    test_count += 1
                    
                    # Run SMART test if requested
                    if test_type in ['smart', 'full']:
                        if self._is_smart_capable(device):
                            self.terminal_output.append(f"\n[{test_count}/{total_tests}] SMART Test...")
                            self._run_smart_test(device, test_type)
                        else:
                            self.terminal_output.append(f"\n[{test_count}/{total_tests}] SMART Test: Not supported on this device")
                    else:
                        self.terminal_output.append(f"\n[{test_count}/{total_tests}] SMART Test: Skipped")
                    test_count += 1
                    
                    # Run badblocks test if requested
                    if test_type in ['badblocks', 'full']:
                        self.terminal_output.append(f"\n[{test_count}/{total_tests}] Bad Blocks Check...")
                        self._run_badblocks_test(device, read_only=True)
                    else:
                        self.terminal_output.append(f"\n[{test_count}/{total_tests}] Bad Blocks Check: Skipped")
                    
                    self.terminal_output.append("\n✓ All tests completed")
                    
                except Exception as e:
                    self.terminal_output.append(f"Error during device test: {str(e)}")
                    
            elif command.lower() == "usage":
                try:
                    # Get disk usage with human-readable sizes
                    df = subprocess.run(
                        ['df', '-h', '--output=source,fstype,size,used,avail,pcent,target'],
                        capture_output=True, text=True
                    )
                    
                    if df.returncode == 0:
                        self.terminal_output.append("\nStorage Usage:")
                        self.terminal_output.append("=" * 80)
                        
                        # Get detailed partition information
                        df_lines = df.stdout.strip().split('\n')
                        header = df_lines[0]  # Header line
                        
                        # Format header for better readability
                        header_parts = header.split()
                        formatted_header = (
                            f"{header_parts[0]:<15} {header_parts[1]:<8} "
                            f"{header_parts[2]:>8} {header_parts[3]:>8} "
                            f"{header_parts[4]:>8} {header_parts[5]:>6} {header_parts[6]}"
                        )
                        
                        self.terminal_output.append(formatted_header)
                        self.terminal_output.append("-" * 80)
                        
                        # Process and format each line
                        for line in df_lines[1:]:
                            if not line.strip():
                                continue
                                
                            parts = line.split()
                            if len(parts) >= 7:
                                # Format the line with proper alignment
                                formatted_line = (
                                    f"{parts[0]:<15} {parts[1]:<8} "
                                    f"{parts[2]:>8} {parts[3]:>8} "
                                    f"{parts[4]:>8} {parts[5]:>6} {parts[6]}"
                                )
                                self.terminal_output.append(formatted_line)
                    else:
                        self.terminal_output.append("Error: Could not retrieve disk usage information")
                        
                    # Show inode usage if available
                    try:
                        df_inodes = subprocess.run(
                            ['df', '-i', '--output=source,itotal,iused,iavail,ipcent,target'],
                            capture_output=True, text=True
                        )
                        
                        if df_inodes.returncode == 0:
                            self.terminal_output.append("\nInode Usage:")
                            self.terminal_output.append("=" * 80)
                            self.terminal_output.append("Filesystem      Inodes  IUsed  IFree IUse% Mounted on")
                            self.terminal_output.append("-" * 80)
                            
                            # Skip the header line and process data
                            for line in df_inodes.stdout.strip().split('\n')[1:]:
                                if line.strip():
                                    self.terminal_output.append(line)
                    except Exception as e:
                        self.terminal_output.append(f"\nCould not retrieve inode information: {str(e)}")
                    
                    # Show disk I/O statistics
                    try:
                        iostat = subprocess.run(
                            ['iostat', '-d', '-x', '1', '1'],
                            capture_output=True, text=True
                        )
                        
                        if iostat.returncode == 0:
                            self.terminal_output.append("\nDisk I/O Statistics (last second):")
                            self.terminal_output.append("=" * 80)
                            
                            # Find the start of the device statistics
                            lines = iostat.stdout.strip().split('\n')
                            start_idx = -1
                            for i, line in enumerate(lines):
                                if 'Device' in line and 'r/s' in line:
                                    start_idx = i
                                    break
                            
                            if start_idx >= 0 and start_idx + 1 < len(lines):
                                # Print header and data
                                self.terminal_output.append(lines[start_idx])  # Header
                                self.terminal_output.append(lines[start_idx + 1])  # Data
                    except Exception as e:
                        self.terminal_output.append(f"\nCould not retrieve I/O statistics: {str(e)}")
                    
                    # Show disk usage summary for home directory
                    try:
                        du = subprocess.run(
                            ['du', '-sh', os.path.expanduser('~')],
                            capture_output=True, text=True
                        )
                        
                        if du.returncode == 0:
                            size, path = du.stdout.strip().split('\t')
                            self.terminal_output.append(f"\nHome Directory Usage: {size} in {path}")
                    except:
                        pass
                        
                except Exception as e:
                    self.terminal_output.append(f"Error getting storage usage: {str(e)}")
                    
            elif command.lower() == "update":
                self.terminal_output.append("Starting update process...")
                self.terminal_output.append("")
                
                try:
                    # Check if pip is available
                    try:
                        pip_check = subprocess.run(
                            ['pip', '--version'],
                            capture_output=True,
                            text=True
                        )
                        if pip_check.returncode != 0:
                            raise Exception("pip is not installed")
                    except Exception as e:
                        self.terminal_output.append("Error: pip is required for updates. Please install pip first.")
                        return
                    
                    # Update Python packages
                    self.terminal_output.append("\nUpdating Python packages...")
                    requirements_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'requirements.txt')
                    update_cmd = [
                        sys.executable, '-m', 'pip', 'install',
                        '--upgrade', '-r', requirements_path,
                        '--break-system-packages',  # Added as per user's preference
                        '--user'  # Install to user site-packages
                    ]
                    
                    # Install system packages using pkexec
                    self.terminal_output.append("\nInstalling system packages (requires admin privileges)...")
                    system_pkgs = ["smartmontools", "wipe", "dcfldd"]
                    
                    # Create a temporary script to run the commands
                    script = """#!/bin/bash
                    echo "Updating package lists..."
                    apt-get update -q
                    
                    # Install each package
                    for pkg in %s; do
                        if ! dpkg -s "$pkg" &>/dev/null; then
                            echo "Installing $pkg..."
                            apt-get install -y "$pkg"
                        else
                            echo "$pkg is already installed."
                        fi
                    done
                    
                    echo "System packages installation complete."
                    """ % " ".join(f'"{pkg}"' for pkg in system_pkgs)
                    
                    # Write the script to a temporary file
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sh') as f:
                        f.write(script)
                        script_path = f.name
                    
                    # Make the script executable
                    os.chmod(script_path, 0o755)
                    
                    # Run the script with pkexec
                    try:
                        pkexec_proc = subprocess.Popen(
                            ['pkexec', 'bash', script_path],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
                        )
                        
                        # Stream output with real-time updates
                        while True:
                            output = pkexec_proc.stdout.readline()
                            if output == '':
                                if pkexec_proc.poll() is not None:
                                    break
                                QApplication.processEvents()  # Process GUI events
                                time.sleep(0.1)  # Small delay to prevent busy-waiting
                                continue
                            if output:
                                self.terminal_output.append(f"[System] {output.strip()}")
                                cursor = self.terminal_output.textCursor()
                                cursor.movePosition(cursor.MoveOperation.End)
                                self.terminal_output.setTextCursor(cursor)
                                QApplication.processEvents()  # Update the GUI
                        
                        # Check for errors
                        _, stderr = pkexec_proc.communicate()
                        if pkexec_proc.returncode != 0:
                            self.terminal_output.append(f"Error installing system packages: {stderr.strip()}")
                            self.terminal_output.append("Please install them manually with:")
                            self.terminal_output.append("  sudo apt-get update && sudo apt-get install -y smartmontools wipe dcfldd")
                    except Exception as e:
                        self.terminal_output.append(f"Error running system package installer: {str(e)}")
                        self.terminal_output.append("Please install the packages manually:")
                        self.terminal_output.append("  sudo apt-get update && sudo apt-get install -y smartmontools wipe dcfldd")
                    finally:
                        # Clean up the temporary script
                        try:
                            os.unlink(script_path)
                        except:
                            pass
                    
                    self.terminal_output.append("\nProceeding with Python package updates...")
                    
                    update_process = subprocess.Popen(
                        update_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        cwd=os.path.dirname(os.path.abspath(__file__))
                    )
                    
                    # Stream output with real-time updates
                    while True:
                        output = update_process.stdout.readline()
                        if output == '':
                            if update_process.poll() is not None:
                                break
                            QApplication.processEvents()  # Process GUI events
                            time.sleep(0.1)  # Small delay to prevent busy-waiting
                            continue
                        if output:
                            self.terminal_output.append(output.strip())
                            cursor = self.terminal_output.textCursor()
                            cursor.movePosition(cursor.MoveOperation.End)
                            self.terminal_output.setTextCursor(cursor)
                            QApplication.processEvents()  # Update the GUI
                    
                    # Check for errors
                    stdout, stderr = update_process.communicate()
                    if update_process.returncode != 0:
                        self.terminal_output.append("Error updating packages:")
                        if stderr:
                            self.terminal_output.append(stderr.strip())
                        if stdout:
                            self.terminal_output.append(stdout.strip())
                    else:
                        self.terminal_output.append("Python packages updated successfully!")
                    
                    # Check for Git updates if this is a Git repository
                    try:
                        # Check if git is available
                        git_check = subprocess.run(
                            ['git', '--version'],
                            capture_output=True,
                            text=True
                        )
                        
                        if git_check.returncode == 0:
                            current_dir = os.path.dirname(os.path.abspath(__file__))
                            
                            # Check if this is a git repository
                            if os.path.exists(os.path.join(current_dir, '.git')):
                                self.terminal_output.append("")
                                self.terminal_output.append("Checking for application updates...")
                                
                                # Fetch latest changes
                                fetch = subprocess.run(
                                    ['git', 'fetch'],
                                    cwd=current_dir,
                                    capture_output=True,
                                    text=True
                                )
                                
                                if fetch.returncode != 0:
                                    self.terminal_output.append("Warning: Failed to fetch updates from Git")
                                    self.terminal_output.append(fetch.stderr)
                                else:
                                    # Check for updates
                                    status = subprocess.run(
                                        ['git', 'status', '-uno'],
                                        cwd=current_dir,
                                        capture_output=True,
                                        text=True
                                    )
                                    
                                    if "Your branch is behind" in status.stdout:
                                        self.terminal_output.append("Application updates available!")
                                        self.terminal_output.append("Updating to the latest version...")
                                        
                                        # Pull the latest changes
                                        pull = subprocess.run(
                                            ['git', 'pull'],
                                            cwd=current_dir,
                                            capture_output=True,
                                            text=True
                                        )
                                        
                                        if pull.returncode == 0:
                                            self.terminal_output.append("Successfully updated application!")
                                            self.terminal_output.append("Please restart the application to apply changes.")
                                        else:
                                            self.terminal_output.append("Error updating application:")
                                            self.terminal_output.append(pull.stderr)
                                    else:
                                        self.terminal_output.append("BLACKSTORM is up to date!")
                    except Exception as e:
                        self.terminal_output.append(f"Warning: Could not check for application updates: {str(e)}")
                    
                    self.terminal_output.append("")
                    self.terminal_output.append("Update process completed!")
                    
                except Exception as e:
                    self.terminal_output.append(f"Error during update: {str(e)}")
                    import traceback
                    self.terminal_output.append(traceback.format_exc())
                    
            elif command.lower() == "shutdown":
                # Get the parent window (BlackStormLauncher) and close it
                parent = self.parent()
                while parent is not None and not isinstance(parent, QMainWindow):
                    parent = parent.parent()
                
                if parent is not None:
                    reply = QMessageBox.question(
                        self,
                        'Confirm Shutdown',
                        'Are you sure you want to shut down BLACKSTORM?',
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )
                    
                    if reply == QMessageBox.StandardButton.Yes:
                        self.terminal_output.append("Shutting down BLACKSTORM...")
                        QTimer.singleShot(1000, parent.close)  # Give time for the message to be displayed
                        return
                else:
                    self.terminal_output.append("Error: Could not find main application window")
                    
            elif command.startswith("!"):
                # Execute system command
                try:
                    result = subprocess.run(
                        command[1:], 
                        shell=True, 
                        capture_output=True, 
                        text=True
                    )
                    output = result.stdout if result.stdout else result.stderr
                    if output:
                        self.terminal_output.append(output)
                except Exception as e:
                    self.terminal_output.append(f"Command execution failed: {str(e)}")
            
            # Storage Management Commands
            elif command.startswith("mount "):
                device = command[6:].strip()
                self.terminal_output.append(f"Mounted device: {device} (simulated)")
                
            elif command.startswith("unmount "):
                device = command[8:].strip()
                self.terminal_output.append(f"Unmounted device: {device} (simulated)")
                
            elif command.startswith("format "):
                device = command[7:].strip()
                self.terminal_output.append(f"Formatting device: {device} (simulated)")
                self.terminal_output.append("Format complete (simulated)")
                
            elif command == "scan":
                self.terminal_output.append("Scanning for new storage devices... (simulated)")
                self.terminal_output.append("No new devices found (simulated)")
                
            elif command == "usage":
                self.terminal_output.append("Storage Usage (simulated):")
                self.terminal_output.append("Device       Size  Used  Avail Use% Mounted on")
                self.terminal_output.append("/dev/sda1    100G   45G    55G  45% /mnt/data")
                
            elif command.startswith("backup "):
                args = command[7:].strip().split()
                if len(args) >= 2:
                    src, dst = args[0], ' '.join(args[1:])
                    self.terminal_output.append(f"Creating backup from {src} to {dst} (simulated)")
                    self.terminal_output.append("Backup completed successfully (simulated)")
                else:
                    self.terminal_output.append("Error: Please specify source and destination")
                    
            elif command.startswith("restore "):
                args = command[8:].strip().split()
                if len(args) >= 2:
                    src, dst = args[0], ' '.join(args[1:])
                    self.terminal_output.append(f"Restoring from {src} to {dst} (simulated)")
                    self.terminal_output.append("Restore completed successfully (simulated)")
                else:
                    self.terminal_output.append("Error: Please specify backup source and restore destination")
            
            # Diagnostics & Maintenance Commands
            elif command.startswith("test "):
                device = command[5:].strip()
                self.terminal_output.append(f"Running diagnostics on {device} (simulated)")
                self.terminal_output.append("Diagnostics complete. No issues found. (simulated)")
                
            elif command.startswith("benchmark "):
                device = command[10:].strip()
                self.terminal_output.append(f"Benchmarking {device} (simulated)")
                self.terminal_output.append("Sequential Read:  550 MB/s (simulated)")
                self.terminal_output.append("Sequential Write: 480 MB/s (simulated)")
                self.terminal_output.append("4K Random Read:   45.2 MB/s (simulated)")
                self.terminal_output.append("4K Random Write:  38.7 MB/s (simulated)")
                
            elif command.startswith("verify "):
                device = command[7:].strip()
                self.terminal_output.append(f"Verifying integrity of {device} (simulated)")
                self.terminal_output.append("Verification complete. No errors found. (simulated)")
                
            elif command.startswith("recover "):
                device = command[8:].strip()
                self.terminal_output.append(f"Attempting data recovery on {device} (simulated)")
                self.terminal_output.append("Recovery completed. 12 files recovered. (simulated)")
                
            elif command == "logs":
                self.terminal_output.append("=== Application Logs (simulated) ===")
                self.terminal_output.append("[2025-06-05 01:30:15] INFO: System initialized")
                self.terminal_output.append("[2025-06-05 01:30:20] INFO: 3 storage devices detected")
                self.terminal_output.append("[2025-06-05 01:30:25] INFO: All systems nominal")
            
            # Security & Automation Commands
            elif command.startswith("encrypt "):
                args = command[8:].strip().split()
                if len(args) >= 2:
                    device, password = args[0], ' '.join(args[1:])
                    self.terminal_output.append(f"Encrypting {device} (simulated)")
                    self.terminal_output.append("Encryption completed successfully (simulated)")
                else:
                    self.terminal_output.append("Error: Please specify device and password")
                    
            elif command.startswith("decrypt "):
                args = command[8:].strip().split()
                if len(args) >= 2:
                    device, password = args[0], ' '.join(args[1:])
                    self.terminal_output.append(f"Decrypting {device} (simulated)")
                    self.terminal_output.append("Decryption completed successfully (simulated)")
                else:
                    self.terminal_output.append("Error: Please specify device and password")
                    
            elif command.startswith("schedule "):
                args = command[9:].strip().split(' ', 1)
                if len(args) == 2:
                    time, cmd = args
                    self.terminal_output.append(f"Scheduled command '{cmd}' to run at {time} (simulated)")
                else:
                    self.terminal_output.append("Error: Please specify time and command")
                    
            elif command.startswith("script "):
                filename = command[7:].strip()
                self.terminal_output.append(f"Running script: {filename} (simulated)")
                self.terminal_output.append("Script completed successfully (simulated)")
                
            elif command.startswith("export "):
                args = command[7:].strip().split(' ', 1)
                if len(args) == 2:
                    data, filename = args
                    self.terminal_output.append(f"Exported {data} to {filename} (simulated)")
                else:
                    self.terminal_output.append("Error: Please specify data and filename")
                    
            elif command.startswith("import "):
                filename = command[7:].strip()
                self.terminal_output.append(f"Importing from {filename} (simulated)")
                self.terminal_output.append("Import completed successfully (simulated)")
                
            elif command == "config":
                self.terminal_output.append("=== Configuration (simulated) ===")
                self.terminal_output.append("autosave: true")
                self.terminal_output.append("theme: dark")
                self.terminal_output.append("notifications: enabled")
                self.terminal_output.append("language: en_US")
                
            else:
                self.terminal_output.append(f"Command not found: {command}")
                
        except Exception as e:
            self.terminal_output.append(f"Error: {str(e)}")
            self.terminal_output.append(f"Command not found: {command}")
        
        # Add new prompt
        self.terminal_output.append(">")
        
        # Clear input
        self.cmd_input.clear()

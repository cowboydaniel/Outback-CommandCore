#!/usr/bin/env python3
"""PC Tools Module - Compatibility Bridge

This module serves as a bridge to the refactored PC Tools module in nest.ui.modules.pc_tools
It allows the main Nest application to continue to import from nest.ui.pc_tools while
we transition to the new modular architecture.

This module can also run as a standalone application.
"""

import os
import sys
import time
import platform
import os
import time
import datetime
import psutil
import threading
import tempfile
import re
import math
import glob
import shutil
import json
import logging
import importlib.util
import tkinter as tk
import socket
import struct
import subprocess
from tkinter import ttk, scrolledtext, messagebox
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import tempfile
import getpass
import shlex

def check_and_setup_sudoers(parent=None) -> Tuple[bool, str]:
    """
    Check if sudoers setup is needed and run it with a GUI prompt if required.
    
    Args:
        parent: Parent window for the dialog
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Check if we already have the required permissions
        test_cmd = ['sudo', '-n', 'smartctl', '--version']
        result = subprocess.run(test_cmd, capture_output=True, text=True)
        
        # If the command succeeded, we already have passwordless sudo
        if result.returncode == 0:
            return True, "Already configured with passwordless sudo access"
            
        # If we get here, we need to set up passwordless sudo
        if parent:
            response = messagebox.askyesno(
                "Elevated Permissions Required",
                "PC Tools requires elevated permissions to access hardware information.\n\n"
                "Would you like to set up passwordless sudo access now?\n\n"
                "You will be prompted for your password once.",
                parent=parent
            )
            if not response:
                return False, "User declined to set up passwordless sudo"
        
        # Get the path to the setup script
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'setup_sudoers.sh')
        
        if not os.path.exists(script_path):
            return False, f"Setup script not found at {script_path}"
            
        # Make sure the script is executable
        os.chmod(script_path, 0o755)
        
        # Get the current username
        username = getpass.getuser()
        
        # Run the setup script with pkexec for GUI password prompt
        cmd = ['pkexec', '--user', 'root', 'bash', script_path]
        
        # Show a message that we're about to prompt for password
        if parent:
            messagebox.showinfo(
                "Authentication Required",
                f"You will now be prompted for your password to set up passwordless sudo access for user '{username}'.",
                parent=parent
            )
        
        # Run the command
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return True, "Successfully set up passwordless sudo access"
        else:
            error_msg = f"Failed to set up passwordless sudo: {result.stderr or 'Unknown error'}"
            if parent:
                messagebox.showerror("Setup Failed", error_msg, parent=parent)
            return False, error_msg
            
    except Exception as e:
        error_msg = f"Error setting up passwordless sudo: {str(e)}"
        if parent:
            messagebox.showerror("Error", error_msg, parent=parent)
        return False, error_msg

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Function to check and install required system packages
def check_and_install_dependencies():
    """Check for required system packages and install them if missing"""
    logging.info("Checking for required system packages...")
    
    # Define required tools by distro family
    required_tools = {
        'debian': {
            'smartmontools': 'smartctl',
            'lm-sensors': 'sensors',
            'dmidecode': 'dmidecode',
            'lshw': 'lshw',
            'pciutils': 'lspci',
            'parted': 'parted',
            'iw': 'iw',
            'ethtool': 'ethtool',
            'iputils-ping': 'ping',
            'speedtest-cli': 'speedtest-cli',
            'python3-tk': None,  # No specific binary to check
            'sudo': 'sudo',
            'libcap2-bin': 'setcap'  # For setting capabilities
        },
        'redhat': {
            'smartmontools': 'smartctl',
            'lm_sensors': 'sensors',
            'dmidecode': 'dmidecode',
            'lshw': 'lshw',
            'pciutils': 'lspci',
            'parted': 'parted',
            'iw': 'iw',
            'ethtool': 'ethtool',
            'iputils': 'ping',
            'speedtest-cli': 'speedtest-cli',
            'python3-tkinter': None,  # No specific binary to check
            'sudo': 'sudo',
            'libcap2': 'setcap'  # For setting capabilities on RedHat-based systems
        }
    }
    
    # Detect distro family
    distro_family = None
    try:
        if os.path.exists('/etc/debian_version'):
            distro_family = 'debian'
        elif os.path.exists('/etc/redhat-release') or os.path.exists('/etc/fedora-release'):
            distro_family = 'redhat'
        else:
            # Try to use the distro module if available
            try:
                import distro
                dist_id = distro.id()
                if dist_id in ['ubuntu', 'debian', 'linuxmint', 'pop']:
                    distro_family = 'debian'
                elif dist_id in ['fedora', 'rhel', 'centos', 'rocky', 'almalinux']:
                    distro_family = 'redhat'
            except ImportError:
                pass
    except Exception as e:
        logging.error(f"Error detecting Linux distribution: {e}")
    
    if not distro_family or platform.system() != 'Linux':
        logging.info("Auto-installation only supported on Linux. Skipping dependency check.")
        return
    
    # Determine installation command
    if distro_family == 'debian':
        install_cmd = 'apt-get -y install'
    elif distro_family == 'redhat':
        install_cmd = 'dnf -y install'
    
    # Check for missing tools
    missing_tools = []
    for package, binary in required_tools[distro_family].items():
        if binary:
            # Check if binary exists in PATH
            which_cmd = f"which {binary} 2>/dev/null"
            if subprocess.run(which_cmd, shell=True).returncode != 0:
                missing_tools.append(package)
        else:
            # For packages without a specific binary to check
            # We could implement more sophisticated checks here
            # For now, just add python3-tk/python3-tkinter if tkinter isn't available
            if package in ['python3-tk', 'python3-tkinter']:
                try:
                    import tkinter
                except ImportError:
                    missing_tools.append(package)
    
    # Install missing tools if any
    if missing_tools:
        # Always use sudo for package installation
        cmd = f"sudo {install_cmd} {' '.join(missing_tools)}"
        print(f"Installing missing tools with: {cmd}")
        try:
            subprocess.run(cmd, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to install packages: {e}")
            print("Please make sure you have sudo permissions or install the following packages manually:")
            print(" ".join(missing_tools))
            return
        except Exception as e:
            logging.error(f"Error installing system packages: {e}")
    else:
        logging.info("All required system packages are already installed")

def setup_passwordless_sudo():
    """Set up passwordless sudo for required commands.
    
    This function creates a temporary script to configure sudoers and runs it with sudo.
    The user will be prompted for their password once.
    """
    import tempfile
    import getpass
    import stat
    
    # Check if we're already root
    if os.geteuid() == 0:
        return True
        
    # Create a temporary script
    script_content = """#!/bin/bash
# This script will be created temporarily to set up passwordless sudo
set -e

# Get the current user who invoked sudo
CURRENT_USER=$(who am i | awk '{print $1}')
if [ -z "$CURRENT_USER" ]; then
    CURRENT_USER=$(whoami)
fi

echo "Setting up passwordless sudo for user: $CURRENT_USER"

# Create a sudoers file
SUDOERS_FILE="/etc/sudoers.d/99-nest-pc-tools"

# Check if the file already exists and back it up
if [ -f "$SUDOERS_FILE" ]; then
    echo "Backing up existing sudoers file to ${SUDOERS_FILE}.bak"
    cp "$SUDOERS_FILE" "${SUDOERS_FILE}.bak"
fi

# Create the sudoers file
echo "# Allow $CURRENT_USER to run required commands without a password" > "$SUDOERS_FILE"
echo "# This file was automatically generated by Nest PC Tools" >> "$SUDOERS_FILE"
echo "# It will be automatically removed when the application is uninstalled" >> "$SUDOERS_FILE"
echo "" >> "$SUDOERS_FILE"

# Add commands that need passwordless sudo
cat << 'EOT' >> "$SUDOERS_FILE"
# Disk and storage commands
CURRENT_USER ALL=(root) NOPASSWD: /usr/sbin/smartctl *
CURRENT_USER ALL=(root) NOPASSWD: /sbin/hdparm *
CURRENT_USER ALL=(root) NOPASSWD: /sbin/fdisk *
CURRENT_USER ALL=(root) NOPASSWD: /sbin/parted *
CURRENT_USER ALL=(root) NOPASSWD: /sbin/lsblk *
CURRENT_USER ALL=(root) NOPASSWD: /bin/mount *
CURRENT_USER ALL=(root) NOPASSWD: /bin/umount *
CURRENT_USER ALL=(root) NOPASSWD: /sbin/wipefs *
CURRENT_USER ALL=(root) NOPASSWD: /sbin/sfdisk *
CURRENT_USER ALL=(root) NOPASSWD: /usr/bin/lshw *
CURRENT_USER ALL=(root) NOPASSWD: /usr/bin/dmidecode *
CURRENT_USER ALL=(root) NOPASSWD: /usr/sbin/hddtemp *
CURRENT_USER ALL=(root) NOPASSWD: /usr/bin/lspci *
CURRENT_USER ALL=(root) NOPASSWD: /usr/bin/lsusb *
CURRENT_USER ALL=(root) NOPASSWD: /usr/bin/killall *
CURRENT_USER ALL=(root) NOPASSWD: /usr/bin/pkexec *

# Allow setting capabilities on smartctl
CURRENT_USER ALL=(root) NOPASSWD: /usr/sbin/setcap *

# Allow reading system logs
CURRENT_USER ALL=(root) NOPASSWD: /usr/bin/journalctl *
CURRENT_USER ALL=(root) NOPASSWD: /bin/cat /var/log/*
EOT

# Replace CURRENT_USER with actual username
sed -i "s/CURRENT_USER/$CURRENT_USER/g" "$SUDOERS_FILE"

# Set the correct permissions on the sudoers file
chmod 0440 "$SUDOERS_FILE"

# Set capabilities on smartctl to allow non-root access to SMART data
if [ -x "/usr/sbin/smartctl" ]; then
    setcap cap_sys_rawio,cap_dac_override,cap_sys_admin,cap_sys_nice+ep /usr/sbin/smartctl 2>/dev/null || true
    echo "Set capabilities on smartctl for non-root access"
fi

echo ""
echo "Passwordless sudo setup complete!"
echo "You may need to log out and log back in for all changes to take effect."
"""

    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            script_path = f.name
            f.write(script_content)
        
        # Make the script executable
        os.chmod(script_path, 0o755)
        
        # Run the script with sudo
        print("Setting up passwordless sudo. You may be prompted for your password...")
        result = subprocess.run(['sudo', 'bash', script_path], 
                              stderr=subprocess.PIPE,
                              stdout=subprocess.PIPE,
                              text=True)
        
        # Clean up the temporary script
        try:
            os.unlink(script_path)
        except:
            pass
            
        if result.returncode == 0:
            print("Successfully set up passwordless sudo!")
            return True
        else:
            print("Failed to set up passwordless sudo:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"Error setting up passwordless sudo: {e}")
        return False

# Run dependency check when module is imported
if platform.system() == 'Linux':
    check_and_install_dependencies()
    # Set up passwordless sudo on first run
    if not os.path.exists("/etc/sudoers.d/99-nest-pc-tools"):
        setup_passwordless_sudo()

# Get the absolute path to this file
THIS_FILE = os.path.abspath(__file__)

# Get the ui directory (parent of this file)
UI_DIR = os.path.dirname(THIS_FILE)

# Get the nest directory (parent of ui)
NEST_DIR = os.path.dirname(UI_DIR)

# Get the project root directory (parent of nest)
ROOT_DIR = os.path.dirname(NEST_DIR)

# Add the project root to the Python path if not already there
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Ensure log directory exists
os.makedirs(os.path.join(ROOT_DIR, 'logs'), exist_ok=True)

# Define placeholder PC Tools module class for fallback
class PCToolsModule(ttk.Frame):
    """PC Tools module for Nest"""
    # Class variables for caching SMART data with timestamp support
    smart_data_cache = {}
    smart_cache_timestamps = {}  # Store timestamps for each drive's cache entry
    smart_cache_max_age = 600  # Default cache lifetime in seconds (10 minutes)
    sudo_authenticated = False  # Track if we've authenticated with sudo
    smartctl_capabilities_set = False  # Track if smartctl capabilities have been set
    
    def __init__(self, parent, current_user=None):
        """Initialize the PC Tools module with enhanced caching and performance tracking.
        
        Args:
            parent: Parent widget
            current_user: Dictionary containing current user information
        """
        # Check dependencies when module is instantiated (in case import-time check was missed)
        if platform.system() == 'Linux':
            check_and_install_dependencies()
            
            # Check and set up passwordless sudo when the module is first instantiated
            if not hasattr(PCToolsModule, '_sudo_checked'):
                # Get the root window from the parent if it exists
                root_window = None
                if parent:
                    root_window = parent.winfo_toplevel()
                success, message = check_and_setup_sudoers(root_window)
                logging.info(f"Sudo setup check: {message}")
                PCToolsModule._sudo_checked = True
            
        super().__init__(parent, padding=10)
        self.parent = parent
        
        # Timer for live updates
        self.refresh_timer_id = None
        
        # Initialize cache configuration
        self.cache_config = {
            'smart_cache_max_age': PCToolsModule.smart_cache_max_age,  # Default from class variable
            'refresh_on_tab_switch': True  # Refresh data when switching tabs
        }
        self.current_user = current_user or {}
        self.threads = []  # Keep track of threads
        self.log_text = None
        
        # Session start time for performance tracking
        self.session_start_time = time.time()
        
        # Initialize performance metrics
        self.performance_metrics = {
            'startup_time': 0,
            'tab_switch_times': [],
            'data_load_times': {}
        }
        
        # Initialize colors
        self.colors = {
            "primary": "#017E84",  # RepairDesk teal (official brand color)
            "primary_dark": "#016169", # Darker teal for hover states
            "secondary": "#4CAF50",
            "warning": "#FF9800",
            "danger": "#F44336",
            "background": "#F5F5F5",
            "card_bg": "#FFFFFF",
            "text_primary": "#212121",
            "text_secondary": "#757575",
            "border": "#E0E0E0",
            "highlight": "#E6F7F7",
            "accent": "#00B8D4"
        }
        
        # Initialize shared state with additional metadata
        self.shared_state = {
            # User and system information
            "current_user": current_user,
            "system_info": {},
            "diagnostic_results": {},
            "benchmark_results": {},
            "colors": self.colors,
            "refresh_callbacks": {},  # For live updates in different tabs
            
            # Metadata and tracking
            "_session_id": f"pc_tools_session_{int(time.time())}",
            "_timestamps": {},
            "_performance": self.performance_metrics,
            "_cache_config": {
                "enabled": True,
                "ttl": 300,  # 5 minutes default cache lifetime
                "refresh_on_tab_switch": True
            }
        }
        
        # Cache configuration
        self.cache_config = self.shared_state["_cache_config"]
        
        # Initialize tab instances
        self.tab_instances = {}
        
        # Create the PC Tools interface
        self.create_widgets()
    
    def create_widgets(self):
        # Create main container frame that fills the entire window
        main_container = ttk.Frame(self)
        main_container.pack(fill="both", expand=True)
        
        # Ensure the main container uses all available space
        self.pack_propagate(False)
        
        # Start the live refresh timer (every 1000 ms = 1 second)
        self.start_live_refresh()
        
        # Create a simple frame for content
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill="both", expand=True)
        
        # Initialize status bar first to ensure it's available for other methods
        self.status_bar = ttk.Frame(content_frame, style="StatusBar.TFrame")
        self.status_bar.pack(side="bottom", fill="x")
        
        # Status message (left side)
        self.status_message = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(
            self.status_bar,
            textvariable=self.status_message,
            anchor="w",
            style="StatusBar.TLabel"
        )
        self.status_label.pack(side="left", padx=8, fill="x", expand=True)
        
        # Last update time (right side)
        self.last_update = tk.StringVar()
        self.update_time_label = ttk.Label(
            self.status_bar,
            textvariable=self.last_update,
            anchor="e",
            style="StatusBar.TLabel"
        )
        self.update_time_label.pack(side="right", padx=8)
        
        # Main header with logo
        header_frame = ttk.Frame(content_frame)
        header_frame.pack(fill="x", padx=10, pady=5)

        header_label = ttk.Label(
            header_frame, 
            text="PC Tools & Diagnostics", 
            font=("Arial", 14, "bold"),
            foreground=self.colors["primary"]
        )
        header_label.pack(side="left", pady=10)
        
        # Setup status frame for tools status only (similar to Android Tools)
        self.setup_status_frame = ttk.LabelFrame(content_frame, text="Tools Status")
        self.setup_status_frame.pack(fill="x", padx=10, pady=5, expand=False)
        
        # Check Smart Tools availability
        smartctl_available = shutil.which("smartctl") is not None
        tools_status = "✅ Available" if smartctl_available else "❌ Not Available"
        
        self.smartctl_label = ttk.Label(
            self.setup_status_frame, 
            text=f"SMART Diagnostics Tools: {tools_status}", 
            font=("Arial", 10),
            foreground=self.colors["text_primary"]
        )
        self.smartctl_label.pack(anchor="w", padx=5, pady=2)
        
        # Add status for additional tools if needed
        lshw_available = shutil.which("lshw") is not None
        lshw_status = "✅ Available" if lshw_available else "❌ Not Available"
        
        self.lshw_label = ttk.Label(
            self.setup_status_frame, 
            text=f"Hardware Info Tools: {lshw_status}", 
            font=("Arial", 10),
            foreground=self.colors["text_primary"]
        )
        self.lshw_label.pack(anchor="w", padx=5, pady=2)
        
        # Status message (left side)
        self.status_message = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(
            self.status_bar,
            textvariable=self.status_message,
            anchor="w",
            style="StatusBar.TLabel"
        )
        self.status_label.pack(side="left", padx=8, fill="x", expand=True)
        
        # Last update time (right side)
        self.last_update = tk.StringVar()
        self.update_time_label = ttk.Label(
            self.status_bar,
            textvariable=self.last_update,
            anchor="e",
            style="StatusBar.TLabel"
        )
        self.update_time_label.pack(side="right", padx=8)
        
        # Configure styles
        self._configure_styles()
        
        # Create the main notebook for the two primary tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Initialize tabs dictionary
        self.tabs = {}
        
        # Create the two main tabs
        self.device_info_tab = ttk.Frame(self.notebook)
        self.pc_tools_tab = ttk.Frame(self.notebook)
        
        # Add main tabs to the notebook
        self.notebook.add(self.device_info_tab, text="Device Info")
        self.notebook.add(self.pc_tools_tab, text="PC Tools")
        
        # Create a notebook for Device Info subtabs
        self.device_notebook = ttk.Notebook(self.device_info_tab)
        self.device_notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create Device Info subtabs
        device_subtabs = ["System", "Hardware", "Storage", "Network"]
        self.device_tabs = {}
        
        for name in device_subtabs:
            tab = ttk.Frame(self.device_notebook)
            self.device_notebook.add(tab, text=name)
            self.device_tabs[name.lower()] = tab
        
        # Create a notebook for PC Tools subtabs
        self.tools_notebook = ttk.Notebook(self.pc_tools_tab)
        self.tools_notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create PC Tools subtabs
        tools_subtabs = ["Benchmarks", "Utilities", "Diagnostics"]
        self.tools_tabs = {}
        
        for name in tools_subtabs:
            tab = ttk.Frame(self.tools_notebook)
            self.tools_notebook.add(tab, text=name)
            self.tools_tabs[name.lower()] = tab
        
        # Store all tabs in the main tabs dictionary for backward compatibility
        self.tabs = {**{'device_' + k: v for k, v in self.device_tabs.items()}, 
                    **{'tools_' + k: v for k, v in self.tools_tabs.items()}}
        
        # Set up tab contents
        self.setup_system_info_tab()
        self.setup_hardware_tab()
        self.setup_storage_tab()
        self.setup_network_tab()
        self.setup_benchmarks_tab()
        self.setup_utilities_tab()
        self.setup_diagnostics_tab()
        
        # Bind tab change event
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
        # Initial update
        self.update_last_update_time()
        self.refresh_system_info()
        
        # Log initialization
        self.log_message("PC Tools module initialized")
        self.update_status("Ready")
    
    def _create_scrollable_tab(self, name):
        """Create a scrollable tab with the given name."""
        # Create main container for the tab
        tab = ttk.Frame(self.notebook, padding=5)
        self.notebook.add(tab, text=name)
        
        # Create canvas and scrollbar
        canvas = tk.Canvas(tab, highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        
        # Create scrollable frame
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # Configure canvas scrolling
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack everything
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Store references
        tab.canvas = canvas
        tab.scrollbar = scrollbar
        tab.scrollable_frame = scrollable_frame
        
        return tab
    
    def _configure_styles(self):
        """Configure ttk styles for the application."""
        style = ttk.Style()
        
        # Configure status bar style
        style.configure(
            "StatusBar.TFrame",
            background=self.colors["border"]
        )
        style.configure(
            "StatusBar.TLabel",
            background=self.colors["border"],
            foreground=self.colors["text_primary"],
            font=("Arial", 8)
        )
        
        # Configure notebook style
        style.configure(
            "TNotebook",
            background=self.colors["background"],
            borderwidth=0
        )
        style.configure(
            "TNotebook.Tab",
            padding=[15, 5],
            font=("Arial", 9, "bold"),
            background=self.colors["background"]
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", self.colors["card_bg"])],
            foreground=[("selected", self.colors["primary"])]
        )
        
        # Configure card style
        style.configure(
            "Card.TFrame",
            background=self.colors["card_bg"],
            borderwidth=1,
            relief="solid"
        )
        
        # Configure heading style
        style.configure(
            "Heading.TLabel",
            font=("Arial", 10, "bold"),
            foreground=self.colors["primary"],
            padding=(0, 5, 0, 5)
        )
    
    def setup_hardware_tab(self):
        """Set up the Hardware tab with CPU, RAM, and GPU information."""
        import platform
        import os
        import re
        import logging
        import tkinter as tk
        from tkinter import ttk
        
        # Get the hardware tab from device tabs
        hardware_tab = self.device_tabs["hardware"]
        
        # Create a frame for the hardware content
        hardware_frame = ttk.Frame(hardware_tab)
        hardware_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create container frame that dynamically sizes based on parent
        hw_container = ttk.Frame(hardware_frame)
        hw_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Get container to use all available space by preventing propagation
        hw_container.pack_propagate(False)
        
        # Set up a window resize handler to adjust the container height
        def update_hw_container_size(event=None):
            # Get the parent container's height (hardware_tab)
            tab_height = hardware_tab.winfo_height()
            # Use most of available height but leave room for padding/margins
            if tab_height > 50:  # Only resize if we have meaningful height
                # Calculate available height, account for padding and other elements
                available_height = tab_height - 40  # Subtract padding/margins
                hw_container.configure(height=available_height)
                hardware_canvas.configure(height=available_height - 10)  # Slight adjustment for inner padding
        
        # Bind to Configure events for dynamic resizing
        hardware_tab.bind("<Configure>", update_hw_container_size)
        
        # Create canvas and scrollbar for scrolling
        hardware_canvas = tk.Canvas(hw_container, highlightthickness=0)
        hardware_canvas.pack(side="left", fill="both", expand=True)
        
        # Add scrollbar - this is essential
        hardware_scrollbar = ttk.Scrollbar(hw_container, orient="vertical", command=hardware_canvas.yview)
        hardware_scrollbar.pack(side="right", fill="y")
        
        # Configure the canvas
        hardware_canvas.configure(yscrollcommand=hardware_scrollbar.set)
        
        # Create a frame inside the canvas to hold content
        hw_content_frame = ttk.Frame(hardware_canvas)
        
        # Create a window in the canvas to display the frame
        hardware_canvas_frame = hardware_canvas.create_window((0, 0), window=hw_content_frame, anchor="nw")
        
        # Configure canvas resize handling
        def _configure_hw_canvas(event):
            # Update the scrollregion to encompass the inner frame
            hardware_canvas.configure(scrollregion=hardware_canvas.bbox("all"))
            # Update canvas window width to match canvas width
            hardware_canvas.itemconfig(hardware_canvas_frame, width=event.width)
            
        hw_content_frame.bind("<Configure>", _configure_hw_canvas)
        hardware_canvas.bind("<Configure>", lambda e: hardware_canvas.itemconfig(hardware_canvas_frame, width=e.width))
        
        # Header for hardware information with brand styling
        header_label = ttk.Label(
            hw_content_frame, text="Hardware Information", font=("Arial", 12, "bold"),
            foreground=self.colors["primary"]
        )
        header_label.pack(anchor="w", pady=5)
        
        # Create a single main frame to hold all hardware info
        main_hw_frame = ttk.Frame(hw_content_frame, style="Clean.TFrame")
        main_hw_frame.pack(fill="both", expand=True, padx=3, pady=5)
        
        # Create hardware info frames with consistent styling and dynamic sizing
        cpu_frame = ttk.LabelFrame(main_hw_frame, text="CPU Information", style="Clean.TLabelframe")
        cpu_frame.pack(fill="x", expand=True, pady=5, padx=3)
        
        # Add content to CPU frame in a grid for better alignment with dynamic sizing
        cpu_grid = ttk.Frame(cpu_frame, padding=(5, 3))
        cpu_grid.pack(fill="both", expand=True, padx=5, pady=3)
        
        # Memory frame with consistent styling
        memory_frame = ttk.LabelFrame(main_hw_frame, text="Memory Information", style="Clean.TLabelframe")
        memory_frame.pack(fill="x", expand=True, pady=5, padx=3)
        
        # Add content to Memory frame in a grid - dynamic sizing
        memory_grid = ttk.Frame(memory_frame, padding=(5, 3))
        memory_grid.pack(fill="both", expand=True, padx=5, pady=3)
        
        # GPU frame with consistent styling and dynamic sizing
        gpu_frame = ttk.LabelFrame(main_hw_frame, text="Graphics Information", style="Clean.TLabelframe")
        gpu_frame.pack(fill="x", expand=True, pady=5, padx=3)
        
        # Add content to GPU frame in a grid with dynamic sizing
        gpu_grid = ttk.Frame(gpu_frame, padding=(5, 3))
        gpu_grid.pack(fill="both", expand=True, padx=5, pady=3)
        
        # GPU temperature will be added with the actual GPU info later
        
        # Battery frame with consistent styling and dynamic sizing
        battery_frame = ttk.LabelFrame(main_hw_frame, text="Battery Information", style="Clean.TLabelframe")
        battery_frame.pack(fill="x", expand=True, pady=5, padx=3)
        
        # Add content to Battery frame in a grid with dynamic sizing
        battery_grid = ttk.Frame(battery_frame, padding=(5, 3))
        battery_grid.pack(fill="both", expand=True, padx=5, pady=3)
        
        # Detect battery information
        battery_info = self.get_battery_info()
        
        # Display battery information if present
        if battery_info['present']:
            row = 0
            
            # Create battery information grid
            battery_items = [
                ("Battery Device", battery_info['device']),
                ("Model/Manufacturer", battery_info['model']),
                ("Serial Number", battery_info['serial']),
                ("Charge Level", f"{battery_info['capacity']}%"),
                ("Status", battery_info['status']),
                ("Health", battery_info['health']),
                ("Recommendation", battery_info['recommendation'])
            ]
            
            # Create individual labels for each battery information item
            # Battery Device
            ttk.Label(battery_grid, text="Battery Device:", font=("Arial", 10, "bold"), width=15, anchor="w").grid(
                row=row, column=0, sticky="w", padx=5, pady=3
            )
            ttk.Label(battery_grid, text=battery_info['device']).grid(
                row=row, column=1, sticky="w", padx=5, pady=3
            )
            row += 1
            
            # Model/Manufacturer
            ttk.Label(battery_grid, text="Model/Manufacturer:", font=("Arial", 10, "bold"), width=15, anchor="w").grid(
                row=row, column=0, sticky="w", padx=5, pady=3
            )
            ttk.Label(battery_grid, text=battery_info['model']).grid(
                row=row, column=1, sticky="w", padx=5, pady=3
            )
            row += 1
            
            # Serial Number
            ttk.Label(battery_grid, text="Serial Number:", font=("Arial", 10, "bold"), width=15, anchor="w").grid(
                row=row, column=0, sticky="w", padx=5, pady=3
            )
            ttk.Label(battery_grid, text=battery_info['serial']).grid(
                row=row, column=1, sticky="w", padx=5, pady=3
            )
            row += 1
            
            # Charge Level - using the same pattern as CPU usage for live updates
            ttk.Label(battery_grid, text="Charge Level:", font=("Arial", 10, "bold"), width=15, anchor="w").grid(
                row=row, column=0, sticky="w", padx=5, pady=3
            )
            battery_charge = f"{battery_info['capacity']}%"
            battery_charge_label = ttk.Label(battery_grid, text=battery_charge)
            battery_charge_label.grid(row=row, column=1, sticky="w", padx=5, pady=3)
            # Store a direct reference to the label that won't be lost when dictionaries are reinitialized
            self.battery_charge_label = battery_charge_label

            row += 1
            
            # Status - using the same pattern as CPU usage for live updates
            ttk.Label(battery_grid, text="Status:", font=("Arial", 10, "bold"), width=15, anchor="w").grid(
                row=row, column=0, sticky="w", padx=5, pady=3
            )
            battery_status_label = ttk.Label(battery_grid, text=battery_info['status'])
            battery_status_label.grid(row=row, column=1, sticky="w", padx=5, pady=3)
            # Store a direct reference to the label that won't be lost when dictionaries are reinitialized
            self.battery_status_label = battery_status_label

            row += 1
            
            # Health
            ttk.Label(battery_grid, text="Health:", font=("Arial", 10, "bold"), width=15, anchor="w").grid(
                row=row, column=0, sticky="w", padx=5, pady=3
            )
            battery_health_label = ttk.Label(battery_grid, text=battery_info['health'])
            battery_health_label.grid(row=row, column=1, sticky="w", padx=5, pady=3)
            # Store a direct reference to the label that won't be lost when dictionaries are reinitialized
            self.battery_health_label = battery_health_label

            row += 1
            
            # Recommendation
            ttk.Label(battery_grid, text="Recommendation:", font=("Arial", 10, "bold"), width=15, anchor="w").grid(
                row=row, column=0, sticky="w", padx=5, pady=3
            )
            ttk.Label(battery_grid, text=battery_info['recommendation']).grid(
                row=row, column=1, sticky="w", padx=5, pady=3
            )
            row += 1
        else:
            ttk.Label(battery_grid, text="No battery detected on this system", font=("Arial", 10, "italic")).grid(
                row=0, column=0, columnspan=2, sticky="w", padx=5, pady=10
            )
        
        # Add a spacer frame with background matching the parent
        spacer = ttk.Frame(main_hw_frame, style="Clean.TFrame")
        spacer.pack(fill="both", expand=True)
        
        # Store hardware frame reference for later use
        self.hardware_frame = hw_content_frame
        
        # Add mousewheel scrolling - matches System tab
        def _hw_on_mousewheel(event):
            hardware_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        # Store the mousewheel function for binding/unbinding
        self._hw_mousewheel_func = _hw_on_mousewheel
        
        # We'll bind when tab is selected and unbind when leaving the tab
        hardware_canvas.bind_all("<MouseWheel>", self._hw_mousewheel_func)
        
        # Update scroll region automatically
        def update_hw_scroll_region(event=None):
            hardware_canvas.configure(scrollregion=hardware_canvas.bbox("all"))
        
        # Update the scroll region when the content frame changes
        hw_content_frame.bind("<Configure>", update_hw_scroll_region)
        
        # Dictionary to store hardware info labels for updating
        self.hardware_info_labels = {}
        
        # Detect CPU cores
        try:
            cpu_count = os.cpu_count()
            cpu_cores = str(cpu_count) if cpu_count else "Unknown"
        except Exception as e:
            logging.error(f"Error detecting CPU cores: {e}")
            cpu_cores = "Error detecting"

        # Detect CPU frequency
        try:
            cpu_freq = "Unknown"
            # Try to read from /proc/cpuinfo
            if os.path.exists('/proc/cpuinfo'):
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if line.startswith('cpu MHz'):
                            freq = float(line.split(':')[1].strip())
                            cpu_freq = f"{freq:.2f} MHz"
                            break
            elif os.path.exists('/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq'):
                with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq', 'r') as f:
                    freq = float(f.read().strip()) / 1000
                    cpu_freq = f"{freq:.2f} MHz"
        except Exception as e:
            logging.error(f"Error detecting CPU frequency: {e}")
            cpu_freq = "Error detecting"
            
        # Detect CPU model name
        try:
            cpu_model = "Unknown"
            if os.path.exists('/proc/cpuinfo'):
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if line.startswith('model name'):
                            cpu_model = line.split(':', 1)[1].strip()
                            break
        except Exception as e:
            logging.error(f"Error detecting CPU model: {e}")
            cpu_model = "Error detecting"

        # Detect CPU cache information
        try:
            cpu_cache = "Unknown"
            if os.path.exists('/proc/cpuinfo'):
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo = f.read()
                    cache_match = re.search(r'cache size\s+:\s+(\d+)\s+KB', cpuinfo)
                    if cache_match:
                        cache_kb = int(cache_match.group(1))
                        if cache_kb >= 1024:
                            cpu_cache = f"{cache_kb / 1024:.1f} MB"
                        else:
                            cpu_cache = f"{cache_kb} KB"
        except Exception as e:
            logging.error(f"Error detecting CPU cache: {e}")
            cpu_cache = "Error detecting"
            
        # Create a grid in the CPU frame to display information
        cpu_grid = ttk.Frame(cpu_frame)
        cpu_grid.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Display CPU information in a grid
        row = 0
        ttk.Label(cpu_grid, text="CPU Model:").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(cpu_grid, text=cpu_model).grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1
        
        ttk.Label(cpu_grid, text="CPU Cores:").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(cpu_grid, text=cpu_cores).grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1
        
        ttk.Label(cpu_grid, text="CPU Cache:").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(cpu_grid, text=cpu_cache).grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1
        
        ttk.Label(cpu_grid, text="CPU Frequency:").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        cpu_freq_label = ttk.Label(cpu_grid, text=cpu_freq)
        cpu_freq_label.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        self.hardware_info_labels["CPU Frequency"] = cpu_freq_label
        row += 1
        
        # Add CPU usage with live updates
        ttk.Label(cpu_grid, text="CPU Usage:").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        cpu_usage = f"{psutil.cpu_percent(interval=0.1)}%"
        cpu_usage_label = ttk.Label(cpu_grid, text=cpu_usage)
        cpu_usage_label.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        self.hardware_info_labels["CPU Usage"] = cpu_usage_label
        row += 1
        
        # Add CPU temperature with live updates
        ttk.Label(cpu_grid, text="CPU Temperature:").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        temp = self.get_cpu_temp()
        cpu_temp_label = ttk.Label(cpu_grid, text=f"{temp:.1f}°C" if temp else "N/A")
        cpu_temp_label.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        self.hardware_info_labels["CPU Temperature"] = cpu_temp_label
        row += 1
        
        # GPU temperature is now in the Graphics Information section
        row += 0
        
        # No need for hidden battery labels here anymore
        # Battery labels are now properly added in the Battery Information section
    
        # Detect RAM
        try:
            mem = psutil.virtual_memory()
            total_ram = f"{mem.total / (1024**3):.2f} GB"
            available_ram = f"{mem.available / (1024**3):.2f} GB"
            used_ram = f"{mem.used / (1024**3):.2f} GB ({mem.percent}%)"
            
            # Detect RAM speed using various methods (Linux-specific)
            ram_speed = "Unknown"
            error_msg = ""
            try:
                # First attempt: Use sudo dmidecode to get memory information (preferred method)
                import subprocess
                logging.info("Attempting to detect RAM speed using sudo dmidecode -t memory")
                result = subprocess.run(['sudo', 'dmidecode', '-t', 'memory'], capture_output=True, text=True)
                if result.returncode == 0:
                    # Parse dmidecode output for speed information
                    for line in result.stdout.split('\n'):
                        if 'Speed:' in line and 'Unknown' not in line:
                            speed_line = line.strip()
                            ram_speed = speed_line.split(':')[1].strip()
                            logging.info(f"Successfully detected RAM speed: {ram_speed}")
                            break
                    
                    # If we didn't find speed info, log what we did find
                    if ram_speed == "Unknown":
                        logging.warning("No memory speed found in dmidecode output")
                else:
                    # Log the specific error output from dmidecode
                    error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                    logging.error(f"sudo dmidecode failed with code {result.returncode}: {error_msg}")
            except (subprocess.SubprocessError, FileNotFoundError, PermissionError) as e:
                # Log the specific error
                error_msg = str(e)
                logging.error(f"Error running sudo dmidecode: {error_msg}")
                
                # Second attempt: Use regular dmidecode without sudo
                try:
                    logging.info("Attempting to detect RAM speed using dmidecode without sudo")
                    result = subprocess.run(['dmidecode', '-t', 'memory'], capture_output=True, text=True)
                    if result.returncode == 0:
                        # Parse dmidecode output for speed information
                        for line in result.stdout.split('\n'):
                            if 'Speed:' in line and 'Unknown' not in line:
                                speed_line = line.strip()
                                ram_speed = speed_line.split(':')[1].strip()
                                logging.info(f"Successfully detected RAM speed: {ram_speed}")
                                break
                except (subprocess.SubprocessError, FileNotFoundError, PermissionError) as e:
                    # Log the specific error
                    logging.error(f"Error running dmidecode without sudo: {str(e)}")
                    
                    # Third attempt: Use lshw command
                    try:
                        logging.info("Attempting to detect RAM speed using lshw -class memory")
                        result = subprocess.run(['lshw', '-class', 'memory'], capture_output=True, text=True)
                        if result.returncode == 0:
                            for line in result.stdout.split('\n'):
                                if 'clock' in line.lower():
                                    ram_speed = line.split(':')[1].strip()
                                    logging.info(f"Successfully detected RAM speed with lshw: {ram_speed}")
                                    break
                    except (subprocess.SubprocessError, FileNotFoundError) as e:
                        # Log the specific error
                        logging.error(f"Error running lshw: {str(e)}")
                        
                        # Fourth attempt: Check for memory info in sysfs (some systems)
                        try:
                            logging.info("Attempting to detect RAM speed using sysfs")
                            if os.path.exists('/sys/devices/system/cpu/cpu0/cache/index0/size'):
                                with open('/sys/devices/system/cpu/cpu0/cache/index0/size', 'r') as f:
                                    ram_speed = f.read().strip()
                                    logging.info(f"Successfully detected RAM info from sysfs: {ram_speed}")
                        except Exception as e:
                            logging.error(f"Error reading from sysfs: {str(e)}")
                            ram_speed = "Unknown (sudo required)"

        except Exception as e:
            logging.error(f"Error detecting RAM: {e}")
            total_ram = "Error detecting"
            available_ram = "Error detecting"
            used_ram = "Error detecting"
            ram_speed = "Unknown"
            
        # Display RAM information in the memory_grid
        memory_info = [
            ("Total Memory", total_ram),
            ("Available Memory", available_ram),
            ("Used Memory", used_ram),
            ("Memory Speed", ram_speed)
        ]
        
        # Create memory grid with labels and values
        for i, (label_text, value) in enumerate(memory_info):
            # Create label (left column)
            label = ttk.Label(
                memory_grid,
                text=f"{label_text}:",
                font=("Arial", 10, "bold"),
                width=15,
                anchor="w"
            )
            label.grid(row=i, column=0, sticky="w", padx=5, pady=3)
            
            # Create value (right column)
            value_label = ttk.Label(
                memory_grid,
                text=value,
                font=("Arial", 10),
                anchor="w"
            )
            value_label.grid(row=i, column=1, sticky="w", padx=5, pady=3)
            
            # Store for updating
            if label_text in ["Used Memory", "Available Memory"]:
                self.hardware_info_labels[label_text] = value_label

        # Detect CPU cache information
        try:
            cpu_cache = "Unknown"
            if os.path.exists('/proc/cpuinfo'):
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo = f.read()
                    cache_match = re.search(r'cache size\s+:\s+(\d+)\s+KB', cpuinfo)
                    if cache_match:
                        cache_kb = int(cache_match.group(1))
                        if cache_kb >= 1024:
                            cpu_cache = f"{cache_kb / 1024:.1f} MB"
                        else:
                            cpu_cache = f"{cache_kb} KB"
        except Exception as e:
            logging.error(f"Error detecting CPU cache: {e}")
            cpu_cache = "Error detecting"

        # Calculate RAM usage percentage
        try:
            ram_percent = "Unknown"
            if os.path.exists('/proc/meminfo'):
                with open('/proc/meminfo', 'r') as f:
                    meminfo = f.read()
                total_match = re.search(r'MemTotal:\s+(\d+)', meminfo)
                avail_match = re.search(r'MemAvailable:\s+(\d+)', meminfo)
                if total_match and avail_match:
                    total_kb = int(total_match.group(1))
                    avail_kb = int(avail_match.group(1))
                    used_kb = total_kb - avail_kb
                    ram_percent = f"{(used_kb / total_kb) * 100:.1f}%"
        except Exception as e:
            logging.error(f"Error calculating RAM percentage: {e}")
            ram_percent = "Error calculating"

        # Detect GPU information
        try:
            import subprocess
            gpu_info = "Unknown"
            # Try lspci for PCI GPU devices
            lspci_result = subprocess.run(
                ['lspci', '-v'], 
                capture_output=True, text=True, timeout=5
            )
            if lspci_result.returncode == 0:
                # Search for VGA or 3D controller
                gpu_lines = []
                for line in lspci_result.stdout.splitlines():
                    if "VGA" in line or "3D controller" in line:
                        # Extract just the essential GPU model information
                        full_desc = line.split(':', 1)[1].strip()
                        
                        # Try to extract GPU name from square brackets first (usually Intel/NVIDIA)
                        bracket_match = re.search(r'\[(.*?)\]', line)
                        if bracket_match and 'Intel' in line:
                            gpu_in_bracket = bracket_match.group(1)
                            # Make sure we include 'Intel' in the name if not already present
                            if not gpu_in_bracket.startswith('Intel'):
                                gpu_in_bracket = 'Intel ' + gpu_in_bracket
                            friendly_name = self.get_friendly_gpu_name(gpu_in_bracket)
                        else:
                            friendly_name = self.get_friendly_gpu_name(full_desc)
                        
                        gpu_lines.append(friendly_name)
                        
                # Create a grid in the GPU frame to display information
                gpu_grid = ttk.Frame(gpu_frame)
                gpu_grid.pack(fill="both", expand=True, padx=5, pady=5)
                
                # Start row counter for GPU grid
                gpu_row = 0
                
                # Display GPU information in a grid
                for i, gpu in enumerate(gpu_lines):
                    ttk.Label(gpu_grid, text=f"GPU {i+1}:").grid(row=gpu_row, column=0, sticky="w", padx=5, pady=2)
                    ttk.Label(gpu_grid, text=gpu).grid(row=gpu_row, column=1, sticky="w", padx=5, pady=2)
                    gpu_row += 1
                
                # Add GPU temperature with live updates after the GPU listings
                ttk.Label(gpu_grid, text="GPU Temperature:").grid(row=gpu_row, column=0, sticky="w", padx=5, pady=2)
                gpu_temp = self.get_gpu_temp()
                gpu_temp_label = ttk.Label(gpu_grid, text=f"{gpu_temp:.1f}°C" if gpu_temp else "N/A")
                gpu_temp_label.grid(row=gpu_row, column=1, sticky="w", padx=5, pady=2)
                self.hardware_info_labels["GPU Temperature"] = gpu_temp_label
                gpu_row += 1
                
                # Add GPU frequency with live updates
                ttk.Label(gpu_grid, text="GPU Frequency:").grid(row=gpu_row, column=0, sticky="w", padx=5, pady=2)
                gpu_freq = self.get_gpu_freq()
                gpu_freq_label = ttk.Label(gpu_grid, text=f"{gpu_freq:.0f} MHz" if gpu_freq else "N/A")
                gpu_freq_label.grid(row=gpu_row, column=1, sticky="w", padx=5, pady=2)
                self.hardware_info_labels["GPU Frequency"] = gpu_freq_label
                if gpu_lines:
                    gpu_info = ", ".join(gpu_lines)
        except Exception as e:
            logging.error(f"Error detecting GPU: {e}")
            gpu_info = "Error detecting"

        # Display hardware information in a grid
        row = 0
        # We already displayed the hardware information in dedicated frames above
        # No need to display it again

    def list_block_devices(self):
        """List all block devices on the system
        
        Returns:
            list: List of device paths properly formatted for SMART operations
        """
        try:
            # Get all block devices, showing only disk devices (not partitions)
            result = subprocess.run(
                ['lsblk', '-dn', '-o', 'NAME'], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                timeout=5  # Add timeout to prevent hanging
            )
            
            if result.returncode != 0:
                logging.error(f"lsblk command failed: {result.stderr}")
                return ["/dev"]  # Return minimal fallback if command fails
                
            devices = [dev for dev in result.stdout.strip().split('\n') if dev]  # Filter empty lines
            
            if not devices:
                # If no devices found with lsblk, try alternative approach using glob
                logging.warning("No devices found with lsblk, trying alternative method")
                disk_paths = glob.glob('/dev/sd*') + glob.glob('/dev/hd*') + glob.glob('/dev/nvme*n*')
                # Filter out partitions (devices with numbers at the end for non-nvme)
                devices = []
                for path in disk_paths:
                    dev_name = os.path.basename(path)
                    if ('nvme' in dev_name and 'n' in dev_name) or not any(c.isdigit() for c in dev_name):
                        devices.append(dev_name)
            
            # Process the device list to handle NVMe controllers correctly
            processed_devices = []
            nvme_controllers = set()
            
            logging.info(f"Found devices: {devices}")
            
            for dev in devices:
                if not dev:  # Skip empty device names
                    continue
                    
                if 'nvme' in dev and 'n' in dev:
                    # Extract controller name from namespace (e.g., nvme0n1 -> nvme0)
                    controller = dev.split('n')[0]
                    if controller not in nvme_controllers:
                        nvme_controllers.add(controller)
                        processed_devices.append(f"/dev/{controller}")
                    # Also add the full device path as it may be needed for operations
                    processed_devices.append(f"/dev/{dev}")
                else:
                    processed_devices.append(f"/dev/{dev}")
            
            # Remove duplicates while preserving order
            seen = set()
            processed_devices = [x for x in processed_devices if not (x in seen or seen.add(x))]
            
            if not processed_devices:
                logging.warning("No block devices found, returning fallback")
                return ["/dev"]  # Fallback if no devices found
                
            logging.info(f"Processed devices for SMART: {processed_devices}")
            return processed_devices
            
        except Exception as e:
            logging.error(f"Error listing block devices: {e}")
            return ["/dev"]  # Return minimal fallback on error

    def get_device_type(self, device):
        """Determine device type for SMART commands
    
        Args:
            device: Device path (e.g., /dev/sda)
            
        Returns:
            str: Device type for smartctl ('nvme' or 'ata')
        """
        if "nvme" in device:
            return "nvme"
        elif "sd" in device or "hd" in device:
            return "ata"
        # Add support for SCSI devices
        elif "sg" in device:
            return "scsi"
        else:
            # Try to determine by running a command
            try:
                result = subprocess.run(
                    ['sudo', 'smartctl', '-i', device],
                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True
                )
                output = result.stdout.lower()
                if "nvme" in output:
                    return "nvme"
                elif "ata" in output:
                    return "ata"
                elif "scsi" in output:
                    return "scsi"
            except:
                pass
            return None

    def check_smart_support(self, device, dev_type):
        """Check if device supports SMART
        
        Args:
            device: Device path (e.g., /dev/sda)
            dev_type: Device type ('nvme' or 'ata')
            
        Returns:
            bool: True if SMART is supported and available
        """
        try:
            result = subprocess.run(
                ['sudo', 'smartctl', '-i', '-d', dev_type, device],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True
            )
            output = result.stdout
            
            # For NVMe drives, we check for NVMe specific indicators
            if dev_type == 'nvme':
                # NVMe drives should show the 'nvme' device type and SMART capabilities
                return 'NVMe' in output or 'nvme' in output or '/dev/nvme' in output
            # For traditional ATA drives
            else:
                return 'SMART support is: Available' in output or 'SMART support is: Enabled' in output
        except Exception as e:
            logging.error(f"Error checking SMART support for {device}: {e}")
            return False

    def get_smart_info(self, device, dev_type):
        """Get SMART information for a device
        
        Args:
            device: Device path (e.g., /dev/sda)
            dev_type: Device type ('nvme' or 'ata')
            
        Returns:
            str: SMART information output
        """
        try:
            result = subprocess.run(
                ['sudo', 'smartctl', '-a', '-d', dev_type, device],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True
            )
            return result.stdout
        except Exception as e:
            logging.error(f"Failed to read SMART info for {device}: {e}")
            return f"Failed to read SMART info for {device}: {e}"
            
    def update_smart_info(self, frame):
        """Update SMART information for the selected drive in the given frame
        
        Args:
            frame: Frame to display SMART information in
        """
        # Clear existing widgets
        for widget in frame.winfo_children():
            widget.destroy()
            
        # Get reference to the storage canvas for scroll region updates
        storage_canvas = None
        try:
            # Find the storage canvas in the widget hierarchy
            current = frame
            while current and current.winfo_name() != 'storage':
                if isinstance(current, tk.Canvas) and 'storage_canvas' in str(current):
                    storage_canvas = current
                    break
                current = current.master
        except Exception as e:
            logging.error(f"Error finding storage canvas: {e}")

            
        # Check if there's a selected drive
        if not hasattr(self, 'selected_drive') or not self.selected_drive.get():
            ttk.Label(frame, text="No drive selected", font=("Arial", 10)).pack(padx=5, pady=10)
            return
            
        device = self.selected_drive.get()
        dev_type = self.get_device_type(device)
        
        # For NVMe devices, we need to use the controller, not the namespace
        if dev_type == 'nvme' and 'nvme' in device:
            # Convert /dev/nvme0n1 to /dev/nvme0
            import re
            controller_device = re.sub(r'(nvme\d+)n\d+', r'\1', device)
            device = controller_device
        
        if not dev_type:
            ttk.Label(frame, text=f"Unknown device type for {device}", font=("Arial", 10)).pack(padx=5, pady=10)
            return
            
        # Check if SMART is supported
        if not self.check_smart_support(device, dev_type):
            ttk.Label(frame, text=f"{device} does not support SMART or is inaccessible", font=("Arial", 10)).pack(padx=5, pady=10)
            return
            
        # Show loading message
        loading_label = ttk.Label(frame, text=f"Loading SMART data for {device}...", font=("Arial", 10))
        loading_label.pack(padx=5, pady=10)
        frame.update_idletasks()  # Force update to show loading message
        
        # Get SMART data
        smart_output = self.get_smart_info(device, dev_type)
        
        # Remove loading message
        loading_label.destroy()
        
        # Create a notebook for SMART information sections
        smart_notebook = ttk.Notebook(frame)
        smart_notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Summary tab
        summary_tab = ttk.Frame(smart_notebook)
        smart_notebook.add(summary_tab, text="Summary")
        
        # Raw output tab
        raw_tab = ttk.Frame(smart_notebook)
        smart_notebook.add(raw_tab, text="Raw Output")
        
        # Parse and display summary information
        summary_frame = ttk.LabelFrame(summary_tab, text="SMART Status")
        summary_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Extract overall health status based on device type
        health_status = "Unknown"
        dev_type = self.get_device_type(device)
        
        # Different parsing for NVMe vs ATA drives
        if dev_type == 'nvme':
            # For NVMe drives, look for SMART health status or other indicators
            for line in smart_output.splitlines():
                if "smart overall-health self-assessment" in line.lower() or "smart health status" in line.lower() or "smart status" in line.lower():
                    health_parts = line.split(":")
                    if len(health_parts) > 1:
                        health_status = health_parts[1].strip()
                        break
                # NVMe sometimes reports health differently
                elif "critical warning" in line.lower():
                    # Critical warning of 0 is good (no warnings)
                    if "0x00" in line or "0x0" in line:
                        health_status = "PASS"
                    else:
                        health_status = "FAIL"
                    break
        else:
            # For ATA drives, standard SMART health check
            for line in smart_output.splitlines():
                if "overall-health self-assessment" in line.lower() or "smart health status" in line.lower():
                    health_parts = line.split(":")
                    if len(health_parts) > 1:
                        health_status = health_parts[1].strip()
                    break
                
        # Display health status with appropriate color
        health_label = ttk.Label(summary_frame, text="Health Status:", font=("Arial", 12, "bold"))
        health_label.pack(pady=(10, 5))
        
        status_color = "green" if "PASS" in health_status.upper() else "red"
        status_label = tk.Label(summary_frame, text=health_status, font=("Arial", 14, "bold"), fg=status_color)
        status_label.pack(pady=(0, 10))
        
        # Add important SMART attributes in a table
        attribute_frame = ttk.LabelFrame(summary_tab, text="Key Attributes")
        attribute_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create a table for attributes
        attributes_table = ttk.Treeview(attribute_frame, columns=("attribute", "value", "status"), show="headings", height=10)
        attributes_table.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Set column headings
        attributes_table.heading("attribute", text="Attribute")
        attributes_table.heading("value", text="Value")
        attributes_table.heading("status", text="Status")
        
        # Set column widths
        attributes_table.column("attribute", width=200)
        attributes_table.column("value", width=100)
        attributes_table.column("status", width=100)
        
        # Extract important attributes based on device type
        if dev_type == 'nvme':
            # Key attributes for NVMe drives
            nvme_attributes = {
                "Critical Warning": None,
                "Temperature": None,
                "Available Spare": None,
                "Percentage Used": None,
                "Data Units Read": None,
                "Data Units Written": None,
                "Power Cycles": None,
                "Power On Hours": None,
                "Unsafe Shutdowns": None
            }
            
            # Parse the output for NVMe attributes
            for line in smart_output.splitlines():
                for attr in nvme_attributes.keys():
                    if attr.lower() in line.lower():
                        parts = line.split(":" if ":" in line else "=")
                        if len(parts) > 1:
                            nvme_attributes[attr] = parts[1].strip()
            
            # Add NVMe attributes to the table
            for attr, value in nvme_attributes.items():
                if value is not None:
                    # Determine status based on attribute
                    status = "OK"
                    status_tag = "ok"
                    
                    if "critical" in attr.lower() and value.strip() != "0x00" and value.strip() != "0x0" and value.strip() != "0":
                        status = "Warning"
                        status_tag = "warning"
                    elif "percentage used" in attr.lower():
                        # Extract numeric value if possible
                        try:
                            pct_value = int(''.join(filter(str.isdigit, value.split('%')[0])))
                            if pct_value > 90:
                                status = "Critical"
                                status_tag = "critical"
                            elif pct_value > 70:
                                status = "Warning"
                                status_tag = "warning"
                        except:
                            pass
                    elif "temperature" in attr.lower():
                        try:
                            # Extract temperature value
                            temp_value = int(''.join(filter(str.isdigit, value.split(' ')[0])))
                            if temp_value > 70:
                                status = "Critical"
                                status_tag = "critical"
                            elif temp_value > 60:
                                status = "Warning"
                                status_tag = "warning"
                        except:
                            pass
                    
                    # Add to table with tag for coloring
                    item_id = attributes_table.insert("", "end", values=(attr, value, status), tags=(status_tag,))
            
            # Configure tag colors
            attributes_table.tag_configure("ok", background="#e6ffe6")  # Light green
            attributes_table.tag_configure("warning", background="#fff2cc")  # Light yellow
            attributes_table.tag_configure("critical", background="#ffcccc")  # Light red
        else:
            # For ATA drives, look for different important attributes
            ata_attributes = {}
            in_smart_attributes = False
            
            for line in smart_output.splitlines():
                if "SMART Attributes Data Structure" in line:
                    in_smart_attributes = True
                    continue
                if in_smart_attributes and line.strip() and not line.startswith("ID#"):
                    if "\"" in line:  # End of attributes section
                        in_smart_attributes = False
                        continue
                    parts = line.strip().split()
                    if len(parts) >= 10:
                        try:
                            attr_id = parts[0]
                            attr_name = parts[1]
                            value = parts[9]
                            threshold = parts[5]
                            status = "OK"
                            status_tag = "ok"
                            
                            # Commonly important attributes
                            if attr_name in ["Reallocated_Sector_Ct", "Reported_Uncorrect", "Command_Timeout", "Current_Pending_Sector", "Offline_Uncorrectable", "UDMA_CRC_Error_Count"]:
                                if int(value) > 0:
                                    status = "Warning"
                                    status_tag = "warning"
                            
                            # Add to table
                            item_id = attributes_table.insert("", "end", values=(attr_name, value, status), tags=(status_tag,))
                        except:
                            continue
            
            # Configure tag colors
            attributes_table.tag_configure("ok", background="#e6ffe6")  # Light green
            attributes_table.tag_configure("warning", background="#fff2cc")  # Light yellow
            attributes_table.tag_configure("critical", background="#ffcccc")  # Light red
        
        # Display raw output
        raw_frame = ttk.Frame(raw_tab)
        raw_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create text widget for raw output with substantially increased height
        raw_text = scrolledtext.ScrolledText(raw_frame, height=45)  # Significantly increased height
        raw_text.pack(fill="both", expand=True, padx=0, pady=0)  # Remove padding to maximize space
        raw_text.insert(tk.END, smart_output)
        raw_text.configure(state="disabled")  # Make read-only
        
        # Update the global scroll region to ensure all content is visible
        self.update_idletasks()  # Process all pending UI updates
        
        # Find the storage_content_frame in the widget hierarchy and update its scroll region
        if storage_canvas:
            try:
                # Update the scroll region to encompass all content
                storage_canvas.update_idletasks()
                storage_canvas.configure(scrollregion=storage_canvas.bbox("all"))
                logging.info("Updated scroll region for SMART data display")
                
            except Exception as e:
                logging.error(f"Error updating scroll region: {e}")
            
    def prefetch_smart_data(self):
        """Prefetch SMART data for all drives using sudo for authentication"""
        import subprocess
        import logging
        import time
        
        # Get list of drives using the improved method
        drives = self.list_block_devices()
        
        if not drives:
            logging.info("No drives found for SMART data prefetch")
            return
            
        logging.info(f"Prefetching SMART data for drives: {drives}")
        
        # Process each drive with proper device type detection
        for drive in drives:
            dev_type = self.get_device_type(drive)
            
            # Skip devices without a recognized type
            if not dev_type:
                logging.info(f"Skipping {drive}: unknown device type")
                continue
                
            # Check if SMART is supported
            if not self.check_smart_support(drive, dev_type):
                logging.info(f"{drive} does not support SMART or is inaccessible")
                continue
                
            try:
                # Get SMART data with the proper device type using sudo
                smart_output = self.get_smart_info(drive, dev_type)
                
                # Parse the output to separate health and attributes data
                health_output = ""
                attr_output = ""
                
                # Extract health status and attributes from the output
                if smart_output:
                    for line in smart_output.splitlines():
                        if "overall-health self-assessment" in line.lower() or "smart health status" in line.lower():
                            health_output += line + "\n"
                            
                        # Collect attribute lines for ATA drives
                        if "id#" in line.lower() or "attribute_name" in line.lower() or "raw_value" in line.lower():
                            attr_output += line + "\n"
                            continue
                            
                        # For numerical attribute rows (ATA)
                        if line.strip() and line[0].isdigit() and len(line.split()) >= 5:
                            attr_output += line + "\n"
                            
                        # For NVMe attributes
                        if any(x in line.lower() for x in ["temperature", "available spare", "percentage used", "data units read", "data units written"]):
                            attr_output += line + "\n"
                
                # Cache the results
                PCToolsModule.smart_data_cache[drive] = {
                    'health_output': health_output,
                    'attr_output': attr_output,
                    'timestamp': time.time()
                }
                
                logging.info(f"Successfully cached SMART data for {drive} (type: {dev_type})")
                
            except Exception as e:
                logging.error(f"Error prefetching SMART data for {drive}: {e}")
        
        # Set flag to indicate we have authenticated SMART data access
        PCToolsModule.sudo_authenticated = True
    
    def _prefetch_with_direct_access(self, drives):
        """Prefetch SMART data when direct access is available"""
        logging.info("Direct SMART access available, no authentication needed")
        PCToolsModule.sudo_authenticated = True
        
        for drive in drives:
            try:
                # Get health status
                health_result = subprocess.run(
                    ['sudo', 'smartctl', '-H', drive],
                    capture_output=True, text=True, timeout=3
                )
                    
                # Get attributes
                attr_result = subprocess.run(
                    ['sudo', 'smartctl', '-A', drive],
                    capture_output=True, text=True, timeout=3
                )
                    
                # Cache the results
                PCToolsModule.smart_data_cache[drive] = {
                    'health_output': health_result.stdout if health_result.returncode == 0 else None,
                    'attr_output': attr_result.stdout if attr_result.returncode == 0 else None,
                    'timestamp': time.time()
                }
                logging.debug(f"Cached SMART data for {drive}")
                
            except subprocess.TimeoutExpired:
                logging.warning(f"Timeout getting SMART data for {drive}")
            except subprocess.CalledProcessError as e:
                logging.error(f"Error getting SMART data for {drive}: {e.stderr}")
            except Exception as e:
                logging.error(f"Unexpected error getting SMART data for {drive}: {e}")
    
    def _prefetch_with_sudo(self, drives):
        """Prefetch SMART data using sudo for authentication"""
        try:
            logging.info("Using sudo to get SMART data for all drives")
            
            if not drives:
                return
                
            # Try to get data for the first drive with sudo
            drive = drives[0]
            remaining_drives = drives[1:]
            
            try:
                # Get health status with sudo
                health_result = subprocess.run(
                    ['sudo', '--non-interactive', 'smartctl', '-H', drive],
                    capture_output=True, text=True, timeout=15
                )
                
                # Get attributes with sudo
                attr_result = subprocess.run(
                    ['sudo', '--non-interactive', 'smartctl', '-A', drive],
                    capture_output=True, text=True, timeout=5
                )
            except subprocess.TimeoutExpired as e:
                logging.error(f"Timeout getting SMART data for {drive} with sudo: {e}")
                return
            except subprocess.CalledProcessError as e:
                logging.error(f"Error getting SMART data for {drive} with sudo: {e.stderr}")
                return
            except Exception as e:
                logging.error(f"Unexpected error getting SMART data for {drive} with sudo: {e}")
                return
                
            # If we got here, sudo authentication was successful
            PCToolsModule.sudo_authenticated = True
            
            # Cache the results
            PCToolsModule.smart_data_cache[drive] = {
                'health_output': health_result.stdout if health_result.returncode == 0 else None,
                'attr_output': attr_result.stdout if attr_result.returncode == 0 else None,
                'timestamp': time.time()
            }
            
            logging.info(f"Successfully got SMART data for {drive} with sudo")
            
            # Now try to get data for remaining drives without sudo if possible
            for remaining_drive in remaining_drives:
                try:
                    # First try without sudo (in case we have direct access now)
                    self._prefetch_drive_data(remaining_drive, use_sudo=False)
                except Exception as e:
                    # If that fails, try with sudo
                    logging.debug(f"Direct access failed for {remaining_drive}, trying with sudo: {e}")
                    try:
                        self._prefetch_drive_data(remaining_drive, use_sudo=True)
                    except Exception as e2:
                        logging.error(f"Error getting SMART data for {remaining_drive} with sudo: {e2}")
                    
        except Exception as e:
            logging.error(f"Unexpected error in _prefetch_with_sudo: {e}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Authentication failed: {e}")
        except Exception as e:
            logging.error(f"Unexpected error in _prefetch_with_pkexec: {e}")
    
    def _prefetch_drive_data(self, drive, use_sudo=True):
        """Helper method to get SMART data for a single drive"""
        try:
            cmd = ['sudo'] if use_sudo else []
            cmd.extend(['smartctl', '-H', drive])
            health_result = subprocess.run(
                cmd, 
                capture_output=True, text=True, timeout=5 if use_sudo else 3
            )
            
            cmd = ['sudo'] if use_sudo else []
            cmd.extend(['smartctl', '-A', drive])
            attr_result = subprocess.run(
                cmd, 
                capture_output=True, text=True, timeout=5 if use_sudo else 3
            )
            
            # Cache the results
            PCToolsModule.smart_data_cache[drive] = {
                'health_output': health_result.stdout if health_result.returncode == 0 else None,
                'attr_output': attr_result.stdout if attr_result.returncode == 0 else None,
                'timestamp': time.time()
            }
            logging.debug(f"Cached SMART data for {drive} (sudo: {use_sudo})")
            
        except subprocess.TimeoutExpired:
            raise Exception(f"Timeout getting SMART data for {drive}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error getting SMART data for {drive}: {e.stderr}")
        except Exception as e:
            raise Exception(f"Unexpected error getting SMART data for {drive}: {e}")
    
    def add_smart_info(self, parent_frame, disk_path):
        """Add S.M.A.R.T. information for a specific disk using cached data"""
        import re
        import os
        import logging
        import shutil
        
        try:
            # Create overall health frame
            health_frame = ttk.LabelFrame(parent_frame, text="Overall Health")
            health_frame.pack(fill="x", expand=False, padx=5, pady=5)
            
            # Default health status
            disk_health_status = "Unknown"
            attributes_data = []
            disk_name = os.path.basename(disk_path)
            
            # Check if we need to refresh the SMART data cache
            if not PCToolsModule.smart_data_cache:
                logging.info("SMART data cache is empty, getting fresh data")
                self.get_all_smart_data()
            
            # Use cached data for this drive if available
            if disk_path in PCToolsModule.smart_data_cache:
                logging.info(f"Using cached SMART data for {disk_path}")
                cached_data = PCToolsModule.smart_data_cache[disk_path]
                # Extract health status from cached data
                if cached_data['health_output']:
                    for line in cached_data['health_output'].splitlines():
                        if "overall-health self-assessment test result" in line.lower():
                            disk_health_status = line.split(":")[1].strip()
                            break
                
                # Use cached attributes data
                if cached_data['attr_output']:
                    attributes_data = cached_data['attr_output'].splitlines()
            
            # If we couldn't get data for this disk and we haven't tried already
            elif not PCToolsModule.sudo_authenticated:
                # Try to refresh the cache again
                logging.info(f"No data found for {disk_path}, trying to get fresh data")
                self.get_all_smart_data()
                
                # Check if we got the data after refreshing
                if disk_path in PCToolsModule.smart_data_cache:
                    cached_data = PCToolsModule.smart_data_cache[disk_path]
                    
                    # Extract health status from newly cached data
                    if cached_data['health_output']:
                        for line in cached_data['health_output'].splitlines():
                            if "overall-health self-assessment test result" in line.lower():
                                disk_health_status = line.split(":")[1].strip()
                                break
                    
                    # Use newly cached attributes data
                    if cached_data['attr_output']:
                        attributes_data = cached_data['attr_output'].splitlines()
            
            # If no cached data, try to get it directly after setting capabilities
            if disk_health_status == "Unknown" or not attributes_data:
                # Make sure capabilities are set
                if not hasattr(PCToolsModule, 'smartctl_capabilities_set'):
                    self.set_smartctl_capabilities()
                
                # Try direct access now that capabilities should be set
                try:
                    import subprocess
                    # Get health status directly (should work if capabilities are set)
                    health_result = subprocess.run(
                        ['smartctl', '-H', disk_path],
                        capture_output=True, text=True, timeout=3
                    )
                    
                    if health_result.returncode == 0:
                        for line in health_result.stdout.splitlines():
                            if "overall-health self-assessment test result" in line.lower():
                                disk_health_status = line.split(":")[1].strip()
                                logging.info(f"Got SMART health status with direct access: {disk_health_status}")
                                break
                        
                        # Get attributes data directly (should work with capabilities set)
                        attr_result = subprocess.run(
                            ['smartctl', '-A', disk_path],
                            capture_output=True, text=True, timeout=3
                        )
                        
                        if attr_result.returncode == 0:
                            attributes_data = attr_result.stdout.splitlines()
                            logging.info("Got SMART attributes with direct access")
                            
                            # Cache the results for future use
                            PCToolsModule.smart_data_cache[disk_path] = {
                                'health_output': health_result.stdout if health_result.returncode == 0 else None,
                                'attr_output': attr_result.stdout if attr_result.returncode == 0 else None
                            }
                except Exception as e:
                    logging.error(f"Error getting SMART data with direct access: {e}")
                try:
                    # Check if SSD using rotational attribute
                    is_ssd = False
                    disk_name = disk_path.split('/')[-1]
                    rota_path = f"/sys/block/{disk_name}/queue/rotational"
                    if os.path.exists(rota_path):
                        with open(rota_path, 'r') as f:
                            is_ssd = f.read().strip() == '0'  # 0 means non-rotational (SSD)
                    
                    # For NVMe, check if device exists
                    is_nvme = "nvme" in disk_name
                    
                    # For SATA/SSD drives, check for reallocated sectors or bad blocks
                    bad_sectors = 0
                    if os.path.exists(f"/sys/block/{disk_name}/device/badblocks"):
                        bad_sectors = 1  # If the file exists, it likely has bad blocks
                    
                    # Make a best-effort assessment based on available info
                    if is_ssd or is_nvme:
                        disk_health_status = "Likely GOOD" if bad_sectors == 0 else "Needs Check"
                    else:
                        disk_health_status = "Basic Check Only"
                except Exception as e:
                    logging.error(f"Error reading from /sys/block: {e}")
            
            # Display health status with color coding
            health_label = ttk.Label(health_frame, text="SMART Health Status:", font=("Arial", 10, "bold"))
            health_label.pack(side="left", padx=5, pady=5)
            
            health_value = tk.Label(health_frame, text=disk_health_status)
            if "PASS" in disk_health_status.upper() or "GOOD" in disk_health_status.upper():
                health_value.configure(foreground="green", font=("Arial", 10, "bold"))
            elif "FAIL" in disk_health_status.upper() or "BAD" in disk_health_status.upper():
                health_value.configure(foreground="red", font=("Arial", 10, "bold"))
            else:
                health_value.configure(foreground="orange", font=("Arial", 10, "bold"))
            health_value.pack(side="left", padx=5, pady=5)
            
            # Get SMART attributes
            attributes_frame = ttk.LabelFrame(parent_frame, text="SMART Attributes")
            attributes_frame.pack(fill="both", expand=True, padx=5, pady=5)
            
            # Create canvas with scrollbar for potentially long list of attributes
            canvas = tk.Canvas(attributes_frame)
            scrollbar = ttk.Scrollbar(attributes_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Create headers based on drive type - will be added in the drive-specific sections
            
            # Define critical attributes to highlight
            critical_attributes = [
                "Reallocated_Sector_Ct", "Current_Pending_Sector", "Offline_Uncorrectable",
                "Reallocated_Event_Count", "Spin_Retry_Count", "UDMA_CRC_Error_Count"
            ]
            
            # Process S.M.A.R.T. attributes if available
            if attributes_data:
                # Check if this is NVMe or traditional SATA format
                is_nvme = any("NVMe" in line for line in attributes_data)
                
                if is_nvme:
                    # Handle NVMe format
                    found_attributes = False
                    row = 1
                    
                    # Create a proper table with consistent column widths for NVMe format
                    table_frame = ttk.Frame(scrollable_frame, relief="solid", borderwidth=1)
                    table_frame.pack(fill="both", expand=True, padx=5, pady=5)
                    
                    # Fixed column widths
                    col_widths = [30, 25, 10]  # Character widths for each column
                    
                    # Add headers with borders
                    nvme_headers = ["Attribute", "Value", "Status"]
                    for i, header in enumerate(nvme_headers):
                        header_cell = ttk.Frame(table_frame, relief="solid", borderwidth=1)
                        header_cell.grid(row=0, column=i, sticky="nsew")
                        header_label = ttk.Label(header_cell, text=header, font=("Arial", 9, "bold"), width=col_widths[i], anchor="center")
                        header_label.pack(padx=5, pady=2)
                    
                    # Configure column weights to maintain sizes
                    for i in range(len(nvme_headers)):
                        table_frame.columnconfigure(i, weight=1)
                    
                    # Create a 2-column display for NVMe attributes
                    for line in attributes_data:
                        # Skip headers and copyright lines
                        if not line.strip() or "smartctl" in line or "Copyright" in line or "START OF" in line:
                            continue
                            
                        # Process attribute lines with colon separator
                        if ":" in line:
                            found_attributes = True
                            try:
                                name, value = line.split(":", 1)
                                name = name.strip()
                                value = value.strip()
                                
                                # Determine status for certain critical NVMe attributes
                                status = "OK"
                                if name == "Critical Warning" and value != "0x00":
                                    status = "Critical"
                                elif name == "Media and Data Integrity Errors" and value != "0":
                                    status = "Critical"
                                elif name == "Percentage Used" and int(value.split('%')[0]) > 90:
                                    status = "Warning"
                                elif name == "Available Spare" and int(value.split('%')[0]) < 25:
                                    status = "Warning"
                                
                                # Add data row to table with borders
                                # Name column
                                name_cell = ttk.Frame(table_frame, relief="solid", borderwidth=1)
                                name_cell.grid(row=row, column=0, sticky="nsew")
                                name_label = ttk.Label(name_cell, text=name, font=("Arial", 9, "bold"), width=col_widths[0], anchor="w")
                                name_label.pack(padx=5, pady=2, fill="both")
                                
                                # Value column
                                value_cell = ttk.Frame(table_frame, relief="solid", borderwidth=1)
                                value_cell.grid(row=row, column=1, sticky="nsew")
                                value_label = ttk.Label(value_cell, text=value, width=col_widths[1], anchor="w")
                                value_label.pack(padx=5, pady=2, fill="both")
                                
                                # Status column
                                status_cell = ttk.Frame(table_frame, relief="solid", borderwidth=1)
                                status_cell.grid(row=row, column=2, sticky="nsew")
                                status_label = ttk.Label(status_cell, text=status, width=col_widths[2], anchor="center")
                                
                                # Style critical values
                                if status == "Critical":
                                    status_label.configure(foreground="red", font=("Arial", 9, "bold"))
                                elif status == "Warning":
                                    status_label.configure(foreground="orange", font=("Arial", 9, "bold"))
                                status_label.pack(padx=5, pady=2, fill="both")
                                
                                row += 1
                            except Exception as e:
                                logging.error(f"Error parsing NVMe attribute: {e} - {line}")
                    
                    if not found_attributes:
                        ttk.Label(scrollable_frame, text="No NVMe health information available").pack(padx=10, pady=10)
                else:
                    # Handle traditional SATA format
                    found_attributes = False
                    row = 1
                    
                    # Create a proper table with consistent column widths for SATA format
                    table_frame = ttk.Frame(scrollable_frame, relief="solid", borderwidth=1)
                    table_frame.pack(fill="both", expand=True, padx=5, pady=5)
                    
                    # Fixed column widths
                    col_widths = [5, 25, 10, 10, 10, 10]  # Character widths for each column
                    
                    # Add headers with borders
                    sata_headers = ["ID", "Attribute", "Value", "Worst", "Threshold", "Status"]
                    for i, header in enumerate(sata_headers):
                        header_cell = ttk.Frame(table_frame, relief="solid", borderwidth=1)
                        header_cell.grid(row=0, column=i, sticky="nsew")
                        header_label = ttk.Label(header_cell, text=header, font=("Arial", 9, "bold"), width=col_widths[i], anchor="center")
                        header_label.pack(padx=5, pady=2)
                    
                    # Configure column weights to maintain sizes
                    for i in range(len(sata_headers)):
                        table_frame.columnconfigure(i, weight=1)
                    for line in attributes_data:
                        # Skip headers and empty lines
                        if not line.strip() or "ID#" in line or "Attribute" in line or "smartctl" in line or "Copyright" in line or "START OF" in line:
                            continue
                        
                        found_attributes = True
                        parts = line.split()
                        if len(parts) >= 6:  # Ensure line has enough parts
                            try:
                                # Extract components based on standard smartctl output format
                                attr_id = parts[0]
                                attr_name = parts[1]
                                attr_value = parts[3]
                                attr_worst = parts[4]
                                attr_threshold = parts[5]
                                
                                # Determine status
                                attr_status = "OK"
                                if attr_name in critical_attributes:
                                    if int(attr_value) > 0 and attr_name in ["Reallocated_Sector_Ct", "Current_Pending_Sector", "Offline_Uncorrectable"]:
                                        attr_status = "Critical"
                                
                                # Add data row to table with borders
                                # ID column
                                id_cell = ttk.Frame(table_frame, relief="solid", borderwidth=1)
                                id_cell.grid(row=row, column=0, sticky="nsew")
                                id_label = ttk.Label(id_cell, text=attr_id, width=col_widths[0], anchor="center")
                                id_label.pack(padx=5, pady=2, fill="both")
                                
                                # Attribute name column
                                name_cell = ttk.Frame(table_frame, relief="solid", borderwidth=1)
                                name_cell.grid(row=row, column=1, sticky="nsew")
                                name_label = ttk.Label(name_cell, text=attr_name, width=col_widths[1], anchor="w")
                                name_label.pack(padx=5, pady=2, fill="both")
                                
                                # Value column
                                value_cell = ttk.Frame(table_frame, relief="solid", borderwidth=1)
                                value_cell.grid(row=row, column=2, sticky="nsew")
                                value_label = ttk.Label(value_cell, text=attr_value, width=col_widths[2], anchor="center")
                                value_label.pack(padx=5, pady=2, fill="both")
                                
                                # Worst column
                                worst_cell = ttk.Frame(table_frame, relief="solid", borderwidth=1)
                                worst_cell.grid(row=row, column=3, sticky="nsew")
                                worst_label = ttk.Label(worst_cell, text=attr_worst, width=col_widths[3], anchor="center")
                                worst_label.pack(padx=5, pady=2, fill="both")
                                
                                # Threshold column
                                threshold_cell = ttk.Frame(table_frame, relief="solid", borderwidth=1)
                                threshold_cell.grid(row=row, column=4, sticky="nsew")
                                threshold_label = ttk.Label(threshold_cell, text=attr_threshold, width=col_widths[4], anchor="center")
                                threshold_label.pack(padx=5, pady=2, fill="both")
                                
                                # Status column
                                status_cell = ttk.Frame(table_frame, relief="solid", borderwidth=1)
                                status_cell.grid(row=row, column=5, sticky="nsew")
                                status_label = ttk.Label(status_cell, text=attr_status, width=col_widths[5], anchor="center")
                                
                                # Style critical values
                                if attr_status == "Critical":
                                    status_label.configure(foreground="red", font=("Arial", 9, "bold"))
                                status_label.pack(padx=5, pady=2, fill="both")
                                
                                row += 1
                            except (IndexError, ValueError) as e:
                                logging.error(f"Error parsing SMART attribute: {e} - {line}")
                    
                    if not found_attributes:
                        ttk.Label(scrollable_frame, text="No S.M.A.R.T. attributes available for this drive").pack(padx=10, pady=10)
            else:
                ttk.Label(scrollable_frame, text="S.M.A.R.T. attributes unavailable without root access").pack(padx=10, pady=10)
            
        except Exception as e:
            logging.error(f"Error getting S.M.A.R.T. data: {e}")
            ttk.Label(parent_frame, text=f"Error retrieving S.M.A.R.T. data: {str(e)}", 
                     font=("Arial", 10)).pack(padx=5, pady=10)
    def display_partition_table(self, parent_frame, partition_data):
        """Display partition information in a table format"""
        if not partition_data:
            ttk.Label(parent_frame, text="No partition information available", 
                      font=("Arial", 10)).pack(padx=5, pady=10)
            return
        
        # Create a frame for the table
        table_frame = ttk.Frame(parent_frame)
        table_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Define headers based on partition data fields
        headers = ["Device", "Size", "Type", "Mount Point", "Label", "UUID"]
        
        # Create header row
        for i, header in enumerate(headers):
            ttk.Label(table_frame, text=header, font=("Arial", 9, "bold"),
                  foreground=self.colors["primary"]).grid(
                row=0, column=i, sticky="w", padx=5, pady=2
            )
        
        # Add partition rows
        for i, partition in enumerate(partition_data, 1):
            # Device name
            device_name = f"/dev/{partition['name']}"
            ttk.Label(table_frame, text=device_name, font=("Courier", 9)).grid(
                row=i, column=0, sticky="w", padx=5, pady=2
            )
            
            # Size
            ttk.Label(table_frame, text=partition["size"], font=("Courier", 9)).grid(
                row=i, column=1, sticky="w", padx=5, pady=2
            )
            
            # Type/Filesystem
            fs_type = partition["fstype"] if partition["fstype"] else "Unknown"
            ttk.Label(table_frame, text=fs_type, font=("Courier", 9)).grid(
                row=i, column=2, sticky="w", padx=5, pady=2
            )
            
            # Mount point
            mount_point = partition["mountpoint"] if partition["mountpoint"] else "Not mounted"
            ttk.Label(table_frame, text=mount_point, font=("Courier", 9)).grid(
                row=i, column=3, sticky="w", padx=5, pady=2
            )
            
            # Label
            label = partition["label"] if partition["label"] else ""
            ttk.Label(table_frame, text=label, font=("Courier", 9)).grid(
                row=i, column=4, sticky="w", padx=5, pady=2
            )
            
            # UUID
            uuid = partition["uuid"] if partition["uuid"] else ""
            ttk.Label(table_frame, text=uuid, font=("Courier", 9)).grid(
                row=i, column=5, sticky="w", padx=5, pady=2
            )
        
        # Add an info button for more details
        for i, partition in enumerate(partition_data, 1):
            info_button = ttk.Button(
                table_frame, 
                text="Details", 
                command=lambda p=partition: self.show_partition_details(p)
            )
            info_button.grid(row=i, column=6, padx=5, pady=2)
    
    def show_partition_details(self, partition):
        """Show detailed information for a specific partition"""
        # Create a new top-level window for details
        details_window = tk.Toplevel(self.master)
        details_window.title(f"Partition Details: {partition['name']}")
        details_window.geometry("600x400")
        
        # Create a frame for the details
        details_frame = ttk.Frame(details_window, padding=10)
        details_frame.pack(fill="both", expand=True)
        
        # Add a header
        ttk.Label(details_frame, text=f"Detailed Information for /dev/{partition['name']}", 
                  font=("Arial", 12, "bold"), foreground=self.colors["primary"]).pack(anchor="w", pady=10)
        
        # Create a frame for the detailed information
        info_frame = ttk.Frame(details_frame)
        info_frame.pack(fill="both", expand=True)
        
        # Display all partition details
        row = 0
        detail_items = [
            ("Device", f"/dev/{partition['name']}"),
            ("Size", partition["size"]),
            ("Filesystem Type", partition["fstype"]),
            ("Mount Point", partition["mountpoint"] if partition["mountpoint"] else "Not mounted"),
            ("Label", partition["label"]),
            ("UUID", partition["uuid"]),
            ("Partition UUID", partition["partuuid"]),
            ("Partition Label", partition["partlabel"]),
            ("Flags", partition["flags"])
        ]
        
        for label, value in detail_items:
            ttk.Label(info_frame, text=f"{label}:", font=("Arial", 10, "bold"),
                  foreground=self.colors["text_primary"]).grid(
                row=row, column=0, sticky="w", padx=5, pady=2
            )
            ttk.Label(info_frame, text=value if value else "None", font=("Courier", 10)).grid(
                row=row, column=1, sticky="w", padx=5, pady=2
            )
            row += 1
        
        # Add buttons for actions
        button_frame = ttk.Frame(details_frame)
        button_frame.pack(fill="x", pady=10)
        
        # Mount button (if not mounted)
        if not partition["mountpoint"]:
            mount_button = ttk.Button(
                button_frame, 
                text="Mount Partition", 
                command=lambda: self.log_message(f"Mount requested for /dev/{partition['name']}")
            )
            mount_button.pack(side="left", padx=5)
        
        # Close button
        close_button = ttk.Button(
            button_frame, 
            text="Close", 
            command=details_window.destroy
        )
        close_button.pack(side="right", padx=5)
    
    def _run_disk_benchmark(self, disk, test_type, size, temp_dir):
        """Run disk benchmark and return results
        
        Args:
            disk: Disk path to test
            test_type: Type of test to run ('sequential', 'random', 'all')
            size: Size of test file in MB
            temp_dir: Temporary directory for test files
            
        Returns:
            dict: Dictionary containing benchmark results
        """
        import time
        import os
        
        test_file = os.path.join(temp_dir, 'speedtest.tmp')
        block_size = 1024 * 1024  # 1MB blocks
        file_size = size * 1024 * 1024  # Convert MB to bytes
        
        try:
            # Sequential write test
            if test_type in ['sequential', 'all']:
                start_time = time.time()
                with open(test_file, 'wb') as f:
                    for _ in range(file_size // block_size):
                        # Write random data
                        f.write(os.urandom(block_size))
                        f.flush()
                        os.fsync(f.fileno())
                write_time = time.time() - start_time
                write_speed = (file_size / (1024 * 1024)) / write_time  # MB/s
            else:
                write_speed = 0
            
            # Sequential read test
            if test_type in ['sequential', 'all'] and os.path.exists(test_file):
                start_time = time.time()
                with open(test_file, 'rb') as f:
                    while f.read(block_size):  # Read through the file
                        pass
                read_time = time.time() - start_time
                read_speed = (file_size / (1024 * 1024)) / read_time  # MB/s
            else:
                read_speed = 0
                
            # Clean up
            if os.path.exists(test_file):
                os.remove(test_file)
                
            return {
                'write_speed': write_speed,
                'read_speed': read_speed,
                'test_type': test_type,
                'file_size_mb': size,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            self.log_message(f"Error running disk benchmark: {str(e)}")
            return None
            
    def run_disk_speed_test(self):
        """Run a disk speed test and display results"""
        import tempfile
        import threading
        
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Get a writable disk path (using the first available disk or temp directory)
            disk_path = temp_dir
            
            # Update status
            self.log_message("Running disk speed test (this may take a minute)...")
            
            # Run benchmark in a separate thread to keep UI responsive
            def run_test():
                result = self._run_disk_benchmark(
                    disk=disk_path,
                    test_type='sequential',
                    size=100,  # 100MB test file
                    temp_dir=temp_dir
                )
                
                if result:
                    # Format results
                    results = (
                        f"=== Disk Speed Test Results ===\n"
                        f"Test Type: {result['test_type']}\n"
                        f"File Size: {result['file_size_mb']} MB\n"
                        f"Write Speed: {result['write_speed']:.2f} MB/s\n"
                        f"Read Speed: {result['read_speed']:.2f} MB/s\n"
                        f"Tested on: {result['timestamp']}"
                    )
                    
                    # Update UI with results
                    self.after(0, lambda: self.log_message(results))
                else:
                    self.after(0, lambda: self.log_message("Error: Could not complete disk speed test"))
            
            # Start the test in a separate thread
            test_thread = threading.Thread(target=run_test, daemon=True)
            test_thread.start()
            
    def setup_system_info_tab(self):
        """Set up the System Information tab with detailed system information"""
        # Initialize label dictionaries for updating later
        self.system_info_labels = {}
        # Preserve existing hardware_info_labels if they exist
        if not hasattr(self, 'hardware_info_labels'):
            self.hardware_info_labels = {}
        # Don't reset hardware_info_labels! It already contains our battery labels!
        # Log existing labels to confirm they're preserved
        if hasattr(self, 'hardware_info_labels'):
            logging.info(f"Preserving existing hardware_info_labels with {len(self.hardware_info_labels)} items")
            logging.info(f"Preserved labels: {list(self.hardware_info_labels.keys())}")
        self.storage_info_labels = {}

        # Get the system tab from device tabs
        system_tab = self.device_tabs["system"]
        
        # Create a frame for the system info content
        system_frame = ttk.Frame(system_tab)
        system_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create container frame that dynamically sizes based on parent
        info_container = ttk.Frame(system_frame)
        info_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Get container to use all available space by preventing propagation
        info_container.pack_propagate(False)
        
        # Set up a window resize handler to adjust the container height
        def update_container_size(event=None):
            # Get the parent container's height (system_tab)
            tab_height = system_tab.winfo_height()
            # Use most of available height but leave room for padding/margins
            if tab_height > 50:  # Only resize if we have meaningful height
                # Calculate available height, account for padding and other elements
                available_height = tab_height - 40  # Subtract padding/margins
                info_container.configure(height=available_height)
                self.info_canvas.configure(height=available_height - 10)  # Slight adjustment for inner padding
        
        # Bind to Configure events for dynamic resizing
        system_tab.bind("<Configure>", update_container_size)
        
        # Create canvas and scrollbar for scrolling
        self.info_canvas = tk.Canvas(info_container, highlightthickness=0)
        self.info_canvas.pack(side="left", fill="both", expand=True)
        
        # Add scrollbar back - this is essential
        info_scrollbar = ttk.Scrollbar(info_container, orient="vertical", command=self.info_canvas.yview)
        info_scrollbar.pack(side="right", fill="y")
        
        # Configure the canvas
        self.info_canvas.configure(yscrollcommand=info_scrollbar.set)
        
        # Create a frame inside the canvas to hold content
        info_frame = ttk.Frame(self.info_canvas)
        
        # Create a window in the canvas to display the frame
        self.info_canvas_frame = self.info_canvas.create_window((0, 0), window=info_frame, anchor="nw")
        
        # Configure canvas resize handling
        def _configure_info_canvas(event):
            # Update the scrollregion to encompass the inner frame
            self.info_canvas.configure(scrollregion=self.info_canvas.bbox("all"))
            # Update canvas window width to match canvas width
            self.info_canvas.itemconfig(self.info_canvas_frame, width=event.width)
            
        info_frame.bind("<Configure>", _configure_info_canvas)
        self.info_canvas.bind("<Configure>", lambda e: self.info_canvas.itemconfig(self.info_canvas_frame, width=e.width))
        
        # Header for system information with brand styling
        header_label = ttk.Label(
            info_frame, text="System Information", font=("Arial", 12, "bold"),
            foreground=self.colors["primary"]
        )
        header_label.pack(anchor="w", pady=5)
        
        # Place system information content directly in info_frame (no inner notebook)
        system_frame = ttk.LabelFrame(info_frame, text="Operating System")
        system_frame.pack(fill="both", expand=True, pady=5, padx=3, ipady=5)
        
        # Define the scroll region update function (was removed with the notebook)
        def update_info_canvas_width(event):
            canvas_width = event.width
            self.info_canvas.itemconfig(self.info_canvas_frame, width=canvas_width)
        self.info_canvas.bind("<Configure>", update_info_canvas_width)

        # Add mousewheel scrolling
        def _info_on_mousewheel(event):
            self.info_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        # Store the mousewheel function for binding/unbinding
        self._info_mousewheel_func = _info_on_mousewheel
        # We'll bind when tab is selected and unbind when leaving the tab
        # Initial binding since the tab is currently active
        self.info_canvas.bind_all("<MouseWheel>", self._info_mousewheel_func)
        def update_info_scroll_region(event=None):
            self.info_canvas.configure(scrollregion=self.info_canvas.bbox("all"))
        # Update the scroll region when the size of scrollable_frame changes
        info_frame.bind("<Configure>", update_info_scroll_region)
        
        
        self.info_canvas.bind("<Configure>", update_info_canvas_width)
        
        # Add mousewheel scrolling
        def _info_on_mousewheel(event):
            self.info_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        # Store the mousewheel function for binding/unbinding
        self._info_mousewheel_func = _info_on_mousewheel
        
        # We'll bind when tab is selected and unbind when leaving the tab
        # Initial binding since the tab is currently active
        self.info_canvas.bind_all("<MouseWheel>", self._info_mousewheel_func)
        
        
        # Gather system information
        # Calculate boot time and uptime
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
            boot_time = time.time() - uptime_seconds
            boot_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(boot_time))
            
            # Format uptime nicely
            days, remainder = divmod(uptime_seconds, 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, seconds = divmod(remainder, 60)
            uptime_str = f"{int(days)} days, {int(hours)} hours, {int(minutes)} minutes"
        except Exception as e:
            logging.error(f"Error calculating boot time/uptime: {e}")
            boot_time_str = "Error calculating"
            uptime_str = "Error calculating"
        
        # Get kernel version
        try:
            kernel_version = platform.release()
        except:
            kernel_version = "Unknown"
            
        # Get desktop environment
        try:
            desktop_env = "Unknown"
            de_vars = ['XDG_CURRENT_DESKTOP', 'DESKTOP_SESSION', 'GNOME_DESKTOP_SESSION_ID']
            for var in de_vars:
                if var in os.environ:
                    desktop_env = os.environ[var]
                    break
        except:
            desktop_env = "Unknown"
        
        # Check for systemd (init system)
        try:
            init_system = "Unknown"
            if os.path.exists('/usr/bin/systemctl') or os.path.exists('/bin/systemctl'):
                init_system = "systemd"
            elif os.path.exists('/sbin/init'):
                # Check if init is a symlink to systemd
                if os.path.islink('/sbin/init') and 'systemd' in os.readlink('/sbin/init'):
                    init_system = "systemd"
                else:
                    init_system = "SysV or other"
        except:
            init_system = "Unknown"
        
        # Count pending updates (for apt-based systems)
        try:
            updates_available = "Checking..."
            # This will be updated later in a background thread
        except:
            updates_available = "Unknown"
        
        # Get Python version
        try:
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        except:
            python_version = "Unknown"
        
        # Get last update time (for apt-based systems)
        try:
            last_update = "Checking..."
            # This will be updated later in a background thread
        except:
            last_update = "Unknown"
        
        system_info = {
            "OS": f"{platform.system()} {platform.release()}",
            "Version": platform.version(),
            "Build": platform.uname().version,
            "Kernel": kernel_version,
            "Desktop Environment": desktop_env,
            "Init System": init_system,
            "Python Version": python_version,
            "Updates Available": updates_available,
            "Last System Update": last_update,
            "Architecture": platform.machine(),
            "Computer Name": platform.node(),
            "User": os.environ.get('USER', 'Unknown'),
            "Boot Time": boot_time_str,
            "Uptime": uptime_str,
        }
        
        # Configure grid weights to allow resizing
        system_frame.grid_columnconfigure(0, weight=1, minsize=150)
        system_frame.grid_columnconfigure(1, weight=3, minsize=300)
        
        # Display system information
        row = 0
        for key, value in system_info.items():
            # Key with bold font
            key_label = ttk.Label(system_frame, text=f"{key}:", font=("Arial", 10, "bold"))
            key_label.grid(row=row, column=0, sticky="w", padx=5, pady=2)
            
            # Value with monospace font for technical information
            value_label = ttk.Label(system_frame, text=value, font=("Courier", 10), wraplength=500, justify="left")
            value_label.grid(row=row, column=1, sticky="w", padx=5, pady=2)
            
            # Store reference to this label for refreshing later
            self.system_info_labels[key] = value_label
            
            row += 1
    
    def _process_wifi_interface(self, interface, if_info):
        """Process WiFi interface details"""
        try:
            # Try to get detailed WiFi info using iw
            iw_result = subprocess.run(
                ['iw', 'dev', interface, 'link'],
                capture_output=True, text=True, timeout=2
            )
            
            if iw_result.returncode == 0 and iw_result.stdout.strip():
                ssid = "Not connected"
                signal = "N/A"
                tx_bitrate = "N/A"
                rx_bitrate = "N/A"
                freq = "N/A"
                
                for line in iw_result.stdout.split('\n'):
                    line = line.strip()
                    if 'SSID:' in line:
                        ssid = line.split('SSID:')[1].strip() or "(hidden)"
                    elif 'tx bitrate:' in line:
                        tx_bitrate = line.split('tx bitrate:')[1].strip()
                    elif 'rx bitrate:' in line:
                        rx_bitrate = line.split('rx bitrate:')[1].strip()
                    elif 'signal:' in line:
                        signal_parts = line.split('signal:')
                        if len(signal_parts) > 1:
                            signal = signal_parts[1].split()[0].strip() + ' dBm'
                    elif 'freq:' in line:
                        freq_parts = line.split('freq:')
                        if len(freq_parts) > 1:
                            freq = freq_parts[1].strip()
                
                # Update interface info with WiFi details
                if_info['SSID'] = ssid
                if_info['Signal'] = signal
                if_info['Frequency'] = freq
                
                # Process bitrates if available
                if rx_bitrate != "N/A":
                    rx_value = self._extract_mbit_value(rx_bitrate)
                    if rx_value is not None:
                        if_info['Download'] = f"{rx_value:.1f} MBit/s"
                
                if tx_bitrate != "N/A":
                    tx_value = self._extract_mbit_value(tx_bitrate)
                    if tx_value is not None:
                        if_info['Upload'] = f"{tx_value:.1f} MBit/s"
                
                # Add ping information if connected
                if ssid != "Not connected":
                    self._add_ping_info(if_info)
                    
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            logging.debug(f"Could not get WiFi info for {interface}: {e}")
            if_info['WiFi Status'] = 'Error getting WiFi information'
    
    def _get_network_interfaces(self):
        """Get network interfaces and their information
        
        Returns:
            dict: Dictionary with interface names as keys and interface info as values
        """
        interfaces = {}
        
        try:
            # Get all network interfaces using psutil
            net_if_addrs = psutil.net_if_addrs()
            net_if_stats = psutil.net_if_stats()
            net_io_counters = psutil.net_io_counters(pernic=True)
            
            # Process each interface
            for interface, addrs in net_if_addrs.items():
                if_info = {
                    'Name': interface,
                    'Status': 'Up' if net_if_stats.get(interface, None) and net_if_stats[interface].isup else 'Down',
                    'MTU': str(net_if_stats.get(interface, None) and net_if_stats[interface].mtu or 0)
                }
                
                # Add traffic stats if available
                if interface in net_io_counters:
                    if_info['Bytes Sent'] = self._format_bytes(net_io_counters[interface].bytes_sent)
                    if_info['Bytes Received'] = self._format_bytes(net_io_counters[interface].bytes_recv)
                    if_info['Packets Sent'] = str(net_io_counters[interface].packets_sent)
                    if_info['Packets Received'] = str(net_io_counters[interface].packets_recv)
                    if_info['Errors In'] = str(net_io_counters[interface].errin)
                    if_info['Errors Out'] = str(net_io_counters[interface].errout)
                    if_info['Dropped In'] = str(net_io_counters[interface].dropin)
                    if_info['Dropped Out'] = str(net_io_counters[interface].dropout)
                
                # Process addresses
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        if_info['IPv4 Address'] = addr.address
                        if_info['IPv4 Netmask'] = addr.netmask
                    elif addr.family == socket.AF_INET6:
                        if_info['IPv6 Address'] = addr.address
                    elif addr.family == psutil.AF_LINK:
                        if_info['MAC Address'] = addr.address
                
                # Add interface to result
                interfaces[interface] = if_info
                
                # Add ping info for non-loopback interfaces
                if interface != 'lo':
                    self._add_ping_info(if_info)
                    
                # Add WiFi info if this is a wireless interface
                if interface.startswith('wl') or 'wifi' in interface.lower() or 'wlan' in interface.lower():
                    try:
                        wifi_info = self._get_wifi_info(interface)
                        for key, value in wifi_info.items():
                            if key != 'rate':
                                if_info[f"WiFi {key.title()}"] = value
                    except Exception as e:
                        logging.error(f"Error getting WiFi info: {e}")
                        if_info['WiFi Status'] = 'Error'
                            
            return interfaces
        except Exception as e:
            logging.error(f"Error getting network interfaces: {e}")
            return {"Error": {"Status": f"Error: {str(e)}"}}
    
    def _add_general_network_info(self, parent_frame):
        """Add general network information to the parent frame"""
        try:
            info_grid = ttk.Frame(parent_frame)
            info_grid.pack(fill="both", expand=True, padx=5, pady=5)
            
            # Host information
            host_info = {
                'Hostname': socket.gethostname(),
                'FQDN': socket.getfqdn(),
                'IP Address': self._get_primary_ip(),
                'DNS Servers': self._get_dns_servers(),
                'Default Gateway': self._get_default_gateway(),
                'Internet Connection': self._check_internet_connection()
            }
            
            # Display host info in a grid
            row = 0
            for key, value in host_info.items():
                if value:  # Only show non-empty values
                    ttk.Label(
                        info_grid,
                        text=f"{key}:",
                        font=("Arial", 9, "bold"),
                        width=18,
                        anchor="w"
                    ).grid(row=row, column=0, sticky="w", padx=5, pady=2)
                    
                    label = ttk.Label(
                        info_grid,
                        text=value,
                        font=("Arial", 9),
                        anchor="w"
                    )
                    label.grid(row=row, column=1, sticky="w", padx=5, pady=2)
                    
                    # Store label reference for updating
                    self.network_info_labels[key] = label
                    
                    row += 1
                    
        except Exception as e:
            logging.error(f"Error adding general network info: {e}")
            ttk.Label(
                parent_frame,
                text=f"Error loading network information: {str(e)}",
                font=("Arial", 9),
                foreground="red"
            ).pack(fill="x", padx=5, pady=5)
    
    def _get_primary_ip(self):
        """Get the primary IP address of the machine"""
        try:
            # Create a socket connection to a public IP and get the local address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            logging.error(f"Error getting primary IP: {e}")
            return "Not available"
    
    def _get_dns_servers(self):
        """Get DNS servers from /etc/resolv.conf"""
        try:
            dns_servers = []
            
            if os.path.exists('/etc/resolv.conf'):
                with open('/etc/resolv.conf', 'r') as f:
                    for line in f:
                        if line.startswith('nameserver'):
                            dns_servers.append(line.split()[1])
            
            return ', '.join(dns_servers) if dns_servers else "Not available"
        except Exception as e:
            logging.error(f"Error getting DNS servers: {e}")
            return "Not available"
    
    def _get_default_gateway(self):
        """Get the default gateway"""
        try:
            # Try to get the default gateway using /proc/net/route
            with open('/proc/net/route', 'r') as f:
                for line in f.readlines()[1:]:
                    fields = line.strip().split()
                    if fields[1] == '00000000' and int(fields[3], 16) & 2:  # Default route has dest 0.0.0.0 and RTF_GATEWAY flag
                        gateway = socket.inet_ntoa(struct.pack("<L", int(fields[2], 16)))
                        return gateway
            
            return "Not available"
        except Exception as e:
            logging.error(f"Error getting default gateway: {e}")
            return "Not available"
    
    def _check_internet_connection(self):
        """Check if there is an active internet connection"""
        try:
            # Try to connect to a reliable server
            socket.create_connection(("8.8.8.8", 53), timeout=1)
            return "Connected"
        except Exception:
            return "Disconnected"
            
    def _format_bytes(self, num_bytes):
        """Format bytes to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if num_bytes < 1024.0:
                return f"{num_bytes:.2f} {unit}"
            num_bytes /= 1024.0
        return f"{num_bytes:.2f} PB"
            
    def _add_ping_info(self, if_info):
        """Add ping information to interface info"""
        try:
            # Try to ping a reliable server
            result = subprocess.run(['ping', '-c', '1', '-W', '1', '8.8.8.8'], capture_output=True, text=True)
            if result.returncode == 0:
                # Extract ping time
                for line in result.stdout.splitlines():
                    if 'time=' in line:
                        ping_time = line.split('time=')[1].split()[0]
                        if_info['Ping (8.8.8.8)'] = ping_time
                        break
        except Exception as e:
            logging.error(f"Error pinging: {e}")
            if_info['Ping (8.8.8.8)'] = 'Error'
    
    def run_speed_test(self):
        """Run a network speed test and update the UI with results"""
        if hasattr(self, 'test_running') and self.test_running:
            return
            
        self.test_running = True
        self.test_button.config(state='disabled', text='Testing...')
        
        # Reset UI
        self.download_speed.config(text="0.00 Mbps")
        self.upload_speed.config(text="0.00 Mbps")
        self.ping_label.config(text="-- ms")
        self.server_label.config(text="Finding best server...")
        self.phase_label.config(text="Initializing speed test...")
        self.progress_bar_green['value'] = 0
        self.progress_bar_blue['value'] = 0
        
        # Variables to track test progress
        self.test_phase = 0  # 0=initializing, 1=download, 2=upload, 3=complete
        self.test_start_time = time.time()
        self.last_progress_update = 0
        
        def update_progress():
            if not hasattr(self, 'test_running') or not self.test_running:
                return
                
            current_time = time.time()
            elapsed = current_time - self.test_start_time
            test_complete = self.test_phase == 3  # Test is complete when phase is 3
            
            # Only update progress if test is still running
            if not test_complete:
                # Different progress patterns based on test phase
                if self.test_phase == 0:  # Initializing
                    # 0-5% during init (faster init phase)
                    progress = min(5, (elapsed / 1.0) * 5)
                    if progress >= 5 and self.test_phase == 0:
                        self.test_phase = 1
                        self.test_start_time = current_time
                        self.phase_label.after(0, lambda: self.phase_label.config(
                            text="Testing download speed..."))
                
                elif self.test_phase == 1:  # Download test (longest phase)
                    # 0-50% for download (takes ~10-15s)
                    progress = 0 + min(50, (elapsed / 15.0) * 50)
                
                elif self.test_phase == 2:  # Upload test
                    # 50-100% for upload (takes ~15-20s)
                    progress = 50 + min(50, (elapsed / 15.0) * 50)
                    
                    # If we're still in upload after 30 seconds, cap at 100%
                    if elapsed > 30:
                        progress = 100
                        

                
                # Update progress bars with split color effect
                if progress > getattr(self, 'last_progress', 0):  # Only move forward, never backward
                    # Update the progress values for both bars
                    if progress <= 50:
                        # Only update green bar (0-50% of total)
                        self.progress_bar_green['value'] = progress * 2  # Scale 0-50 to 0-100
                        self.progress_bar_blue['value'] = 0
                    else:
                        # Green bar stays at 100%, update blue bar (50-100% of total)
                        self.progress_bar_green['value'] = 100
                        self.progress_bar_blue['value'] = (progress - 50) * 2  # Scale 50-100 to 0-100
                    
                    self.last_progress = progress
            
            # Continue updating if not complete or still in progress
            if (not test_complete or self.test_phase < 3) and hasattr(self, 'test_running') and self.test_running:
                self.after(100, update_progress)
            elif test_complete or self.test_phase >= 3:
                # Only update button state here, progress is handled in the test completion
                self.test_button.after(0, lambda: self.test_button.config(
                    state='normal', text='Test Again'))
                self.test_running = False
        
        # Initialize progress tracking
        self.current_style = 'green'
        
        # Start progress updates
        self.after(100, update_progress)
        
        # Run the actual speed test in a separate thread
        def run_test():
            try:
                import speedtest
                
                def update_download_speed(current, total, start=False, end=False):
                    if start:
                        return  # Skip start callback
                    if end:
                        return total  # Return final speed
                    
                    # Update UI with current speed
                    speed_mbps = current / 1_000_000
                    self.download_speed.after(0, lambda: self.download_speed.config(
                        text=f"{speed_mbps:.2f} Mbps"))
                    return current
                
                def update_upload_speed(current, total, start=False, end=False):
                    if start:
                        return  # Skip start callback
                    if end:
                        return total  # Return final speed
                    
                    # Update UI with current speed
                    speed_mbps = current / 1_000_000
                    self.upload_speed.after(0, lambda: self.upload_speed.config(
                        text=f"{speed_mbps:.2f} Mbps"))
                    return current
                
                # Create speedtest object with callbacks
                st = speedtest.Speedtest()
                
                # Find best server with progress updates
                self.server_label.after(0, lambda: self.server_label.config(text="Server: Finding best server..."))
                try:
                    server = st.get_best_server()
                    # Update server info
                    self.server_label.after(0, lambda: self.server_label.config(
                        text=f"{server['name']} ({server['country']})"))
                except Exception as e:
                    error_msg = f"Failed to find server: {str(e)}"
                    self.server_label.after(0, lambda: self.server_label.config(
                        text=error_msg))
                    self.phase_label.after(0, lambda: self.phase_label.config(
                        text=error_msg, foreground="#F44336"))
                    return
                
                # Test download speed with progress
                self.phase_label.after(0, lambda: self.phase_label.config(
                    text="Testing download speed..."))
                try:
                    # Run download test and wait for completion
                    download_speed = st.download(callback=update_download_speed)
                    self.download_speed.after(0, lambda: self.download_speed.config(
                        text=f"{download_speed / 1_000_000:.2f} Mbps"))
                    
                    # Move to upload phase in progress tracking
                    self.test_phase = 2
                    self.test_start_time = time.time()
                    # No need to reset style flag as we're using dynamic updates now
                    
                    # Test upload speed with progress
                    self.phase_label.after(0, lambda: self.phase_label.config(
                        text="Testing upload speed..."))
                    
                    # Run upload test and wait for completion
                    upload_speed = st.upload(callback=update_upload_speed, threads=1)
                    self.upload_speed.after(0, lambda: self.upload_speed.config(
                        text=f"{upload_speed / 1_000_000:.2f} Mbps"))
                    
                    # Get final results
                    results = st.results.dict()
                    
                    # Update UI with final results
                    self.ping_label.after(0, lambda: self.ping_label.config(
                        text=f"{results['ping']:.0f} ms"))
                    
                    # Mark test as complete and update progress to 100%
                    self.test_phase = 3  # Mark test as complete
                    # Update both progress bars to show completion
                    self.progress_bar_green.after(0, lambda: self.progress_bar_green.config(value=100))
                    self.progress_bar_blue.after(0, lambda: self.progress_bar_blue.config(value=100))
                    self.phase_label.after(0, lambda: self.phase_label.config(
                        text="Test completed successfully!", 
                        foreground=self.colors["primary"]))
                    
                except Exception as e:
                    error_msg = f"Speed test failed: {str(e)}"
                    self.phase_label.after(0, lambda msg=error_msg: self.phase_label.config(
                        text=msg, foreground="#F44336"))
                    raise Exception(error_msg)
                
            except Exception as e:
                error_msg = str(e)
                logging.error(f"Speed test error: {error_msg}")
                self.server_label.after(0, lambda: self.server_label.config(
                    text="Error"))
                self.phase_label.after(0, lambda msg=error_msg: self.phase_label.config(
                    text=f"Error: {msg}", 
                    foreground="#F44336"))
            finally:
                self.test_running = False
                self.test_button.after(0, lambda: self.test_button.config(
                    state='normal', text='Start Speed Test'))
        
        # Start the test in a separate thread
        import threading
        test_thread = threading.Thread(target=run_test, daemon=True)
        test_thread.start()

    def _display_interface_info(self, parent, if_info):
        """Display interface information in the UI"""
        for key, value in if_info.items():
            # Skip WiFi speed related entries
            if key.lower() in ['wifi speed', 'speed']:
                continue
                
            if value:  # Only show non-empty values
                info_frame = ttk.Frame(parent)
                info_frame.pack(fill="x", padx=5, pady=2)
                
                ttk.Label(
                    info_frame,
                    text=f"{key}:",
                    font=("Arial", 9, "bold"),
                    width=15,
                    anchor="w"
                ).pack(side="left")
                
                ttk.Label(
                    info_frame,
                    text=value,
                    font=("Arial", 9),
                    anchor="w"
                ).pack(side="left", fill="x", expand=True)
    
    def get_cpu_temp(self):
        """Get CPU temperature with support for Intel, AMD, and ARM processors.
        Returns the temperature in Celsius or None if unavailable.
        """
        # Detect CPU architecture and vendor
        try:
            arch = platform.machine()
            cpu_vendor = "Unknown"
            
            # Check for x86/x64 architecture
            if arch in ['x86_64', 'i386', 'i686', 'AMD64']:
                # Detect vendor (Intel vs AMD)
                try:
                    with open('/proc/cpuinfo', 'r') as f:
                        cpuinfo = f.read()
                        if 'AuthenticAMD' in cpuinfo:
                            cpu_vendor = "AuthenticAMD"
                        elif 'GenuineIntel' in cpuinfo:
                            cpu_vendor = "GenuineIntel"
                except Exception as e:
                    logging.debug(f"Error reading CPU vendor: {e}")
            
            logging.debug(f"Detected architecture: {arch}, vendor: {cpu_vendor}")
            
            # Try psutil first (works on many systems)
            try:
                if hasattr(psutil, "sensors_temperatures"):
                    temps = psutil.sensors_temperatures()
                    if temps:
                        # For AMD CPUs
                        if cpu_vendor == "AuthenticAMD":
                            for module in ['k10temp', 'zenpower']:
                                if module in temps and temps[module]:
                                    return temps[module][0].current
                        
                        # For Intel CPUs
                        elif cpu_vendor == "GenuineIntel":
                            if 'coretemp' in temps and temps['coretemp']:
                                return temps['coretemp'][0].current
                        
                        # For ARM
                        elif arch in ['aarch64', 'armv7l', 'armv6l']:
                            if 'cpu_thermal' in temps and temps['cpu_thermal']:
                                return temps['cpu_thermal'][0].current
                        
                        # Generic fallback - try any available temperature sensor
                        for module, entries in temps.items():
                            if entries:
                                return entries[0].current
            except (AttributeError, IndexError) as e:
                logging.debug(f"psutil temperature detection failed: {e}")
            
            # If psutil didn't work, try lm-sensors directly
            try:
                result = subprocess.run(['sensors'], capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    output = result.stdout
                    
                    # Look for temperature readings
                    for line in output.splitlines():
                        if re.search(r'(Core|Tdie|CPU|Package).*\+[0-9.]+°C', line):
                            match = re.search(r'\+([0-9.]+)°C', line)
                            if match:
                                return float(match.group(1))
            except Exception as e:
                logging.debug(f"sensors command failed: {e}")
            
            # ARM-specific method (read directly from thermal zones)
            if arch in ['aarch64', 'armv7l', 'armv6l']:
                try:
                    for zone in range(10):  # Check first 10 thermal zones
                        zone_path = f"/sys/class/thermal/thermal_zone{zone}/"
                        if os.path.exists(zone_path):
                            # Check if this is a CPU temperature sensor
                            type_path = os.path.join(zone_path, "type")
                            temp_path = os.path.join(zone_path, "temp")
                            
                            if os.path.exists(type_path) and os.path.exists(temp_path):
                                with open(type_path, 'r') as f:
                                    zone_type = f.read().strip()
                                    
                                if 'cpu' in zone_type.lower() or 'soc' in zone_type.lower():
                                    with open(temp_path, 'r') as f:
                                        temp = float(f.read().strip()) / 1000  # Convert from millidegrees
                                        return temp
                except Exception as e:
                    logging.debug(f"ARM thermal zone detection failed: {e}")
            
            return None
        
        except Exception as e:
            logging.error(f"Error detecting CPU temperature: {e}")
            return None
            
    def get_friendly_gpu_name(self, gpu_string):
        """Convert raw GPU identification strings to more user-friendly names.
        
        Args:
            gpu_string (str): The raw GPU identification string from lspci or similar tools
            
        Returns:
            str: A more user-friendly GPU name
        """
        try:
            # Remove common verbose parts
            clean_name = gpu_string
            
            # Remove PCI information and controller specifications
            patterns_to_remove = [
                r'\[.*?\]',  # Text in square brackets
                r'\(rev \w+\)',  # Revision info
                r'Corporation\s+',  # Corporation
                r'Technologies\s+Inc\.?\s*',  # Technologies Inc.
                r'Semiconductor\s+',  # Semiconductor
                r'Electronics\s+',  # Electronics
                r'Co\.,?\s+Ltd\.?\s*',  # Co., Ltd.
                r'Computer\s+',  # Computer
                r'Integrated\s+Systems\s+',  # Integrated Systems
            ]
            
            for pattern in patterns_to_remove:
                clean_name = re.sub(pattern, ' ', clean_name, flags=re.IGNORECASE)
            
            # Handle specific manufacturer formats
            if 'NVIDIA' in clean_name:
                # For NVIDIA, try to get just the model number (like RTX 3080, GTX 1660, etc.)
                nvidia_match = re.search(r'((?:RTX|GTX|GT)\s+\d+\w*)', clean_name)
                if nvidia_match:
                    clean_name = f"NVIDIA {nvidia_match.group(1)}"
                else:
                    clean_name = f"NVIDIA {clean_name.replace('NVIDIA', '').strip()}"
                    
            elif 'AMD' in clean_name or 'ATI' in clean_name or 'Radeon' in clean_name:
                # For AMD/ATI, prioritize Radeon model names
                clean_name = clean_name.replace('ATI', 'AMD')
                radeon_match = re.search(r'(Radeon\s+(?:RX|R\d+|HD)\s+\d+\w*)', clean_name, re.IGNORECASE)
                if radeon_match:
                    clean_name = f"AMD {radeon_match.group(1)}"
                else:
                    clean_name = f"AMD {clean_name.replace('Advanced Micro Devices', '').replace('AMD', '').strip()}"
                    
            elif 'Intel' in clean_name:
                # For Intel UHD/HD Graphics models
                if re.search(r'(?:UHD|HD)\s+Graphics', clean_name, re.IGNORECASE):
                    # Try to extract model number for UHD/HD Graphics
                    intel_uhd_match = re.search(r'(?:UHD|HD)\s+Graphics\s+(\d+\w*)', clean_name, re.IGNORECASE)
                    if intel_uhd_match:
                        # Format as 'Intel UHD Graphics 620' or 'Intel HD Graphics 4000'
                        model_num = intel_uhd_match.group(1)
                        if re.search(r'UHD', clean_name, re.IGNORECASE):
                            clean_name = f"Intel UHD Graphics {model_num}"
                        else:
                            clean_name = f"Intel HD Graphics {model_num}"
                    else:
                        # Just UHD/HD Graphics with no number
                        if re.search(r'UHD', clean_name, re.IGNORECASE):
                            clean_name = "Intel UHD Graphics"
                        else:
                            clean_name = "Intel HD Graphics"
                
                # For Intel Iris Graphics
                elif re.search(r'Iris', clean_name, re.IGNORECASE):
                    iris_match = re.search(r'Iris\s+(\w+)\s*(?:Graphics)*\s*(\d*)', clean_name, re.IGNORECASE)
                    if iris_match:
                        model = iris_match.group(1)
                        number = iris_match.group(2)
                        clean_name = f"Intel Iris {model}{' ' + number if number else ''}"
                    else:
                        clean_name = "Intel Iris Graphics"
                
                # For other Intel GPUs
                else:
                    # Remove common Intel prefixes/suffixes and keep the model information
                    clean_name = re.sub(r'WhiskeyLake-\w+\s+|CoffeeLake-\w+\s+|GT\d+\s+', '', clean_name, flags=re.IGNORECASE)
                    clean_name = f"Intel {clean_name.strip()}"
            
            # Clean up excessive whitespace
            clean_name = re.sub(r'\s+', ' ', clean_name).strip()
            
            # If the cleaning resulted in an empty string, return the original
            if not clean_name:
                return gpu_string
                
            return clean_name
            
        except Exception as e:
            logging.error(f"Error creating friendly GPU name: {e}")
            return gpu_string  # Return the original on error
    
    def get_gpu_freq(self):
        """Get GPU frequency using multiple detection methods for different GPU manufacturers.
        Returns the frequency in MHz or None if unavailable.
        """
        try:
            # Method 1: Check for Nvidia GPU using nvidia-smi
            if shutil.which('nvidia-smi'):
                try:
                    result = subprocess.run(
                        ['nvidia-smi', '--query-gpu=clocks.current.graphics', '--format=csv,noheader,nounits'],
                        capture_output=True, text=True, timeout=3
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        freq = float(result.stdout.strip())

                        return freq
                except Exception as e:
                    logging.error(f"Error detecting Nvidia GPU frequency: {e}")
            
            # Method 2: Check for Intel GPU using intel_gpu_top
            if shutil.which('intel_gpu_top'):
                try:
                    # Run intel_gpu_top with minimal output and terminate quickly
                    result = subprocess.run(
                        ['timeout', '1', 'intel_gpu_top', '-o', '-', '-s', '100'],
                        capture_output=True, text=True, timeout=2
                    )
                    if result.returncode in [0, 124] and result.stdout:  # 124 is timeout's exit code
                        # Parse the output looking for MHz
                        match = re.search(r'(\d+)\s*/\s*(\d+)\s*MHz', result.stdout)
                        if match:
                            current_freq = float(match.group(1))
                            max_freq = float(match.group(2))

                            return current_freq
                except Exception as e:
                    logging.error(f"Error detecting Intel GPU frequency: {e}")
            
            # Method 3: Check for AMD GPU using rocm-smi
            if shutil.which('rocm-smi'):
                try:
                    result = subprocess.run(
                        ['rocm-smi', '--showclocks'],
                        capture_output=True, text=True, timeout=3
                    )
                    if result.returncode == 0 and result.stdout:
                        # Extract GPU clock frequency
                        match = re.search(r'GPU Clock Level:\s*(\d+)\s*\((\d+)MHz\)', result.stdout)
                        if match:
                            freq = float(match.group(2))

                            return freq
                except Exception as e:
                    logging.error(f"Error detecting AMD GPU frequency: {e}")
            
            # Method 4: Check for frequency information in sysfs
            try:
                # Find available cards
                cards = glob.glob('/sys/class/drm/card*')
                for card in cards:
                    # For AMD GPUs
                    amd_path = os.path.join(card, 'device/pp_dpm_sclk')
                    if os.path.exists(amd_path):
                        with open(amd_path, 'r') as f:
                            content = f.read()
                            # Look for the active state (marked with *)
                            match = re.search(r'\*\s*\d+:\s*(\d+)MHz', content)
                            if match:
                                freq = float(match.group(1))

                                return freq
                    
                    # For Intel GPUs via i915 driver
                    intel_path = os.path.join(card, 'gt_cur_freq_mhz')
                    if os.path.exists(intel_path):
                        with open(intel_path, 'r') as f:
                            freq = float(f.read().strip())

                            return freq
            except Exception as e:
                logging.error(f"Error detecting GPU frequency via sysfs: {e}")
            
            pass
            return None
        except Exception as e:
            logging.error(f"Error in GPU frequency detection: {e}")
            return None
            
    def get_gpu_temp(self):
        """Get GPU temperature using multiple detection methods.
        Returns the temperature in Celsius or None if unavailable.
        """
        try:
            # Method 1: Check for Nvidia GPU using nvidia-smi
            if shutil.which('nvidia-smi'):
                try:
                    result = subprocess.run(
                        ['nvidia-smi', '--query-gpu=temperature.gpu', '--format=csv,noheader,nounits'],
                        capture_output=True, text=True, timeout=3
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        temp = float(result.stdout.strip())

                        return temp
                except Exception as e:
                    logging.error(f"Error detecting Nvidia GPU temperature: {e}")
            
            # Method 2: Check for Intel or AMD GPU via hwmon temp sensors
            try:
                card_path = '/sys/class/drm/card0/device/hwmon/'
                if os.path.exists(card_path):
                    # Find first hwmon directory
                    hwmon_dirs = glob.glob(os.path.join(card_path, 'hwmon*'))
                    if hwmon_dirs:
                        temp_path = os.path.join(hwmon_dirs[0], 'temp1_input')
                        if os.path.exists(temp_path):
                            with open(temp_path, 'r') as f:
                                temp_raw = int(f.read().strip())
                                temp = temp_raw / 1000.0

                                return temp
            except Exception as e:
                logging.error(f"Error detecting GPU temperature via hwmon: {e}")
            
            # Method 3: Fallback to lm-sensors
            if shutil.which('sensors'):
                try:
                    output = subprocess.check_output(['sensors'], universal_newlines=True)
                    # Look for GPU-related sensors
                    gpu_patterns = ['amdgpu', 'radeon', 'nouveau', 'nvidia', 'intel.*gpu']
                    pattern = '|'.join(gpu_patterns)
                    for line in output.split('\n'):
                        if re.search(pattern, line, re.IGNORECASE) and 'temp1' in line.lower():
                            # Extract temperature value (+45.0°C)
                            temp_match = re.search(r'\+([\d\.]+)°C', line)
                            if temp_match:
                                temp = float(temp_match.group(1))

                                return temp
                except Exception as e:
                    logging.error(f"Error detecting GPU temperature via sensors: {e}")
            
            pass
            return None
        except Exception as e:
            logging.error(f"Error in GPU temperature detection: {e}")
            return None
            
    def get_battery_info(self):
        """Get detailed battery information.
        Returns a dictionary with battery status, health, and other information.
        """
        try:
            battery_info = {
                'present': False,
                'device': 'Unknown',
                'model': 'Unknown',
                'serial': 'Unknown',
                'capacity': 'Unknown',
                'status': 'Unknown',
                'health': 'Unknown',
                'health_percent': 0,
                'recommendation': 'Unknown'
            }
            
            # Base path for battery information
            bat_path = '/sys/class/power_supply'
            
            # Check if the directory exists
            if not os.path.exists(bat_path):
                pass
                return battery_info
            
            # Find battery directory (e.g. BAT0, BAT1)
            bat_dirs = [d for d in os.listdir(bat_path) if d.startswith('BAT')]
            if not bat_dirs:
                pass
                return battery_info
            
            # Use the first battery found
            battery_dir = bat_dirs[0]
            full_path = os.path.join(bat_path, battery_dir)
            battery_info['device'] = battery_dir
            battery_info['present'] = True
            
            # Helper function to safely read battery files
            def read_battery_file(filename, default="Unknown"):
                try:
                    path = os.path.join(full_path, filename)
                    if os.path.exists(path):
                        with open(path, 'r') as f:
                            return f.read().strip()
                    return default
                except Exception as e:
                    logging.debug(f"Error reading {filename}: {e}")
                    return default
            
            # Read basic battery information
            try:
                capacity_value = read_battery_file('capacity', '0')
                battery_info['capacity'] = int(capacity_value)

            except (ValueError, TypeError) as e:
                logging.error(f"Error converting battery capacity: {e}")
                battery_info['capacity'] = 0
            
            battery_info['status'] = read_battery_file('status', 'Unknown')
            
            # Try to get model name or manufacturer
            battery_info['model'] = read_battery_file('model_name', 'Unknown')
            if battery_info['model'] == 'Unknown':
                battery_info['model'] = read_battery_file('manufacturer', 'Unknown')
            
            # Get serial number
            battery_info['serial'] = read_battery_file('serial_number', 'Unknown')
            
            # Read design capacity and full charge capacity
            design_capacity = 0
            full_charge_capacity = 0
            
            # Try different possible file names for design capacity
            if os.path.exists(os.path.join(full_path, 'charge_full_design')):
                design_capacity = int(read_battery_file('charge_full_design', '0'))
            elif os.path.exists(os.path.join(full_path, 'energy_full_design')):
                design_capacity = int(read_battery_file('energy_full_design', '0'))
            
            # Try different possible file names for full charge capacity
            if os.path.exists(os.path.join(full_path, 'charge_full')):
                full_charge_capacity = int(read_battery_file('charge_full', '0'))
            elif os.path.exists(os.path.join(full_path, 'energy_full')):
                full_charge_capacity = int(read_battery_file('energy_full', '0'))
            
            # Calculate health percentage
            if design_capacity > 0 and full_charge_capacity > 0:
                health_percent = (full_charge_capacity / design_capacity) * 100
                battery_info['health_percent'] = health_percent
                battery_info['health'] = f"{health_percent:.1f}%"
                
                # Determine recommendation based on health
                if health_percent < 70:
                    battery_info['recommendation'] = "Replace battery recommended (health < 70%)"
                elif health_percent < 85:
                    battery_info['recommendation'] = "Consider replacement soon (health 70-85%)"
                else:
                    battery_info['recommendation'] = "Battery health good"
            else:
                battery_info['health'] = "Not available"
                battery_info['recommendation'] = "Cannot determine battery health"
            
            pass
            return battery_info
            
        except Exception as e:
            logging.error(f"Error detecting battery information: {e}")
            return battery_info
            
    def extract_mbit_value(self, speed_str):
        """Extract numeric value from speed string
        
        Args:
            speed_str: String containing speed value (e.g., '100 MBit/s')
            
        Returns:
            float: Numeric value if successful, None otherwise
        """
        if not speed_str or speed_str == "N/A":
            return None
        try:
            # Extract the first number from the string
            match = re.search(r'(\d+(?:\.\d+)?)', speed_str)
            if match:
                return float(match.group(1))
        except (ValueError, TypeError):
            pass
        return None
    
    def run_speedtest(self, interface):
        """Run speedtest and return download and upload speeds in MBit/s"""
        try:
            # Try speedtest-cli first (older versions)
            try:
                result = subprocess.run(
                    ['speedtest', '--format=json', '--accept-license', '--accept-gdpr'],
                    capture_output=True, text=True, timeout=60
                )
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    download = data['download']['bandwidth'] * 8 / 1_000_000  # Convert to Mbit/s
                    upload = data['upload']['bandwidth'] * 8 / 1_000_000  # Convert to Mbit/s
                    ping = data['ping']['latency']
                    return {
                        'download': download,
                        'upload': upload,
                        'ping': ping
                    }
            except (subprocess.SubprocessError, FileNotFoundError, json.JSONDecodeError, KeyError) as e:
                logging.error(f"Speed test failed: {e}")
                return None
            else:
                logging.error("Speed test failed")
                return None
        except Exception as e:
            logging.error(f"Unexpected error during speed test: {e}")
            return None

    def update_network_speeds(self, interface, download=None, upload=None, ping=None):
        """Update the network speed display for a specific interface
        
        Args:
            interface: Network interface name
            download: Download speed in MBit/s
            upload: Upload speed in MBit/s
            ping: Ping time in ms
        """
        try:
            if not hasattr(self, 'network_scrollable_frame') or not self.network_scrollable_frame.winfo_exists():
                return
            
            for child in self.network_scrollable_frame.winfo_children():
                if hasattr(child, 'interface_id') and child.interface_id == interface:
                    for widget in child.winfo_children():
                        try:
                            if hasattr(widget, 'speed_metric'):
                                if widget.speed_metric == 'download' and download is not None:
                                    for w in widget.winfo_children():
                                        if isinstance(w, ttk.Label) and ':' not in w.cget('text'):
                                            w.config(text=f"{download:.1f} MBit/s")
                                elif widget.speed_metric == 'upload' and upload is not None:
                                    for w in widget.winfo_children():
                                        if isinstance(w, ttk.Label) and ':' not in w.cget('text'):
                                            w.config(text=f"{upload:.1f} MBit/s")
                                elif widget.speed_metric == 'ping' and ping is not None:
                                    for w in widget.winfo_children():
                                        if isinstance(w, ttk.Label) and ':' not in w.cget('text'):
                                            w.config(text=f"{ping:.1f} ms")
                        except Exception as e:
                            logging.error(f"Error updating network speed display: {str(e)}")
        except Exception as e:
            logging.error(f"Error in update_network_speeds: {str(e)}")
    
    def _get_wifi_info(self, interface):
        """Get WiFi information using iwconfig
        
        Args:
            interface: Network interface name
            
        Returns:
            dict: Dictionary containing WiFi information with keys:
                - ssid: Network name
                - rate: Connection rate in Mbps (float)
                - frequency: Operating frequency with unit
                - signal: Signal strength in dBm or quality
                - status: Connection status
        """
        wifi_info = {
            'ssid': 'Not connected',
            'rate': 0.0,
            'frequency': 'N/A',
            'signal': 'N/A',
            'status': 'Disconnected',
            'Speed': 'N/A'
        }
        
        try:
            # First try iw for detailed WiFi info
            try:
                result = subprocess.run(
                    ['iw', 'dev', interface, 'link'],
                    capture_output=True, text=True, timeout=2
                )
                
                if result.returncode == 0:
                    # Parse iw output
                    for line in result.stdout.split('\n'):
                        line = line.strip()
                        if 'SSID:' in line:
                            wifi_info['ssid'] = line.split('SSID:')[1].strip()
                        elif 'freq:' in line:
                            freq = line.split('freq:')[1].split()[0]
                            wifi_info['frequency'] = f"{freq} MHz"
                        elif 'signal:' in line:
                            signal = line.split('signal:')[1].split()[0]
                            wifi_info['signal'] = f"{signal} dBm"
                        elif 'tx bitrate:' in line:
                            rate = line.split('tx bitrate:')[1].split()[0]
                            try:
                                wifi_info['rate'] = float(rate)
                                wifi_info['Speed'] = f"{rate} Mbps"
                            except (ValueError, IndexError):
                                pass
                    
                    if wifi_info['ssid'] != 'Not connected':
                        wifi_info['status'] = 'Connected'
                    
                    return wifi_info
            except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
                pass  # Fall through to iwconfig
            
            # Fall back to iwconfig if iw fails
            result = subprocess.run(
                ['iwconfig', interface],
                capture_output=True, text=True, timeout=2
            )
            
            if result.returncode == 0:
                ssid = 'Not connected'
                rate = 0.0
                signal = 'N/A'
                
                # Parse iwconfig output
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    
                    # Extract SSID
                    if 'ESSID:' in line:
                        ssid = line.split('ESSID:')[1].strip(' \"') or "(hidden)"
                    # Extract bit rate
                    elif 'Bit Rate=' in line:
                        rate_parts = line.split('Bit Rate=')
                        if len(rate_parts) > 1:
                            rate_str = rate_parts[1].split()[0]
                            try:
                                if 'Mb/s' in rate_str or 'Mbit/s' in rate_str or 'MBit/s' in rate_str:
                                    rate = float(rate_str.split('M')[0])
                                    wifi_info['rate'] = rate
                                    wifi_info['Speed'] = f"{rate} Mbps"
                                elif 'kb/s' in rate_str or 'kbit/s' in rate_str or 'kBit/s' in rate_str:
                                    rate = float(rate_str.split('k')[0]) / 1000
                                    wifi_info['rate'] = rate
                                    wifi_info['Speed'] = f"{rate:.1f} Mbps"
                            except (ValueError, IndexError):
                                pass
                    # Extract frequency
                    elif 'Frequency:' in line:
                        freq_parts = line.split('Frequency:')
                        if len(freq_parts) > 1:
                            freq = freq_parts[1].split()[0]
                            wifi_info['frequency'] = f"{freq} {freq_parts[1].split()[1]}" if len(freq_parts[1].split()) > 1 else freq
                    # Extract signal level
                    elif 'Signal level=' in line:
                        signal_parts = line.split('Signal level=')
                        if len(signal_parts) > 1:
                            signal = signal_parts[1].split()[0]
                            # Convert signal to dBm if it's a percentage
                            if '/' in signal:  # Format: 70/100
                                try:
                                    quality = int(signal.split('/')[0])
                                    # Rough conversion: 100% = -20 dBm, 0% = -100 dBm
                                    dbm = int(quality * 0.8 - 100)
                                    signal = f"{dbm} dBm"
                                except (ValueError, IndexError):
                                    signal += ' (quality)'
                            elif signal.isdigit() or signal.replace('-', '').isdigit():
                                signal += ' dBm'
                            wifi_info['signal'] = signal
                
                # Update connection status based on SSID
                if ssid not in ('off/any', 'Not connected'):
                    wifi_info['ssid'] = ssid
                    wifi_info['status'] = 'Connected'
                    if wifi_info['signal'] == '0':
                        wifi_info['signal'] = 'Weak'
                
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            logging.error(f"Error getting WiFi info: {e}")
            wifi_info['Speed'] = f"WiFi (error: {str(e)[:30]})"
        
        return wifi_info

    def _get_ethernet_info(self, interface, if_info):
        """Get detailed Ethernet interface information"""
        try:
            # Get link detection status
            ethtool_result = subprocess.run(
                ['ethtool', interface],
                capture_output=True, text=True, timeout=5
            )
            # Process ethtool result here
            return {}
        except Exception as e:
            logging.error(f"Error getting Ethernet info for {interface}: {e}")
            return {}
            
            ethtool_output = ethtool_result.stdout
            
            link_detected = False
            for line in ethtool_output.split('\n'):
                if 'Link detected:' in line:
                    link_status = line.split('Link detected:')[1].strip()
                    if_info['Link'] = link_status.capitalize()
                    link_detected = link_status.lower() == 'yes'
                    break
            
            # If no link, update status
            if not link_detected:
                if_info['Status'] = 'No link'
                if_info['Speed'] = 'N/A (cable unplugged?)'
            
            # Get duplex mode
            for line in ethtool_output.split('\n'):
                if 'Duplex:' in line:
                    duplex = line.split('Duplex:')[1].strip()
                    if_info['Duplex'] = duplex
                    break
            
            # Get driver information
            driver_path = f'/sys/class/net/{interface}/device/driver/module'
            if os.path.exists(driver_path):
                try:
                    driver = os.path.basename(os.readlink(driver_path))
                    if_info['Driver'] = driver
                except (OSError, IOError):
                    pass
            
            # Fall back to sysfs if ethtool fails
            try:
                speed_path = f'/sys/class/net/{interface}/speed'
                if os.path.exists(speed_path):
                    with open(speed_path, 'r') as f:
                        speed = f.read().strip()
                        if speed.isdigit() and int(speed) > 0:
                            if_info['Speed'] = f"{speed} Mbps"
            except (IOError, OSError) as e:
                logging.debug(f"Could not read speed for {interface}: {e}")
            
            # Check if cable is connected
            carrier_path = f'/sys/class/net/{interface}/carrier'
            if os.path.exists(carrier_path):
                try:
                    with open(carrier_path, 'r') as f:
                        carrier = f.read().strip()
                        if carrier == '1':
                            if_info['Link'] = 'Yes'
                            if_info['Status'] = 'Connected'
                            
                            # Check for VPN interfaces
                            if 'oc' in interface or 'vpn' in interface:
                                if_info['VPN'] = 'VPN (Cisco/OpenConnect)'
                                if_info['Speed'] = "N/A (Tunnel)"
                                
                            # Check if interface is up
                            try:
                                with open(f'/sys/class/net/{interface}/operstate', 'r') as f:
                                    state = f.read().strip()
                                    if_info['Status'] = state.capitalize()
                            except (IOError, OSError):
                                pass
                        else:
                            if_info['Link'] = 'No'
                            if_info['Status'] = 'No link'
                except (IOError, OSError) as e:
                    logging.debug(f"Could not read carrier status for {interface}: {e}")
                    if_info['Speed'] = "Check interface"
            
            # Check for different interface types
            if interface.startswith('veth'):
                if_info['Type'] = "Virtual Ethernet"
                if_info['Speed'] = "N/A (Virtual)"
            
            elif interface.startswith(('br', 'ovs')):
                if_info['Type'] = "Bridge (Virtual Switch)"
                # Try to get bridge info
                try:
                    bridge_result = subprocess.run(
                        ['brctl', 'show', interface],
                        capture_output=True, text=True, timeout=2
                    )
                    if bridge_result.returncode == 0:
                        lines = bridge_result.stdout.split('\n')
                        if len(lines) > 1:
                            ports = ', '.join(p.strip() for p in lines[1].split() if p.strip())
                            if ports:
                                if_info['Ports'] = ports
                except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
                    pass
                if_info['Speed'] = "N/A (Bridge)"
            
            elif interface.startswith('docker'):
                if_info['Type'] = "Docker Network"
                if_info['Speed'] = "N/A (Container)"
            
            elif interface.startswith('virbr'):
                if_info['Type'] = "Virtual Bridge (libvirt)"
                if_info['Speed'] = "N/A (Virtual)"
            
    def setup_storage_tab(self):
        """Set up the Storage tab with disk information and SMART data."""
        
        # Initialize the storage tab using the device_tabs dictionary
        storage_tab = self.device_tabs["storage"]
        
        # Create container frame that dynamically sizes based on parent
        storage_container = ttk.Frame(storage_tab)
        storage_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Get container to use all available space by preventing propagation
        storage_container.pack_propagate(False)
        
        # Set up a window resize handler to adjust the container height
        def update_storage_container_size(event=None):
            # Get the parent container's height (storage_tab)
            tab_height = storage_tab.winfo_height()
            # Use most of available height but leave room for padding/margins
            if tab_height > 50:  # Only resize if we have meaningful height
                # Calculate available height, account for padding and other elements
                available_height = tab_height - 40  # Subtract padding/margins
                storage_container.configure(height=available_height)
                storage_canvas.configure(height=available_height - 10)  # Slight adjustment for inner padding
        
        # Bind to Configure events for dynamic resizing
        storage_tab.bind("<Configure>", update_storage_container_size)
        
        # Create canvas and scrollbar for scrolling
        storage_canvas = tk.Canvas(storage_container, highlightthickness=0)
        storage_canvas.pack(side="left", fill="both", expand=True)
        
        # Add scrollbar - this is essential
        storage_scrollbar = ttk.Scrollbar(storage_container, orient="vertical", command=storage_canvas.yview)
        storage_scrollbar.pack(side="right", fill="y")
        
        # Configure the canvas
        storage_canvas.configure(yscrollcommand=storage_scrollbar.set)
        
        # Create a frame inside the canvas to hold content
        storage_content_frame = ttk.Frame(storage_canvas)
        
        # Create a window in the canvas to display the frame
        storage_canvas_frame = storage_canvas.create_window((0, 0), window=storage_content_frame, anchor="nw")
        
        # Configure canvas resize handling
        def _configure_storage_canvas(event):
            # Update the scrollregion to encompass the inner frame
            storage_canvas.configure(scrollregion=storage_canvas.bbox("all"))
            # Update canvas window width to match canvas width
            storage_canvas.itemconfig(storage_canvas_frame, width=event.width)
            
        storage_content_frame.bind("<Configure>", _configure_storage_canvas)
        storage_canvas.bind("<Configure>", lambda e: storage_canvas.itemconfig(storage_canvas_frame, width=e.width))
        
        # Add mousewheel scrolling
        def _storage_on_mousewheel(event):
            storage_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        # Store the mousewheel function for binding/unbinding
        self._storage_mousewheel_func = _storage_on_mousewheel
        
        # Bind mousewheel since the tab is currently active
        storage_canvas.bind_all("<MouseWheel>", self._storage_mousewheel_func)
        
        # Create a main container with padding inside the scrollable area
        main_frame = ttk.Frame(storage_content_frame, padding=10)
        main_frame.pack(fill='both', expand=True)
        
        # Create a frame for the disk and partition information with significant height
        storage_frame = ttk.LabelFrame(main_frame, text="Disk and Partition Information", padding=10)
        storage_frame.pack(fill="both", expand=True, pady=5)
        # Ensure main_frame uses its full allocated space
        main_frame.pack_propagate(False)
        
        # Create a direct frame for storage information with minimum height to ensure sufficient display space
        storage_content_frame = ttk.Frame(storage_frame, height=800)  # Increased minimum height
        storage_content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        # Prevent the frame from shrinking below specified height
        storage_content_frame.pack_propagate(False)
        
        # Create a vertical paned window to show both overview and SMART data directly
        # without using a tab - the heading is sufficient
        paned_window = ttk.PanedWindow(storage_content_frame, orient=tk.VERTICAL)
        paned_window.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Calculate initial dimensions once storage tab is shown
        def configure_paned_window(event=None):
            # Set initial sash position to provide balanced space (about 40% to partitions, 60% to SMART)
            total_height = storage_content_frame.winfo_height()
            if total_height > 100:  # Only adjust if we have meaningful height
                # Position sash at 40% of the height for better partition display
                paned_window.sashpos(0, int(total_height * 0.40))
                # Unbind after initial positioning to allow user adjustments
                storage_content_frame.unbind('<Map>')
                
        # Bind to when the frame becomes visible
        storage_content_frame.bind('<Map>', configure_paned_window)
        
        # Top frame for partitions overview
        partitions_frame = ttk.LabelFrame(paned_window, text="Disk Partitions")
        paned_window.add(partitions_frame, weight=3)  # Increased weight for partition section
        
        # Bottom frame for SMART data
        smart_main_frame = ttk.LabelFrame(paned_window, text="SMART Data")
        paned_window.add(smart_main_frame, weight=6)  # Increased weight from 4 to 6 to give even more vertical space
        
        # Create a dropdown for device selection in the SMART section
        device_frame = ttk.Frame(smart_main_frame)
        device_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(device_frame, text="Select Drive:", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        
        # Get list of drives
        drives = self.list_block_devices()
        
        # Create StringVar for dropdown
        self.selected_drive = tk.StringVar()
        if drives:
            self.selected_drive.set(drives[0])  # Default to first drive
        
        # Create dropdown menu
        drive_dropdown = ttk.Combobox(device_frame, textvariable=self.selected_drive, state="readonly")
        drive_dropdown.pack(side="left", padx=5)
        drive_dropdown['values'] = drives
        
        # Create refresh button
        refresh_btn = ttk.Button(device_frame, text="Refresh", command=lambda: self.update_smart_info(smart_info_frame))
        refresh_btn.pack(side="right", padx=5)
        
        # Create frame for SMART information
        # Create frame for SMART information
        smart_info_frame = ttk.Frame(smart_main_frame)
        smart_info_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Bind selection change event
        drive_dropdown.bind("<<ComboboxSelected>>", lambda e: self.update_smart_info(smart_info_frame))
        
        # Initial update of SMART info
        self.update_smart_info(smart_info_frame)
        
        # Display partition information in the partitions_frame
        try:
            # Get detailed partition information using lsblk
            lsblk_result = subprocess.run(
                ['lsblk', '-o', 'NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE', '--json'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            
            # Create a treeview for partition information
            # Create partition frame with fixed minimum height
            partition_container = ttk.Frame(partitions_frame, height=350)
            partition_container.pack(fill='both', expand=True)
            partition_container.pack_propagate(False)  # Prevent shrinking below minimum height
            
            # Create treeview with large explicit height in the container
            part_tree = ttk.Treeview(partition_container, columns=('size', 'type', 'mountpoint', 'fstype'), show='tree headings', height=25)
            # Use aggressive expand with minimal padding
            part_tree.pack(fill='both', expand=True, padx=0, pady=0)
            
            # Configure columns
            part_tree.heading('#0', text='Device')
            part_tree.heading('size', text='Size')
            part_tree.heading('type', text='Type')
            part_tree.heading('mountpoint', text='Mount Point')
            part_tree.heading('fstype', text='File System')
            
            part_tree.column('#0', width=150)
            part_tree.column('size', width=80)
            part_tree.column('type', width=80)
            part_tree.column('mountpoint', width=150)
            part_tree.column('fstype', width=100)
            
            # Parse JSON output
            import json
            part_data = json.loads(lsblk_result.stdout)
            
            # Add devices and partitions to the treeview
            for device in part_data.get('blockdevices', []):
                # Add the main device
                device_id = part_tree.insert('', 'end', text=f"/dev/{device['name']}", 
                                            values=(device.get('size', ''), 
                                                   device.get('type', ''), 
                                                   device.get('mountpoint', ''), 
                                                   device.get('fstype', '')))
                
                # Add children (partitions)
                for child in device.get('children', []):
                    part_tree.insert(device_id, 'end', text=f"/dev/{child['name']}", 
                                   values=(child.get('size', ''), 
                                          child.get('type', ''), 
                                          child.get('mountpoint', ''), 
                                          child.get('fstype', '')))
                                          
        except Exception as e:
            error_label = ttk.Label(partitions_frame, text=f"Error getting partition info: {e}", foreground='red')
            error_label.pack(padx=5, pady=10)
        
        # Now let's expand the partitions view with additional information
        # Add partition scheme information below the treeview
        partition_info_frame = ttk.Frame(partitions_frame)
        partition_info_frame.pack(fill='x', expand=False, padx=5, pady=5)
        
        # Add button to check partition scheme (MBR vs GPT)
        check_scheme_btn = ttk.Button(partition_info_frame, text="Check Partition Scheme", 
                                     command=lambda: self.check_partition_scheme(partition_info_frame))
        check_scheme_btn.pack(side='left', padx=5)
        
    def check_partition_scheme(self, parent_frame):
        """Check the partition scheme (MBR vs GPT) for all disks
        
        Args:
            parent_frame: Frame to display results in
        """
        # Clear existing results
        for widget in list(parent_frame.winfo_children())[1:]:  # Keep the button
            widget.destroy()
            
        # Find all disks
        disks = []
        try:
            result = subprocess.run(['lsblk', '-dn', '-o', 'NAME'], stdout=subprocess.PIPE, text=True)
            disk_names = result.stdout.strip().split('\n')
            disks = [f"/dev/{disk}" for disk in disk_names]
        except Exception as e:
            error_label = ttk.Label(parent_frame, text=f"Error finding disks: {e}", foreground='red')
            error_label.pack(side='left', padx=5)
            return
            
        # Check partition scheme for each disk
        for disk in disks:
            try:
                # Use parted to get partition table type
                result = subprocess.run(['sudo', 'parted', '-s', disk, 'print'], 
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                
                # Extract partition table type
                partition_table = "Unknown"
                for line in result.stdout.splitlines():
                    if "Partition Table:" in line:
                        partition_table = line.split(":")[1].strip()
                        break
                        
                # Create a label with the result
                scheme_label = ttk.Label(parent_frame, 
                                        text=f"{disk}: {partition_table}", 
                                        font=("Arial", 9))
                scheme_label.pack(side='left', padx=10)
            except Exception as e:
                error_label = ttk.Label(parent_frame, text=f"Error checking {disk}: {e}", foreground='red')
                error_label.pack(side='left', padx=5)
            
            # We've already created a comprehensive partition display above
            # No need for additional partition frames here.
            
            
            if disks:
                # Check partition table type using parted
                try:
                    # Use the disk path directly since it already includes /dev/
                    parted_result = subprocess.run(
                        ['parted', disks[0], 'print'],
                        capture_output=True, text=True, timeout=3
                        )
                        
                    if parted_result.returncode == 0:
                        for line in parted_result.stdout.splitlines():
                            if "Partition Table:" in line:
                                partition_scheme = line.split(":")[1].strip()
                                break
                except Exception as e:
                    logging.error(f"Error detecting partition scheme: {e}")
                
            # Create a frame for partition scheme info
            scheme_frame = ttk.LabelFrame(parent_frame, text="Partition Scheme")
            scheme_frame.pack(fill="x", expand=False, padx=5, pady=5)
                
            ttk.Label(scheme_frame, text=f"Partition Table Type: {partition_scheme}", 
                      font=("Arial", 10)).pack(anchor="w", padx=5, pady=5)
                
            if partition_scheme.lower() == "msdos":
                ttk.Label(scheme_frame, text="MBR (Master Boot Record) allows up to 4 primary partitions or 3 primary and 1 extended", 
                          font=("Arial", 9, "italic")).pack(anchor="w", padx=5, pady=2)
            elif partition_scheme.lower() == "gpt":
                ttk.Label(scheme_frame, text="GPT (GUID Partition Table) supports larger disks and up to 128 partitions", 
                          font=("Arial", 9, "italic")).pack(anchor="w", padx=5, pady=2)
                            # Process partition data
                partition_data = []
                for line in lsblk_result.stdout.splitlines()[1:]:  # Skip header
                    parts = re.split(r'\s+', line.strip(), maxsplit=9)
                    if len(parts) > 2 and parts[2] == "part":  # Only process partitions
                        name = parts[0]
                        indent_level = name.count("├") + name.count("└") + name.count("│")
                        name = name.replace("├─", "").replace("└─", "").replace("│", "")
                            
                        partition_info = {
                            "name": name,
                            "size": parts[1] if len(parts) > 1 else "Unknown",
                            "mountpoint": parts[3] if len(parts) > 3 else "",
                            "fstype": parts[4] if len(parts) > 4 else "Unknown",
                            "label": parts[5] if len(parts) > 5 else "",
                            "uuid": parts[6] if len(parts) > 6 else "",
                            "partuuid": parts[7] if len(parts) > 7 else "",
                            "partlabel": parts[8] if len(parts) > 8 else "",
                            "flags": parts[9] if len(parts) > 9 else ""
                        }
                            
                        partition_data.append(partition_info)
                            
                        # Initialize partition type flags
                        is_extended = False
                        is_logical = False
                        is_primary = False
                            
                        # Get additional partition information with fdisk
                        try:
                            disk_base = name.rstrip('0123456789')  # Remove trailing numbers to get base disk name
                            fdisk_result = subprocess.run(
                                ['fdisk', '-l', f'/dev/{disk_base}'],
                                capture_output=True, text=True, timeout=3
                            )
                            
                            if fdisk_result.returncode == 0:
                                # Define regex patterns for partition types
                                device_pattern = re.compile(rf'/dev/{re.escape(name)}')
                                extended_pattern = re.compile(r'Extended')
                                logical_pattern = re.compile(r'Logical')
                                primary_pattern = re.compile(r'Primary')
                                
                                # Reset partition type flags
                                is_extended = False
                                is_logical = False
                                is_primary = False
                                
                                output_lines = fdisk_result.stdout.splitlines()
                                for line_idx, output_line in enumerate(output_lines):
                                    if device_pattern.search(output_line):
                                        # Check this line and the next few lines for partition type
                                        for check_idx in range(line_idx, min(line_idx+3, len(output_lines))):
                                            check_line = output_lines[check_idx]
                                            if extended_pattern.search(check_line):
                                                is_extended = True
                                                break
                                            if logical_pattern.search(check_line):
                                                is_logical = True
                                                break
                                            if primary_pattern.search(check_line):
                                                is_primary = True
                                                break
                        except Exception as e:
                            logging.error(f"Error getting fdisk details: {e}")
                        
                        # Determine partition type based on detection or fallback to naming convention
                        try:
                            if is_extended:
                                partition_categories["Extended Partitions"].append(partition_info)
                            elif is_logical:
                                partition_categories["Logical Partitions"].append(partition_info)
                            elif is_primary:
                                partition_categories["Primary Partitions"].append(partition_info)
                            else:
                                # Fallback: try to guess based on partition name
                                if len(name) > len(disk_base) and name[len(disk_base)] in '123456789':
                                    # Primary partitions usually have single-digit suffixes (1-4)
                                    if int(name[len(disk_base):]) <= 4:
                                        partition_categories["Primary Partitions"].append(partition_info)
                                    else:
                                        partition_categories["Logical Partitions"].append(partition_info)
                                else:
                                    partition_categories["Other Partitions"].append(partition_info)
                        except Exception as e:
                            logging.error(f"Error categorizing partition: {e}")
                            partition_categories["Other Partitions"].append(partition_info)
                
                # Display partitions by category
                for category_name, parts in partition_categories.items():
                    if parts:  # Only create category if it has partitions
                        part_frame = ttk.LabelFrame(partitions_main_frame, text=category_name)
                        part_frame.pack(fill="x", expand=False, padx=5, pady=5)
                        
                        # Create headers
                        header_labels = ["Partition", "Size", "Filesystem", "Mount Point", "Label"]
                        for col_idx, header_text in enumerate(header_labels):
                            ttk.Label(
                                part_frame, 
                                text=header_text, 
                                font=("Arial", 10, "bold")
                            ).grid(row=0, column=col_idx, padx=5, pady=5, sticky="w")
                        
                        # Add partition data
                        for part_idx, part_info in enumerate(parts):
                            ttk.Label(part_frame, text=part_info["name"], font=("Arial", 10)).grid(
                                row=part_idx+1, column=0, padx=5, pady=2, sticky="w")
                            ttk.Label(part_frame, text=part_info["size"], font=("Arial", 10)).grid(
                                row=part_idx+1, column=1, padx=5, pady=2, sticky="w")
                            ttk.Label(part_frame, text=part_info["fstype"], font=("Arial", 10)).grid(
                                row=part_idx+1, column=2, padx=5, pady=2, sticky="w")
                            ttk.Label(part_frame, text=part_info["mountpoint"], font=("Arial", 10)).grid(
                                row=part_idx+1, column=3, padx=5, pady=2, sticky="w")
                            ttk.Label(part_frame, text=part_info["label"], font=("Arial", 10)).grid(
                                row=part_idx+1, column=4, padx=5, pady=2, sticky="w")
            else:
                ttk.Label(partitions_main_frame, text="Error getting partition information", 
                       font=("Arial", 10)).pack(padx=5, pady=10)

            # Removed reference to undefined error_label

            # Get partition usage information
            usage_tab = ttk.Frame(partitions_notebook)
            partitions_notebook.add(usage_tab, text="Usage")
            
            # Run df to get usage information
            df_result = subprocess.run(['df', '-h'], capture_output=True, text=True)
            if df_result.returncode == 0:
                # Create a frame for usage information
                usage_frame = ttk.Frame(usage_tab)
                usage_frame.pack(fill="both", expand=True, padx=5, pady=5)
                
                # Create headers from df output
                headers = df_result.stdout.splitlines()[0].split()
                for i, header in enumerate(headers):
                    ttk.Label(usage_frame, text=header, font=("Arial", 9, "bold"),
                          foreground=self.colors["primary"]).grid(
                            row=0, column=i, sticky="w", padx=5, pady=2
                        )
                
                # Add partition usage rows
                row = 1
                for line in df_result.stdout.splitlines()[1:]:
                    parts = re.split(r'\s+', line.strip(), maxsplit=5)
                    
                    # Skip if the first column doesn't start with /dev
                    # This helps filter out virtual filesystems
                    if not (parts[0].startswith('/dev') or parts[0] == '/'):
                        continue
                        
                    for j, part in enumerate(parts):
                        # For usage percentage, add color coding
                        if j == 4 and part.endswith("%"):
                            try:
                                usage_pct = int(part.strip("%"))
                                text_color = "green"
                                if usage_pct > 85:
                                    text_color = "red"
                                elif usage_pct > 70:
                                    text_color = "orange"
                                    
                                ttk.Label(usage_frame, text=part, font=("Courier", 9),
                                      foreground=text_color).grid(
                                    row=row, column=j, sticky="w", padx=5, pady=2
                                )
                            except (ValueError, IndexError) as e:
                                logging.error(f"Error processing usage percentage: {e}")
                                ttk.Label(usage_frame, text=part, font=("Courier", 9)).grid(
                                    row=row, column=j, sticky="w", padx=5, pady=2
                                )
                        else:
                            ttk.Label(usage_frame, text=part, font=("Courier", 9)).grid(
                                row=row, column=j, sticky="w", padx=5, pady=2
                            )
                    row += 1
            else:
                ttk.Label(partitions_main_frame, text="Error getting partition information", 
                          font=("Arial", 10)).pack(padx=5, pady=10)

# All UI code has been moved into the PCToolsModule class methods
            
            # Update status when done
            self.update_status("System information refreshed")
        
        # We already have a refresh button in the header, no need for a second one here
        
        # We no longer need the placeholder text section since we've implemented real-time system information above
    
    def set_smartctl_capabilities(self):
        """Set the capabilities on smartctl to avoid multiple password prompts"""
        import subprocess
        import os
        import logging
        import shutil
        
        # Check if we've already set capabilities in this session
        if hasattr(PCToolsModule, 'smartctl_capabilities_set') and PCToolsModule.smartctl_capabilities_set:
            logging.info("smartctl capabilities already set for this session")
            return True
            
        # Check if the capability is already set on the system
        try:
            getcap_result = subprocess.run(
                ['getcap', '/usr/sbin/smartctl'],
                capture_output=True, text=True, timeout=5
            )
            
            # If the capability is already set correctly, just mark it as set
            result = subprocess.run(
                ['sudo', 'getcap', '/usr/sbin/smartctl'],
                capture_output=True, text=True
            )
            
            if 'cap_sys_rawio+ep' in result.stdout:
                logging.info("smartctl already has required capabilities")
                PCToolsModule.smartctl_capabilities_set = True
                return True
                
            # If we get here, we need to set the capabilities
            logging.info("Setting capabilities on smartctl to avoid password prompts")
            
            # Try to set capabilities with sudo
            result = subprocess.run(
                ['sudo', 'setcap', 'cap_sys_rawio+ep', '/usr/sbin/smartctl'],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                logging.info("Successfully set capabilities on smartctl")
                PCToolsModule.smartctl_capabilities_set = True
                return True
            else:
                logging.error(f"Failed to set capabilities on smartctl: {result.stderr}")
                return False
                
        except Exception as e:
            logging.error(f"Error setting smartctl capabilities: {e}")
            return False
    
    def configure_smart_cache(self, max_age=None, refresh_on_tab_switch=None):
        """Configure SMART data cache settings
        
        Args:
            max_age: Maximum age of cache entries in seconds before refresh (None = don't change)
            refresh_on_tab_switch: Whether to refresh cache when switching tabs (None = don't change)
            
        Returns:
            Dictionary with the current cache configuration
        """
        # Update class-level setting if requested
        if max_age is not None:
            PCToolsModule.smart_cache_max_age = max_age
            self.cache_config['smart_cache_max_age'] = max_age
            
        # Update instance-level setting if requested
        if refresh_on_tab_switch is not None:
            self.cache_config['refresh_on_tab_switch'] = refresh_on_tab_switch
            
        # Log current settings
        logging.info(f"SMART cache configuration: max_age={PCToolsModule.smart_cache_max_age}s, "
                   f"refresh_on_tab_switch={self.cache_config.get('refresh_on_tab_switch', True)}")
        
        return self.cache_config
    
    def get_all_smart_data(self):
        """Get SMART data for all disks with a single authentication"""
        import subprocess
        import os
        import logging
        import shutil
        
        # Update status
        self.update_status("Collecting SMART data...")
        
        # First, try to set capabilities on smartctl to avoid multiple password prompts
        self.set_smartctl_capabilities()
        
        # Get current time for cache timestamp checks
        import time
        current_time = time.time()
        
        # Check if we already have data cached and it's still valid
        if PCToolsModule.smart_data_cache and PCToolsModule.sudo_authenticated:
            # Check if any cache entries need refresh
            expired_disks = []
            for disk, timestamp in PCToolsModule.smart_cache_timestamps.items():
                if current_time - timestamp > PCToolsModule.smart_cache_max_age:
                    logging.info(f"Cache for {disk} has expired (age: {current_time - timestamp:.1f}s)")
                    expired_disks.append(disk)
            
            # If no expired entries, use existing cache
            if not expired_disks:
                logging.info("Using existing SMART data cache (all entries are fresh)")
                return
            else:
                logging.info(f"Need to refresh {len(expired_disks)} expired cache entries")
                # Continue with the method to refresh expired entries
            
        # Get list of all disks
        disks = self.list_block_devices()
        if not disks:
            logging.warning("No disks found for SMART data collection")
            return {}
            
        # Try to set capabilities first (this will prompt for password once)
        if not PCToolsModule.smartctl_capabilities_set:
            self.set_smartctl_capabilities()
            
        # Check for expired cache entries
        current_time = time.time()
        expired_disks = []
        if PCToolsModule.smart_data_cache:
            for disk, timestamp in PCToolsModule.smart_cache_timestamps.items():
                if current_time - timestamp > PCToolsModule.smart_cache_max_age:
                    expired_disks.append(disk)
                    
            # If all cached data is still fresh, return it
            if not expired_disks and all(disk in PCToolsModule.smart_data_cache for disk in disks):
                logging.debug("Using cached SMART data")
                return PCToolsModule.smart_data_cache
                
            logging.info(f"Refreshing expired SMART data for {len(expired_disks)} disks")
        
        # Try to get data for each disk
        for disk in disks:
            # Skip if we already have fresh data for this disk
            if (disk in PCToolsModule.smart_data_cache and 
                disk not in expired_disks and 
                current_time - PCToolsModule.smart_cache_timestamps.get(disk, 0) < PCToolsModule.smart_cache_max_age):
                continue
                
            try:
                # Get device type
                dev_type = self.get_device_type(disk)
                if not dev_type:
                    logging.warning(f"Could not determine device type for {disk}, skipping")
                    continue
                    
                # Check if SMART is supported
                if not self.check_smart_support(disk, dev_type):
                    logging.info(f"SMART not supported on {disk}")
                    continue
                    
                # Try to get SMART data with sudo
                try:
                    # First try with sudo directly
                    health_result = subprocess.run(
                        ['sudo', '--non-interactive', 'smartctl', '-H', '-d', dev_type, disk],
                        capture_output=True, text=True, timeout=10
                    )
                    
                    attr_result = subprocess.run(
                        ['sudo', '--non-interactive', 'smartctl', '-A', '-d', dev_type, disk],
                        capture_output=True, text=True, timeout=10
                    )
                    
                    # If we got here, sudo worked
                    PCToolsModule.smart_data_cache[disk] = {
                        'health_output': health_result.stdout if health_result.returncode == 0 else None,
                        'attr_output': attr_result.stdout if attr_result.returncode == 0 else None,
                        'timestamp': current_time
                    }
                    PCToolsModule.smart_cache_timestamps[disk] = current_time
                    PCToolsModule.sudo_authenticated = True
                    
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                    # If sudo failed, try without sudo (in case capabilities are set)
                    try:
                        health_result = subprocess.run(
                            ['smartctl', '-H', '-d', dev_type, disk],
                            capture_output=True, text=True, timeout=5
                        )
                        
                        attr_result = subprocess.run(
                            ['smartctl', '-A', '-d', dev_type, disk],
                            capture_output=True, text=True, timeout=5
                        )
                        
                        PCToolsModule.smart_data_cache[disk] = {
                            'health_output': health_result.stdout if health_result.returncode == 0 else None,
                            'attr_output': attr_result.stdout if attr_result.returncode == 0 else None,
                            'timestamp': current_time
                        }
                        PCToolsModule.smart_cache_timestamps[disk] = current_time
                        PCToolsModule.sudo_authenticated = False
                    except Exception as e2:
                        logging.error(f"Error getting SMART data for {disk} with direct access: {e2}")
                        continue
                    
            except Exception as e:
                logging.error(f"Unexpected error getting SMART data for {disk}: {e}")
                continue
        
        # For any remaining disks, try a batch approach with a single sudo command
        remaining_disks = [disk for disk in disks if disk not in PCToolsModule.smart_data_cache]
        if remaining_disks:
            script_path = "/tmp/nest_smart_data.sh"
            try:
                logging.info(f"Attempting to get SMART data for {len(remaining_disks)} disks with a single authentication")
                
                # Create a shell script to get all SMART data
                script_content = '#!/bin/bash\n'
                script_content += 'echo "Starting SMART data collection..." >&2\n\n'
                
                for disk in remaining_disks:
                    dev_type = self.get_device_type(disk) or 'auto'
                    script_content += f'echo "=== SMART data for {disk} (type: {dev_type}) ==="\n'
                    script_content += f'smartctl -H -d {dev_type} {disk} 2>&1 || echo "Error getting health for {disk}"\n'
                    script_content += f'smartctl -A -d {dev_type} {disk} 2>&1 || echo "Error getting attributes for {disk}"\n\n'
                
                # Write the script to a temporary file
                with open(script_path, 'w') as f:
                    f.write(script_content)
                os.chmod(script_path, 0o755)  # Make the script executable
                
                # Run the script with sudo
                proc = subprocess.run(['sudo', '--non-interactive', script_path], 
                                   capture_output=True, text=True, timeout=30)
                
                if proc.returncode == 0:
                    # Parse the output to extract data for each disk
                    current_disk = None
                    current_health = ""
                    current_attrs = ""
                    
                    for line in proc.stdout.splitlines():
                        if line.startswith('=== SMART data for '):
                            # Save previous disk's data if we have one
                            if current_disk and (current_health or current_attrs):
                                PCToolsModule.smart_data_cache[current_disk] = {
                                    'health_output': current_health,
                                    'attr_output': current_attrs,
                                    'timestamp': current_time
                                }
                                PCToolsModule.smart_cache_timestamps[current_disk] = current_time
                            
                            # Start a new disk
                            current_disk = line.split(' ')[3]
                            current_health = ""
                            current_attrs = ""
                            
                            # Add the header line to both outputs
                            current_health += line + '\n'
                            current_attrs += line + '\n'
                            
                        elif current_disk:
                            # Check if this is a health or attributes line
                            if 'SMART overall-health self-assessment test result:' in line or \
                               'SMART Health Status:' in line or \
                               'SMART overall-health self-assessment test result:' in line:
                                current_health += line + '\n'
                            else:
                                current_attrs += line + '\n'
                    
                    # Save the last disk's data
                    if current_disk and (current_health or current_attrs):
                        PCToolsModule.smart_data_cache[current_disk] = {
                            'health_output': current_health,
                            'attr_output': current_attrs,
                            'timestamp': current_time
                        }
                        PCToolsModule.smart_cache_timestamps[current_disk] = current_time
                    
                    # Set the authentication flag
                    PCToolsModule.sudo_authenticated = True
                else:
                    logging.error(f"Error running sudo script: {proc.stderr}")
            except subprocess.CalledProcessError as e:
                logging.error(f"Error running sudo script: {e.stderr if hasattr(e, 'stderr') else str(e)}")
            except Exception as e:
                logging.error(f"Unexpected error: {e}")
            finally:
                # Clean up the temporary script
                try:
                    if os.path.exists(script_path):
                        os.unlink(script_path)
                except Exception as e:
                    logging.error(f"Error cleaning up temporary script: {e}")
        
        return PCToolsModule.smart_data_cache
    
    def refresh_network_info(self):
        """Refresh the network interface information"""
        if not hasattr(self, 'network_content'):
            return
            
        # Clear existing widgets
        for widget in self.network_content.winfo_children():
            widget.destroy()
        
        # Get network interfaces
        try:
            import netifaces
            interfaces = netifaces.interfaces()
            
            for i, iface in enumerate(interfaces):
                # Skip loopback interface
                if iface == 'lo':
                    continue
                    
                # Create frame for each interface
                if_frame = ttk.LabelFrame(
                    self.network_content,
                    text=iface,
                    padding=10
                )
                if_frame.pack(fill="x", pady=5, padx=5)
                
                # Get interface details
                addrs = netifaces.ifaddresses(iface)
                
                # Display IP addresses
                for family in (netifaces.AF_INET, netifaces.AF_INET6):
                    if family in addrs:
                        for addr in addrs[family]:
                            addr_str = addr.get('addr', '')
                            if addr_str and not addr_str.startswith('fe80'):  # Skip link-local IPv6
                                ttk.Label(
                                    if_frame,
                                    text=f"IP: {addr_str}",
                                    font=("Arial", 10)
                                ).pack(anchor="w")
                
                # Get MAC address
                if netifaces.AF_LINK in addrs and addrs[netifaces.AF_LINK]:
                    mac = addrs[netifaces.AF_LINK][0].get('addr', 'N/A')
                    ttk.Label(
                        if_frame,
                        text=f"MAC: {mac}",
                        font=("Arial", 10)
                    ).pack(anchor="w")
                
                # Get interface status
                try:
                    with open(f"/sys/class/net/{iface}/operstate") as f:
                        status = f.read().strip()
                        ttk.Label(
                            if_frame,
                            text=f"Status: {'Up' if status == 'up' else 'Down'}",
                            font=("Arial", 10)
                        ).pack(anchor="w")
                except:
                    pass
                    
        except ImportError:
            ttk.Label(
                self.network_content,
                text="netifaces module not installed. Install with: pip install netifaces",
                foreground="red"
            ).pack(pady=10)
        except Exception as e:
            logging.error(f"Error getting network info: {e}")
            ttk.Label(
                self.network_content,
                text=f"Error: {str(e)}",
                foreground="red"
            ).pack(pady=10)
       
    def setup_utilities_tab(self):
        """Create the Utilities tab with system maintenance and cleanup tools"""
        # Get the utilities tab from tools tabs
        utilities_tab = self.tools_tabs["utilities"]
        
        # Create main frame for the utilities tab
        main_frame = ttk.Frame(utilities_tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create a header with description
        header_label = ttk.Label(
            main_frame,
            text="System Utilities",
            font=("Arial", 14, "bold"),
            foreground=self.colors["primary"]
        )
        header_label.pack(anchor="w", pady=5)
        
        description = ttk.Label(
            main_frame,
            text="Maintenance and repair tools to keep your system running smoothly.",
            wraplength=600
        )
        description.pack(anchor="w", pady=5)
        
        # Create categories for utilities
        categories = [
            {
                "name": "System Maintenance",
                "tools": [
                    {"name": "Disk Cleanup", "description": "Remove temporary files and free disk space"},
                    {"name": "System Restore", "description": "Create or restore system restore points"},
                    {"name": "Registry Cleaner", "description": "Scan and fix registry issues"}, 
                ]
            },
            {
                "name": "Boot & Startup",
                "tools": [
                    {"name": "Startup Manager", "description": "Manage programs that run at startup"},
                    {"name": "Boot Configuration", "description": "Modify boot settings and repair boot issues"},
                ]
            },
            {
                "name": "System Optimization",
                "tools": [
                    {"name": "Service Manager", "description": "Manage system services"},
                    {"name": "Process Explorer", "description": "Advanced task manager with detailed system information"},
                    {"name": "Performance Optimizer", "description": "Tune system settings for better performance"},
                ]
            }
        ]
        
        # Create each category section
        for category in categories:
            # Create a labeled frame for the category
            cat_frame = ttk.LabelFrame(main_frame, text=category["name"])
            cat_frame.pack(fill="x", pady=10, padx=5)
            
            # Add each tool in this category
            for tool in category["tools"]:
                # Create a frame for this tool
                tool_frame = ttk.Frame(cat_frame)
                tool_frame.pack(fill="x", pady=5, padx=5)
                
                # Tool name
                name_label = ttk.Label(
                    tool_frame,
                    text=tool["name"],
                    font=("Arial", 11, "bold"),
                    foreground=self.colors["text_primary"]
                )
                name_label.pack(side="left", padx=5)
                
                # Tool description
                desc_label = ttk.Label(
                    tool_frame,
                    text=tool["description"],
                    wraplength=350
                )
                desc_label.pack(side="left", padx=10)
                
                # Tool button
                tool_btn = ttk.Button(
                    tool_frame,
                    text="Run",
                    width=10,
                    command=lambda name=tool["name"]: self.log_message(f"Running {name}...")
                )
                tool_btn.pack(side="right", padx=5)
        
        # Add a log section at the bottom
        log_frame = ttk.LabelFrame(main_frame, text="Activity Log")
        log_frame.pack(fill="x", pady=10, padx=5)
        
        self.utils_log = scrolledtext.ScrolledText(log_frame, height=6)
        self.utils_log.pack(fill="both", expand=True, padx=5, pady=5)
        self.utils_log.insert(tk.END, "Select a utility to run...")
        self.utils_log.configure(state="disabled")
    
    def setup_benchmarks_tab(self):
        """Create the Benchmarks tab with performance testing tools"""
        # Get the benchmarks tab from tools tabs
        benchmarks_tab = self.tools_tabs["benchmarks"]
        
        # Create main frame for the benchmarks tab
        main_frame = ttk.Frame(benchmarks_tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create a header with description
        header_label = ttk.Label(
            main_frame,
            text="System Benchmarks",
            font=("Arial", 14, "bold"),
            foreground=self.colors["primary"]
        )
        header_label.pack(anchor="w", pady=5)
        
        description = ttk.Label(
            main_frame,
            text="Measure performance metrics for various system components.",
            wraplength=600
        )
        description.pack(anchor="w", pady=5)
        
        # Create test selection frame
        test_frame = ttk.LabelFrame(main_frame, text="Available Benchmarks")
        test_frame.pack(fill="x", padx=10, pady=10)
        
        # Create benchmark buttons
        benchmarks = [
            {"name": "CPU Benchmark", "description": "Measures processor speed and multi-threading performance"},
            {"name": "Memory Benchmark", "description": "Tests RAM read/write speeds and latency"},
            {"name": "Disk Benchmark", "description": "Evaluates storage performance (read/write speeds, access time)"},
            {"name": "GPU Benchmark", "description": "Tests graphics performance for 2D and 3D operations"},
            {"name": "System Score", "description": "Calculates overall system performance rating"}
        ]
        
        # Create a grid of benchmark options
        for i, benchmark in enumerate(benchmarks):
            # Create a frame for each benchmark
            bench_item = ttk.Frame(test_frame)
            bench_item.pack(fill="x", padx=5, pady=5)
            
            # Benchmark name
            name_label = ttk.Label(
                bench_item, 
                text=benchmark["name"],
                font=("Arial", 11, "bold"),
                foreground=self.colors["text_primary"]
            )
            name_label.pack(side="left", padx=5)
            
            # Benchmark description
            desc_label = ttk.Label(
                bench_item,
                text=benchmark["description"],
                wraplength=400
            )
            desc_label.pack(side="left", padx=10)
            
            # Run button
            run_btn = ttk.Button(
                bench_item,
                text="Run",
                command=lambda name=benchmark["name"]: self.log_message(f"Running {name}...")
            )
            run_btn.pack(side="right", padx=5)
        
        # Results section
        results_frame = ttk.LabelFrame(main_frame, text="Benchmark Results")
        results_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Initial message in results area
        self.bench_results = scrolledtext.ScrolledText(results_frame, height=10)
        self.bench_results.pack(fill="both", expand=True, padx=5, pady=5)
        self.bench_results.insert(tk.END, "Run a benchmark to see results here.")
        self.bench_results.configure(state="disabled")
        
        # Button container
        button_container = ttk.Frame(main_frame)
        button_container.pack(fill="x", pady=(0, 10))
        
        # Save results button
        save_btn = ttk.Button(
            button_container,
            text="Save Results",
            command=lambda: self.log_message("Saving benchmark results...")
        )
        save_btn.pack(side="right", padx=10, pady=10)
        
        # Compare button
        compare_btn = ttk.Button(
            button_container,
            text="Compare with Previous",
            command=lambda: self.log_message("Comparing benchmark results...")
        )
        compare_btn.pack(side="right", padx=0, pady=10)
        
    def setup_diagnostics_tab(self):
        """Create the Diagnostics tab with hardware and software testing tools"""
        # Get the diagnostics tab from tools tabs
        diagnostics_tab = self.tools_tabs["diagnostics"]
        
        # Create main frame for the diagnostics tab
        main_frame = ttk.Frame(diagnostics_tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Create a header with description
        header_label = ttk.Label(
            main_frame,
            text="System Diagnostics",
            font=("Arial", 14, "bold"),
            foreground=self.colors["primary"]
        )
        header_label.pack(anchor="w", pady=5)
        
        description = ttk.Label(
            main_frame,
            text="Run tests to diagnose hardware and software issues on this PC.",
            wraplength=600
        )
        description.pack(anchor="w", pady=5)
        
        # Create canvas and scrollbar
        canvas_container = ttk.Frame(main_frame)
        canvas_container.pack(fill="both", expand=True)
        
        self.canvas = tk.Canvas(canvas_container)
        scrollbar = ttk.Scrollbar(canvas_container, orient="vertical", command=self.canvas.yview)
        
        # Configure the canvas
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Create a frame inside the canvas to hold the content
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Define the categories and their respective buttons
        categories = [
            {
                "name": "Hardware Tests",
                "buttons": [
                    {"text": "CPU Stress Test", "command": lambda: self.log_message("CPU Stress Test requested")},
                    {"text": "Memory Test", "command": lambda: self.log_message("Memory Test requested")},
                    {"text": "Disk Speed Test", "command": lambda: self.log_message("Disk Speed Test requested")},
                    {"text": "GPU Benchmark", "command": lambda: self.log_message("GPU Benchmark requested")},
                ]
            },
            {
                "name": "Software Tests",
                "buttons": [
                    {"text": "System File Checker", "command": lambda: self.log_message("System File Checker requested")},
                    {"text": "Disk Error Check", "command": lambda: self.log_message("Disk Error Check requested")},
                    {"text": "System Restore Points", "command": lambda: self.log_message("System Restore Points requested")},
                ]
            },
            {
                "name": "Network Tests",
                "buttons": [
                    {"text": "Network Interfaces", "command": lambda: self.log_message("Network Interfaces requested")},
                    {"text": "Network Connections", "command": lambda: self.log_message("Network Connections requested")},
                    {"text": "DNS Lookup", "command": lambda: self.log_message("DNS Lookup requested")},
                    {"text": "Ping Test", "command": lambda: self.log_message("Ping Test requested")},
                    {"text": "Trace Route", "command": lambda: self.log_message("Trace Route requested")},
                ]
            },
        ]
        
        # Create category frames with buttons
        for category in categories:
            # Create a labeled frame for each category
            category_frame = ttk.LabelFrame(self.scrollable_frame, text=category["name"])
            category_frame.pack(fill="x", padx=10, pady=5, ipady=5)
            
            # Create a grid for buttons
            button_frame = ttk.Frame(category_frame)
            button_frame.pack(fill="x", padx=5, pady=5)
            
            # Add buttons for this category
            for i, button_info in enumerate(category["buttons"]):
                btn = ttk.Button(
                    button_frame, 
                    text=button_info["text"], 
                    command=button_info["command"],
                    width=15
                )
                btn.grid(row=i//3, column=i%3, padx=5, pady=3, sticky="w")
        
        # Add a note about scrolling
        scroll_note = ttk.Label(
            self.scrollable_frame,
            text="Scroll down to see more tools",
            font=("Arial", 9, "italic"),
            foreground="gray"
        )
        scroll_note.pack(pady=(10, 20))
        
        # Set up scrolling functionality
        def update_scroll_region(event=None):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        # Update the scroll region when the size of scrollable_frame changes
        self.scrollable_frame.bind("<Configure>", update_scroll_region)
        
        # Update canvas width to match parent
        def update_canvas_width(event):
            canvas_width = event.width
            self.canvas.itemconfig(self.canvas_frame, width=canvas_width)
            
        self.canvas.bind("<Configure>", update_canvas_width)
        
        # Add mousewheel scrolling
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Add a simple log area at the bottom for messages
        log_frame = ttk.LabelFrame(main_frame, text="Activity Log")
        log_frame.pack(fill="x", pady=5, padx=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=4)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.log_text.configure(state="disabled")
    def setup_pc_tools_tab(self):
        """Create the PC Tools tab content"""
        # Get the proper tab
        pc_tools_tab = self.pc_tools_tab
        
        # Create a content area for buttons
        tools_content_frame = ttk.Frame(pc_tools_tab)
        tools_content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Define the categories and their respective buttons
        categories = [
            {
                "name": "Device Info",
                "buttons": [
                    {"text": "System Information", "command": lambda: self.log_message("System Information requested")},
                    {"text": "CPU Information", "command": lambda: self.log_message("CPU Information requested")},
                    {"text": "Memory Status", "command": lambda: self.log_message("Memory Status requested")},
                    {"text": "Disk Information", "command": lambda: self.log_message("Disk Information requested")},
                    {"text": "Display Information", "command": lambda: self.log_message("Display Information requested")}
                ]
            },
            {
                "name": "Diagnostics",
                "buttons": [
                    {"text": "Hardware Diagnostics", "command": lambda: self.log_message("Hardware Diagnostics requested")},
                    {"text": "Memory Test", "command": lambda: self.log_message("Memory Test requested")},
                    {"text": "Disk Health Check", "command": lambda: self.log_message("Disk Health Check requested")},
                    {"text": "System Logs", "command": lambda: self.log_message("System Logs requested")},
                    {"text": "Network Diagnostics", "command": lambda: self.log_message("Network Diagnostics requested")}
                ]
            },
            {
                "name": "Benchmarks",
                "buttons": [
                    {"text": "CPU Benchmark", "command": lambda: self.log_message("CPU Benchmark requested")},
                    {"text": "Memory Benchmark", "command": lambda: self.log_message("Memory Benchmark requested")},
                    {"text": "Disk Speed Test", "command": lambda: self.log_message("Disk Speed Test requested")},
                    {"text": "Network Speed Test", "command": lambda: self.log_message("Network Speed Test requested")},
                    {"text": "Graphics Benchmark", "command": lambda: self.log_message("Graphics Benchmark requested")}
                ]
            },
            {
                "name": "Utilities",
                "buttons": [
                    {"text": "Disk Cleanup", "command": lambda: self.log_message("Disk Cleanup requested")},
                    {"text": "System Optimizer", "command": lambda: self.log_message("System Optimizer requested")},
                    {"text": "Driver Manager", "command": lambda: self.log_message("Driver Manager requested")},
                    {"text": "Startup Manager", "command": lambda: self.log_message("Startup Manager requested")},
                    {"text": "System Updates", "command": lambda: self.log_message("System updates requested")}
                ]
            },
            {
                "name": "Data Recovery",
                "buttons": [
                    {"text": "File Recovery", "command": lambda: self.log_message("File Recovery requested")},
                    {"text": "Partition Recovery", "command": lambda: self.log_message("Partition Recovery requested")},
                    {"text": "Disk Clone", "command": lambda: self.log_message("Disk Clone requested")},
                    {"text": "Backup Manager", "command": lambda: self.log_message("Backup Manager requested")},
                    {"text": "Secure Erase", "command": lambda: self.log_message("Secure Erase requested")}
                ]
            },
            {
                "name": "Security Tools",
                "buttons": [
                    {"text": "Firewall Status", "command": lambda: self.log_message("Firewall Status requested")},
                    {"text": "Open Ports", "command": lambda: self.log_message("Open Ports requested")},
                    {"text": "Process Security", "command": lambda: self.log_message("Process Security requested")},
                    {"text": "User Accounts", "command": lambda: self.log_message("User Accounts requested")},
                    {"text": "System Permissions", "command": lambda: self.log_message("System Permissions requested")}
                ]
            },
            {
                "name": "Advanced Tests",
                "buttons": [
                    {"text": "Driver Verifier", "command": lambda: self.log_message("Driver Verifier requested")},
                    {"text": "Memory Diagnostic", "command": lambda: self.log_message("Memory Diagnostic requested")},
                    {"text": "System File Checker", "command": lambda: self.log_message("System File Checker requested")},
                    {"text": "Disk Error Check", "command": lambda: self.log_message("Disk Error Check requested")},
                    {"text": "System Restore Points", "command": lambda: self.log_message("System Restore Points requested")}
                ]
            }
        ]
        
        # Create sections for each category
        row = 0
        for category in categories:
            # Category header
            category_frame = ttk.LabelFrame(tools_content_frame, text=category["name"])
            category_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
            tools_content_frame.columnconfigure(0, weight=1)
            
            # Create buttons
            for i, button_info in enumerate(category["buttons"]):
                btn = ttk.Button(
                    category_frame,
                    text=button_info["text"],
                    command=button_info["command"]
                )
                btn.grid(row=i, column=0, sticky="w", padx=10, pady=5)
            
            row += 1

    def setup_network_tab(self):
        """Set up the Network tab with interface information."""
        # Initialize label dictionaries for updating later
        self.network_info_labels = {}
        
        # Get the network tab from device tabs
        network_tab = self.device_tabs["network"]
        
        # Create a frame for the network info content
        network_frame = ttk.Frame(network_tab)
        network_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create container frame that dynamically sizes based on parent
        net_container = ttk.Frame(network_frame)
        net_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Get container to use all available space by preventing propagation
        net_container.pack_propagate(False)
        
        # Set up a window resize handler to adjust the container height
        def update_net_container_size(event=None):
            # Get the parent container's height (network_tab)
            tab_height = network_tab.winfo_height()
            # Use most of available height but leave room for padding/margins
            if tab_height > 50:  # Only resize if we have meaningful height
                # Calculate available height, account for padding and other elements
                available_height = tab_height - 40  # Subtract padding/margins
                net_container.configure(height=available_height)
                self.net_canvas.configure(height=available_height - 10)  # Slight adjustment for inner padding
        
        # Bind to Configure events for dynamic resizing
        network_tab.bind("<Configure>", update_net_container_size)
        
        # Create canvas and scrollbar for scrolling
        self.net_canvas = tk.Canvas(net_container, highlightthickness=0)
        self.net_canvas.pack(side="left", fill="both", expand=True)
        
        # Add scrollbar
        net_scrollbar = ttk.Scrollbar(net_container, orient="vertical", command=self.net_canvas.yview)
        net_scrollbar.pack(side="right", fill="y")
        
        # Configure the canvas
        self.net_canvas.configure(yscrollcommand=net_scrollbar.set)
        
        # Create a frame inside the canvas to hold content
        net_frame = ttk.Frame(self.net_canvas)
        
        # Create a window in the canvas to display the frame
        self.net_canvas_frame = self.net_canvas.create_window((0, 0), window=net_frame, anchor="nw")
        
        # Configure canvas resize handling
        def _configure_net_canvas(event):
            # Update the scrollregion to encompass the inner frame
            self.net_canvas.configure(scrollregion=self.net_canvas.bbox("all"))
            # Update canvas window width to match canvas width
            self.net_canvas.itemconfig(self.net_canvas_frame, width=event.width)
            
        net_frame.bind("<Configure>", _configure_net_canvas)
        self.net_canvas.bind("<Configure>", lambda e: self.net_canvas.itemconfig(self.net_canvas_frame, width=e.width))
        
        # Header for network information with brand styling
        header_label = ttk.Label(
            net_frame, text="Network Information", font=("Arial", 12, "bold"),
            foreground=self.colors["primary"]
        )
        header_label.pack(anchor="w", pady=5)
        net_interfaces = self._get_network_interfaces()
        
        # Display network interfaces
        for interface, if_data in net_interfaces.items():
            if interface == 'lo':  # Skip loopback interface
                continue
                
            interface_frame = ttk.LabelFrame(net_frame, text=f"{if_data.get('Name', interface)} Interface")
            interface_frame.pack(fill="both", expand=True, pady=5, padx=3, ipady=5)
            interface_frame.interface_id = interface  # Store interface ID for later updates
            
            # Display interface information
            self._display_interface_info(interface_frame, if_data)
        
        # Define the scroll region update function
        def update_net_canvas_width(event):
            canvas_width = event.width
            self.net_canvas.itemconfig(self.net_canvas_frame, width=canvas_width)
        self.net_canvas.bind("<Configure>", update_net_canvas_width)

        # Add mousewheel scrolling
        def _net_on_mousewheel(event):
            self.net_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        # Store the mousewheel function for binding/unbinding
        self._net_mousewheel_func = _net_on_mousewheel
        # We'll bind when tab is selected and unbind when leaving the tab
        # Initial binding since the tab is currently active
        self.net_canvas.bind_all("<MouseWheel>", self._net_mousewheel_func)
        
        def update_net_scroll_region(event=None):
            self.net_canvas.configure(scrollregion=self.net_canvas.bbox("all"))
        # Update the scroll region when the size of scrollable_frame changes
        net_frame.bind("<Configure>", update_net_scroll_region)
        
        # Add Speed Test section
        speed_frame = ttk.LabelFrame(net_frame, text="Internet Speed Test")
        speed_frame.pack(fill="x", expand=False, pady=(15, 5), padx=5, ipady=10)
        
        # Speed test results
        results_frame = ttk.Frame(speed_frame)
        results_frame.pack(fill="x", pady=5)
        
        # Download speed
        ttk.Label(results_frame, text="Download:", font=("Arial", 9, "bold"), width=10, anchor="e").grid(row=0, column=0, padx=5, pady=2, sticky="e")
        self.download_speed = ttk.Label(results_frame, text="0.00 Mbps", font=("Arial", 9), width=15, anchor="w")
        self.download_speed.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        
        # Upload speed
        ttk.Label(results_frame, text="Upload:", font=("Arial", 9, "bold"), width=10, anchor="e").grid(row=1, column=0, padx=5, pady=2, sticky="e")
        self.upload_speed = ttk.Label(results_frame, text="0.00 Mbps", font=("Arial", 9), width=15, anchor="w")
        self.upload_speed.grid(row=1, column=1, padx=5, pady=2, sticky="w")
        
        # Ping
        ttk.Label(results_frame, text="Ping:", font=("Arial", 9, "bold"), width=10, anchor="e").grid(row=2, column=0, padx=5, pady=2, sticky="e")
        self.ping_label = ttk.Label(results_frame, text="-- ms", font=("Arial", 9), width=15, anchor="w")
        self.ping_label.grid(row=2, column=1, padx=5, pady=2, sticky="w")
        
        # Server info
        ttk.Label(results_frame, text="Server:", font=("Arial", 9, "bold"), width=10, anchor="e").grid(row=0, column=2, padx=5, pady=2, sticky="e")
        self.server_label = ttk.Label(results_frame, text="Ready", font=("Arial", 9), anchor="w")
        self.server_label.grid(row=0, column=3, padx=5, pady=2, sticky="w", columnspan=2)
        
        # Progress bars frame
        progress_bars_frame = ttk.Frame(speed_frame)
        progress_bars_frame.pack(fill="x", padx=5, pady=10)
        
        # Configure styles for both progress bars
        style = ttk.Style()
        style.theme_use('default')
        
        # Style for the first half (green) progress bar
        style.configure('Green.Horizontal.TProgressbar',
                      troughcolor='white',
                      background='#4CAF50',
                      troughrelief='flat',
                      borderwidth=0)
        
        # Style for the second half (blue) progress bar
        style.configure('Blue.Horizontal.TProgressbar',
                      troughcolor='white',
                      background='#2196F3',
                      troughrelief='flat',
                      borderwidth=0)
        
        # Frame to hold both progress bars
        self.progress_container = ttk.Frame(progress_bars_frame)
        self.progress_container.pack(fill='x', expand=True, pady=5)
        
        # First progress bar (0-50%)
        self.progress_bar_green = ttk.Progressbar(
            self.progress_container,
            style='Green.Horizontal.TProgressbar',
            orient='horizontal',
            mode='determinate',
            length=150  # Half the total width
        )
        self.progress_bar_green.pack(side='left', fill='both', expand=True)
        
        # Second progress bar (50-100%)
        self.progress_bar_blue = ttk.Progressbar(
            self.progress_container,
            style='Blue.Horizontal.TProgressbar',
            orient='horizontal',
            mode='determinate',
            length=150,  # Half the total width
            value=0  # Start at 0
        )
        self.progress_bar_blue.pack(side='left', fill='both', expand=True)
        
        # Status label for test phase
        self.phase_label = ttk.Label(progress_bars_frame, text="Ready to test", font=("Arial", 8), foreground="#757575")
        self.phase_label.pack(side='top', fill='x', pady=(0, 5))
        
        # Test button
        button_frame = ttk.Frame(speed_frame)
        button_frame.pack(fill="x", pady=(5, 0))
        
        self.test_button = ttk.Button(button_frame, 
                                    text="Start Speed Test", 
                                    command=self.run_speed_test,
                                    style="Accent.TButton")
        self.test_button.pack(side="right", padx=5)
        
        # Configure grid weights for responsive layout
        for i in range(4):
            results_frame.columnconfigure(i, weight=1)
        
        # Network tab setup complete
    
    def on_tab_changed(self, event):
        """Handle tab change event with intelligent cache refresh policy.
        
        Args:
            event: Tab change event
        """
        # Record tab switch time for performance tracking
        switch_start = time.time()
        
        # Get current tab
        tab_id = self.notebook.select()
        tab_index = self.notebook.index(tab_id)
        tab_text = self.notebook.tab(tab_id, "text")
        
        # Log tab change
        self.log_message(f"Switched to {tab_text} tab")
        
        # Update status
        self.update_status(f"Loading {tab_text} tab...")
        
        # Unbind all mousewheel events to avoid conflicts
        if hasattr(self, '_info_mousewheel_func'):
            self.info_canvas.unbind_all("<MouseWheel>")
        
        # Determine if we should refresh based on cache config
        should_refresh = self.cache_config.get("refresh_on_tab_switch", True)
        
        # Update tab-specific data if needed
        if should_refresh:
            # Handle specific tabs
            if tab_text == "System Info":
                # Rebind mousewheel for system info tab
                if hasattr(self, '_info_mousewheel_func'):
                    self.info_canvas.bind_all("<MouseWheel>", self._info_mousewheel_func)
                # Refresh device information
                self.refresh_system_info()
            
            elif tab_text == "Storage":
                # Refresh storage information
                self.log_message("Refreshing storage information...")
            
            elif tab_text == "PC Tools":
                # PC Tools tab specific refreshing
                self.log_message("Refreshing PC tools information...")
        
        # Calculate and record switch time
        switch_time = time.time() - switch_start
        self.performance_metrics['tab_switch_times'].append({
            'tab': tab_text,
            'time': switch_time
        })
        
        # Update status when done
        self.update_status(f"Ready - {tab_text} tab loaded")

    def update_last_update_time(self):
        """Update the last update time label in the status bar."""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if hasattr(self, 'last_update'):
            self.last_update.set(f"Last updated: {current_time}")
        
    def refresh_system_info(self):
        """Refresh all system information and tools status"""
        self.log_message("Refreshing system information and tools status...")
        
        # 1. First refresh tools status in the main tab
        smartctl_available = shutil.which("smartctl") is not None
        tools_status = "✅ Available" if smartctl_available else "❌ Not Available"
        if hasattr(self, 'smartctl_label'):
            self.smartctl_label.config(text=f"SMART Diagnostics Tools: {tools_status}")
        
        lshw_available = shutil.which("lshw") is not None
        lshw_status = "✅ Available" if lshw_available else "❌ Not Available"
        if hasattr(self, 'lshw_label'):
            self.lshw_label.config(text=f"Hardware Info Tools: {lshw_status}")
        
        # 2. Refresh System tab information
        if hasattr(self, 'system_info_labels'):
            # Update boot time and uptime
            try:
                with open('/proc/uptime', 'r') as f:
                    uptime_seconds = float(f.readline().split()[0])
                boot_time = time.time() - uptime_seconds
                boot_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(boot_time))
                
                # Format uptime nicely
                days, remainder = divmod(uptime_seconds, 86400)
                hours, remainder = divmod(remainder, 3600)
                minutes, seconds = divmod(remainder, 60)
                uptime_str = f"{int(days)} days, {int(hours)} hours, {int(minutes)} minutes"
                
                # Update system info labels if they exist
                for key, label in self.system_info_labels.items():
                    if key == 'Boot Time':
                        label.config(text=boot_time_str)
                    elif key == 'Uptime':
                        label.config(text=uptime_str)
                    elif key == 'Last System Update':
                        label.config(text=time.strftime('%Y-%m-%d %H:%M:%S'))
            except Exception as e:
                logging.error(f"Error updating system info: {e}")
        
        # 3. Refresh Hardware tab information
        if hasattr(self, 'hardware_info_labels'):
            try:
                # Update CPU and memory information
                cpu_percent = psutil.cpu_percent(interval=0.1)
                mem = psutil.virtual_memory()
                mem_total = f"{mem.total / (1024**3):.1f} GB"
                mem_used = f"{mem.used / (1024**3):.1f} GB ({mem.percent}%)"
                
                # Update hardware info labels if they exist
                for key, label in self.hardware_info_labels.items():
                    if key == 'CPU Usage':
                        label.config(text=f"{cpu_percent}%")
                    elif key == 'Memory Total':
                        label.config(text=mem_total)
                    elif key == 'Memory Used':
                        label.config(text=mem_used)
            except Exception as e:
                logging.error(f"Error updating hardware info: {e}")
        
        # 4. Refresh Storage tab information
        if hasattr(self, 'storage_info_labels'):
            try:
                # Update storage information
                for key, label in self.storage_info_labels.items():
                    if 'Disk' in key:
                        # Refresh disk usage information
                        self.get_all_smart_data()  # Refresh SMART data for all disks
            except Exception as e:
                logging.error(f"Error updating storage info: {e}")
        
        # 5. Refresh Network tab information - network info is handled separately
        try:
            # Update network interfaces if needed
            if hasattr(self, 'update_network_interfaces'):
                self.update_network_interfaces()
        except Exception as e:
            logging.error(f"Error updating network info: {e}")
        
        # 6. Check for system updates
        self.check_system_updates()
        
        self.update_status("System information refreshed")
    
    def update_status(self, message):
        """Update status bar with a message."""
        if hasattr(self, 'status_message'):
            self.status_message.set(message)
            # Update the timestamp in the status bar
            if hasattr(self, 'last_update'):
                current_time = time.strftime('%Y-%m-%d %H:%M:%S')
                self.last_update.set(f"Last updated: {current_time}")
            self.update_idletasks()
    
    # Class variable to track uptime refresh counter
    uptime_refresh_counter = 0
    
    def refresh_live_data(self):
        """Refresh only dynamic data like temps, speeds, and utilizations (called every second)"""
        # Only refresh if the module is still active in the UI
        if not hasattr(self, 'winfo_exists') or not self.winfo_exists():
            return False  # Stop timer if widget no longer exists
        
        try:
            # Increment uptime counter
            PCToolsModule.uptime_refresh_counter += 1

            # Check hardware_info_labels and update UI
            if hasattr(self, 'hardware_info_labels'):
                # CPU usage percentage
                cpu_percent = psutil.cpu_percent(interval=0.1)
                
                # Get current CPU frequency (updated in real-time)
                try:
                    current_freq = "Unknown"
                    if hasattr(psutil, 'cpu_freq'):
                        freq = psutil.cpu_freq()
                        if freq and freq.current:
                            current_freq = f"{freq.current:.2f} MHz"
                except Exception:
                    pass
                
                for key, label in self.hardware_info_labels.items():
                    if key == 'CPU Usage':
                        label.config(text=f"{cpu_percent}%")
                    elif key == 'CPU Frequency' and current_freq:
                        label.config(text=current_freq)
                    elif key == 'CPU Temperature' and hasattr(self, 'get_cpu_temp'):
                        # Update CPU temperature if available
                        temp = self.get_cpu_temp()
                        if temp:
                            label.config(text=f"{temp:.1f}°C")
                    elif key == 'GPU Temperature' and hasattr(self, 'get_gpu_temp'):
                        # Update GPU temperature if available
                        temp = self.get_gpu_temp()
                        if temp:
                            label.config(text=f"{temp:.1f}°C")
                    elif key == 'GPU Frequency' and hasattr(self, 'get_gpu_freq'):
                        # Update GPU frequency if available
                        freq = self.get_gpu_freq()
                        if freq:
                            label.config(text=f"{freq:.0f} MHz")
                    elif key == 'Used Memory':
                        # Get memory information
                        mem = psutil.virtual_memory()
                        mem_used = f"{mem.used / (1024**3):.1f} GB"
                        label.config(text=mem_used)
                    elif key == 'Available Memory':
                        mem = psutil.virtual_memory()
                        avail_mem = f"{mem.available / (1024**3):.1f} GB"
                        label.config(text=avail_mem)
                
            # Update battery labels directly
            try:
                # Get battery info
                battery_info = self.get_battery_info()
                
                # If battery is present, update the labels
                if battery_info['present']:
                    # Update battery charge label if it exists
                    if hasattr(self, 'battery_charge_label'):
                        capacity = f"{battery_info['capacity']}%"
                        self.battery_charge_label.config(text=capacity)
                    
                    # Update battery status label if it exists
                    if hasattr(self, 'battery_status_label'):
                        status = battery_info['status']
                        self.battery_status_label.config(text=status)
            
                    # Refresh network data in real-time, including WiFi information
                    if hasattr(self, 'network_info_labels') and self.network_info_labels:
                        self._refresh_network_data()
                    
                    # Update battery health label if it exists
                    if hasattr(self, 'battery_health_label'):
                        health = battery_info['health']
                        self.battery_health_label.config(text=health)
            except Exception as e:
                logging.error(f"Error updating battery labels: {e}")
                
            # Update uptime if needed (every 59 seconds)
            if PCToolsModule.uptime_refresh_counter >= 59:
                PCToolsModule.uptime_refresh_counter = 0  # Reset counter
                
                # Update uptime if the label exists
                try:
                    with open('/proc/uptime', 'r') as f:
                        uptime_seconds = float(f.readline().split()[0])
                    
                    # Format uptime nicely
                    days, remainder = divmod(uptime_seconds, 86400)
                    hours, remainder = divmod(remainder, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    uptime_str = f"{int(days)} days, {int(hours)} hours, {int(minutes)} minutes"
                    
                    # Update uptime label if it exists
                    if hasattr(self, 'system_info_labels') and "Uptime" in self.system_info_labels:

                        self.system_info_labels["Uptime"].config(text=uptime_str)
                except Exception as e:
                    logging.error(f"Error updating uptime: {e}")
            
            # Update network speeds
            self.update_network_speeds_only()
            
            # Return True to keep the timer running
            return True
            
        except Exception as e:
            logging.error(f"Error in live data refresh: {e}")
            return True  # Keep timer running even if there's an error
            
    def start_live_refresh(self):
        """Start the timer for live refresh of dynamic data"""
        # Cancel any existing timer
        self.stop_live_refresh()
        
        # Start a new timer (every 1000ms = 1 second)
        self.refresh_timer_id = self.after(1000, self.live_refresh_callback)
        logging.info("Started live refresh timer")
    
    def stop_live_refresh(self):
        """Stop the live refresh timer"""
        if self.refresh_timer_id is not None:
            self.after_cancel(self.refresh_timer_id)
            self.refresh_timer_id = None
            logging.info("Stopped live refresh timer")
    
    def live_refresh_callback(self):
        """Callback for the live refresh timer"""
        # Call the refresh method
        refresh_result = self.refresh_live_data()
        
        if refresh_result:
            # Schedule the next refresh if returned True
            self.refresh_timer_id = self.after(1000, self.live_refresh_callback)
    
    def update_network_speeds_only(self):
        """Update just the network speeds for live monitoring"""
        try:
            # Get all network interfaces
            net_io_counters = psutil.net_io_counters(pernic=True)
            
            # Get timestamp for speed calculation
            current_time = time.time()
            
            # Process each interface
            for interface, counters in net_io_counters.items():
                # Skip loopback interface
                if interface == 'lo':
                    continue
                    
                # Calculate speeds based on previous counters if available
                if hasattr(self, '_prev_net_counters') and interface in self._prev_net_counters:
                    prev_counters, prev_time = self._prev_net_counters[interface]
                    time_delta = current_time - prev_time
                    
                    if time_delta > 0:
                        # Calculate bytes/sec
                        bytes_sent = counters.bytes_sent - prev_counters.bytes_sent
                        bytes_recv = counters.bytes_recv - prev_counters.bytes_recv
                        
                        # Convert to KB/s or MB/s based on speed
                        upload_speed = bytes_sent / time_delta
                        download_speed = bytes_recv / time_delta
                        
                        # Format as KB/s or MB/s for display
                        if upload_speed > 1024 * 1024:
                            upload_text = f"{upload_speed / (1024 * 1024):.1f} MB/s"
                        else:
                            upload_text = f"{upload_speed / 1024:.1f} KB/s"
                            
                        if download_speed > 1024 * 1024:
                            download_text = f"{download_speed / (1024 * 1024):.1f} MB/s"
                        else:
                            download_text = f"{download_speed / 1024:.1f} KB/s"
                        
                        # Update the interface displays if they exist
                        if hasattr(self, 'network_interface_info') and interface in self.network_interface_info:
                            info = self.network_interface_info[interface]
                            if 'upload_label' in info:
                                info['upload_label'].config(text=upload_text)
                            if 'download_label' in info:
                                info['download_label'].config(text=download_text)
                
                # Store current counters for next calculation
                if not hasattr(self, '_prev_net_counters'):
                    self._prev_net_counters = {}
                self._prev_net_counters[interface] = (counters, current_time)
                
        except Exception as e:
            logging.error(f"Error updating network speeds: {e}")
            # Don't reraise - we want live updates to continue even if there's an error
    
    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def _update_canvas_width(self, event):
        """Update canvas width when window is resized"""
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_frame, width=canvas_width)
        
    def check_system_updates(self):
        """Check for system updates and update the UI labels"""
        import subprocess
        import threading
        import queue
        
        # Create a queue for thread-safe communication if it doesn't exist
        if not hasattr(self, 'update_queue'):
            self.update_queue = queue.Queue()
            # Start the queue processor in the main thread
            self.process_update_queue()
            
        self.log_message("Starting system update check in background...")
        
        # Update UI to show we're checking
        if hasattr(self, 'system_info_labels'):
            if "Updates Available" in self.system_info_labels:
                self.system_info_labels["Updates Available"].config(text="Checking...")
            if "Last System Update" in self.system_info_labels:
                self.system_info_labels["Last System Update"].config(text="Checking...")
        
        def check_updates_apt():
            try:
                # First try to get upgradable packages without apt-get update (faster)
                result = subprocess.run(
                    ['apt', 'list', '--upgradable'], 
                    capture_output=True, text=True, timeout=10
                )
                updates = [line for line in result.stdout.splitlines() 
                          if '/' in line and not line.startswith('Listing...')]
                updates_count = str(len(updates))
            except Exception as e:
                logging.error(f"APT update check failed: {e}")
                updates_count = "Error checking"
            
            try:
                # Try to get last update time from /var/lib/apt/periodic/update-success-stamp
                if os.path.exists('/var/lib/apt/periodic/update-success-stamp'):
                    timestamp = os.path.getmtime('/var/lib/apt/periodic/update-success-stamp')
                    last_update = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    # Fallback to checking apt history logs
                    history_result = subprocess.run(
                        "grep -h 'Start-Date' /var/log/apt/history.log 2>/dev/null | tail -n 1", 
                        shell=True, capture_output=True, text=True, timeout=5
                    )
                    if history_result.returncode == 0 and history_result.stdout.strip():
                        last_line = history_result.stdout.strip()
                        if "Start-Date:" in last_line:
                            last_update = last_line.replace("Start-Date:", "").strip()
                        else:
                            last_update = "No updates found"
                    else:
                        last_update = "No history found"
            except Exception as e:
                logging.error(f"APT last update time check failed: {e}")
                last_update = "Error checking"
            
            return updates_count, last_update
        
        def check_updates_dnf():
            try:
                result = subprocess.run(
                    ['dnf', 'check-update', '--quiet'], 
                    capture_output=True, text=True, timeout=15
                )
                # DNF returns 100 when updates are available
                if result.returncode == 100:
                    updates = [line for line in result.stdout.splitlines() 
                              if line.strip() and not line.startswith('Last metadata')]
                    updates_count = str(len(updates))
                elif result.returncode == 0:
                    updates_count = "0"
                else:
                    updates_count = f"Error ({result.returncode})"
            except Exception as e:
                logging.error(f"DNF update check failed: {e}")
                updates_count = "Error checking"
            
            try:
                result = subprocess.run(
                    ['dnf', 'history', 'list'], 
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0 and result.stdout.strip():
                    lines = result.stdout.splitlines()
                    if len(lines) > 2:  # Header + separator + at least one entry
                        last_update = lines[2].strip()  # First entry after header
                    else:
                        last_update = "No history found"
                else:
                    last_update = "No history found"
            except Exception as e:
                logging.error(f"DNF history check failed: {e}")
                last_update = "Error checking"
            
            return updates_count, last_update
        
        def worker_thread():
            # Default values in case checks fail
            updates_count = "Unknown"
            last_update = "Unknown"
            success = False
            error_msg = ""
            
            try:
                # Determine which package manager to use
                if os.path.exists('/usr/bin/apt') or os.path.exists('/bin/apt'):
                    logging.info("Detecting APT package manager, running apt checks")
                    updates_count, last_update = check_updates_apt()
                elif os.path.exists('/usr/bin/dnf') or os.path.exists('/bin/dnf'):
                    logging.info("Detecting DNF package manager, running dnf checks")
                    updates_count, last_update = check_updates_dnf()
                else:
                    logging.warning("No supported package manager found (apt/dnf)")
                    updates_count = "N/A"
                    last_update = "N/A"
                
                # Log the results
                logging.info(f"Update check complete: {updates_count} updates available, last update: {last_update}")
                success = True
                
            except Exception as e:
                error_msg = str(e)
                logging.error(f"Error in update check thread: {error_msg}")
                success = False
            
            # Put the results in the queue instead of trying to schedule UI updates directly
            # This is completely thread-safe as the queue handles synchronization
            try:
                if success:
                    # Queue the successful result
                    self.update_queue.put(('success', updates_count, last_update))
                else:
                    # Queue the error
                    self.update_queue.put(('error', error_msg))
            except Exception as queue_error:
                logging.error(f"Failed to add to update queue: {queue_error}")
        

        

        
        # Start the background thread
        thread = threading.Thread(target=worker_thread, daemon=True)
        thread.start()
        
        self.log_message("Update check thread started. UI will be updated when complete.")
    
    def process_update_queue(self):
        """Process any pending items in the update queue (runs on main thread)"""
        try:
            # Process all items currently in the queue
            while hasattr(self, 'update_queue') and not self.update_queue.empty():
                try:
                    # Get an item from the queue without blocking
                    item = self.update_queue.get_nowait()
                    
                    # Process the item based on its type
                    if item[0] == 'success':
                        # Item format: ('success', updates_count, last_update)
                        self.update_ui_callback(item[1], item[2])
                    elif item[0] == 'error':
                        # Item format: ('error', error_msg)
                        self.update_error_callback(item[1])
                    
                    # Mark the task as done
                    self.update_queue.task_done()
                except Exception as item_error:
                    logging.error(f"Error processing queue item: {item_error}")
        except Exception as queue_error:
            logging.error(f"Error processing update queue: {queue_error}")
        
        # Schedule the next check (every 100ms)
        if self.winfo_exists():
            self.after(100, self.process_update_queue)
    
    def update_ui_callback(self, updates_count, last_update):
        """Safely update the UI with update check results from the main thread"""
        try:
            # Safely check if widget still exists
            if not self.winfo_exists():
                return
                
            if "Updates Available" in self.system_info_labels:
                self.system_info_labels["Updates Available"].config(text=str(updates_count))
            if "Last System Update" in self.system_info_labels:
                self.system_info_labels["Last System Update"].config(text=str(last_update))
            self.log_message(f"System update check complete. {updates_count} updates available.")
        except Exception as ui_error:
            logging.error(f"Failed to update UI with update results: {ui_error}")
    
    def update_error_callback(self, error_msg):
        """Safely update the UI with error status from the main thread"""
        try:
            # Safely check if widget still exists
            if not self.winfo_exists():
                return
                
            if "Updates Available" in self.system_info_labels:
                self.system_info_labels["Updates Available"].config(text="Error")
            if "Last System Update" in self.system_info_labels:
                self.system_info_labels["Last System Update"].config(text="Error")
            self.log_message(f"System update check failed: {error_msg}")
        except Exception as ui_error:
            logging.error(f"Failed to update UI with error status: {ui_error}")
            
    def log_message(self, message):
        """Log a message to the activity log"""
        # Log to console
        logging.info(message)
        
        # Update UI if available
        if hasattr(self, 'log_text'):
            self.log_text.configure(state="normal")
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_text.configure(state="disabled")
            self.log_text.yview(tk.END)
            
        # Also update utils_log if it exists
        if hasattr(self, 'utils_log'):
            self.utils_log.configure(state="normal")
            self.utils_log.insert(tk.END, f"\n{message}")
            self.utils_log.see(tk.END)
            self.utils_log.configure(state="disabled")

# Export the PCToolsModule for the main Nest application
__all__ = ['PCToolsModule']

# Log successful setup
logging.info("PC Tools module loaded - standalone implementation")

# For standalone execution
if __name__ == "__main__":
    # Simple test app
    root = tk.Tk()
    root.title("PC Tools Module")
    root.geometry("1024x768")
    root.option_add('*applicationVersion', '1.0.0')
    
    # Set a theme that matches the other modules
    style = ttk.Style()
    if "clam" in style.theme_names():
        style.theme_use("clam")
    
    # Create and pack the PC Tools module
    app = PCToolsModule(root, {"name": "Test User"})
    app.pack(fill="both", expand=True)
    
    # Start the main loop
    root.mainloop()

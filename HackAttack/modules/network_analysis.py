"""
Network & Protocol Analysis Module for Hack Attack

This module provides comprehensive network traffic analysis and protocol inspection
capabilities for security testing and ethical hacking purposes.
"""

import json
import logging
import os
import re
import socket
import subprocess
import sys
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union, Callable

# Debug: Create a debug log file in /tmp
try:
    DEBUG_LOG = "/tmp/network_analysis_debug.log"
    with open(DEBUG_LOG, 'a') as f:
        f.write("\n" + "="*80 + "\n")
        f.write(f"[{datetime.now()}] Starting script with PID: {os.getpid()}, UID: {os.getuid()}, EUID: {os.geteuid()}\n")
        f.write(f"Python: {sys.version}\n")
        f.write(f"Args: {sys.argv}\n")
        f.write(f"CWD: {os.getcwd()}\n")
        f.write(f"Environment: {os.environ.get('PYTHONPATH', 'Not set')}\n")
        f.write(f"Full environment: {dict(os.environ)}\n")
except Exception as e:
    print(f"Failed to initialize debug log: {e}")
    DEBUG_LOG = None

# Log to file for debugging
def log_debug(message):
    if not DEBUG_LOG:
        return
    try:
        with open(DEBUG_LOG, 'a') as f:
            f.write(f"[{datetime.now()}] {message}\n")
    except Exception as e:
        print(f"Failed to write to debug log: {e}")

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to see all messages
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Set log level for other modules to WARNING to reduce noise
logging.getLogger('scapy').setLevel(logging.WARNING)
logging.getLogger('asyncio').setLevel(logging.WARNING)

# Log environment information
logger.debug("Python version: %s", os.sys.version)
logger.debug("Current working directory: %s", os.getcwd())

# Network capture dependencies
try:
    from scapy.all import *
    from scapy.layers.inet import IP, TCP, UDP, ICMP
    from scapy.layers.l2 import Ether, ARP
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    logger.warning("Scapy not available. Please install with: pip install scapy")

# GUI Dependencies
from PySide6.QtCore import QThread, Signal, Qt, QSize, QTimer, Slot, QMetaObject, Q_ARG, QObject, QProcess
from PySide6.QtGui import QIcon, QFont, QColor, QAction, QTextCursor
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTreeWidget, QTreeWidgetItem, QTabWidget, QLabel,
    QStatusBar, QMessageBox, QFileDialog, QTableWidget, QTableWidgetItem,
    QLineEdit, QProgressBar, QHeaderView, QStyle, QMenu, QSplitter,
    QComboBox, QFormLayout, QGroupBox, QCheckBox, QTextEdit, QSpinBox, QFrame
)

class NetworkAnalyzer:
    """Main class for network traffic analysis and protocol inspection."""
    
    def __init__(self):
        """Initialize the NetworkAnalyzer class."""
        self.capture_active = threading.Event()
        self.packets = []
        self.capture_filter = ""
        self.interface = self._get_default_interface()
        self.packet_callback = None
        self.capture_thread = None
        self.sniffer = None  # Store the sniffer instance for proper cleanup
    
    def get_available_interfaces(self) -> List[str]:
        """Get a list of available network interfaces."""
        interfaces = []
        
        # Try to get interfaces using scapy
        if SCAPY_AVAILABLE:
            try:
                ifaces = get_working_ifaces()
                if hasattr(ifaces, 'keys'):
                    return list(ifaces.keys())
                else:
                    # Handle case where ifaces is already a list
                    return [iface.name for iface in ifaces if hasattr(iface, 'name')]
            except Exception as e:
                logger.warning(f"Could not get interfaces with scapy: {e}")
        
        # Fallback to netifaces
        try:
            import netifaces
            return netifaces.interfaces()
        except Exception as e:
            logger.error(f"Could not get interfaces with netifaces: {e}")
            
        # Final fallback to common interface names
        return ["eth0", "wlan0", "lo"]
    
    def _get_default_interface(self) -> str:
        """Get the default network interface."""
        if not SCAPY_AVAILABLE:
            return "eth0"
            
        try:
            # Get default gateway interface
            import netifaces
            gateways = netifaces.gateways()
            default_gateway = gateways['default'][netifaces.AF_INET][1]
            
            # Verify the interface exists
            if default_gateway in self.get_available_interfaces():
                return default_gateway
                
            # Fallback to first non-loopback interface
            for iface in self.get_available_interfaces():
                if iface != 'lo' and not iface.startswith('docker') and not iface.startswith('br-'):
                    return iface
                    
            return "eth0"  # Final fallback
            
        except Exception as e:
            logger.error(f"Could not determine default interface: {e}")
            available = self.get_available_interfaces()
            return available[0] if available else "eth0"
    
    def set_interface(self, interface: str) -> None:
        """Set the network interface to capture on."""
        self.interface = interface
        if SCAPY_AVAILABLE:
            conf.iface = interface
    
    def set_capture_filter(self, capture_filter: str) -> None:
        """Set the capture filter (BPF syntax)."""
        self.capture_filter = capture_filter
    
    def start_capture(self) -> bool:
        """Start capturing network traffic using tshark."""
        logger.info("=" * 60)
        logger.info("STARTING CAPTURE WITH TSHARK")
        logger.info(f"Process ID: {os.getpid()}")
        logger.info(f"User ID: {os.getuid()}")
        logger.info(f"Effective User ID: {os.geteuid()}")

        if self.capture_active.is_set():
            warning_msg = "Capture is already running"
            logger.warning(warning_msg)
            if self.packet_callback:
                self.packet_callback({
                    'warning': True,
                    'message': warning_msg,
                    'timestamp': datetime.now().strftime('%H:%M:%S.%f')[:-3]
                })
            return False

        try:
            # Build tshark command with verbose output and line buffering
            cmd = [
                'tshark',
                '-i', self.interface,
                '-V',  # Verbose output
                '-l',  # Line buffered output
                '-c', '0'  # Capture indefinitely until stopped
            ]

            # Start tshark subprocess
            self.capture_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # Line buffered
            )

            self.capture_active.set()

            # Start thread to read tshark output and forward to terminal
            def read_output():
                while self.capture_active.is_set():
                    line = self.capture_process.stdout.readline()
                    if not line:
                        break
                    print(line.strip(), flush=True)  # Forward to Windsurf terminal immediately
                    if self.packet_callback:
                        # Optionally parse line for packet info if needed
                        pass

            import threading
            self.capture_thread = threading.Thread(target=read_output, daemon=True)
            self.capture_thread.start()

            logger.info("Capture started successfully with tshark verbose output")
            return True

        except Exception as e:
            error_msg = f"Failed to start capture with tshark: {str(e)}"
            logger.error(error_msg, exc_info=True)
            if self.packet_callback:
                self.packet_callback({
                    'error': True,
                    'message': error_msg,
                    'timestamp': datetime.now().strftime('%H:%M:%S.%f')[:-3]
                })
            return False

    def stop_capture(self):
        """Stop the tshark capture process."""
        if hasattr(self, 'capture_process') and self.capture_process:
            self.capture_active.clear()
            self.capture_process.terminate()
            self.capture_process.wait(timeout=5)
            self.capture_process = None
            logger.info("Capture stopped")

    def _capture_loop(self):
        """Main capture loop running in a separate thread."""
        try:
            logger.info(f"[DEBUG] Starting capture loop on thread: {threading.current_thread().name}")
            logger.info(f"[DEBUG] Interface: {self.interface}")
            logger.info(f"[DEBUG] Filter: {self.capture_filter}")
            
            # Verify interface exists and is up
            try:
                import netifaces
                if self.interface not in netifaces.interfaces():
                    error_msg = f"Interface {self.interface} not found"
                    logger.error(error_msg)
                    if self.packet_callback:
                        self.packet_callback({
                            'error': True,
                            'message': error_msg,
                            'timestamp': datetime.now().strftime('%H:%M:%S.%f')[:-3]
                        })
                    return
                
                # Get interface flags
                if_flags = netifaces.ifaddresses(self.interface)
                logger.info(f"[DEBUG] Interface flags: {if_flags}")
                
            except Exception as e:
                logger.error(f"[DEBUG] Error checking interface: {e}", exc_info=True)
            
            # Create the sniffer
            try:
                logger.info("[DEBUG] Creating AsyncSniffer instance...")
                self.sniffer = AsyncSniffer(
                    iface=self.interface,
                    filter=self.capture_filter,
                    prn=self._packet_callback,
                    store=0,  # Don't store packets in memory
                    promisc=False,  # Don't use promiscuous mode
                    monitor=False,   # Don't use monitor mode
                    timeout=10       # Add a timeout to prevent hanging
                )
                
                logger.info("[DEBUG] Starting sniffer...")
                self.sniffer.start()
                logger.info("[DEBUG] Sniffer started successfully")
                
                # Keep the thread alive while capture is active
                while self.capture_active.is_set():
                    time.sleep(0.5)
                    if not hasattr(self, 'sniffer') or not self.sniffer:
                        logger.error("[DEBUG] Sniffer instance lost!")
                        break
                        
            except Exception as e:
                logger.error(f"[DEBUG] Error in sniffer: {e}", exc_info=True)
                raise
                
        except Exception as e:
            error_msg = f"Error in capture loop: {str(e)}"
            logger.error(error_msg, exc_info=True)
            if self.packet_callback:
                self.packet_callback({
                    'error': True,
                    'message': error_msg,
                    'timestamp': datetime.now().strftime('%H:%M:%S.%f')[:-3]
                })
        finally:
            # Ensure cleanup
            if hasattr(self, 'sniffer') and self.sniffer:
                try:
                    self.sniffer.stop()
                except:
                    pass
                self.sniffer = None
            
            logger.info("Exiting capture thread")
    
    def _packet_callback(self, packet):
        """Callback for processing each captured packet."""
        try:
            # Process the packet
            packet_info = self._process_packet(packet)
            
            # Add to our packet list
            self.packets.append(packet_info)
            
            # Notify the callback if set
            if self.packet_callback:
                self.packet_callback(packet_info)
                
        except Exception as e:
            logger.error(f"Error processing packet: {e}", exc_info=True)
        
    def packet_handler(self, packet):
        """Process a captured packet."""
        # This method is kept for backward compatibility
        # The actual packet processing is now done in the CaptureThread._packet_callback method
        pass
    
    def set_packet_callback(self, callback: Callable[[Dict], None]) -> None:
        """Set the packet callback function."""
        self.packet_callback = callback
        
    def _process_packet(self, packet):
        """Process a captured packet and return packet info.
        
        Args:
            packet: The captured packet from Scapy
            
        Returns:
            dict: Packet information dictionary
        """
        try:
            # Create a dictionary with packet information
            packet_info = {
                'timestamp': datetime.now().strftime('%H:%M:%S.%f')[:-3],
                'source': '',
                'destination': '',
                'protocol': 'Unknown',
                'length': len(packet) if hasattr(packet, '__len__') else 0,
                'info': packet.summary() if hasattr(packet, 'summary') else str(packet)[:100],
                'raw': packet
            }
            
            # Extract source and destination
            if packet.haslayer('IP'):
                ip = packet['IP']
                packet_info['source'] = ip.src
                packet_info['destination'] = ip.dst
                
                if packet.haslayer('TCP'):
                    tcp = packet['TCP']
                    packet_info['protocol'] = 'TCP'
                    packet_info['source'] += f":{tcp.sport}"
                    packet_info['destination'] += f":{tcp.dport}"
                    packet_info['info'] = f"{ip.src}:{tcp.sport} -> {ip.dst}:{tcp.dport} [{tcp.flags}] Seq={tcp.seq} Ack={tcp.ack} Win={tcp.window}"
                elif packet.haslayer('UDP'):
                    udp = packet['UDP']
                    packet_info['protocol'] = 'UDP'
                    packet_info['source'] += f":{udp.sport}"
                    packet_info['destination'] += f":{udp.dport}"
                    packet_info['info'] = f"{ip.src}:{udp.sport} -> {ip.dst}:{udp.dport} Len={len(udp.payload) if hasattr(udp, 'payload') else 0}"
                elif packet.haslayer('ICMP'):
                    packet_info['protocol'] = 'ICMP'
                    packet_info['info'] = f"{ip.src} -> {ip.dst} ICMP Type: {packet['ICMP'].type}"
                else:
                    packet_info['protocol'] = ip.proto
                    packet_info['info'] = f"{ip.src} -> {ip.dst} Proto: {ip.proto}"
            elif packet.haslayer('ARP'):
                arp = packet['ARP']
                packet_info['protocol'] = 'ARP'
                packet_info['source'] = arp.psrc
                packet_info['destination'] = arp.pdst
                packet_info['info'] = f"Who has {arp.pdst}? Tell {arp.psrc}"
                
            return packet_info
            
        except Exception as e:
            logger.error(f"Error processing packet: {e}", exc_info=True)
            return None
    
    def get_capture_stats(self) -> Dict[str, int]:
        """Get statistics about the current capture."""
        return {
            'total_packets': len(self.packets),
            'tcp_packets': sum(1 for p in self.packets if p.get('protocol') == 'TCP'),
            'udp_packets': sum(1 for p in self.packets if p.get('protocol') == 'UDP'),
            'other_packets': sum(1 for p in self.packets if p.get('protocol') not in ['TCP', 'UDP'])
        }
    
    def get_protocol_distribution(self) -> Dict[str, int]:
        """Get the distribution of protocols in the captured traffic."""
        protocols = {}
        for packet in self.packets:
            proto = packet.get('protocol', 'Unknown')
            protocols[proto] = protocols.get(proto, 0) + 1
        return protocols
    
    def get_top_talkers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the top talkers by packet count."""
        talkers = {}
        for packet in self.packets:
            src = packet.get('source')
            dst = packet.get('destination')
            if src and dst:
                key = f"{src} -> {dst}"
                talkers[key] = talkers.get(key, 0) + 1
        
        return [
            {'conversation': k, 'packet_count': v}
            for k, v in sorted(talkers.items(), key=lambda x: x[1], reverse=True)[:limit]
        ]


class CaptureThread(QThread):
    """Thread for capturing network packets."""
    packet_received = Signal(dict)
    capture_error = Signal(str)
    
    def __init__(self, analyzer, gui=None):
        super().__init__()
        self.analyzer = analyzer
        self.gui = gui  # Reference to the GUI for direct method calls
        self._is_running = True  # Start in running state
        self.sniffer = None
        self._stop_event = threading.Event()
        
        # Set the packet callback
        self.analyzer.set_packet_callback(self._packet_callback)
        
        # Ensure we clean up properly
        self.destroyed.connect(self.stop_capture)
        
        # Set thread priority to low to avoid affecting UI responsiveness
        self.setPriority(QThread.Priority.LowPriority)
    
    def _packet_callback(self, packet):
        """Handle a captured packet and forward it to the GUI."""
        if not self._is_running or not self.analyzer.capture_active.is_set():
            logger.debug("Capture not active, ignoring packet")
            return
            
        try:
            # Process the packet to extract information
            packet_info = self.analyzer._process_packet(packet)
            
            if packet_info is None:
                logger.warning("Failed to process packet")
                return
                
            # Always emit the signal to ensure it reaches the GUI
            self.packet_received.emit(packet_info)
            
            # Also try direct GUI update if available
            try:
                if hasattr(self, 'gui') and self.gui is not None:
                    QMetaObject.invokeMethod(
                        self.gui,
                        'add_packet_safe',
                        Qt.ConnectionType.QueuedConnection,
                        Q_ARG(dict, packet_info)
                    )
            except Exception as e:
                logger.error(f"Error in direct GUI update: {e}", exc_info=True)
                
        except Exception as e:
            logger.error(f"Error in packet callback: {e}", exc_info=True)
            self.capture_error.emit(str(e))
    def run(self):
        """Run the capture loop."""
        try:
            logger.info(f"Starting sniffer on interface: {self.analyzer.interface}")
            logger.info(f"Using filter: {self.analyzer.capture_filter}")
            
            # Define a packet callback that forwards to our handler
            def packet_callback(pkt):
                if hasattr(self, '_packet_callback') and callable(self._packet_callback):
                    self._packet_callback(pkt)
            
            # Start the sniffer in a separate thread
            try:
                logger.debug("Creating AsyncSniffer instance...")
                self.sniffer = AsyncSniffer(
                    iface=self.analyzer.interface,
                    prn=packet_callback,  # Use our callback instead of direct method
                    filter=self.analyzer.capture_filter,
                    store=0
                )
                logger.debug("AsyncSniffer instance created")
                
                logger.debug("Starting sniffer thread...")
                self.sniffer.start()
                logger.info("Sniffer thread started successfully")
                
                # Keep the thread alive while the sniffer is running
                while self._is_running and hasattr(self, 'sniffer') and self.sniffer and self.sniffer.running:
                    if self._stop_event.wait(0.1):  # Wait with timeout to check stop condition
                        break
                        
            except Exception as e:
                error_msg = f"Error starting sniffer: {str(e)}"
                logger.error(error_msg, exc_info=True)
                self.capture_error.emit(error_msg)
                
        except Exception as e:
            error_msg = f"Error in capture thread: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.capture_error.emit(error_msg)
        finally:
            try:
                if hasattr(self, 'sniffer') and self.sniffer:
                    logger.info("Stopping sniffer...")
                    if hasattr(self.sniffer, 'stop'):
                        self.sniffer.stop()
            except Exception as e:
                logger.error(f"Error stopping sniffer: {e}")
            
            self._is_running = False
            logger.info("Exiting capture thread")

    def stop_capture(self):
        """Stop the capture thread."""
        logger.info("Stopping capture thread...")
        self._is_running = False
        
        try:
            if self.analyzer and hasattr(self.analyzer, 'stop_capture'):
                self.analyzer.stop_capture()
        except Exception as e:
            logger.error(f"Error stopping capture: {e}")
        
        self.quit()
        self.wait()
    
    def stop(self):
        """Stop the capture thread."""
        logger.debug("Stop requested for capture thread")
        self._is_running = False
        self._stop_event.set()
        
        # Give the thread a moment to finish
        if not self.wait(1000):  # Wait up to 1 second
            logger.warning("Capture thread did not stop gracefully, terminating...")
            self.terminate()
            self.wait()
        
        logger.debug("Capture thread stopped")


class NetworkAnalysisGUI(QMainWindow):
    """GUI for the Network Analysis tool."""
    
    def __init__(self, parent=None):
        """Initialize the Network Analysis GUI."""
        super().__init__(parent)
        
        # Initialize state flags
        self._is_closing = False
        self.auto_scroll = True  # Enable auto-scroll by default
        
        # Set up the main window style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e2e;
                color: #000000;  /* Black text for maximum contrast */
            }
            QTableWidget {
                background-color: #ffffff;  /* Pure white background */
                color: #000000;  /* Black text */
                gridline-color: #c0c0c0;  /* Slightly darker grid lines */
                font-weight: 500;  /* Slightly bolder text */
            }
            QTableWidget::item {
                color: #000000;  /* Black text */
                padding: 3px 6px;  /* More horizontal padding */
            }
            QTableWidget::item:selected {
                background-color: #0056b3;  /* Darker blue for better contrast */
                color: #ffffff;  /* White text when selected */
            }
            QHeaderView::section {
                background-color: #e0e0e0;  /* Light gray header */
                color: #000000;  /* Black text */
                padding: 6px;
                border: 1px solid #a0a0a0;  /* Darker border */
                font-weight: bold;  /* Bold header text */
            }
            QLineEdit, QComboBox, QPushButton {
                background-color: #ffffff;  /* White background */
                color: #000000;  /* Black text */
                border: 1px solid #a0a0a0;  /* Darker border */
                padding: 4px 8px;  /* More padding */
                border-radius: 3px;
                font-weight: 500;  /* Slightly bolder text */
            }
            QPushButton:hover {
                background-color: #d0d0d0;  /* Darker hover state */
            }
        """)
        self.analyzer = NetworkAnalyzer()
        self.capture_thread = None
        self.init_ui()
        self.apply_styles()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.main_layout = QVBoxLayout()
        
        # Toolbar with a subtle background
        toolbar_container = QWidget()
        toolbar_container.setObjectName("toolbarContainer")
        toolbar_container.setStyleSheet("""
            #toolbarContainer {
                background-color: #181825;
                border-bottom: 1px solid #45475a;
                padding: 8px 15px;
                border-radius: 4px;
                margin-bottom: 10px;
            }
        """)
        toolbar_layout = QVBoxLayout(toolbar_container)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Main toolbar row
        top_toolbar = QWidget()
        top_toolbar_layout = QHBoxLayout(top_toolbar)
        top_toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Interface selection
        interface_label = QLabel("Interface:")
        interface_label.setStyleSheet("color: #a6adc8;")
        
        self.interface_combo = QComboBox()
        self.interface_combo.setFixedWidth(200)
        self.interface_combo.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #45475a;
                border-radius: 4px;
                min-width: 180px;
                background-color: #1e1e2e;
                color: #cdd6f4;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                width: 0;
                height: 0;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #cdd6f4;
            }
            QComboBox QAbstractItemView {
                background-color: #1e1e2e;
                color: #cdd6f4;
                selection-background-color: #89b4fa;
                selection-color: #1e1e2e;
                border: 1px solid #45475a;
                padding: 5px;
            }
        """)
        
        # Populate interfaces
        self.refresh_interfaces()
        
        # Refresh button
        refresh_btn = QPushButton("")
        refresh_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        refresh_btn.setToolTip("Refresh interfaces")
        refresh_btn.setFixedSize(24, 24)
        refresh_btn.clicked.connect(self.refresh_interfaces)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #45475a;
            }
        """)
        
        # Add to layout
        top_toolbar_layout.addWidget(interface_label)
        top_toolbar_layout.addWidget(self.interface_combo)
        top_toolbar_layout.addWidget(refresh_btn)
        top_toolbar_layout.addStretch()
        
        # Filter and controls row
        controls_toolbar = QWidget()
        controls_layout = QHBoxLayout(controls_toolbar)
        controls_layout.setContentsMargins(0, 5, 0, 0)
        
        # Add other controls (filter, buttons) here
        toolbar = self.create_toolbar()
        controls_layout.addWidget(toolbar)
        
        # Add to main toolbar
        toolbar_layout.addWidget(top_toolbar)
        toolbar_layout.addWidget(controls_toolbar)
        
        self.main_layout.addWidget(toolbar_container)
        
        # Main content area
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Packet list
        self.packet_table = QTableWidget()
        self.packet_table.setColumnCount(7)  # Fixed column count to match headers
        self.packet_table.setHorizontalHeaderLabels([
            'No.', 'Time', 'Source', 'Destination', 'Protocol', 'Length', 'Info'
        ])
        header = self.packet_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        header.setSectionsMovable(True)
        
        # Set initial column widths
        self.packet_table.setColumnWidth(0, 50)   # No.
        self.packet_table.setColumnWidth(1, 120)  # Time
        self.packet_table.setColumnWidth(2, 150)  # Source
        self.packet_table.setColumnWidth(3, 150)  # Destination
        self.packet_table.setColumnWidth(4, 80)   # Protocol
        self.packet_table.setColumnWidth(5, 70)   # Length
        
        self.packet_table.verticalHeader().setVisible(False)
        self.packet_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.packet_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.packet_table.setAlternatingRowColors(True)
        self.packet_table.setSortingEnabled(True)
        self.packet_table.doubleClicked.connect(self.show_packet_details)
        
        # Packet details
        self.packet_details = QTextEdit()
        self.packet_details.setReadOnly(True)
        
        # Capture output
        self.capture_output = QTextEdit()
        self.capture_output.setReadOnly(True)
        
        # Add widgets to splitter
        splitter.addWidget(self.packet_table)
        splitter.addWidget(self.packet_details)
        splitter.addWidget(self.capture_output)
        splitter.setSizes([400, 200, 100])
        
        # Stats panel
        stats_group = self.create_stats_panel()
        
        # Add widgets to main layout
        self.main_layout.addWidget(splitter, 1)
        
        # Create status bar
        self.statusBar().showMessage("Ready")
        
        self.central_widget = QWidget()
        self.central_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.central_widget)
    
    def refresh_interfaces(self):
        """Refresh the list of available network interfaces."""
        current = self.interface_combo.currentText()
        self.interface_combo.clear()
        
        interfaces = self.analyzer.get_available_interfaces()
        for iface in interfaces:
            self.interface_combo.addItem(iface, iface)
        
        # Try to restore selection
        index = self.interface_combo.findText(current)
        if index >= 0:
            self.interface_combo.setCurrentIndex(index)
        elif interfaces:
            # Select the default interface if available
            default_iface = self.analyzer._get_default_interface()
            index = self.interface_combo.findText(default_iface)
            if index >= 0:
                self.interface_combo.setCurrentIndex(index)
    
    def create_toolbar(self) -> QWidget:
        """Create the toolbar with capture controls."""
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Add a stretch to push everything to the right
        layout.addStretch()
        
        # Capture filter
        filter_label = QLabel("Filter:")
        filter_label.setStyleSheet("color: #a6adc8;")
        
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("tcp port 80 or udp port 53")
        self.filter_edit.setMinimumWidth(300)
        self.filter_edit.setStyleSheet("""
            QLineEdit {
                padding: 5px 10px;
                border: 1px solid #45475a;
                border-radius: 4px;
                background-color: #1e1e2e;
                color: #cdd6f4;
            }
            QLineEdit:focus {
                border: 1px solid #89b4fa;
            }
        """)
        
        # Buttons
        self.start_button = QPushButton(" Start Capture")
        self.start_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #a6e3a1;
                color: #1e1e2e;
                font-weight: bold;
                padding: 6px 15px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #94e2d5;
            }
            QPushButton:pressed {
                background-color: #89b4fa;
            }
        """)
        self.start_button.clicked.connect(self.start_capture)
        
        self.stop_button = QPushButton(" Stop")
        self.stop_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop))
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f38ba8;
                color: #1e1e2e;
                font-weight: bold;
                padding: 6px 15px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #f5c2e7;
            }
            QPushButton:pressed {
                background-color: #f5e0dc;
            }
            QPushButton:disabled {
                background-color: #45475a;
                color: #6c7086;
            }
        """)
        self.stop_button.clicked.connect(self.stop_capture)
        self.stop_button.setEnabled(False)
        
        # Add widgets to layout with some spacing
        layout.addWidget(filter_label)
        layout.addWidget(self.filter_edit)
        layout.addSpacing(15)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addStretch()
        
        toolbar.setLayout(layout)
        return toolbar
    
    def create_stats_panel(self) -> QGroupBox:
        """Create the statistics panel."""
        stats_group = QGroupBox("Capture Statistics")
        layout = QHBoxLayout()
        layout.setSpacing(20)
        
        # Stats widgets with icons and better styling
        def create_stat_widget(icon, title, initial_value="0"):
            widget = QWidget()
            layout = QVBoxLayout(widget)
            layout.setContentsMargins(10, 5, 10, 5)
            
            # Icon and title
            title_layout = QHBoxLayout()
            icon_label = QLabel(icon)
            icon_label.setStyleSheet("font-size: 14px;")
            title_label = QLabel(title)
            title_label.setStyleSheet("color: #a6adc8; font-size: 11px;")
            title_layout.addWidget(icon_label)
            title_layout.addWidget(title_label)
            title_layout.addStretch()
            
            # Value
            value_label = QLabel(initial_value)
            value_label.setStyleSheet("""
                font-size: 18px;
                font-weight: bold;
                color: #cdd6f4;
            """)
            
            layout.addLayout(title_layout)
            layout.addWidget(value_label)
            return widget, value_label
        
        # Create stat widgets
        self.packet_widget, self.packet_count_label = create_stat_widget("📦", "Total Packets", "0")
        self.tcp_widget, self.tcp_count_label = create_stat_widget("🔗", "TCP", "0")
        self.udp_widget, self.udp_count_label = create_stat_widget("📡", "UDP", "0")
        self.other_widget, self.other_count_label = create_stat_widget("❓", "Other", "0")
        
        # Add a vertical separator
        def create_separator():
            line = QFrame()
            line.setFrameShape(QFrame.Shape.VLine)
            line.setFrameShadow(QFrame.Shadow.Sunken)
            line.setStyleSheet("color: #45475a;")
            return line
        
        # Add widgets to layout
        layout.addWidget(self.packet_widget)
        layout.addWidget(create_separator())
        layout.addWidget(self.tcp_widget)
        layout.addWidget(create_separator())
        layout.addWidget(self.udp_widget)
        layout.addWidget(create_separator())
        layout.addWidget(self.other_widget)
        layout.addStretch()
        
        stats_group.setLayout(layout)
        return stats_group
    
    def apply_styles(self):
        """Apply consistent styling to the UI."""
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
                color: #cdd6f4;
                background-color: #1e1e2e;
            }
            QTableWidget {
                background-color: #181825;
                border: 1px solid #45475a;
                gridline-color: #313244;
                color: #cdd6f4;
                selection-background-color: #89b4fa;
                selection-color: #1e1e2e;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 4px 8px;
                border-bottom: 1px solid #313244;
            }
            QTableWidget::item:selected {
                background-color: #89b4fa;
                color: #1e1e2e;
            }
            QHeaderView::section {
                background-color: #313244;
                color: #cdd6f4;
                padding: 8px;
                border: none;
                border-right: 1px solid #45475a;
                border-bottom: 2px solid #89b4fa;
                font-weight: bold;
            }
            QTextEdit {
                background-color: #181825;
                border: 1px solid #45475a;
                padding: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                color: #cdd6f4;
                border-radius: 4px;
                selection-background-color: #89b4fa;
                selection-color: #1e1e2e;
            }
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #45475a;
                border-radius: 4px;
                background-color: #313244;
                color: #cdd6f4;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #45475a;
                border-color: #89b4fa;
            }
            QPushButton:pressed {
                background-color: #89b4fa;
                color: #1e1e2e;
            }
            QPushButton:disabled {
                color: #6c7086;
                background-color: #24273a;
                border-color: #313244;
            }
            QLineEdit, QComboBox {
                padding: 6px 8px;
                border: 1px solid #45475a;
                border-radius: 4px;
                background-color: #181825;
                color: #cdd6f4;
                selection-background-color: #89b4fa;
                selection-color: #1e1e2e;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }
            QComboBox::down-arrow {
                image: url(none);
                width: 0;
                height: 0;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #cdd6f4;
            }
            QLabel {
                color: #cdd6f4;
            }
            QGroupBox {
                border: 1px solid #45475a;
                border-radius: 6px;
                margin-top: 10px;
                padding: 12px 15px 15px 15px;
                background-color: #181825;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                top: -8px;
                padding: 0 5px;
                color: #89b4fa;
                font-weight: bold;
            }
        """)
    
    def start_capture(self):
        """Start capturing network traffic with root privileges if needed."""
        
        # Get the current user's environment
        user = os.environ.get('SUDO_USER') or os.environ.get('USER') or os.getlogin()
        log_debug(f"Current user: {user}")
        
        xauth_path = f"/home/{user}/.Xauthority"
        if not os.path.exists(xauth_path):
            xauth_path = os.path.join('/run/user', str(os.getuid()), 'gdm/Xauthority')
            log_debug(f"Using alternative XAUTHORITY path: {xauth_path}")
        
        # Build the pkexec command directly without nohup or bash -c
        script_path = os.path.abspath(__file__)
        log_debug(f"Script path: {script_path}")
        log_debug(f"Python executable: {sys.executable}")
        
        # Get capture parameters
        interface = self.interface_combo.currentText()
        capture_filter = self.filter_edit.text()
        log_debug(f"Interface: {interface}, Filter: {capture_filter}")
        
        # Build the pkexec command
        cmd = [
            'pkexec',
            sys.executable,
            script_path,
            '--capture-only',
            interface,
            capture_filter or ''
        ]

        logger.info(f"Starting capture with elevated privileges: {' '.join(cmd)}")

        try:
            # Start the pkexec process detached
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Wait for the process to complete or for password entry
            try:
                # Start threads to read stdout and stderr and forward to terminal
                import threading

                def forward_output(pipe):
                    for line in iter(pipe.readline, ''):
                        if line:
                            print(line.strip())  # Forward to Windsurf terminal

                threading.Thread(target=forward_output, args=(process.stdout,), daemon=True).start()
                threading.Thread(target=forward_output, args=(process.stderr,), daemon=True).start()

                stdout, stderr = process.communicate(timeout=30)  # Wait up to 30 seconds for password
                if process.returncode != 0:
                    error_msg = f"Failed to start capture: {stderr or stdout or 'Unknown error'}"
                    logger.error(error_msg)
                    QMessageBox.critical(
                        self,
                        "Privilege Error",
                        f"Failed to start capture with root privileges.\nError: {error_msg}"
                    )
                    return
                else:
                    logger.info("Capture started with elevated privileges")
                    # Update UI to reflect capture started
                    self.start_button.setEnabled(False)
                    self.stop_button.setEnabled(True)
                    self.interface_combo.setEnabled(False)
                    self.statusBar().showMessage(f"Capturing on {interface} (elevated)...")

            except subprocess.TimeoutExpired:
                logger.info("Waiting for user to enter password in pkexec prompt...")
                self.statusBar().showMessage(f"Waiting for password entry for capture on {interface}...")

        except Exception as e:
            error_msg = f"Failed to start capture with pkexec: {str(e)}"
            logger.error(error_msg, exc_info=True)
            QMessageBox.critical(
                self,
                "Privilege Error",
                f"Failed to start capture with root privileges.\nError: {error_msg}"
            )
            return

        # If already root, start capture normally
        if not self.analyzer.start_capture():
            QMessageBox.critical(self, "Capture Error", "Failed to start capture. Check logs for details.")
            return

    def stop_capture(self):
        """Stop the packet capture and clean up resources."""
        if not hasattr(self, 'capture_thread') or not self.capture_thread:
            return
            
        logger.info("Stopping sniffer...")
        try:
            # Set a flag to indicate we're stopping
            if hasattr(self.capture_thread, 'stop'):
                self.capture_thread.stop()
            
            # Disconnect signals to prevent any callbacks during cleanup
            try:
                if hasattr(self.capture_thread, 'packet_received'):
                    self.capture_thread.packet_received.disconnect()
                if hasattr(self.capture_thread, 'capture_error'):
                    self.capture_thread.capture_error.disconnect()
                if hasattr(self.capture_thread, 'finished'):
                    self.capture_thread.finished.disconnect()
            except RuntimeError:
                # Signals might already be disconnected
                pass
            
            # Stop the analyzer
            if hasattr(self, 'analyzer') and self.analyzer:
                self.analyzer.stop_capture()
            
            # Clean up the thread
            if hasattr(self.capture_thread, 'isRunning') and self.capture_thread.isRunning():
                self.capture_thread.quit()
                if not self.capture_thread.wait(1000):  # Wait up to 1 second
                    self.capture_thread.terminate()
                    self.capture_thread.wait()
                    
        except Exception as e:
            logger.error(f"Error stopping capture: {e}", exc_info=True)
        finally:
            # Clean up references
            try:
                if hasattr(self.capture_thread, 'analyzer'):
                    self.capture_thread.analyzer = None
                if hasattr(self.capture_thread, 'gui'):
                    self.capture_thread.gui = None
                
                # Delete the thread
                self.capture_thread.deleteLater()
                self.capture_thread = None
            except Exception as e:
                logger.error(f"Error cleaning up capture thread: {e}")
            
            # Update UI state
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.interface_combo.setEnabled(True)
            logger.info("Capture stopped")
    
    @Slot(dict)
    def add_packet_safe(self, packet_info):
        """Thread-safe method to add a packet to the UI.
        
        Args:
            packet_info (dict): Dictionary containing packet information
        """
        try:
            # This method is called via signal/slot from the capture thread
            self.add_packet(packet_info)
        except Exception as e:
            logger.error(f"Error adding packet to UI: {e}", exc_info=True)
    
    def add_packet(self, packet_info):
        """Add a packet to the packet table.
        
        Args:
            packet_info (dict): Dictionary containing packet information
        """
        try:
            # Insert a new row at the beginning of the table
            row = self.packet_table.rowCount()
            self.packet_table.insertRow(row)
            
            # Create items for each column with appropriate text colors for alternating rows
            def create_table_item(text, is_dark_row):
                item = QTableWidgetItem(str(text))
                # Set text color based on row background
                if is_dark_row:
                    item.setForeground(QColor('#ffffff'))  # White text for dark rows
                else:
                    item.setForeground(QColor('#000000'))  # Black text for light rows
                return item
                
            # Determine if this is an even or odd row for alternating colors
            is_dark_row = row % 2 == 1  # True for odd rows (0-based index)
                
            items = [
                create_table_item(packet_info.get('number', ''), is_dark_row),   # Packet number
                create_table_item(packet_info.get('timestamp', ''), is_dark_row),      # Timestamp
                create_table_item(packet_info.get('source', ''), is_dark_row),    # Source
                create_table_item(packet_info.get('destination', ''), is_dark_row),  # Destination
                create_table_item(packet_info.get('protocol', ''), is_dark_row),  # Protocol
                create_table_item(packet_info.get('length', 0), is_dark_row),     # Length
                create_table_item(packet_info.get('info', ''), is_dark_row)       # Info
            ]
            
            # Set items in the row
            for col, item in enumerate(items):
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.packet_table.setItem(row, col, item)
                
            # Auto-scroll to the new row if auto-scroll is enabled and we have rows
            try:
                if hasattr(self, 'auto_scroll') and self.auto_scroll and row >= 0:
                    self.packet_table.scrollToBottom()
            except Exception as e:
                logger.error(f"Error in auto-scroll: {e}")
                
            # Update packet count if the method exists
            if hasattr(self, 'update_packet_count') and callable(self.update_packet_count):
                self.update_packet_count()
            
        except Exception as e:
            logger.error(f"Error adding packet to table: {e}", exc_info=True)
    
    def show_packet_details(self, index):
        """Show detailed information about the selected packet.
        
        Args:
            index: QModelIndex of the selected packet in the table
        """
        try:
            # Get the selected row
            row = index.row()
            if row < 0 or row >= self.packet_table.rowCount():
                return
                
            # Get packet info from the table
            packet_num = self.packet_table.item(row, 0).text()
            timestamp = self.packet_table.item(row, 1).text()
            source = self.packet_table.item(row, 2).text()
            destination = self.packet_table.item(row, 3).text()
            protocol = self.packet_table.item(row, 4).text()
            length = self.packet_table.item(row, 5).text()
            info = self.packet_table.item(row, 6).text()
            
            # Format the details
            details = f"""Packet #{packet_num}
{'-' * 50}
Timestamp: {timestamp}
Source: {source}
Destination: {destination}
Protocol: {protocol}
Length: {length} bytes

Additional Information:
{info}
"""
            # Display in the details pane
            self.packet_details.setPlainText(details)
            
        except Exception as e:
            logger.error(f"Error showing packet details: {e}", exc_info=True)
            self.packet_details.setPlainText(f"Error displaying packet details: {str(e)}")
    
    def on_capture_error(self, error_message):
        """Handle errors from the capture thread.
        
        Args:
            error_message (str): The error message to display
        """
        try:
            logger.error(f"Capture error: {error_message}")
            QMessageBox.critical(
                self,
                "Capture Error",
                error_message
            )
            
            # Clean up and reset UI
            self.stop_capture()
            
        except Exception as e:
            logger.error(f"Error handling capture error: {e}", exc_info=True)
    
    def on_capture_finished(self):
        """Handle capture thread finishing."""
        self.start_button.setEnabled(True)
        self.interface_combo.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.statusBar().showMessage("Capture stopped")
    
    def apply_styles(self):
        """Apply consistent styling to the UI."""
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
                color: #cdd6f4;
                background-color: #1e1e2e;
            }
            QTableWidget {
                background-color: #181825;
                border: 1px solid #45475a;
                gridline-color: #313244;
                color: #cdd6f4;
                selection-background-color: #89b4fa;
                selection-color: #1e1e2e;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 4px 8px;
                border-bottom: 1px solid #313244;
            }
            QTableWidget::item:selected {
                background-color: #89b4fa;
                color: #1e1e2e;
            }
            QHeaderView::section {
                background-color: #313244;
                color: #cdd6f4;
                padding: 8px;
                border: none;
                border-right: 1px solid #45475a;
                border-bottom: 2px solid #89b4fa;
                font-weight: bold;
            }
            QTextEdit {
                background-color: #181825;
                border: 1px solid #45475a;
                padding: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                color: #cdd6f4;
                border-radius: 4px;
                selection-background-color: #89b4fa;
                selection-color: #1e1e2e;
            }
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #45475a;
                border-radius: 4px;
                background-color: #313244;
                color: #cdd6f4;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #45475a;
                border-color: #89b4fa;
            }
            QPushButton:pressed {
                background-color: #89b4fa;
                color: #1e1e2e;
            }
            QPushButton:disabled {
                color: #6c7086;
                background-color: #24273a;
                border-color: #313244;
            }
            QLineEdit, QComboBox {
                padding: 6px 8px;
                border: 1px solid #45475a;
                border-radius: 4px;
                background-color: #181825;
                color: #cdd6f4;
                selection-background-color: #89b4fa;
                selection-color: #1e1e2e;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }
            QComboBox::down-arrow {
                image: url(none);
                width: 0;
                height: 0;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #cdd6f4;
            }
            QLabel {
                color: #cdd6f4;
            }
            QGroupBox {
                border: 1px solid #45475a;
                border-radius: 6px;
                margin-top: 10px;
                padding: 12px 15px 15px 15px;
                background-color: #181825;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                top: -8px;
                padding: 0 5px;
                color: #89b4fa;
                font-weight: bold;
            }
        """)
    
    def start_capture(self):
        """Start capturing network traffic with root privileges if needed."""
        interface = self.interface_combo.currentText()
        capture_filter = self.filter_edit.text()
        
        if not interface:
            QMessageBox.warning(self, "No Interface", "Please select a network interface")
            return
        
        if os.geteuid() != 0:
            user = os.environ.get('SUDO_USER') or os.environ.get('USER') or os.getlogin()
            xauth_path = f"/home/{user}/.Xauthority"
            if not os.path.exists(xauth_path):
                xauth_path = os.path.join('/run/user', str(os.getuid()), 'gdm/Xauthority')
            
            script_path = os.path.abspath(__file__)
            log_debug(f"Script path: {script_path}")
            log_debug(f"Python executable: {sys.executable}")
            
            # Get capture parameters
            interface = self.interface_combo.currentText()
            capture_filter = self.filter_edit.text()
            log_debug(f"Interface: {interface}, Filter: {capture_filter}")
            
            # Build the pkexec command
            cmd = [
                'pkexec',
                sys.executable,
                script_path,
                '--capture-only',
                interface,
                capture_filter or ''
            ]

            logger.info(f"Starting capture with elevated privileges: {' '.join(cmd)}")

            try:
                # Start the pkexec process detached
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                # Wait for the process to complete or for password entry
                try:
                    # Start threads to read stdout and stderr and forward to terminal
                    import threading

                    def forward_output(pipe):
                        for line in iter(pipe.readline, ''):
                            if line:
                                print(line.strip())  # Forward to Windsurf terminal

                    threading.Thread(target=forward_output, args=(process.stdout,), daemon=True).start()
                    threading.Thread(target=forward_output, args=(process.stderr,), daemon=True).start()

                    stdout, stderr = process.communicate(timeout=30)  # Wait up to 30 seconds for password
                    if process.returncode != 0:
                        error_msg = f"Failed to start capture: {stderr or stdout or 'Unknown error'}"
                        logger.error(error_msg)
                        QMessageBox.critical(
                            self,
                            "Privilege Error",
                            f"Failed to start capture with root privileges.\nError: {error_msg}"
                        )
                        return
                    else:
                        logger.info("Capture started with elevated privileges")
                        # Update UI to reflect capture started
                        self.start_button.setEnabled(False)
                        self.stop_button.setEnabled(True)
                        self.interface_combo.setEnabled(False)
                        self.statusBar().showMessage(f"Capturing on {interface} (elevated)...")

                except subprocess.TimeoutExpired:
                    logger.info("Waiting for user to enter password in pkexec prompt...")
                    self.statusBar().showMessage(f"Waiting for password entry for capture on {interface}...")

            except Exception as e:
                error_msg = f"Failed to start capture with pkexec: {str(e)}"
                logger.error(error_msg, exc_info=True)
                QMessageBox.critical(
                    self,
                    "Privilege Error",
                    f"Failed to start capture with root privileges.\nError: {error_msg}"
                )
                return

            # If already root, start capture normally
            if not self.analyzer.start_capture():
                QMessageBox.critical(self, "Capture Error", "Failed to start capture. Check logs for details.")
                return

    def display_capture_output(self, text: str):
        # This function should update the GUI with the capture output
        # For example, append text to a QTextEdit or similar widget
        if hasattr(self, 'capture_output') and self.capture_output:
            self.capture_output.append(text)

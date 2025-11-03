"""
Device Discovery & Information Module for Hack Attack

This module provides comprehensive device discovery and information gathering
capabilities for security testing and ethical hacking purposes.

Can be used both as a standalone GUI application or imported as a module.
"""

import json
import subprocess
import re
import platform
import logging
import sys
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any, Union

# GUI Dependencies (only imported when running as standalone)
GUI_ENABLED = True
try:
    # Core Qt imports
    from PyQt6.QtCore import QThread, pyqtSignal, Qt, QSize
    from PyQt6.QtGui import QIcon, QFont, QColor, QAction
    
    # Widget imports
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QTreeWidget, QTreeWidgetItem, QTabWidget, QLabel,
        QStatusBar, QMessageBox, QFileDialog, QTableWidget, QTableWidgetItem,
        QLineEdit, QProgressBar, QHeaderView, QStyle, QMenu
    )
    
    # Additional Qt modules
    from PyQt6 import QtCore, QtGui, QtWidgets
    
    # Don't create QApplication here, just verify imports
    GUI_ENABLED = True
    
except Exception as e:
    print(f"GUI disabled: {e}")
    GUI_ENABLED = False

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DeviceDiscovery:
    """Main class for device discovery and information gathering."""
    
    def __init__(self):
        """Initialize the DeviceDiscovery class."""
        self.system_info = self._get_system_info()
        self.devices = {}
    
    def _run_command(self, command: List[str]) -> str:
        """Run a shell command and return its output."""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e}")
            return ""
    
    def _get_system_info(self) -> Dict[str, str]:
        """Gather basic system information."""
        return {
            'system': platform.system(),
            'node': platform.node(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'timestamp': datetime.now().isoformat()
        }
    
    def discover_usb_devices(self) -> List[Dict[str, str]]:
        """
        Discover and list all USB devices.
        
        Returns:
            List of dictionaries containing USB device information
        """
        devices = []
        try:
            # Get basic USB device list
            output = self._run_command(['lsusb'])
            if not output:
                return devices
                
            # Parse lsusb output
            for line in output.split('\n'):
                match = re.match(
                    r'Bus (\d+) Device (\d+): ID ([0-9a-fA-F]{4}:[0-9a-fA-F]{4})\s+(.+)',
                    line
                )
                if match:
                    bus, device, vid_pid, description = match.groups()
                    vid, pid = vid_pid.split(':')
                    
                    # Get detailed information
                    detailed_info = self._get_usb_device_details(bus, device)
                    
                    device_info = {
                        'bus': bus,
                        'device': device,
                        'vendor_id': vid,
                        'product_id': pid,
                        'description': description.strip(),
                        **detailed_info
                    }
                    devices.append(device_info)
            
            self.devices['usb_devices'] = devices
            return devices
            
        except Exception as e:
            logger.error(f"Error discovering USB devices: {e}")
            return []
    
    def _get_usb_device_details(self, bus: str, device: str) -> Dict[str, str]:
        """
        Get detailed information about a specific USB device.
        
        Args:
            bus: USB bus number
            device: Device number on the bus
            
        Returns:
            Dictionary containing detailed device information
        """
        details = {
            'manufacturer': 'Unknown',
            'serial': 'Unknown',
            'driver': 'Unknown'
        }
        
        try:
            # Get detailed USB information
            output = self._run_command(['lsusb', '-v', '-s', f"{bus}:{device}"])
            if not output:
                return details
                
            # Parse detailed information
            for line in output.split('\n'):
                line = line.strip()
                if 'iManufacturer' in line and 'Unknown' not in line:
                    details['manufacturer'] = line.split(' ', 1)[1].strip()
                elif 'iSerial' in line and 'Unknown' not in line:
                    details['serial'] = line.split(' ', 1)[1].strip()
                elif 'Driver=' in line:
                    details['driver'] = line.split('=')[1].strip()
                    
        except Exception as e:
            logger.warning(f"Could not get detailed info for device {bus}:{device}: {e}")
            
        return details
        
    def discover_network_devices(self, network: str = None) -> List[Dict[str, str]]:
        """
        Discover devices on the local network using nmap.
        
        Args:
            network: Network to scan in CIDR notation (e.g., '192.168.1.0/24')
                   If None, will try to determine the local network automatically.
                   
        Returns:
            List of dictionaries containing discovered device information
        """
        devices = []
        
        try:
            if network is None:
                # Try to get the local network automatically
                import netifaces
                
                # Get default gateway interface
                gateways = netifaces.gateways()
                default_gateway = gateways['default'][netifaces.AF_INET][1]
                
                # Get interface details
                addrs = netifaces.ifaddresses(default_gateway)
                ip_info = addrs[netifaces.AF_INET][0]
                ip = ip_info['addr']
                netmask = ip_info['netmask']
                
                # Convert netmask to CIDR
                cidr = sum([bin(int(x)).count('1') for x in netmask.split('.')])
                network = f"{'.'.join(ip.split('.')[:3])}.0/{cidr}"
            
            # Run nmap scan
            cmd = [
                'nmap', '-sn', network, '-oX', '-',
                '--min-hostgroup', '50', '--max-rtt-timeout', '100ms',
                '--max-retries', '2', '--max-scan-delay', '20ms'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Parse XML output
            import xml.etree.ElementTree as ET
            root = ET.fromstring(result.stdout)
            
            for host in root.findall('.//host'):
                device = {}
                
                # Get IP address
                if host.find('address[@addrtype="ipv4"]') is not None:
                    device['ip'] = host.find('address[@addrtype="ipv4"]').get('addr')
                
                # Get MAC address and vendor
                if host.find('address[@addrtype="mac"]') is not None:
                    device['mac'] = host.find('address[@addrtype="mac"]').get('addr')
                    device['vendor'] = host.find('address[@addrtype="mac"]').get('vendor', 'Unknown')
                
                # Get hostname if available
                hostnames = host.find('hostnames')
                if hostnames is not None and hostnames.find('hostname') is not None:
                    device['hostname'] = hostnames.find('hostname').get('name')
                
                # Get status
                status = host.find('status')
                if status is not None:
                    device['status'] = status.get('state')
                
                # Get OS information if available
                os_info = host.find('os')
                if os_info is not None and os_info.find('osmatch') is not None:
                    device['os'] = os_info.find('osmatch').get('name')
                
                devices.append(device)
                
        except ImportError:
            logger.warning("netifaces module not found. Install with: pip install netifaces")
            return []
        except subprocess.CalledProcessError as e:
            logger.error(f"nmap scan failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Error scanning network: {e}")
            return []
            
        return devices
    
    def discover_pci_devices(self) -> List[Dict[str, str]]:
        """
        Discover and list all PCI devices.
        
        Returns:
            List of dictionaries containing PCI device information
        """
        devices = []
        try:
            # Get PCI device list in machine-readable format
            output = self._run_command(['lspci', '-vmm'])
            if not output:
                return devices
            
            current_device = {}
            
            # Parse lspci output
            for line in output.split('\n'):
                line = line.strip()
                if not line and current_device:
                    # End of device block, add to devices list
                    if 'slot' in current_device:
                        devices.append(current_device)
                    current_device = {}
                    continue
                    
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    # Clean up the key names
                    if key == 'class':
                        key = 'class_name'
                    elif key == 'device':
                        key = 'device_name'
                        
                    current_device[key] = value
            
            # Add the last device if exists
            if current_device and 'slot' in current_device:
                devices.append(current_device)
            
            # Get additional details for each device
            for device in devices:
                slot = device.get('slot', '')
                if slot:
                    details = self._get_pci_device_details(slot)
                    device.update(details)
            
            self.devices['pci_devices'] = devices
            return devices
            
        except Exception as e:
            logger.error(f"Error discovering PCI devices: {e}")
            return []
    
    def _get_pci_device_details(self, slot: str) -> Dict[str, str]:
        """
        Get detailed information about a specific PCI device.
        
        Args:
            slot: PCI slot identifier
            
        Returns:
            Dictionary containing detailed PCI device information
        """
        details = {
            'driver': 'Unknown',
            'module': 'Unknown',
            'iommu_group': 'Unknown'
        }
        
        try:
            # Get detailed PCI information
            output = self._run_command(['lspci', '-v', '-s', slot])
            if not output:
                return details
                
            # Parse detailed information
            for line in output.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                if 'Kernel driver in use:' in line:
                    details['driver'] = line.split(':', 1)[1].strip()
                elif 'Kernel modules:' in line:
                    details['module'] = line.split(':', 1)[1].strip()
                elif 'IOMMU group:' in line:
                    details['iommu_group'] = line.split(':', 1)[1].strip()
                    
        except Exception as e:
            logger.warning(f"Could not get detailed info for PCI device {slot}: {e}")
            
        return details
        
    def discover_block_devices(self) -> List[Dict[str, str]]:
        """
        Discover and list all block devices.
        
        Returns:
            List of dictionaries containing block device information
        """
        devices = []
        try:
            # Get block device list in JSON format
            output = self._run_command(['lsblk', '-J'])
            if not output:
                return devices
                
            # Parse JSON output
            block_data = json.loads(output)
            
            def process_device(device: Dict, parent: str = '') -> List[Dict]:
                """Recursively process block devices and their children."""
                result = []
                
                # Skip devices without a name
                if 'name' not in device:
                    return result
                
                # Skip loop devices by default
                if device['name'].startswith('loop'):
                    return result
                
                # Get device path
                path = f"/dev/{device['name']}"
                
                # Get filesystem information
                fs_info = self._get_filesystem_info(path)
                
                # Create device info
                device_info = {
                    'name': device['name'],
                    'path': path,
                    'type': device.get('type', 'disk'),
                    'size': device.get('size', '0'),
                    'model': device.get('model', '').strip('"'),
                    'vendor': device.get('vendor', '').strip('"'),
                    'mountpoint': device.get('mountpoint', ''),
                    'parent': parent,
                    **fs_info
                }
                
                # Add to results
                result.append(device_info)
                
                # Process children recursively
                if 'children' in device:
                    for child in device['children']:
                        result.extend(process_device(child, device['name']))
                
                return result
            
            # Process all block devices
            if 'blockdevices' in block_data:
                for device in block_data['blockdevices']:
                    devices.extend(process_device(device))
            
            self.devices['block_devices'] = devices
            return devices
            
        except Exception as e:
            logger.error(f"Error discovering block devices: {e}")
            return []
    
    def _get_filesystem_info(self, device_path: str) -> Dict[str, str]:
        """
        Get filesystem information for a block device.
        
        Args:
            device_path: Path to the block device (e.g., /dev/sda1)
            
        Returns:
            Dictionary containing filesystem information
        """
        fs_info = {
            'fstype': 'unknown',
            'label': '',
            'uuid': ''
        }
        
        try:
            # Use blkid to get filesystem information
            output = self._run_command(['blkid', '-o', 'export', device_path])
            if not output:
                return fs_info
                
            # Parse blkid output
            for line in output.split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    if key == 'TYPE':
                        fs_info['fstype'] = value
                    elif key == 'LABEL':
                        fs_info['label'] = value
                    elif key == 'UUID':
                        fs_info['uuid'] = value
                        
        except Exception as e:
            logger.warning(f"Could not get filesystem info for {device_path}: {e}")
            
        return fs_info
        
    def discover_network_interfaces(self) -> List[Dict[str, str]]:
        """
        Discover and list all network interfaces.
        
        Returns:
            List of dictionaries containing network interface information
        """
        interfaces = []
        try:
            # Get list of network interfaces
            output = self._run_command(['ip', '-o', 'link', 'show'])
            if not output:
                return interfaces
                
            # Parse interface list
            for line in output.split('\n'):
                if not line.strip():
                    continue
                    
                # Example: 1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
                match = re.match(r'^\d+:\s+([^:]+):\s+<([^>]+)>.*\s+state\s+(\w+)\s+', line)
                if match:
                    name, flags, state = match.groups()
                    
                    # Skip loopback interface by default
                    if name == 'lo':
                        continue
                    
                    # Get MAC address
                    mac_match = re.search(r'link/\w+\s+([0-9a-fA-F:]+)', line)
                    mac = mac_match.group(1) if mac_match else '00:00:00:00:00:00'
                    
                    # Get IP address and other details
                    ip_info = self._get_interface_ip_info(name)
                    
                    # Create interface info
                    interface_info = {
                        'name': name,
                        'mac': mac.lower(),
                        'state': state.lower(),
                        'flags': flags.lower().split(','),
                        'up': 'UP' in flags,
                        **ip_info
                    }
                    
                    interfaces.append(interface_info)
            
            self.devices['network_interfaces'] = interfaces
            return interfaces
            
        except Exception as e:
            logger.error(f"Error discovering network interfaces: {e}")
            return []
    
    def _get_interface_ip_info(self, interface: str) -> Dict[str, str]:
        """
        Get IP address information for a network interface.
        
        Args:
            interface: Network interface name (e.g., eth0, wlan0)
            
        Returns:
            Dictionary containing IP address information
        """
        ip_info = {
            'ipv4': '',
            'ipv6': '',
            'netmask': '',
            'broadcast': '',
            'mtu': '1500',
            'speed': 'unknown'
        }
        
        try:
            # Get IP address information
            output = self._run_command(['ip', '-o', '-4', 'addr', 'show', 'dev', interface])
            if output:
                # Example: 2: eth0    inet 192.168.1.100/24 brd 192.168.1.255 scope global dynamic eth0
                match = re.search(r'inet\s+([^\s/]+)(?:/(\d+))?\s+brd\s+([^\s]+)', output)
                if match:
                    ip_info['ipv4'] = match.group(1)
                    ip_info['netmask'] = self._prefix_to_netmask(int(match.group(2))) if match.group(2) else ''
                    ip_info['broadcast'] = match.group(3)
            
            # Get IPv6 address
            output = self._run_command(['ip', '-o', '-6', 'addr', 'show', 'dev', interface])
            if output:
                # Just get the first IPv6 address if multiple exist
                match = re.search(r'inet6\s+([0-9a-fA-F:]+)/', output)
                if match:
                    ip_info['ipv6'] = match.group(1)
            
            # Get interface speed and MTU
            output = self._run_command(['ethtool', interface])
            if output:
                speed_match = re.search(r'Speed:\s*(\d+\s*\w+)', output)
                if speed_match:
                    ip_info['speed'] = speed_match.group(1).strip()
                
                mtu_match = re.search(r'MTU:\s*(\d+)', output)
                if mtu_match:
                    ip_info['mtu'] = mtu_match.group(1)
            
        except Exception as e:
            logger.warning(f"Could not get IP info for interface {interface}: {e}")
            
        return ip_info
    
    @staticmethod
    def _prefix_to_netmask(prefix: int) -> str:
        """
        Convert a prefix length to a dotted-decimal netmask.
        
        Args:
            prefix: Network prefix length (0-32)
            
        Returns:
            Dotted-decimal netmask (e.g., '255.255.255.0')
        """
        if not 0 <= prefix <= 32:
            return '0.0.0.0'
            
        netmask = (0xffffffff >> (32 - prefix)) << (32 - prefix)
        return '.'.join([str((netmask >> (24 - i * 8)) & 0xff) for i in range(4)])
    
    def discover_all_devices(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Discover all available devices and return a comprehensive report.
        
        Returns:
            Dictionary containing all discovered devices by category
        """
        logger.info("Starting device discovery...")
        
        # Discover devices in parallel where possible
        import concurrent.futures
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit all discovery tasks
            usb_future = executor.submit(self.discover_usb_devices)
            pci_future = executor.submit(self.discover_pci_devices)
            block_future = executor.submit(self.discover_block_devices)
            net_future = executor.submit(self.discover_network_interfaces)
            
            # Wait for all futures to complete
            concurrent.futures.wait([
                usb_future, pci_future, block_future, net_future
            ])
            
            # Get results
            self.devices['usb_devices'] = usb_future.result()
            self.devices['pci_devices'] = pci_future.result()
            self.devices['block_devices'] = block_future.result()
            self.devices['network_interfaces'] = net_future.result()
        
        logger.info("Device discovery completed successfully")
        return self.devices
    
    def generate_report(self, format: str = 'json', output_file: Optional[str] = None) -> str:
        """
        Generate a report of all discovered devices.
        
        Args:
            format: Output format ('json', 'csv', 'text')
            output_file: Optional file path to save the report
            
        Returns:
            The generated report as a string
        """
        if not self.devices.get('usb_devices') and not self.devices.get('pci_devices') and \
           not self.devices.get('block_devices') and not self.devices.get('network_interfaces'):
            self.discover_all_devices()
        
        report = ""
        
        try:
            if format.lower() == 'json':
                report = json.dumps({
                    'timestamp': datetime.now().isoformat(),
                    'system_info': self.system_info,
                    'devices': self.devices
                }, indent=2)
                
            elif format.lower() == 'csv':
                # Simple CSV format - flattening all device types into one CSV
                import csv
                from io import StringIO
                
                output = StringIO()
                writer = csv.writer(output)
                
                # Write header
                writer.writerow([
                    'Type', 'Name', 'ID', 'Description', 'Driver', 'Status', 'Details'
                ])
                
                # Add USB devices
                for device in self.devices.get('usb_devices', []):
                    writer.writerow([
                        'USB',
                        device.get('description', ''),
                        f"{device.get('vendor_id')}:{device.get('product_id')}",
                        f"Manufacturer: {device.get('manufacturer', 'Unknown')}",
                        device.get('driver', 'Unknown'),
                        'Connected',
                        f"Bus {device.get('bus', '?')} Device {device.get('device', '?')}"
                    ])
                
                # Add PCI devices
                for device in self.devices.get('pci_devices', []):
                    writer.writerow([
                        'PCI',
                        device.get('device_name', ''),
                        device.get('slot', ''),
                        f"Class: {device.get('class_name', 'Unknown')}",
                        device.get('driver', 'Unknown'),
                        'Active',
                        f"Vendor: {device.get('vendor', 'Unknown')}"
                    ])
                
                # Add block devices
                for device in self.devices.get('block_devices', []):
                    writer.writerow([
                        'Block',
                        device.get('name', ''),
                        device.get('uuid', ''),
                        f"Type: {device.get('type', 'Unknown')}, Size: {device.get('size', '0')}",
                        device.get('fstype', 'Unknown'),
                        'Mounted' if device.get('mountpoint') else 'Unmounted',
                        f"Model: {device.get('model', 'Unknown')}, Mount: {device.get('mountpoint', 'N/A')}"
                    ])
                
                # Add network interfaces
                for interface in self.devices.get('network_interfaces', []):
                    writer.writerow([
                        'Network',
                        interface.get('name', ''),
                        interface.get('mac', ''),
                        f"State: {interface.get('state', 'down')}",
                        interface.get('driver', 'Unknown'),
                        'Up' if interface.get('up', False) else 'Down',
                        f"IP: {interface.get('ipv4', 'N/A')}, Speed: {interface.get('speed', 'Unknown')}"
                    ])
                
                report = output.getvalue()
                
            else:  # Text format
                report_parts = [
                    "=" * 80,
                    f"Device Discovery Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    "=" * 80,
                    f"System: {self.system_info['system']} {self.system_info['release']} ({self.system_info['machine']})",
                    f"Hostname: {self.system_info['node']}",
                    "-" * 80,
                    ""
                ]
                
                # Add USB devices
                if self.devices.get('usb_devices'):
                    report_parts.extend([
                        "USB Devices:",
                        "-" * 40
                    ])
                    for device in self.devices['usb_devices']:
                        report_parts.append(
                            f"{device.get('description')} (Bus {device.get('bus')} Device {device.get('device')})\n"
                            f"  Vendor: {device.get('manufacturer')}\n"
                            f"  ID: {device.get('vendor_id')}:{device.get('product_id')}\n"
                            f"  Driver: {device.get('driver')}"
                        )
                    report_parts.append("")
                
                # Add PCI devices
                if self.devices.get('pci_devices'):
                    report_parts.extend([
                        "\nPCI/PCIe Devices:",
                        "-" * 40
                    ])
                    for device in self.devices['pci_devices']:
                        report_parts.append(
                            f"{device.get('device_name')} ({device.get('slot')})\n"
                            f"  Class: {device.get('class_name')}\n"
                            f"  Vendor: {device.get('vendor', 'Unknown')}\n"
                            f"  Driver: {device.get('driver')}"
                        )
                    report_parts.append("")
                
                # Add block devices
                if self.devices.get('block_devices'):
                    report_parts.extend([
                        "\nBlock Devices:",
                        "-" * 40
                    ])
                    for device in self.devices['block_devices']:
                        report_parts.append(
                            f"{device.get('name')} ({device.get('type').title()}) - {device.get('size')}\n"
                            f"  Model: {device.get('model', 'Unknown')}\n"
                            f"  Filesystem: {device.get('fstype', 'Unknown')}\n"
                            f"  Mounted: {device.get('mountpoint', 'No')}"
                        )
                    report_parts.append("")
                
                # Add network interfaces
                if self.devices.get('network_interfaces'):
                    report_parts.extend([
                        "\nNetwork Interfaces:",
                        "-" * 40
                    ])
                    for interface in self.devices['network_interfaces']:
                        report_parts.append(
                            f"{interface.get('name')} ({'UP' if interface.get('up') else 'DOWN'}) - {interface.get('state').upper()}\n"
                            f"  MAC: {interface.get('mac')}\n"
                            f"  IPv4: {interface.get('ipv4', 'N/A')}\n"
                            f"  IPv6: {interface.get('ipv6', 'N/A')}\n"
                            f"  Speed: {interface.get('speed')}, MTU: {interface.get('mtu')}"
                        )
                
                report = "\n".join(report_parts)
            
            # Save to file if requested
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(report)
                logger.info(f"Report saved to {output_file}")
            
            return report
            
        except Exception as e:
            error_msg = f"Error generating report: {e}"
            logger.error(error_msg)
            return error_msg
    
    def get_device_summary(self) -> Dict[str, int]:
        """
        Get a summary count of discovered devices by type.
        
        Returns:
            Dictionary with device type counts
        """
        if not self.devices:
            self.discover_all_devices()
            
        return {
            'usb': len(self.devices.get('usb_devices', [])),
            'pci': len(self.devices.get('pci_devices', [])),
            'block': len(self.devices.get('block_devices', [])),
            'network': len(self.devices.get('network_interfaces', []))
        }


def main():
    """Main function to demonstrate the module's functionality."""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='Hack Attack - Device Discovery Module')
    parser.add_argument('--format', choices=['text', 'json', 'csv'], default='text',
                       help='Output format (default: text)')
    parser.add_argument('--output', help='Output file (default: stdout)')
    parser.add_argument('--discover', action='store_true',
                       help='Discover all devices and print summary')
    parser.add_argument('--usb', action='store_true', help='Show only USB devices')
    parser.add_argument('--pci', action='store_true', help='Show only PCI devices')
    parser.add_argument('--block', action='store_true', help='Show only block devices')
    parser.add_argument('--net', action='store_true', help='Show only network interfaces')
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        stream=sys.stdout
    )
    
    try:
        # Initialize the device discovery
        discovery = DeviceDiscovery()
        
        # Run discovery based on arguments
        if args.usb:
            devices = discovery.discover_usb_devices()
            discovery.devices['usb_devices'] = devices
        elif args.pci:
            devices = discovery.discover_pci_devices()
            discovery.devices['pci_devices'] = devices
        elif args.block:
            devices = discovery.discover_block_devices()
            discovery.devices['block_devices'] = devices
        elif args.net:
            devices = discovery.discover_network_interfaces()
            discovery.devices['network_interfaces'] = devices
        else:
            # Default: discover all devices
            discovery.discover_all_devices()
        
        # Generate and output the report
        report = discovery.generate_report(format=args.format, output_file=args.output)
        
        # Print to stdout if no output file was specified
        if not args.output or args.discover:
            print(report)
        
        # Print summary if requested
        if args.discover:
            summary = discovery.get_device_summary()
            print("\nDevice Discovery Summary:")
            print(f"- USB Devices: {summary['usb']}")
            print(f"- PCI/PCIe Devices: {summary['pci']}")
            print(f"- Block Devices: {summary['block']}")
            print(f"- Network Interfaces: {summary['network']}")
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)


class NetworkScanThread(QThread):
    """
    Thread for performing network scans in the background.
    
    This thread handles the potentially long-running network scan operation
    to keep the UI responsive. It emits signals to update the UI with scan
    progress and results.
    """
    
    scan_complete = pyqtSignal(list)
    scan_progress = pyqtSignal(str)
    scan_error = pyqtSignal(str)
    
    def __init__(self, device_discovery, network=None):
        """
        Initialize the network scan thread.
        
        Args:
            device_discovery: Instance of DeviceDiscovery class
            network: Network to scan in CIDR notation (e.g., '192.168.1.0/24')
        """
        super().__init__()
        self.device_discovery = device_discovery
        self.network = network
        self._is_running = True
    
    def run(self):
        """
        Run the network scan.
        
        This method is called when the thread starts. It performs the network
        scan and emits signals with the results.
        """
        try:
            # Notify UI that scan is starting
            self.scan_progress.emit("Starting network scan...")
            
            # Perform the scan
            devices = self.device_discovery.discover_network_devices(self.network)
            
            # Check if we should continue (in case of cancellation)
            if not self._is_running:
                return
                
            # Notify UI that scan is complete
            self.scan_progress.emit(f"Scan complete. Found {len(devices)} devices.")
            self.scan_complete.emit(devices)
            
        except Exception as e:
            error_msg = f"Error in network scan: {str(e)}"
            logger.error(error_msg, exc_info=True)
            if self._is_running:  # Only emit error if not cancelled
                self.scan_error.emit(error_msg)
                self.scan_complete.emit([])
    
    def stop(self):
        """
        Stop the network scan.
        
        This method can be called to gracefully stop an in-progress scan.
        """
        self._is_running = False
        self.quit()
        self.wait(5000)  # Wait up to 5 seconds for the thread to finish


class DeviceDiscoveryGUI(QMainWindow):
    """Standalone GUI for Device Discovery tool."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hack Attack - Device Discovery")
        self.setMinimumSize(1200, 800)
        self.device_discovery = DeviceDiscovery()
        self.network_scan_thread = None
        self.init_ui()
        self.apply_styles()  # Apply styles after UI is initialized
    
    def init_ui(self):
        """Initialize the user interface."""
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Top panel with buttons
        button_layout = QHBoxLayout()
        
        # Scan button with icon
        self.scan_button = QPushButton("  Scan All Devices")
        self.scan_button.setIcon(self.style().standardIcon(getattr(QStyle.StandardPixmap, 'SP_BrowserReload')))
        self.scan_button.clicked.connect(self.scan_devices)
        
        # Network scan button
        self.network_scan_button = QPushButton("  Scan Network")
        self.network_scan_button.setIcon(self.style().standardIcon(getattr(QStyle.StandardPixmap, 'SP_ComputerIcon')))
        self.network_scan_button.clicked.connect(self.scan_network_only)
        
        self.export_button = QPushButton("  Export Results")
        self.export_button.setIcon(self.style().standardIcon(getattr(QStyle.StandardPixmap, 'SP_DialogSaveButton')))
        self.export_button.setEnabled(False)
        
        button_layout.addWidget(self.scan_button)
        button_layout.addWidget(self.network_scan_button)
        button_layout.addWidget(self.export_button)
        button_layout.addStretch()
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Network Scan Tab
        self.network_scan_widget = QWidget()
        network_scan_layout = QVBoxLayout(self.network_scan_widget)
        
        # Network scan controls
        scan_controls = QHBoxLayout()
        self.network_input = QLineEdit()
        self.network_input.setPlaceholderText("Enter network (e.g., 192.168.1.0/24) or leave empty for auto-detect")
        scan_controls.addWidget(QLabel("Network:"))
        scan_controls.addWidget(self.network_input)
        
        self.scan_button_network = QPushButton("Start Scan")
        self.scan_button_network.setIcon(self.style().standardIcon(getattr(QStyle.StandardPixmap, 'SP_MediaPlay')))
        self.scan_button_network.clicked.connect(self.start_network_scan)
        scan_controls.addWidget(self.scan_button_network)
        
        self.scan_progress = QProgressBar()
        self.scan_progress.setRange(0, 0)  # Indeterminate progress
        self.scan_progress.setVisible(False)
        
        network_scan_layout.addLayout(scan_controls)
        network_scan_layout.addWidget(self.scan_progress)
        
        # Network scan results table
        self.network_scan_table = QTableWidget()
        self.network_scan_table.setColumnCount(5)
        self.network_scan_table.setHorizontalHeaderLabels(["IP", "MAC", "Hostname", "Vendor", "Status"])
        self.network_scan_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.network_scan_table.setSortingEnabled(True)
        self.network_scan_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.network_scan_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.network_scan_table.customContextMenuRequested.connect(self.show_context_menu)
        network_scan_layout.addWidget(self.network_scan_table)
        
        # Set up copy action for the context menu
        self.copy_action = QAction("Copy", self)
        self.copy_action.triggered.connect(self.copy_selected_cells)
        
        # Set up export action for the context menu
        self.export_action = QAction("Export Selected...", self)
        self.export_action.triggered.connect(self.export_selected_devices)
        
        # Set up details action for the context menu
        self.details_action = QAction("View Details...", self)
        self.details_action.triggered.connect(self.show_device_details)
        
        self.tabs.addTab(self.network_scan_widget, "Network Scan")
        
        # Existing tabs
        self.tree_widgets = {}
        
        # Network Interfaces Tab
        self.network_tree = QTreeWidget()
        self.network_tree.setHeaderLabels(["Property", "Value"])
        self.network_tree.setColumnWidth(0, 200)
        self.network_tree.setHeaderHidden(False)
        self.network_tree.setAlternatingRowColors(True)
        self.tabs.addTab(self.network_tree, "Network Interfaces")
        self.tree_widgets["network"] = self.network_tree
        
        # Block Devices Tab
        self.block_tree = QTreeWidget()
        self.block_tree.setHeaderLabels(["Property", "Value"])
        self.block_tree.setColumnWidth(0, 200)
        self.block_tree.setHeaderHidden(False)
        self.block_tree.setAlternatingRowColors(True)
        self.tabs.addTab(self.block_tree, "Storage Devices")
        self.tree_widgets["block"] = self.block_tree
        
        # USB Devices Tab
        self.usb_tree = QTreeWidget()
        self.usb_tree.setHeaderLabels(["Property", "Value"])
        self.usb_tree.setColumnWidth(0, 200)
        self.usb_tree.setHeaderHidden(False)
        self.usb_tree.setAlternatingRowColors(True)
        self.tabs.addTab(self.usb_tree, "USB Devices")
        self.tree_widgets["usb"] = self.usb_tree
        
        # PCI Devices Tab
        self.pci_tree = QTreeWidget()
        self.pci_tree.setHeaderLabels(["Property", "Value"])
        self.pci_tree.setColumnWidth(0, 200)
        self.pci_tree.setHeaderHidden(False)
        self.pci_tree.setAlternatingRowColors(True)
        self.tabs.addTab(self.pci_tree, "PCI Devices")
        self.tree_widgets["pci"] = self.pci_tree
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        
        # Assemble layout
        layout.addLayout(button_layout)
        layout.addWidget(self.tabs)
        
        # Apply styles
        self.apply_styles()
    
    def start_network_scan(self):
        """
        Start a network scan in a separate thread.
        
        This method initializes and starts a network scan in a separate thread
        to keep the UI responsive. It updates the UI to reflect the scanning
        state and connects the necessary signals.
        """
        # If a scan is already in progress, don't start another one
        if self.network_scan_thread and self.network_scan_thread.isRunning():
            QMessageBox.information(
                self, 
                "Scan in Progress", 
                "A network scan is already in progress. Please wait for it to complete."
            )
            return
        
        # Get the network to scan from the input field
        network = self.network_input.text().strip()
        if not network:
            # If no network is specified, try to determine it automatically
            try:
                import netifaces
                # Get the default gateway interface
                gateways = netifaces.gateways()
                default_gateway = gateways['default'][netifaces.AF_INET][1]
                
                # Get the network interface details
                addrs = netifaces.ifaddresses(default_gateway)
                ip_info = addrs[netifaces.AF_INET][0]
                ip = ip_info['addr']
                netmask = ip_info['netmask']
                
                # Convert IP and netmask to network CIDR
                network = f"{ip.rsplit('.', 1)[0]}.0/24"
                self.network_input.setText(network)
                
            except Exception as e:
                logger.warning(f"Could not determine local network: {e}")
                network = None
        
        # Update UI for scanning state
        self.scan_progress.setVisible(True)
        self.scan_button_network.setEnabled(False)
        self.scan_button_network.setIcon(self.style().standardIcon(getattr(QStyle.StandardPixmap, 'SP_MediaPause')))
        self.scan_button_network.setText("Scanning...")
        self.status_bar.showMessage("Scanning network. This may take a few minutes...")
        
        # Clear previous results
        self.network_scan_table.setRowCount(0)
        
        # Create and configure the scan thread
        self.network_scan_thread = NetworkScanThread(self.device_discovery, network)
        
        # Connect signals
        self.network_scan_thread.scan_complete.connect(self.on_network_scan_complete)
        self.network_scan_thread.scan_progress.connect(self.update_scan_progress)
        self.network_scan_thread.scan_error.connect(self.on_scan_error)
        self.network_scan_thread.finished.connect(self.on_scan_finished)
        
        # Start the scan
        self.network_scan_thread.start()
    
    def update_scan_progress(self, message):
        """
        Update the progress message during a network scan.
        
        Args:
            message: Progress message to display
        """
        self.status_bar.showMessage(message)
    
    def on_scan_error(self, error_message):
        """
        Handle errors that occur during a network scan.
        
        Args:
            error_message: Error message to display
        """
        logger.error(f"Network scan error: {error_message}")
        self.status_bar.showMessage(f"Error: {error_message}")
        QMessageBox.critical(self, "Scan Error", error_message)
    
    def on_scan_finished(self):
        """Clean up after a network scan has finished."""
        self.scan_progress.setVisible(False)
        self.scan_button_network.setEnabled(True)
        self.scan_button_network.setIcon(self.style().standardIcon(getattr(QStyle.StandardPixmap, 'SP_MediaPlay')))
        self.scan_button_network.setText("Start Scan")
        
        # Clean up the thread
        if self.network_scan_thread:
            self.network_scan_thread.deleteLater()
            self.network_scan_thread = None
    
    def on_network_scan_complete(self, devices):
        """
        Handle completion of a network scan.
        
        This method processes the results of a network scan and updates the UI
        with the discovered devices. It's called when the scan_complete signal
        is emitted by the NetworkScanThread.
        
        Args:
            devices: List of dictionaries containing device information
        """
        try:
            # Check if we have any devices
            if not devices:
                self.status_bar.showMessage("Network scan completed. No devices found.")
                QMessageBox.information(
                    self, 
                    "Scan Complete", 
                    "No devices were found on the network.\n\n"
                    "This could be because:\n"
                    "- No devices are connected to the network\n"
                    "- The network requires authentication\n"
                    "- The scan was interrupted\n"
                    "- Network access is restricted"
                )
                return
            
            # Sort devices by IP address for better readability
            try:
                devices.sort(key=lambda x: tuple(
                    int(part) if part.isdigit() else 0 
                    for part in x.get('ip', '0.0.0.0').split('.')
                ))
            except (ValueError, AttributeError) as e:
                logger.warning(f"Could not sort devices by IP: {e}")
                # If IP address parsing fails, use the original order
                pass
            
            # Disable sorting while updating to improve performance
            self.network_scan_table.setSortingEnabled(False)
            self.network_scan_table.setRowCount(len(devices))
            
            # Define status icons and colors
            status_icons = {
                'up': self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton),
                'down': self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton),
                'unknown': self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxQuestion)
            }
            
            # Populate the table with device information
            for row, device in enumerate(devices):
                # IP Address
                ip = device.get('ip', 'Unknown')
                ip_item = QTableWidgetItem(ip)
                ip_item.setData(Qt.ItemDataRole.UserRole, device)  # Store full device data
                
                # MAC Address
                mac = device.get('mac', 'Unknown')
                if mac and mac.lower() != 'unknown':
                    # Format MAC address with colons if it's not already formatted
                    mac = mac.upper()
                    if len(mac) == 12 and ':' not in mac:
                        mac = ':'.join(mac[i:i+2] for i in range(0, 12, 2))
                
                # Hostname
                hostname = device.get('hostname', 'Unknown')
                
                # Vendor
                vendor = device.get('vendor', 'Unknown')
                
                # Status with icon
                status = device.get('status', 'unknown').lower()
                status_icon = status_icons.get(status, status_icons['unknown'])
                status_item = QTableWidgetItem(status_icon, status.capitalize())
                
                # Set items in the table
                self.network_scan_table.setItem(row, 0, ip_item)
                self.network_scan_table.setItem(row, 1, QTableWidgetItem(mac))
                self.network_scan_table.setItem(row, 2, QTableWidgetItem(hostname))
                self.network_scan_table.setItem(row, 3, QTableWidgetItem(vendor))
                self.network_scan_table.setItem(row, 4, status_item)
                
                # Make the row selectable and enable tooltips
                for col in range(self.network_scan_table.columnCount()):
                    item = self.network_scan_table.item(row, col)
                    if item:
                        item.setToolTip(item.text())
            
            # Re-enable sorting
            self.network_scan_table.setSortingEnabled(True)
            
            # Resize columns to fit content
            self.network_scan_table.resizeColumnsToContents()
            
            # Update status bar with results
            device_count = len(devices)
            self.status_bar.showMessage(
                f"Network scan completed. Found {device_count} device{'s' if device_count != 1 else ''}."
            )
            
            # Show a notification if many devices were found
            if device_count > 20:
                QMessageBox.information(
                    self,
                    "Scan Complete",
                    f"Found {device_count} devices on the network. "
                    "Consider using filters to narrow down the results."
                )
            
        except Exception as e:
            error_msg = f"Error processing network scan results: {e}"
            logger.error(error_msg, exc_info=True)
            self.scan_error.emit(error_msg)
        finally:
            # Ensure the UI is properly reset
            self.on_scan_finished()
    
    def scan_network_only(self):
        """Switch to network scan tab and start scan."""
        self.tabs.setCurrentIndex(0)  # Switch to network scan tab
        self.start_network_scan()
    
    def show_context_menu(self, position):
        """
        Show a context menu for the network scan table.
        
        Args:
            position: The position where the context menu was requested
        """
        # Only show the menu if there are selected rows
        if not self.network_scan_table.selectedItems():
            return
            
        menu = QMenu()
        menu.addAction(self.copy_action)
        menu.addSeparator()
        menu.addAction(self.export_action)
        menu.addAction(self.details_action)
        
        # Show the context menu at the cursor position
        menu.exec_(self.network_scan_table.viewport().mapToGlobal(position))
    
    def copy_selected_cells(self):
        """Copy the selected cells to the clipboard."""
        selected = self.network_scan_table.selectedItems()
        if not selected:
            return
            
        # Get the selected rows and columns
        rows = sorted({item.row() for item in selected})
        cols = sorted({item.column() for item in selected})
        
        # Get the text from each cell
        text = []
        for row in rows:
            row_data = []
            for col in cols:
                item = self.network_scan_table.item(row, col)
                row_data.append(item.text() if item else '')
            text.append('\t'.join(row_data))
        
        # Copy to clipboard
        QApplication.clipboard().setText('\n'.join(text))
        self.status_bar.showMessage("Copied to clipboard", 3000)  # Show for 3 seconds
    
    def export_selected_devices(self):
        """Export the selected devices to a file."""
        selected = self.network_scan_table.selectedItems()
        if not selected:
            return
            
        # Get unique rows from selected items
        rows = sorted({item.row() for item in selected})
        
        # Get column headers
        headers = []
        for col in range(self.network_scan_table.columnCount()):
            headers.append(self.network_scan_table.horizontalHeaderItem(col).text())
        
        # Get the data for each selected row
        data = []
        for row in rows:
            row_data = {}
            for col in range(self.network_scan_table.columnCount()):
                item = self.network_scan_table.item(row, col)
                row_data[headers[col]] = item.text() if item else ''
            data.append(row_data)
        
        # Ask for file path
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Devices",
            "",
            "CSV Files (*.csv);;JSON Files (*.json);;All Files (*)"
        )
        
        if not file_path:
            return
            
        try:
            if file_path.lower().endswith('.json'):
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2)
            else:  # Default to CSV
                with open(file_path, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=headers)
                    writer.writeheader()
                    writer.writerows(data)
                    
            self.status_bar.showMessage(f"Exported {len(data)} devices to {file_path}", 5000)
        except Exception as e:
            error_msg = f"Error exporting devices: {e}"
            logger.error(error_msg, exc_info=True)
            QMessageBox.critical(self, "Export Error", error_msg)
    
    def show_device_details(self):
        """Show detailed information about the selected device."""
        selected = self.network_scan_table.selectedItems()
        if not selected:
            return
            
        # Get the first selected row
        row = selected[0].row()
        
        # Get the device data that was stored in the first column
        item = self.network_scan_table.item(row, 0)
        if not item:
            return
            
        device_data = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(device_data, dict):
            return
        
        # Create a dialog to show the details
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Device Details - {device_data.get('ip', 'Unknown')}")
        dialog.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        # Create a text edit to display the details
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setFont(QFont("Monospace"))
        
        # Format the device data as a string
        details = []
        for key, value in device_data.items():
            if isinstance(value, (list, dict)):
                value = json.dumps(value, indent=2)
            details.append(f"{key}: {value}")
        
        text_edit.setPlainText('\n'.join(details))
        
        # Add a close button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(dialog.reject)
        
        layout.addWidget(text_edit)
        layout.addWidget(button_box)
        
        dialog.exec()
    
    def scan_devices(self):
        """Scan for all device types and update the UI."""
        self.status_bar.showMessage("Scanning devices...")
        QApplication.processEvents()
        
        try:
            # Clear existing items
            for widget in self.tree_widgets.values():
                widget.clear()
            
            # Discover all devices
            devices = self.device_discovery.discover_all_devices()
            
            # Map device types to the correct widget
            device_mapping = {
                'usb': 'usb_devices',
                'pci': 'pci_devices',
                'block': 'block_devices',
                'network': 'network_interfaces'
            }
            
            # Update each tab
            for dev_type, widget in self.tree_widgets.items():
                device_key = device_mapping.get(dev_type)
                if device_key in devices and devices[device_key]:
                    self._populate_tree_widget(widget, devices[device_key], dev_type.capitalize() + " Device")
            
            # Update status bar with device counts
            device_counts = {
                'USB': len(devices.get('usb_devices', [])),
                'PCI': len(devices.get('pci_devices', [])),
                'Storage': len(devices.get('block_devices', [])),
                'Network': len(devices.get('network_interfaces', []))
            }
            status_msg = ", ".join([f"{count} {dev_type} devices" for dev_type, count in device_counts.items() if count > 0])
            
            self.export_button.setEnabled(True)
            self.status_bar.showMessage(f"Scan completed. Found {status_msg}.")
            
        except Exception as e:
            self.status_bar.showMessage(f"Error: {str(e)}")
            logger.error(f"Error during device scan: {e}")
    
    def _populate_tree_widget(self, widget, devices, device_type):
        """Populate a tree widget with device information."""
        if not devices:
            return
            
        for i, device in enumerate(devices, 1):
            item = QTreeWidgetItem(widget, [f"{device_type} {i}", ""])
            for key, value in device.items():
                if isinstance(value, (list, dict)):
                    child = QTreeWidgetItem(item, [str(key), ""])
                    if isinstance(value, dict):
                        for k, v in value.items():
                            QTreeWidgetItem(child, [str(k), str(v)])
                    else:  # list
                        for v in value:
                            QTreeWidgetItem(child, ["", str(v)])
                else:
                    QTreeWidgetItem(item, [str(key), str(value)])
            item.setExpanded(True)
    
    def apply_styles(self):
        """Apply consistent styling to the UI."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e2e;
                color: #cdd6f4;
            }
            QTreeWidget, QTableWidget {
                background-color: #181825;
                border: none;
                font-size: 13px;
                padding: 10px;
                outline: none;
                gridline-color: #313244;
            }
            QHeaderView::section {
                background-color: #313244;
                color: #cdd6f4;
                padding: 5px;
                border: none;
                font-weight: bold;
            }
            QTabWidget::pane {
                border: 1px solid #45475a;
                background: #1e1e2e;
            }
            QTabBar::tab {
                background: #313244;
                color: #cdd6f4;
                padding: 8px 15px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #89b4fa;
                color: #1e1e2e;
            }
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:disabled {
                background-color: #45475a;
                color: #6c7086;
            }
            QPushButton:hover {
                background-color: #74c7ec;
            }
            QLineEdit {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: 1px solid #45475a;
                padding: 5px;
                border-radius: 4px;
            }
            QProgressBar {
                border: 1px solid #45475a;
                border-radius: 4px;
                text-align: center;
                background: #1e1e2e;
            }
        """)


def main():
    """Main entry point for the Device Discovery tool."""
    if not GUI_ENABLED:
        print("Running in console mode (GUI dependencies not available)")
        print("Installing PyQt6 to enable the GUI: pip install PyQt6")
        
        # Fallback to console mode
        discovery = DeviceDiscovery()
        
        print("\n=== Network Interfaces ===")
        network_devices = discovery.discover_network_devices()
        for i, device in enumerate(network_devices, 1):
            print(f"\nInterface {i}:")
            for key, value in device.items():
                if isinstance(value, list):
                    print(f"  {key}:")
                    for item in value:
                        print(f"    {item}")
                else:
                    print(f"  {key}: {value}")
        
        print("\n=== USB Devices ===")
        usb_devices = discovery.discover_usb_devices()
        for i, device in enumerate(usb_devices, 1):
            print(f"\nUSB Device {i}:")
            for key, value in device.items():
                print(f"  {key}: {value}")
        
        print("\n=== PCI Devices ===")
        pci_devices = discovery.discover_pci_devices()
        for i, device in enumerate(pci_devices, 1):
            print(f"\nPCI Device {i}:")
            for key, value in device.items():
                print(f"  {key}: {value}")
        
        input("\nPress Enter to exit...")
        return
    
    # Run in GUI mode
    app = QApplication(sys.argv)
    window = DeviceDiscoveryGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

# HackAttack

HackAttack is a tactical offensive and penetration testing tool designed for advanced ethical hacking and security research within CommandCore. It enables controlled exploitation, vulnerability scanning, and cyber-intrusion simulations with military-grade precision.

## Key Features
- **Multi-Vector Testing**: Comprehensive penetration testing framework
- **Real-time Exploitation**: Live payload delivery and monitoring
- **Vulnerability Analysis**: Advanced mapping and reporting capabilities
- **Custom Automation**: Support for scripting and attack chain automation
- **Evasion Techniques**: Integrated countermeasure bypass modules
- **Secure Environment**: Protected operation sandbox with audit logging

## Requirements

### Python Version
- Python 3.10 or higher

### Python Dependencies
Install via pip:
```bash
pip install -r requirements.txt
```

**GUI framework:**
- `PySide6>=6.5.0` – Qt6 GUI framework

**Configuration:**
- `PyYAML>=6.0` – YAML configuration parsing
- `python-dotenv>=1.0.0` – Environment variable management

**Networking & security:**
- `requests>=2.28.0` – HTTP requests
- `scapy>=2.5.0` – Network packet capture and analysis
- `netifaces>=0.11.0` – Network interface detection

### Supported Platforms
- Linux (primary – full functionality)
- Windows (limited functionality)

### OS-Level Dependencies (Linux)

For full network analysis capabilities:

**Debian/Ubuntu:**
```bash
sudo apt-get install nmap tshark
```

**Fedora/RHEL:**
```bash
sudo dnf install nmap wireshark-cli
```

### Permissions
- **Root/sudo access required** for network packet capture and device discovery
- USB device access (user in `plugdev` group on Linux)

## Getting Started

1. Clone the repository and navigate to the HackAttack directory
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install OS-level dependencies (see above)
4. Ensure proper permissions for network capture
5. Launch the application:
   ```bash
   python launch.py
   ```

## Usage

### Entry Point
```bash
# Run from repository root (may require sudo for full functionality)
python HackAttack/launch.py

# Or with elevated privileges for network capture
sudo python HackAttack/launch.py
```

### Module Path
`HackAttack.launch` (main launcher: `launch.py`)

### Application Tabs
- **Dashboard** – Security testing overview
- **Device Discovery & Info** – Scan and analyze connected devices
- **Network & Protocol Analysis** – Analyze network traffic and protocols
- **Firmware & OS Analysis** – Inspect firmware images and operating systems
- **Authentication & Password Testing** – Test authentication mechanisms
- **Exploitation & Payloads** – Develop and manage exploits
- **Mobile & Embedded Tools** – Test mobile and embedded device security
- **Forensics & Incident Response** – Investigate security incidents
- **Settings & Reports** – Configure settings and generate reports
- **Automation & Scripting** – Create automated security workflows
- **Logs & History** – View testing activity logs
- **Help & Documentation** – Access guides and tutorials

## License

Proprietary – Outback Electronics
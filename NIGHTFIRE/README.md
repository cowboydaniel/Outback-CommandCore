# NIGHTFIRE

NIGHTFIRE is a real-time active defense and monitoring tool designed for rapid detection and response to security threats within enterprise and field environments.

## Key Features

- **Continuous Monitoring**: Real-time surveillance of network and device activities
- **Intrusion Detection**: Advanced detection with customizable alert thresholds
- **Automated Response**: Pre-configured incident response scripts for immediate action
- **Threat Intelligence**: Integrated live threat intelligence feeds for up-to-date protection
- **Forensic Readiness**: Secure event logging and comprehensive evidence collection
- **Access Control**: Role-based permissions with detailed audit trails

## Requirements

### Python Version
- Python 3.10 or higher

### Python Dependencies
Install via pip:
```bash
pip install -r requirements.txt
```
- `PySide6>=6.5.0` – Qt6 GUI framework

### Supported Platforms
- Linux (primary)
- macOS
- Windows

No additional OS-level dependencies are required.

## Getting Started

1. Clone the repository and navigate to the NIGHTFIRE directory
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Launch the application

## Usage

### Entry Point
```bash
# Run from repository root
python NIGHTFIRE/nightfire.py

# Or directly
cd NIGHTFIRE && python nightfire.py
```

### Module Path
`NIGHTFIRE.nightfire` (main module: `nightfire.py`)

### Examples
```bash
# Launch the NIGHTFIRE GUI
python NIGHTFIRE/nightfire.py
```

**Starting monitoring:**
1. Launch the application
2. Click "Start Monitoring" on the Dashboard tab
3. View real-time alerts in the Alerts tab
4. Review detailed logs in the Logs tab

**Configuring alert thresholds:**
- Network scan attempts: alerts after 10 detected scans
- Failed authentication: alerts after 5 failed attempts
- Thresholds are customizable in the configuration

**Stopping monitoring:**
- Click "Stop Monitoring" to halt the active defense system

## License

Proprietary – Outback Electronics

# ARES-i (Advanced Recon & Exploit Suite - iOS)

ARES-i is a focused iOS device penetration and diagnostic tool, optimized for reconnaissance, exploitation, and forensic analysis on Apple environments.

## Key Features

- **Secure Jailbreak Detection**: Advanced detection and bypass utilities for iOS security mechanisms
- **Filesystem Exploration**: Deep iOS filesystem navigation and manipulation capabilities
- **Vulnerability Scanning**: Automated scanning and comprehensive reporting of iOS device vulnerabilities
- **Security Assessment**: Device integrity and security posture evaluation
- **Forensic Capabilities**: Secure data extraction and export functionality
- **Remote Operations**: Support for remote diagnostics and exploitation workflows

## Requirements

### Python Version
- Python 3.10 or higher

### Python Dependencies
Install via pip:
```bash
pip install -r requirements.txt
```
- `PySide6>=6.5.0` – Qt6 GUI framework
- `requests>=2.28.0` – HTTP library

### OS-Level Dependencies
ARES-i requires the `libimobiledevice` suite for iOS device communication.

> **See [docs/system-deps.md](../docs/system-deps.md#ares-i) for comprehensive system dependency documentation.**

**Debian/Ubuntu:**
```bash
sudo apt-get install libimobiledevice-utils ifuse usbmuxd
```

**Fedora/RHEL:**
```bash
sudo dnf install libimobiledevice-utils ifuse usbmuxd
```

**macOS (Homebrew):**
```bash
brew install libimobiledevice ifuse
```

Required tools: `idevice_id`, `ideviceinfo`, `idevicebackup2`, `ifuse`

### Permissions
- USB device access (user must be in `plugdev` group on Linux)
- Filesystem mount permissions for `ifuse`

## Getting Started

1. Clone the repository and navigate to the ARES-i directory
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install OS-level dependencies (see above)
4. Ensure USB permissions are configured

## Usage

### Entry Point
```bash
# Run as module from repository root
python ARES-i/app/main.py

# Or directly
cd ARES-i && python app/main.py
```

### Module Path
`ARES-i/app/main.py` (main module)

### Examples
```bash
# Launch the ARES-i GUI
python ARES-i/app/main.py

# The application will:
# - Detect connected iOS devices automatically
# - Display device information and status
# - Provide access to filesystem exploration, backup, and diagnostic tools
```

## Documentation

Additional documentation lives in `ARES-i/docs/README.md` and the `ARES-i/docs/` directory.

## License

Proprietary – Outback Electronics

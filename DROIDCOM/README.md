# DROIDCOM (Droid Command)

DROIDCOM is a comprehensive Android diagnostic, penetration, and system control tool within CommandCore, designed for both forensic and offensive security operations.

## Key Features

- **Wide Compatibility**: Extensive support for various Android OS versions and device models
- **Root Management**: Advanced root detection, privilege escalation, and system modification tools
- **Security Scanning**: Automated vulnerability scans specifically tailored for Android ecosystems
- **Remote Control**: Secure shell and command execution interface for device management
- **System Monitoring**: Real-time system monitoring and resource management capabilities
- **Framework Integration**: Seamless integration with custom exploit payload frameworks

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
- Linux (primary – full ADB support)
- Windows (with ADB drivers installed)
- macOS (with ADB installed)

### OS-Level Dependencies
DROIDCOM requires Android Debug Bridge (ADB) and related tools.

> **See [docs/system-deps.md](../docs/system-deps.md#droidcom) for comprehensive system dependency documentation.**

**Debian/Ubuntu:**
```bash
sudo apt-get install android-tools-adb android-tools-fastboot
```

**Fedora/RHEL:**
```bash
sudo dnf install android-tools
```

**macOS (Homebrew):**
```bash
brew install android-platform-tools
```

**Windows:**
- Download [Android SDK Platform Tools](https://developer.android.com/studio/releases/platform-tools)
- Add to system PATH

Required tools:
- `adb` – Android Debug Bridge
- `fastboot` – Bootloader/recovery communication

### Permissions
- USB device access (user in `plugdev` group on Linux)
- USB debugging must be enabled on target Android device
- Device authorization required on first connection

### Android Device Setup
1. Enable Developer Options on the Android device
2. Enable USB Debugging in Developer Options
3. Connect device via USB
4. Accept the RSA key fingerprint prompt on the device

## Getting Started

1. Clone the repository and navigate to the DROIDCOM directory
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install OS-level dependencies (see above)
4. Connect an Android device with USB debugging enabled
5. Launch the application

## Usage

### Entry Point
```bash
# Run as module from repository root
python -m DROIDCOM

# Or run directly
python DROIDCOM/main.py
```

### Module Path
`DROIDCOM` (package with `main.py` entry point)

### Available Features
- **Connection** – Device detection and ADB connection management
- **Device Info** – Hardware and software information display
- **App Manager** – Install, uninstall, and manage applications
- **File Manager** – Browse and transfer files to/from device
- **Screenshot** – Capture device screen
- **Logcat** – Real-time log viewing and filtering
- **Device Control** – Reboot, recovery mode, and system commands
- **Security** – Security scanning and root detection
- **Backup** – Device backup and restore operations
- **Debugging** – Advanced debugging and testing tools

### Examples
```bash
# Launch DROIDCOM GUI
python -m DROIDCOM

# The application will:
# - Automatically detect connected Android devices
# - Display device information and status
# - Provide access to all Android management features
```

**Connecting to a device:**
1. Launch DROIDCOM
2. Connect Android device via USB (USB debugging enabled)
3. Accept RSA key authorization on device if prompted
4. Device appears in the connection panel

**Installing an APK:**
1. Navigate to App Manager
2. Click "Install APK"
3. Select the APK file
4. Monitor installation progress

**Capturing a screenshot:**
1. Navigate to Screenshot tab
2. Click "Capture"
3. Save or copy the captured image

## License

Proprietary – Outback Electronics

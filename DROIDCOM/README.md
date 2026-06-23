# DROIDCOM (Droid Command)

DROIDCOM is a comprehensive Android diagnostic, penetration, and system control tool within CommandCore, designed for both forensic and offensive security operations.

## Key Features

- **Wide Compatibility**: Extensive support for various Android OS versions and device models
- **Root Management**: Root detection, lock-screen bypass/brute-force, and boot integrity verification
- **Security Scanning**: Encryption, lock screen, dangerous permissions, certificate, AppOps, and keystore audits
- **Remote Control**: Secure shell and command execution interface for device management
- **System Monitoring**: Real-time battery, memory, CPU, network, thermal, storage, and service monitoring
- **Stress & Benchmark Testing**: CPU/RAM/GPU/Dalvik cache stress tests, app crash forcing, and looped benchmarking
- **Automation**: Shell script execution, batch app management, scheduled tasks, and combined logcat/screencap capture
- **Forensics Integration**: Native Andriller extraction/lockscreen cracking plus launchers for ALEAPP, MVT, and Autopsy

## Requirements

### Python Version
- Python 3.10 or higher

### Python Dependencies
Install via pip:
```bash
pip install -r requirements.txt
```
- `PySide6>=6.5.0` – Qt6 GUI framework

### UI Baseline
DROIDCOM now targets PySide6 exclusively. Legacy Tkinter compatibility has been
removed in favor of native Qt widgets and dialogs (`QMessageBox`,
`QFileDialog`, `QDialog`).

### Supported Platforms
- Linux (primary – full ADB support)
- Windows (with ADB drivers installed)
- macOS (with ADB installed)

### OS-Level Dependencies
DROIDCOM requires Android Debug Bridge (ADB) and related tools, plus `scrcpy`
(>= 2.1) for screen mirroring/control. DROIDCOM will attempt to auto-install
both on Linux at startup, but installing them yourself first avoids the
pkexec prompts.

> **See [docs/system-deps.md](../docs/system-deps.md#droidcom) for comprehensive system dependency documentation.**

**Debian/Ubuntu:**
```bash
sudo apt-get install android-tools-adb android-tools-fastboot scrcpy
```

**Fedora/RHEL:**
```bash
sudo dnf install android-tools scrcpy
```

**macOS (Homebrew):**
```bash
brew install android-platform-tools scrcpy
```

**Windows:**
- Download [Android SDK Platform Tools](https://developer.android.com/studio/releases/platform-tools)
- Download [scrcpy](https://github.com/Genymobile/scrcpy/releases)
- Add both to system PATH

Required tools:
- `adb` – Android Debug Bridge
- `fastboot` – Bootloader/recovery communication
- `scrcpy` (>= 2.1) – Screen mirroring and input control

Distro-packaged `scrcpy` is frequently older than 2.1; DROIDCOM detects this
and builds the latest release from source automatically on Linux at startup.

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

- **Connection** – Device detection, Wi-Fi ADB pairing/setup, auto-refreshing device list, and removal of offline devices

- **Device Info** – Hardware/software details, IMEI retrieval, and dialer-based diagnostics

- **App Manager** – Install/uninstall APKs, extract APKs, clear app data, force-stop, freeze/unfreeze, view permissions, app usage/battery stats, and list installed apps

- **File Manager** – Browse, push/pull, and transfer files to/from device; clean app caches; explore protected storage; export SQLite databases; calculate directory size and file checksums; view mount info and recent files

- **Screenshot** – Capture, preview, and save device screenshots

- **Logcat** – Real-time log viewing, filtering, colorized output, and saving logs to file

- **Device Control** – Reboot (normal/recovery/bootloader/EDL), toggle Wi-Fi/Bluetooth/mobile data/airplane mode/Do Not Disturb/flashlight/screen, simulate power button, set brightness and screen timeout, and blind device setup

- **Security** – Root detection, encryption and lock-screen status checks, screen lock brute-forcer (PIN/password/pattern) with lockout handling, security patch level and update checks, dangerous permission scanning (with export), certificate inspection (with export), boot integrity verification, AppOps inspection/modification, and keystore info

- **Backup** – Device backup (apps/data/media) and restore operations

- **Debugging** – Bug report generation, ANR trace viewing, crash dump inspection, system log viewer, and screen recording

- **Automation** – Run custom shell scripts, batch app management across multiple apps, combined logcat + screencap capture, and scheduled/recurring tasks

- **Advanced/Stress Tests** – Screen lock duplicator, battery drain test, app crash forcer (memory pressure, broadcast storm, activity stack, native signal), CPU/RAM/GPU stress tests, Dalvik cache stress test, and looped CPU/storage/memory/UI benchmarking

- **System Tools** – Battery, memory, CPU, network, thermal, and storage stats; running services; detailed device info; sensor status; power profile; location settings; Doze mode; SELinux status; time/date info; CPU governor info

- **Forensics** – Native Andriller extraction and lockscreen cracker dialog, plus launchers for ALEAPP, MVT (Mobile Verification Toolkit), and Autopsy (see [docs/system-deps.md](../docs/system-deps.md#droidcom) for optional install instructions)

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

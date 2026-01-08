# System Dependencies Reference

This document provides a comprehensive list of OS-level packages, drivers, and tooling required by each Outback CommandCore module.

> **Quick Links:** [BLACKSTORM](#blackstorm) | [HackAttack](#hackattack) | [PC-X](#pc-x) | [ARES-i](#ares-i) | [DROIDCOM](#droidcom) | [All Platforms](#all-platforms-summary)

---

## Overview

While most CommandCore modules only require Python packages (installed via `pip`), some modules depend on system-level tools for hardware access, network analysis, or device communication. This document details those requirements.

### Modules with No System Dependencies

The following modules work with Python dependencies only:

| Module | Notes |
|--------|-------|
| **CommandCore** | Launcher only requires Python packages |
| **Codex** | AI code analysis (Python only) |
| **NIGHTFIRE** | Monitoring tool (Python only) |
| **OMNISCRIBE** | Scripting suite (Python only) |
| **VANTAGE** | Analytics platform (Python only) |

---

## BLACKSTORM

**Purpose:** Forensic disk cloning and secure data erasure

### Required Packages

| Package | Purpose | Command |
|---------|---------|---------|
| `smartmontools` | SMART disk health monitoring | `smartctl` |
| `wipe` | Secure file/disk wiping | `wipe` |
| `dcfldd` | Forensic disk imaging (enhanced dd) | `dcfldd` |
| `hdparm` | Disk parameter control | `hdparm` |

### Optional Packages

| Package | Purpose | Command |
|---------|---------|---------|
| `badblocks` | Disk surface testing | `badblocks` |
| `fio` | Flexible I/O tester | `fio` |
| `pv` | Pipe viewer (progress monitoring) | `pv` |
| `libdbus-1-dev` | D-Bus development libraries | – |

### Installation

**Debian/Ubuntu:**
```bash
# Required
sudo apt-get install smartmontools wipe dcfldd hdparm

# Optional
sudo apt-get install e2fsprogs fio pv libdbus-1-dev libdbus-glib-1-dev
```

**Fedora/RHEL:**
```bash
# Required
sudo dnf install smartmontools wipe dcfldd hdparm

# Optional
sudo dnf install e2fsprogs fio pv dbus-devel dbus-glib-devel
```

**Arch Linux:**
```bash
# Required
sudo pacman -S smartmontools wipe dcfldd hdparm

# Optional
sudo pacman -S e2fsprogs fio pv dbus
```

### Permissions

- **Root access required** for secure wipe and forensic operations
- Add user to `disk` group for direct disk access: `sudo usermod -aG disk $USER`

---

## HackAttack

**Purpose:** Penetration testing and vulnerability assessment

### Required Packages

| Package | Purpose | Command |
|---------|---------|---------|
| `nmap` | Network scanner | `nmap` |
| `tshark` / `wireshark-cli` | Packet capture and analysis | `tshark` |

### Optional Packages

| Package | Purpose | Command |
|---------|---------|---------|
| `tcpdump` | Command-line packet analyzer | `tcpdump` |
| `netcat` | Network utility | `nc` / `netcat` |
| `hping3` | TCP/IP packet assembler | `hping3` |

### Installation

**Debian/Ubuntu:**
```bash
# Required
sudo apt-get install nmap tshark

# Optional
sudo apt-get install tcpdump netcat-openbsd hping3
```

**Fedora/RHEL:**
```bash
# Required
sudo dnf install nmap wireshark-cli

# Optional
sudo dnf install tcpdump nmap-ncat hping3
```

**Arch Linux:**
```bash
# Required
sudo pacman -S nmap wireshark-cli

# Optional
sudo pacman -S tcpdump openbsd-netcat hping
```

### Permissions

- **Root/sudo access required** for network packet capture
- Add user to `wireshark` group for non-root capture: `sudo usermod -aG wireshark $USER`
- Alternative: Set capabilities on dumpcap: `sudo setcap cap_net_raw,cap_net_admin+eip /usr/bin/dumpcap`

---

## PC-X

**Purpose:** System diagnostics and hardware monitoring

### Required Packages

| Package | Purpose | Command |
|---------|---------|---------|
| `smartmontools` | SMART disk monitoring | `smartctl` |
| `policykit-1` / `polkit` | Privilege escalation | `pkexec` |

### Optional Packages

| Package | Purpose | Command |
|---------|---------|---------|
| `lm-sensors` | Hardware sensor monitoring | `sensors` |
| `dmidecode` | DMI/SMBIOS table decoder | `dmidecode` |
| `lshw` | Hardware lister | `lshw` |
| `parted` | Disk partitioning | `parted` |
| `lsblk` | Block device listing | `lsblk` |

### Installation

**Debian/Ubuntu:**
```bash
# Required
sudo apt-get install smartmontools policykit-1

# Optional (recommended for full functionality)
sudo apt-get install lm-sensors dmidecode lshw parted util-linux
```

**Fedora/RHEL:**
```bash
# Required
sudo dnf install smartmontools polkit

# Optional
sudo dnf install lm_sensors dmidecode lshw parted util-linux
```

**Arch Linux:**
```bash
# Required
sudo pacman -S smartmontools polkit

# Optional
sudo pacman -S lm_sensors dmidecode lshw parted util-linux
```

### Permissions

- Application prompts for password via `pkexec` when elevated access needed
- Optional: Configure passwordless sudo for specific commands (see PC-X documentation)
- For SMART access without sudo, set capabilities:
  ```bash
  sudo setcap cap_sys_rawio,cap_dac_override,cap_sys_admin+ep /usr/sbin/smartctl
  ```

### Sensor Detection

After installing `lm-sensors`, run sensor detection:
```bash
sudo sensors-detect
```

---

## ARES-i

**Purpose:** iOS device reconnaissance and diagnostics

### Required Packages

| Package | Purpose | Command |
|---------|---------|---------|
| `libimobiledevice-utils` | iOS device communication | `idevice_id`, `ideviceinfo` |
| `ifuse` | iOS filesystem mounting | `ifuse` |
| `usbmuxd` | USB multiplexing daemon | `usbmuxd` |

### Installation

**Debian/Ubuntu:**
```bash
sudo apt-get install libimobiledevice-utils ifuse usbmuxd
```

**Fedora/RHEL:**
```bash
sudo dnf install libimobiledevice-utils ifuse usbmuxd
```

**Arch Linux:**
```bash
sudo pacman -S libimobiledevice ifuse usbmuxd
```

**macOS (Homebrew):**
```bash
brew install libimobiledevice ifuse
```

### Required CLI Tools

After installation, verify these commands are available:

| Command | Purpose |
|---------|---------|
| `idevice_id` | List connected iOS devices |
| `ideviceinfo` | Query device information |
| `idevicebackup2` | Device backup operations |
| `idevicediagnostics` | Diagnostic commands (restart, shutdown) |
| `ideviceenterrecovery` | Enter recovery mode |
| `ifuse` | Mount iOS filesystem |

### Permissions

- User must be in `plugdev` group: `sudo usermod -aG plugdev $USER`
- Filesystem mount permissions for `ifuse`
- The `usbmuxd` daemon should start automatically; if not: `sudo systemctl start usbmuxd`

### Troubleshooting

If device is not detected:
```bash
# Check usbmuxd is running
systemctl status usbmuxd

# Restart usbmuxd
sudo systemctl restart usbmuxd

# Check device connection
idevice_id -l
```

---

## DROIDCOM

**Purpose:** Android device management and debugging

### Required Packages

| Package | Purpose | Command |
|---------|---------|---------|
| `android-tools-adb` | Android Debug Bridge | `adb` |
| `android-tools-fastboot` | Bootloader communication | `fastboot` |

### Installation

**Debian/Ubuntu:**
```bash
sudo apt-get install android-tools-adb android-tools-fastboot
```

**Fedora/RHEL:**
```bash
sudo dnf install android-tools
```

**Arch Linux:**
```bash
sudo pacman -S android-tools
```

**macOS (Homebrew):**
```bash
brew install android-platform-tools
```

**Windows:**
1. Download [Android SDK Platform Tools](https://developer.android.com/studio/releases/platform-tools)
2. Extract to a folder (e.g., `C:\platform-tools`)
3. Add folder to system PATH

### Permissions

- User must be in `plugdev` group: `sudo usermod -aG plugdev $USER`
- Create udev rules for Android devices:
  ```bash
  # Create rules file
  sudo nano /etc/udev/rules.d/51-android.rules

  # Add this line (covers most Android devices)
  SUBSYSTEM=="usb", ATTR{idVendor}=="*", MODE="0666", GROUP="plugdev"

  # Reload rules
  sudo udevadm control --reload-rules
  sudo udevadm trigger
  ```

### Android Device Setup

1. Enable **Developer Options** on the device (tap Build Number 7 times)
2. Enable **USB Debugging** in Developer Options
3. Connect device via USB
4. Accept RSA key fingerprint when prompted

### Verification

```bash
# List connected devices
adb devices

# Should show device serial number with "device" status
```

---

## All Platforms Summary

### Quick Install Scripts

**Debian/Ubuntu – Install All System Dependencies:**
```bash
#!/bin/bash
# Install all CommandCore system dependencies

# BLACKSTORM dependencies
sudo apt-get install -y smartmontools wipe dcfldd hdparm

# HackAttack dependencies
sudo apt-get install -y nmap tshark

# PC-X dependencies
sudo apt-get install -y smartmontools policykit-1 lm-sensors dmidecode lshw

# ARES-i dependencies
sudo apt-get install -y libimobiledevice-utils ifuse usbmuxd

# DROIDCOM dependencies
sudo apt-get install -y android-tools-adb android-tools-fastboot

# Add user to required groups
sudo usermod -aG plugdev,wireshark,disk $USER

echo "System dependencies installed. Please log out and back in for group changes to take effect."
```

**Fedora/RHEL – Install All System Dependencies:**
```bash
#!/bin/bash
# Install all CommandCore system dependencies

# BLACKSTORM dependencies
sudo dnf install -y smartmontools wipe dcfldd hdparm

# HackAttack dependencies
sudo dnf install -y nmap wireshark-cli

# PC-X dependencies
sudo dnf install -y smartmontools polkit lm_sensors dmidecode lshw

# ARES-i dependencies
sudo dnf install -y libimobiledevice-utils ifuse usbmuxd

# DROIDCOM dependencies
sudo dnf install -y android-tools

# Add user to required groups
sudo usermod -aG plugdev,wireshark,disk $USER

echo "System dependencies installed. Please log out and back in for group changes to take effect."
```

### Package Summary by Distribution

| Package | Debian/Ubuntu | Fedora/RHEL | Arch Linux | Used By |
|---------|---------------|-------------|------------|---------|
| smartmontools | `smartmontools` | `smartmontools` | `smartmontools` | BLACKSTORM, PC-X |
| wipe | `wipe` | `wipe` | `wipe` | BLACKSTORM |
| dcfldd | `dcfldd` | `dcfldd` | `dcfldd` | BLACKSTORM |
| hdparm | `hdparm` | `hdparm` | `hdparm` | BLACKSTORM |
| nmap | `nmap` | `nmap` | `nmap` | HackAttack |
| tshark | `tshark` | `wireshark-cli` | `wireshark-cli` | HackAttack |
| polkit | `policykit-1` | `polkit` | `polkit` | PC-X |
| lm-sensors | `lm-sensors` | `lm_sensors` | `lm_sensors` | PC-X |
| dmidecode | `dmidecode` | `dmidecode` | `dmidecode` | PC-X |
| lshw | `lshw` | `lshw` | `lshw` | PC-X |
| libimobiledevice | `libimobiledevice-utils` | `libimobiledevice-utils` | `libimobiledevice` | ARES-i |
| ifuse | `ifuse` | `ifuse` | `ifuse` | ARES-i |
| usbmuxd | `usbmuxd` | `usbmuxd` | `usbmuxd` | ARES-i |
| adb | `android-tools-adb` | `android-tools` | `android-tools` | DROIDCOM |
| fastboot | `android-tools-fastboot` | `android-tools` | `android-tools` | DROIDCOM |

### User Groups

Add your user to these groups for proper access:

| Group | Purpose | Command |
|-------|---------|---------|
| `plugdev` | USB device access | `sudo usermod -aG plugdev $USER` |
| `wireshark` | Packet capture without root | `sudo usermod -aG wireshark $USER` |
| `disk` | Direct disk access | `sudo usermod -aG disk $USER` |

**Note:** Log out and back in after adding groups for changes to take effect.

---

## Verification

After installing dependencies, verify tools are available:

```bash
# BLACKSTORM tools
which smartctl wipe dcfldd hdparm

# HackAttack tools
which nmap tshark

# PC-X tools
which smartctl pkexec sensors dmidecode lshw

# ARES-i tools
which idevice_id ideviceinfo ifuse

# DROIDCOM tools
which adb fastboot
```

---

## Related Documentation

- [Main README](../README.md) – Installation overview
- [BLACKSTORM README](../BLACKSTORM/README.md) – Forensic tools documentation
- [HackAttack README](../HackAttack/README.md) – Penetration testing documentation
- [PC-X README](../PC-X/README.md) – System diagnostics documentation
- [ARES-i README](../ARES-i/README.md) – iOS tools documentation
- [DROIDCOM README](../DROIDCOM/README.md) – Android tools documentation

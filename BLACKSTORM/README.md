**BLACKSTORM** is a full-suite forensic and secure wipe utility built for safe data destruction, forensic-grade extraction, and system recovery workflows. Developed as part of the **Outback CommandCore** arsenal, BLACKSTORM delivers uncompromising power in hostile environments, enterprise labs, and high-security tactical deployments.

## Key Features

### **Secure Data Erasure**

* Implements military-grade multi-pass wipe algorithms (e.g., DoD 5220.22-M, NIST 800-88, Schneier, Gutmann)
* Optional cryptographic wipe using key destruction for encrypted drives (BitLocker, LUKS, FileVault)

### **Forensic Tools**

* Full forensic-grade disk cloning with hash verification (MD5/SHA256/SHA512)
* Hidden partition detection and cold storage scan for low-level artifacts (bootkits, bootloaders, stealth malware)

### **Bulk Operations**

* Simultaneous wipe and recovery management for dozens of devices
* Queue system with progress tracking and error handling
* Custom device groups for predefined parallel workflows

### **Audit Trail**

* Tamper-evident logs with digital signing and checksum chaining
* Chain-of-custody metadata (operator ID, timestamp, device serial, algorithm used)
* Optional GPS and location tagging via mobile tethering

### **Complete Coverage**

* Supports wiping of:

  * Internal HDD/SSD
  * USB drives and SD cards
  * Volatile memory (RAM dump and flush)
  * eMMC/UFS modules
  * UEFI/NVRAM and bootloader areas (advanced mode)

### **Predefined Profiles**

* Deploy secure wipe presets by compliance framework:

  * DoD 5220.22-M
  * NIST 800-88 Rev. 1
  * GDPR Article 17 (“Right to be Forgotten”)
  * HIPAA/HITECH Secure Disposal
  * ISO/IEC 27040
* Save and export custom profiles


## Advanced Features

### **Live OS Wiping (Hot Wipe Mode)**

* Securely destroy mounted volumes without requiring system reboot or unmount
* Useful for field operations, emergency wipes, or covert sanitization

### **Device Anti-Recovery Engine**

* Post-wipe entropy analysis and slack space cleanup
* Overwrites file system metadata, journaling regions, and shadow tables
* Compatible with forensic recovery software countermeasures

### **Cryptographic Degauss & Secure Key Purge**

* Targeted destruction of encryption keys in TPM/NVRAM and keystore environments
* Secure erasure of LUKS headers, Keychain, BitLocker protectors, and vaults

### **Stealth Wipe Mode**

* Covert wipe operation under obfuscated shell environment
* GUI mimicry or no-output terminal modes for plausible deniability

### **OS-Aware Selective Destruction**

* Secure deletion of individual files, directories, browser data, SQLite databases, Slack caches, logs, and staged backups
* Slack space, journal, and metadata destruction

### **Device KillSwitch**

* Optional USB-based failsafe trigger for auto-wipe if unplugged
* Configurable destruct sequence: TPM wipe, MBR overwrite, drive corruption, system disablement

### **Remote Wipe Interface**

* Controlled via CommandCore network console or satellite CLI
* Assign wipe tasks to distributed agents and receive post-wipe forensic reports

### **Thermal Burn Verification (Hardware-Linked)**

* Optional thermal stress testing after flash wipe to degrade NAND domains
* Helps thwart forensic voltage probing or NAND remanence attacks


## Requirements

### Python Version
- Python 3.10 or higher

### Python Dependencies
Install via pip:
```bash
pip install -r requirements.txt
```

**Core dependencies:**
- `PySide6>=6.4.0` – Qt6 GUI framework
- `PySide6-Addons>=6.4.0` – Additional Qt6 components
- `PySide6-Essentials>=6.4.0` – Essential Qt6 modules
- `psutil>=5.9.0` – System monitoring

**Security & cryptography:**
- `cryptography>=38.0.0` – Cryptographic operations
- `pycryptodome>=3.15.0` – Low-level crypto primitives

**Data processing:**
- `numpy>=1.21.0,<2.0.0` – Numerical operations
- `pandas>=1.3.0,<3.0.0` – Data analysis

**Hardware & low-level:**
- `pyserial>=3.5` – Serial port communication
- `pyusb>=1.2.1` – USB device access

**Utilities:**
- `python-dateutil>=2.8.2` – Date parsing
- `pytz>=2021.3` – Timezone handling

**Optional (advanced features):**
- `scapy>=2.4.5` – Network forensic tools
- `matplotlib>=3.4.3,<4.0.0` – Visualization
- `scipy>=1.7.0,<2.0.0` – Scientific computing

### Supported Platforms
- Linux (primary – full functionality)
- Windows (limited functionality)

### OS-Level Dependencies (Linux)

**Debian/Ubuntu:**
```bash
sudo apt-get install smartmontools wipe dcfldd hdparm
```

**Fedora/RHEL:**
```bash
sudo dnf install smartmontools wipe dcfldd hdparm
```

Required system tools:
- `smartmontools` – SMART data access and disk health
- `wipe` – Secure file/disk wiping utility
- `dcfldd` – Forensic disk imaging (enhanced dd)
- `hdparm` – Disk parameter control

### Permissions
- **Root/sudo access required** for secure wipe and forensic operations
- USB device access (user in `plugdev` group on Linux)
- Direct disk access permissions

## Getting Started

1. Clone the repository and navigate to the BLACKSTORM directory
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install OS-level dependencies (see above)
4. Ensure proper permissions for disk access
5. Launch the application with appropriate privileges

## Usage

### Entry Point
```bash
# Run from repository root (may require sudo for full functionality)
python BLACKSTORM/blackstorm_launcher.py

# Or with elevated privileges
sudo python BLACKSTORM/blackstorm_launcher.py
```

### Module Path
`BLACKSTORM.blackstorm_launcher` (main launcher: `blackstorm_launcher.py`)

### Application Tabs
- **Dashboard** – System overview and quick actions
- **Wipe Operations** – Secure data erasure with compliance profiles
- **Forensic Tools** – Disk cloning, hash verification, artifact detection
- **Device Management** – Device enumeration and selection
- **Bulk Operations** – Multi-device parallel workflows
- **Security & Compliance** – Audit trails and compliance reporting
- **Settings** – Application configuration
- **Advanced** – Expert-level operations

### Examples
```bash
# Launch BLACKSTORM GUI
sudo python BLACKSTORM/blackstorm_launcher.py

# Configuration is stored in:
# ~/.config/blackstorm/settings.json

# Logs are stored in:
# ~/.config/blackstorm/logs/blackstorm.log
```

**Performing a secure wipe:**
1. Select target device in Device Management
2. Navigate to Wipe Operations tab
3. Choose compliance profile (DoD, NIST, GDPR, etc.)
4. Configure wipe parameters
5. Execute and monitor progress

**Forensic imaging:**
1. Select source device
2. Navigate to Forensic Tools tab
3. Configure hash algorithm (MD5/SHA256/SHA512)
4. Specify destination path
5. Execute cloning with verification

## License

Proprietary – Outback Electronics

# PC-X

PC-X is a powerful cross-platform tactical systems toolkit designed for advanced diagnostics, system manipulation, and penetration testing on Windows, Linux, and macOS desktops and laptops.

## Key Features

- **System Diagnostics**: Comprehensive hardware and software analysis tools
- **Privileged Access**: Deep system internals exploration with elevated privileges
- **Security Testing**: Custom exploit and payload deployment capabilities
- **Real-time Monitoring**: Live tracking of system resources and security status
- **Extensible Design**: Modular architecture supporting plugin extensions
- **Secure Operations**: Protected execution environment with detailed audit trails

## Requirements

### Python Version
- Python 3.10 or higher

### Python Dependencies
Install via pip:
```bash
pip install -r requirements.txt
```
- `psutil>=5.9.0` – System and process monitoring library

### Built-in Dependencies
- `tkinter` – Standard Python GUI library (included with Python)

### Supported Platforms
- Linux (primary target)
- macOS (partial support)
- Windows (partial support)

### OS-Level Dependencies (Linux)
For full hardware diagnostics functionality:

**Debian/Ubuntu:**
```bash
sudo apt-get install smartmontools policykit-1
```

**Fedora/RHEL:**
```bash
sudo dnf install smartmontools polkit
```

Required tools:
- `smartctl` – SMART disk monitoring
- `pkexec` – PolicyKit for privilege escalation

### Permissions
- Elevated privileges required for hardware access (SMART data, low-level diagnostics)
- The application will prompt for password via `pkexec` when needed
- Optionally configure passwordless sudo for specific commands

## Getting Started

1. Clone the repository and navigate to the PC-X directory
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install OS-level dependencies (see above)
4. Launch the application

## Usage

### Entry Point
```bash
# Run from repository root
python PC-X/pc_tools_linux.py

# Or directly
cd PC-X && python pc_tools_linux.py
```

### Module Path
`PC-X.pc_tools_linux` (main module: `pc_tools_linux.py`)

### Examples
```bash
# Launch the PC-X GUI
python PC-X/pc_tools_linux.py
```

**First-time setup:**
- On first run, you may be prompted to configure passwordless sudo access for hardware monitoring tools
- This allows seamless access to SMART data and other low-level diagnostics

**Available diagnostics:**
- CPU and memory monitoring
- Disk health (SMART data)
- Network interface information
- Process management
- System resource tracking

## License

Proprietary – Outback Electronics

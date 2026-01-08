# Outback CommandCore

A comprehensive software suite by Outback Electronics featuring system management, security testing, device control, and monitoring tools—all accessible from a central launcher.

## Overview

Outback CommandCore is a collection of specialized applications unified under a single launcher interface. The **CommandCore Launcher** automatically discovers installed modules, manages their dependencies, and provides one-click launching with proper privilege escalation when needed.

## Directory Layout

```
Outback-CommandCore/
├── CommandCore/          # Central launcher (install first)
│   ├── app/              # Main application code
│   │   ├── main.py       # Entry point
│   │   ├── config.py     # Configuration manager
│   │   └── dependency_installer.py  # Auto-installs all module deps
│   ├── tabs/             # Dashboard and Application Manager
│   ├── ui/               # UI components (splash screen, themes)
│   └── requirements.txt  # Launcher dependencies
│
├── ARES-i/               # AI-powered research and analysis tool
├── BLACKSTORM/           # Forensic and secure wipe utility
├── Codex/                # AI-powered code generation and analysis
├── DROIDCOM/             # Android device management toolkit
├── HackAttack/           # Penetration testing framework
├── NIGHTFIRE/            # System monitor and controller
├── OMNISCRIBE/           # Transcription and analysis tool
├── PC-X/                 # PC tools for Linux system management
├── VANTAGE/              # System monitoring and performance analysis
│
├── docs/                 # Documentation
│   └── system-deps.md    # OS-level dependencies reference
├── icons/                # Application icons
├── STYLE_GUIDE.md        # Coding and UI/UX standards
└── README.md             # This file
```

## Module Descriptions

| Module | Description | Entry Point |
|--------|-------------|-------------|
| **CommandCore** | Central launcher and application manager | `CommandCore/app/main.py` |
| **ARES-i** | AI-powered research and analysis tool | `ARES-i/ares-i.py` |
| **BLACKSTORM** | Forensic disk cloning and secure data erasure | `BLACKSTORM/app/main.py` |
| **Codex** | AI-powered code generation and analysis | `Codex/app/gui.py` |
| **DROIDCOM** | Android device management and debugging | `DROIDCOM/main.py` |
| **HackAttack** | Penetration testing and vulnerability assessment | `HackAttack/launch.py` |
| **NIGHTFIRE** | System monitor and controller | `NIGHTFIRE/nightfire.py` |
| **OMNISCRIBE** | Transcription and analysis tool | `OMNISCRIBE/omniscribe.py` |
| **PC-X** | PC tools for Linux system management | `PC-X/pc_tools_linux.py` |
| **VANTAGE** | Advanced system monitoring and performance analysis | `VANTAGE/launch_vantage.py` |

## Installation

### Prerequisites

- **Python 3.10 or higher**
- **pip** (Python package manager)
- **Git** (for cloning the repository)

### Step 1: Clone the Repository

```bash
git clone https://github.com/cowboydaniel/Outback-CommandCore.git
cd Outback-CommandCore
```

### Step 2: Install CommandCore (Recommended)

CommandCore includes an automatic dependency installer that discovers and installs all dependencies from every module's `requirements.txt`:

```bash
# Install CommandCore and all module dependencies at once
pip install -r CommandCore/requirements.txt
pip install -e .

# Launch CommandCore (auto-installs missing deps on first run)
python -m CommandCore
```

On first launch, CommandCore will:
1. Scan all module directories for `requirements.txt` files
2. Identify missing Python packages
3. Prompt to install them automatically

### Step 3: Install Individual Modules (Alternative)

If you prefer to install modules individually:

```bash
# Install a specific module's dependencies
pip install -r HackAttack/requirements.txt
pip install -r VANTAGE/requirements.txt
# ... etc.
```

### Installation Order

For manual installation, follow this recommended order:

1. **CommandCore** (first) – The launcher and dependency manager
2. **Shared dependencies** – PySide6 is used by most modules
3. **Individual modules** – Any order after CommandCore

## Shared Dependencies

Most modules share these common dependencies:

| Package | Version | Used By |
|---------|---------|---------|
| `PySide6` | >=6.5.0 | CommandCore, VANTAGE, HackAttack, BLACKSTORM, NIGHTFIRE, OMNISCRIBE, DROIDCOM, Codex, ARES-i |
| `GitPython` | >=3.1.0 | CommandCore |
| `psutil` | >=5.9.0 | CommandCore, BLACKSTORM, PC-X |
| `requests` | >=2.28.0 | HackAttack, ARES-i |

Installing CommandCore first ensures these shared dependencies are available for all modules.

## How CommandCore Discovers Modules

CommandCore automatically discovers modules using these conventions:

### Module Discovery

The Application Manager tab (`CommandCore/tabs/application_manager_tab.py`) maintains a registry of known modules with their:
- **id**: Unique identifier (e.g., `hackattack`)
- **name**: Display name (e.g., `HackAttack`)
- **path**: Entry point script path
- **process_name**: Process identifier for status tracking

### Directory Convention

Each module must be a top-level directory containing:
```
ModuleName/
├── requirements.txt      # Python dependencies (REQUIRED for auto-install)
├── <entry_point>.py      # Main script referenced in ApplicationManagerTab
└── README.md             # Module documentation
```

### Adding a New Module

To add a new module to CommandCore:

1. Create a directory at the repository root
2. Add a `requirements.txt` with dependencies
3. Create an entry point script (e.g., `launch.py` or `main.py`)
4. Register the module in `CommandCore/tabs/application_manager_tab.py`:
   ```python
   {
       "id": "mymodule",
       "name": "My Module",
       "description": "Description of the module.",
       "path": os.path.join(base_dir, "MyModule/launch.py"),
       "version": None,
       "status": "stopped",
       "process_name": "mymodule_process"
   }
   ```

## Configuration

### CommandCore Settings

Settings are stored in `CommandCore/config/settings.json`:

```json
{
    "ui": {
        "theme": "dark",
        "font_family": "Segoe UI",
        "font_size": 10,
        "window_width": 1024,
        "window_height": 768,
        "animation_enabled": true,
        "animation_duration": 200
    }
}
```

### Module-Specific Configuration

Each module may have its own configuration:

| Module | Config Location |
|--------|-----------------|
| BLACKSTORM | `~/.config/blackstorm/settings.json` |
| VANTAGE | `VANTAGE/app/config.py` |
| HackAttack | `HackAttack/src/config.py` (uses `.env` files) |

### Environment Variables

Some modules support environment variables via `.env` files:

```bash
# HackAttack/.env example
DEBUG=true
LOG_LEVEL=INFO
```

The `python-dotenv` package (included in HackAttack requirements) loads these automatically.

## Usage

### Running CommandCore Launcher

```bash
# Standard launch (with dependency check)
python -m CommandCore

# Skip dependency check for faster startup
python -m CommandCore --skip-deps

# Or run directly
python CommandCore/app/main.py
```

### Running Individual Modules

Each module can be run standalone:

```bash
# HackAttack (may require sudo for network capture)
sudo python HackAttack/launch.py

# VANTAGE
python VANTAGE/launch_vantage.py

# BLACKSTORM (requires sudo for disk operations)
sudo python BLACKSTORM/app/main.py

# PC-X
python PC-X/pc_tools_linux.py
```

### Dependency Management CLI

CommandCore includes a CLI tool for dependency management:

```bash
# Check for missing dependencies
python -m CommandCore.app.dependency_installer --check-only

# List all discovered dependencies
python -m CommandCore.app.dependency_installer --list

# Install missing dependencies (with output)
python -m CommandCore.app.dependency_installer

# Quiet mode (errors only)
python -m CommandCore.app.dependency_installer -q
```

## Logs

Application logs are stored in module-specific locations:

| Module | Log Location |
|--------|--------------|
| CommandCore | `CommandCore/logs/` |
| BLACKSTORM | `~/.config/blackstorm/logs/blackstorm.log` |
| Launched apps | `<module>/logs/<app_id>_stdout.log` and `<app_id>_stderr.log` |

## OS-Level Dependencies

Some modules require system packages for hardware access, network analysis, or device communication.

> **See [docs/system-deps.md](docs/system-deps.md) for comprehensive system dependency documentation**, including per-module requirements, installation scripts, and troubleshooting guides.

### Quick Reference

| Module | System Packages Required |
|--------|-------------------------|
| **BLACKSTORM** | smartmontools, wipe, dcfldd, hdparm |
| **HackAttack** | nmap, tshark/wireshark-cli |
| **PC-X** | smartmontools, polkit, lm-sensors, dmidecode |
| **ARES-i** | libimobiledevice-utils, ifuse, usbmuxd |
| **DROIDCOM** | android-tools-adb, android-tools-fastboot |

### Debian/Ubuntu Quick Install

```bash
# Install all system dependencies
sudo apt-get install \
    smartmontools wipe dcfldd hdparm \
    nmap tshark \
    policykit-1 lm-sensors dmidecode lshw \
    libimobiledevice-utils ifuse usbmuxd \
    android-tools-adb android-tools-fastboot

# Add user to required groups
sudo usermod -aG plugdev,wireshark,disk $USER
```

### Fedora/RHEL Quick Install

```bash
# Install all system dependencies
sudo dnf install \
    smartmontools wipe dcfldd hdparm \
    nmap wireshark-cli \
    polkit lm_sensors dmidecode lshw \
    libimobiledevice-utils ifuse usbmuxd \
    android-tools

# Add user to required groups
sudo usermod -aG plugdev,wireshark,disk $USER
```

> **Note:** Log out and back in after adding groups for changes to take effect.

## Supported Platforms

- **Linux** (primary) – Full functionality
- **Windows** – Limited functionality (some modules may not work)

## Development

### Project Structure

See `STYLE_GUIDE.md` for coding conventions and UI/UX standards.

### Running Tests

```bash
# Run tests for a specific module
pytest VANTAGE/tests/
pytest BLACKSTORM/tests/
```

## License

Proprietary – Outback Electronics

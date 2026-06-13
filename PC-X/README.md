# PC-X

PC-X is a Linux system management toolkit with a dark-themed GUI. It provides a single window with sidebar navigation covering 20 system management areas.

## Features

| Section | Tools |
|---------|-------|
| **Device Info** | System overview, Hardware (CPU/RAM/GPU/battery), Storage, Network interfaces |
| **Tools** | Package manager, Process manager, Benchmarks, Disk usage, Utilities, Diagnostics |
| **Management** | Services (systemd), Firewall (UFW), Users & groups, Scheduler (cron), System config, Logs, Startup apps, Environment variables, SSH keys, Kernel modules |

## Requirements

**Python:** 3.10 or higher

**Python dependencies:**
```bash
pip install -r PC-X/requirements.txt
```
- `psutil>=5.9.0`
- `PySide6>=6.5.0`

**OS-level tools (Debian/Ubuntu):**
```bash
sudo apt-get install smartmontools lshw pciutils policykit-1 ufw
```

**OS-level tools (Fedora/RHEL):**
```bash
sudo dnf install smartmontools lshw pciutils polkit ufw
```

> See [docs/system-deps.md](../docs/system-deps.md#pc-x) for the full dependency list.

## Running

```bash
# From the repository root
python PC-X/app/main.py

# Or via the launcher wrapper
python PC-X/pc_tools_linux.py
```

## Permissions

Many features (SMART diagnostics, hardware info, service control) require elevated privileges. PC-X handles this without needing a terminal password prompt:

1. **Passwordless sudo** — if already configured for the relevant commands, used automatically with `sudo -n`
2. **PolicyKit (pkexec)** — if sudo isn't configured, a single desktop authentication prompt appears on first privileged action; that session is reused until PC-X closes

To configure passwordless sudo, use the optional setup in Settings or follow the instructions in the docs.

## Platform

Linux only. Tested on Debian/Ubuntu and Fedora.

## License

Proprietary – Outback Electronics

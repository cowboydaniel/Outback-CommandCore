# Hardware Tools Integration Guide

This document outlines the hardware-related tools integrated into the Hack Attack platform for security testing and analysis of embedded systems, mobile devices, and hardware components.

## Table of Contents

1. [Hardware Communication & Debugging](#hardware-communication--debugging)
2. [Firmware & Bootloader Analysis](#firmware--bootloader-analysis)
3. [Mobile Device Tools](#mobile-device-tools)
4. [IoT & Embedded Reverse Engineering](#iot--embedded-reverse-engineering)
5. [Hardware Bus & Protocol Analysis](#hardware-bus--protocol-analysis)
6. [System Requirements](#system-requirements)

## Hardware Communication & Debugging

### Key Tools
- **PySerial**: Python serial port access for UART communication
- **PyUSB**: USB device communication and control
- **PyVISA**: Hardware abstraction layer for test and measurement equipment
- **PyLibFTDI**: Python interface to FTDI USB devices

### Usage Examples

```python
import serial

# Basic serial communication
with serial.Serial('/dev/ttyUSB0', 115200, timeout=1) as ser:
    ser.write(b'AT+COMMAND\r\n')
    response = ser.read_all()
    print(response.decode())
```

## Firmware & Bootloader Analysis

### Key Tools
- **CHIPSEC**: Framework for analyzing platform security
- **UEFI Firmware Parser**: UEFI firmware image parser and analyzer
- **python-magic**: File type detection using libmagic

### Usage Examples

```python
import chipsec.chipset
from chipsec.hal import mmio

def check_spi_protection():
    cs = chipsec.chipset.cs()
    mmio = mmio.MMIO(cs)
    # Check SPI flash protection
    if not mmio.is_MMIO_enabled():
        print("SPI flash protection is not enabled")
```

## Mobile Device Tools

### Key Tools
- **ADB Shell**: Android Debug Bridge for device communication
- **Frida**: Dynamic instrumentation toolkit
- **Libimobiledevice**: iOS device communication

### Usage Examples

```python
import frida

def on_message(message, data):
    print(f"[Message] {message}")

device = frida.get_usb_device()
pid = device.spawn(["com.example.app"])
session = device.attach(pid)

with open("script.js") as f:
    script = session.create_script(f.read())

script.on("message", on_message)
script.load()
device.resume(pid)
```

## IoT & Embedded Reverse Engineering

### Key Tools
- **Radare2**: Reverse engineering framework
- **Ghidra**: Software reverse engineering suite
- **Angr**: Binary analysis platform

### Usage Examples

```python
import angr

# Load a binary
proj = angr.Project('./firmware.bin', load_options={'main_opts': {'base_addr': 0x1000}})

# Perform symbolic execution
state = proj.factory.entry_state()
simgr = proj.factory.simulation_manager(state)
simgr.explore(find=0x1234, avoid=0x5678)
```

## Hardware Bus & Protocol Analysis

### Key Tools
- **i2c-tools**: I2C bus debugging
- **spidev**: SPI interface access
- **python-can**: CAN bus interface

### Usage Examples

```python
import smbus2

# Initialize I2C bus
bus = smbus2.SMBus(1)

# Read from I2C device
data = bus.read_i2c_block_data(0x48, 0, 4)
print(f"Sensor data: {data}")
```

## System Requirements

### Hardware Requirements
- **Processor**: x86_64 or ARM64 (recommended: 4+ cores)
- **RAM**: 8GB minimum, 16GB+ recommended for complex analysis
- **Storage**: 50GB+ free space (for firmware storage, virtual machines, and analysis artifacts)
- **USB Ports**: Multiple USB 2.0/3.0/3.1 ports (recommended: USB 3.0+ for better performance)
- **Specialized Hardware** (optional but recommended):
  - USB-to-TTL/UART adapter (e.g., FTDI, CP2102, CH340)
  - Logic analyzer (e.g., Saleae, FX2LAFW-compatible)
  - JTAG/SWD debugger (e.g., J-Link, ST-Link, CMSIS-DAP)
  - Bus Pirate or similar tool

### Software Requirements
- **Operating System**: Linux (recommended: Ubuntu 20.04/22.04 LTS or Arch Linux)
- **Kernel**: 5.4+ (recommended: 5.10+ for latest hardware support)
- **Python**: 3.8+ with venv or conda
- **QEMU**: For firmware emulation and testing
- **Docker**: For containerized analysis environments (optional)

### Installation

#### 1. Install System Dependencies

Run the following command to install all required system dependencies:

```bash
# Make the script executable
chmod +x scripts/install_system_deps.sh

# Run as root (will prompt for password)
sudo ./scripts/install_system_deps.sh
```

This script will:
- Install all required system packages
- Configure udev rules for hardware tools
- Set up user permissions and groups
- Install OpenOCD, Sigrok, and other essential tools

#### 2. Create a Python Virtual Environment

```bash
# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

#### 3. Verify Installation

```bash
# Check if essential tools are installed
which openocd sigrok-cli adb fastboot qemu-system-arm

# Verify Python packages
python -c "import frida; print('Frida version:', frida.__version__)"
```

### Post-Installation

1. **Log out and back in** to apply group membership changes
2. **Connect your hardware** and verify it's detected:
   ```bash
   lsusb
   dmesg | tail -n 50
   ```
3. **Test basic functionality** with your hardware tools
4. **Consider adding** your user to additional groups if needed:
   ```bash
   sudo usermod -a -G tty $USER
   sudo usermod -a -G disk $USER
   ```

## Troubleshooting

1. **Permission Issues**:
   - Add your user to the `dialout`, `plugdev`, and `usb` groups
   - Create udev rules for persistent device permissions

2. **Missing Dependencies**:
   - Install system packages: `build-essential`, `libusb-1.0-0-dev`, `libftdi1-dev`
   - Use virtual environments to manage Python dependencies

3. **Hardware Detection**:
   - Check `lsusb` and `dmesg` for device detection
   - Verify kernel modules are loaded for your hardware

## Security Considerations

- Always work on isolated test networks
- Use write-blockers when analyzing storage media
- Document all changes made during analysis
- Follow responsible disclosure guidelines for vulnerabilities found

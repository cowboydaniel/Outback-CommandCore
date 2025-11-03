#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

error_exit() {
    echo -e "${RED}Error: $1${NC}" >&2
    exit 1
}

# Detect Linux distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    # Map Linux Mint to Ubuntu for package management
    if [ "$ID" = "linuxmint" ]; then
        echo -e "${YELLOW}Detected Linux Mint, using Ubuntu package repositories${NC}"
        OS="ubuntu"
    fi
    VERSION=$VERSION_ID
else
    echo -e "${RED}Could not detect Linux distribution. Only Debian/Ubuntu and Arch Linux are supported.${NC}"
    exit 1
fi

# Common dependencies
COMMON_DEPS=(
    # General
    build-essential
    git
    wget
    curl
    unzip
    p7zip-full
    p7zip-rar
    squashfs-tools
    
    # USB
    libusb-1.0-0-dev
    libusb-0.1-4
    usbutils
    
    # Network
    tcpdump
    nmap
    net-tools
    
    # Filesystem
    e2fsprogs
    mtd-utils
    ubi-utils
    
    # Debugging
    gdb
    gdb-multiarch
    strace
    ltrace
    
    # Other
    xxd
    file
    binwalk
    minicom
    i2c-tools
    python3-ldap
    libldap2-dev
    libsasl2-dev
    libftdi1
    libftdi1-dev
    
    # Virtualization
    qemu-system
    qemu-utils
    libvirt-daemon-system
    libvirt-clients
    bridge-utils
    virt-manager
)

# Update package lists and install system dependencies
echo -e "${YELLOW}Updating package lists and installing system dependencies...${NC}"

# Function to install packages with error handling
install_packages() {
    local packages=("$@")
    local pkg
    local failed_pkgs=()
    
    for pkg in "${packages[@]}"; do
        echo -e "${YELLOW}Attempting to install: $pkg${NC}"
        if [[ $OS == "debian" || $OS == "ubuntu" ]]; then
            apt-get install -y "$pkg" || {
                echo -e "${YELLOW}Warning: Failed to install $pkg${NC}"
                failed_pkgs+=("$pkg")
                continue
            }
        elif [[ $OS == "arch" || $OS == "manjaro" ]]; then
            pacman -S --noconfirm "$pkg" || {
                echo -e "${YELLOW}Warning: Failed to install $pkg${NC}"
                failed_pkgs+=("$pkg")
                continue
            }
        fi
    done
    
    if [ ${#failed_pkgs[@]} -gt 0 ]; then
        echo -e "${YELLOW}Warning: The following packages failed to install:${NC}"
        printf ' - %s\n' "${failed_pkgs[@]}"
        echo -e "${YELLOW}Some features might not work as expected.${NC}"
    fi
}

# Update package lists
if [[ $OS == "debian" || $OS == "ubuntu" ]]; then
    apt-get update || echo -e "${YELLOW}Warning: Failed to update package lists, continuing anyway...${NC}
    # Install common dependencies
    install_packages "${COMMON_DEPS[@]}"
    
    # Install additional packages
    echo -e "\n${YELLOW}Installing Android tools...${NC}"
    apt-get install -y adb fastboot android-tools-adb android-tools-fastboot || \
        echo -e "${YELLOW}Warning: Failed to install Android tools${NC}"
    
    echo -e "\n${YELLOW}Installing Heimdall...${NC}"
    add-apt-repository -y ppa:team-gb/heimdall
    apt-get update
    apt-get install -y heimdall-flash || \
        echo -e "${YELLOW}Warning: Failed to install Heimdall${NC}"
    
    echo -e "\n${YELLOW}Installing iOS tools...${NC}"
    apt-get install -y libimobiledevice6 libimobiledevice-utils ideviceinstaller ifuse || \
        echo -e "${YELLOW}Warning: Failed to install iOS tools${NC}"
    
    # Other packages
    ADDITIONAL_PKGS=(
        # Hardware tools
        openocd
        sigrok
        sigrok-cli
        sigrok-firmware-fx2lafw
        # Forensics
        sleuthkit
        autopsy
        # Other
        qemu-system-arm
        qemu-system-mips
    )
    install_packages "${ADDITIONAL_PKGS[@]}"
    
elif [[ $OS == "arch" || $OS == "manjaro" ]]; then
    pacman -Syu --noconfirm || echo -e "${YELLOW}Warning: Failed to update package lists, continuing anyway...${NC}
    # Install common dependencies
    install_packages "${COMMON_DEPS[@]}"
    
    # Install additional packages
    ADDITIONAL_PKGS=(
        # Hardware tools
        openocd
        sigrok
        # Android tools
        android-tools
        heimdall
        # iOS tools
        libimobiledevice
        ifuse
        # Forensics
        sleuthkit
        autopsy
        # Other
        qemu-arch-extra
    )
    install_packages "${ADDITIONAL_PKGS[@]}"
else
    echo -e "${RED}Unsupported distribution: $OS${NC}"
    exit 1
fi

# Install Python packages from requirements.txt
echo -e "\n${YELLOW}Installing Python packages...${NC}\nNote: Using --no-deps to avoid conflicts with system packages"
python3 -m pip install -r ../requirements.txt --no-deps --break-system-packages || error_exit "Failed to install requirements.txt packages"

# Install packages that need special handling
echo -e "\n${YELLOW}Installing packages with special requirements...${NC}"

# Install pyusb
echo -e "${YELLOW}Installing pyusb...${NC}"
python3 -m pip install --user --no-deps pyusb --break-system-packages || echo -e "${RED}Warning: Failed to install pyusb${NC}"

# Install uefi-firmware-parser
echo -e "\n${YELLOW}Installing uefi-firmware-parser...${NC}"
python3 -m pip install --user --no-deps git+https://github.com/theopolis/uefi-firmware-parser.git --break-system-packages || echo -e "${RED}Warning: Failed to install uefi-firmware-parser${NC}"

# Install peepdf
echo -e "\n${YELLOW}Installing peepdf...${NC}"
python3 -m pip install --user --no-deps git+https://github.com/jesparza/peepdf.git --break-system-packages || echo -e "${RED}Warning: Failed to install peepdf${NC}"

# Install w3af-api-client
echo -e "\n${YELLOW}Installing w3af-api-client...${NC}"
python3 -m pip install --user --no-deps git+https://github.com/andresriancho/w3af-api-client.git --break-system-packages || echo -e "${RED}Warning: Failed to install w3af-api-client${NC}"

# Install FTDI tools
echo -e "\n${YELLOW}Installing FTDI tools...${NC}"
apt-get install -y libftdi1 libftdi1-dev || \
    echo -e "${YELLOW}Warning: Failed to install FTDI libraries${NC}"
python3 -m pip install --user --no-deps pyftdi --break-system-packages || \
    echo -e "${YELLOW}Warning: Failed to install pyftdi${NC}"

# Note about peepdf
echo -e "\n${YELLOW}Note:${NC} peepdf is unmaintained and has compatibility issues with modern Python."
echo -e "Consider using alternatives like pdf-parser by Didier Stevens or other PDF analysis tools."


# Install udev rules for common hardware tools
echo -e "\n${YELLOW}Setting up udev rules...${NC}"

# Create udev rules directory if it doesn't exist
mkdir -p /etc/udev/rules.d/

# OpenOCD udev rules
cat > /etc/udev/rules.d/98-openocd.rules << 'EOL'
# ST-Link V1
ATTRS{idVendor}=="0483", ATTRS{idProduct}=="3744", MODE="660", GROUP="plugdev"
# ST-Link V2
ATTRS{idVendor}=="0483", ATTRS{idProduct}=="3748", MODE="660", GROUP="plugdev"
# J-Link
ATTRS{idVendor}=="1366", ATTRS{idProduct}=="0101", MODE="660", GROUP="plugdev"
# CMSIS-DAP
ATTRS{idVendor}=="c251", ATTRS{idProduct}=="f001", MODE="660", GROUP="plugdev"
# FTDI
ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6010", MODE="660", GROUP="plugdev"
# Bus Pirate
ATTRS{idVendor}=="04d8", ATTRS{idProduct}=="fb00", MODE="660", GROUP="plugdev"
# Bus Blaster
ATTRS{idVendor}=="04d8", ATTRS{idProduct}=="fc0f", MODE="660", GROUP="plugdev"
EOL

# Reload udev rules
echo -e "${YELLOW}Reloading udev rules...${NC}"
udevadm control --reload-rules || echo -e "${YELLOW}Warning: Failed to reload udev rules${NC}"
udevadm trigger || echo -e "${YELLOW}Warning: Failed to trigger udev events${NC}"

# Add user to required groups
echo -e "\n${YELLOW}Adding user to required groups...${NC}"
CURRENT_USER=${SUDO_USER:-$(whoami)}
usermod -a -G plugdev,dialout,video,usb,kvm "$CURRENT_USER" || echo -e "${YELLOW}Warning: Failed to add user to all groups${NC}"

echo -e "\n${GREEN}Installation complete!${NC}"
echo -e "Note: Some tools may require additional configuration or system setup."
echo -e "You may need to log out and back in for group changes to take effect.${NC}"

#!/bin/bash

# Exit on error
set -e

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root. Please use 'sudo' or run as root."
    exit 1
fi

# Install directory for the application
INSTALL_DIR="/opt/hack-attack"
BIN_DIR="/usr/local/bin"
POLICY_DIR="/usr/share/polkit-1/actions"
DESKTOP_DIR="/usr/share/applications"
ICON_DIR="/usr/share/icons/hicolor/256x256/apps"

# Create directories
mkdir -p "$INSTALL_DIR" "$ICON_DIR"

# Copy files
echo "Installing Hack Attack to $INSTALL_DIR..."
# Use rsync to exclude git directory and other unnecessary files
rsync -av --progress --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' . "$INSTALL_DIR/"

# Install icon
echo "Installing icon..."
cp "$INSTALL_DIR/Hack_Attack.png" "$ICON_DIR/hack-attack.png" 2>/dev/null || \
    { echo "Warning: Could not find Hack_Attack.png, using default icon"; 
      # Create a simple default icon if needed
      convert -size 256x256 xc:black -fill red -pointsize 72 -gravity center \
               -draw "text 0,0 'HA'" "$ICON_DIR/hack-attack.png"; }

# Install policy file
echo "Installing policy file..."
install -Dm644 "$INSTALL_DIR/data/hack-attack.policy" "$POLICY_DIR/org.hackattack.policy"

# Create desktop entry
echo "Creating desktop entry..."
cat > "$DESKTOP_DIR/hack-attack.desktop" <<EOL
[Desktop Entry]
Name=Hack Attack
Comment=Professional Security Testing Suite
Exec=pkexec $INSTALL_DIR/launch.py
Icon=hack-attack
Terminal=false
Type=Application
Categories=System;Security;Utility;
StartupNotify=true
EOL

# Create launcher script
echo "Creating launcher script..."
cat > "$BIN_DIR/hack-attack" <<EOL
#!/bin/bash
cd "$INSTALL_DIR"
python3 launch.py "$@"
EOL
chmod +x "$BIN_DIR/hack-attack"

echo "Installation complete! You can now run 'hack-attack' from the terminal or launch it from your applications menu.
echo "Note: You will be prompted for your password when launching the application to enable network capture features."

#!/bin/bash
# Build script for PC-X .deb package
# Bundles psutil, PySide6, and speedtest-cli — no pip install needed by the user.
# System tool dependencies are declared in Depends: and handled automatically by apt.
#
# Usage (from repo root or build/):
#   bash build/build-pc-x.sh
#
# Output: build/pc-x_<version>-1_amd64.deb

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
PCX_SRC="$REPO_ROOT/PC-X"
BUILD_DIR="$SCRIPT_DIR/deb/pc-x"
PKG_NAME="pc-x"
VERSION="0.1.0"
ARCH="amd64"

echo "==> Building PC-X .deb v${VERSION}..."

# ── Validate prerequisites ──────────────────────────────────────────────────
for tool in python3 dpkg-deb pip3; do
    if ! command -v "$tool" &>/dev/null; then
        echo "Error: '$tool' is required to build the package." >&2
        exit 1
    fi
done

# ── Clean previous build ────────────────────────────────────────────────────
rm -rf "$BUILD_DIR"
mkdir -p \
    "$BUILD_DIR/DEBIAN" \
    "$BUILD_DIR/usr/share/pc-x/icons" \
    "$BUILD_DIR/usr/bin" \
    "$BUILD_DIR/usr/share/applications" \
    "$BUILD_DIR/usr/share/pixmaps"

# ── Copy PC-X source ────────────────────────────────────────────────────────
echo "--> Copying source..."
cp -r "$PCX_SRC/app"             "$BUILD_DIR/usr/share/pc-x/"
cp -r "$PCX_SRC/core"            "$BUILD_DIR/usr/share/pc-x/"
cp -r "$PCX_SRC/tabs"            "$BUILD_DIR/usr/share/pc-x/"
cp -r "$PCX_SRC/ui"              "$BUILD_DIR/usr/share/pc-x/"
cp    "$PCX_SRC/pc_tools_linux.py" "$BUILD_DIR/usr/share/pc-x/"

# Remove test directories and __pycache__ to keep the package lean
find "$BUILD_DIR/usr/share/pc-x" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$BUILD_DIR/usr/share/pc-x" -type d -name "tests"       -exec rm -rf {} + 2>/dev/null || true

# Copy icon — install to hicolor theme tree for proper desktop integration
if [ -f "$REPO_ROOT/icons/pc-x.png" ]; then
    cp "$REPO_ROOT/icons/pc-x.png" "$BUILD_DIR/usr/share/pc-x/icons/pc-x.png"
    cp "$REPO_ROOT/icons/pc-x.png" "$BUILD_DIR/usr/share/pixmaps/pc-x.png"
    mkdir -p "$BUILD_DIR/usr/share/icons/hicolor/256x256/apps"
    cp "$REPO_ROOT/icons/pc-x.png" "$BUILD_DIR/usr/share/icons/hicolor/256x256/apps/pc-x.png"
fi

# ── Bundle Python venv ──────────────────────────────────────────────────────
echo "--> Creating bundled venv (this may take a few minutes — PySide6 is large)..."
VENV_DIR="$BUILD_DIR/usr/share/pc-x/venv"
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip --quiet
"$VENV_DIR/bin/pip" install psutil PySide6 speedtest-cli --quiet
echo "--> venv ready."

# Remove pip to slim the venv (not needed at runtime)
"$VENV_DIR/bin/pip" uninstall pip -y --quiet 2>/dev/null || true
find "$VENV_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# ── Launcher script ─────────────────────────────────────────────────────────
cat > "$BUILD_DIR/usr/bin/pc-x" <<'LAUNCHER'
#!/bin/bash
exec /usr/share/pc-x/venv/bin/python /usr/share/pc-x/app/main.py "$@"
LAUNCHER
chmod 755 "$BUILD_DIR/usr/bin/pc-x"

# ── DEBIAN/control ──────────────────────────────────────────────────────────
INSTALLED_SIZE=$(du -sk "$BUILD_DIR/usr" | awk '{print $1}')

cat > "$BUILD_DIR/DEBIAN/control" <<EOF
Package: ${PKG_NAME}
Version: ${VERSION}-1
Section: utils
Priority: optional
Architecture: ${ARCH}
Maintainer: Outback Electronics <outbackhutelectronics@gmail.com>
Depends: python3, smartmontools, lshw, pciutils, dmidecode, lm-sensors, parted, iw, ethtool, iputils-ping, ufw, policykit-1 | polkit, libcap2-bin, cron | cron-daemon
Installed-Size: ${INSTALLED_SIZE}
Description: Linux system management toolkit
 PC-X provides a dark-themed graphical interface for managing a Linux system.
 Sidebar navigation covers 20 areas including hardware diagnostics, package
 management, process control, systemd services, UFW firewall, SSH keys,
 kernel modules, cron scheduling, and more.
 .
 Python dependencies (PySide6, psutil, speedtest-cli) are bundled inside
 the package — no pip install required after installation.
EOF

# ── DEBIAN/postinst ─────────────────────────────────────────────────────────
cat > "$BUILD_DIR/DEBIAN/postinst" <<'EOF'
#!/bin/bash
set -e

cat > /usr/share/applications/pc-x.desktop <<DESKTOP
[Desktop Entry]
Name=PC-X
Comment=Linux System Management Toolkit
Exec=/usr/bin/pc-x
Icon=pc-x
Terminal=false
Type=Application
Categories=Utility;System;
Keywords=system;hardware;monitor;manager;
DESKTOP

chmod 644 /usr/share/applications/pc-x.desktop
update-desktop-database /usr/share/applications 2>/dev/null || true
gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true

exit 0
EOF
chmod 755 "$BUILD_DIR/DEBIAN/postinst"

# ── DEBIAN/prerm ────────────────────────────────────────────────────────────
cat > "$BUILD_DIR/DEBIAN/prerm" <<'EOF'
#!/bin/bash
set -e

rm -f /usr/share/applications/pc-x.desktop
update-desktop-database /usr/share/applications 2>/dev/null || true
gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true

exit 0
EOF
chmod 755 "$BUILD_DIR/DEBIAN/prerm"

# ── Build the .deb ──────────────────────────────────────────────────────────
OUTPUT_DEB="$SCRIPT_DIR/${PKG_NAME}_${VERSION}-1_${ARCH}.deb"
echo "--> Running dpkg-deb..."
dpkg-deb --build --root-owner-group "$BUILD_DIR" "$OUTPUT_DEB"

echo ""
echo "==> Done: $OUTPUT_DEB"
echo "    Size: $(du -sh "$OUTPUT_DEB" | awk '{print $1}')"
echo ""
echo "    Install:   sudo apt install \"$OUTPUT_DEB\""
echo "    Run:       pc-x"
echo "    Uninstall: sudo apt remove pc-x"

#!/bin/bash
set -e

# Build script for DROIDCOM deb package with bundled dependencies

VERSION="1.1.0"
BUILD_DIR="build/deb"
PACKAGE_NAME="droidcom"

echo "Building DROIDCOM deb package version ${VERSION}..."

# Clean previous build
rm -rf ${BUILD_DIR}
mkdir -p ${BUILD_DIR}

# Create package directory structure
mkdir -p ${BUILD_DIR}/${PACKAGE_NAME}/DEBIAN
mkdir -p ${BUILD_DIR}/${PACKAGE_NAME}/usr/bin
mkdir -p ${BUILD_DIR}/${PACKAGE_NAME}/usr/lib/${PACKAGE_NAME}
mkdir -p ${BUILD_DIR}/${PACKAGE_NAME}/usr/share/${PACKAGE_NAME}/icons
mkdir -p ${BUILD_DIR}/${PACKAGE_NAME}/usr/share/${PACKAGE_NAME}/ui/icons
mkdir -p ${BUILD_DIR}/${PACKAGE_NAME}/usr/share/applications

# Copy debian control files
cp DROIDCOM/debian/control ${BUILD_DIR}/${PACKAGE_NAME}/DEBIAN/
cp DROIDCOM/debian/postinst ${BUILD_DIR}/${PACKAGE_NAME}/DEBIAN/
cp DROIDCOM/debian/prerm ${BUILD_DIR}/${PACKAGE_NAME}/DEBIAN/
chmod +x ${BUILD_DIR}/${PACKAGE_NAME}/DEBIAN/postinst
chmod +x ${BUILD_DIR}/${PACKAGE_NAME}/DEBIAN/prerm

# Update control file with version
sed -i "s/^Package: droidcom$/Package: droidcom\nVersion: ${VERSION}-1/" ${BUILD_DIR}/${PACKAGE_NAME}/DEBIAN/control

# Create virtual environment and install dependencies
echo "Installing Python dependencies..."
python3 -m venv ${BUILD_DIR}/venv
source ${BUILD_DIR}/venv/bin/activate
pip install --upgrade pip

# Retry pip install with network error handling
MAX_RETRIES=3
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if pip install -r DROIDCOM/requirements.txt; then
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo "pip install failed (attempt $RETRY_COUNT/$MAX_RETRIES), retrying..."
        sleep 5
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "Failed to install dependencies after $MAX_RETRIES attempts"
    exit 1
fi

deactivate

# Copy application files
echo "Copying application files..."
cp -r DROIDCOM ${BUILD_DIR}/${PACKAGE_NAME}/usr/lib/${PACKAGE_NAME}/
cp icons/droidcom.png ${BUILD_DIR}/${PACKAGE_NAME}/usr/share/${PACKAGE_NAME}/icons/
cp -r DROIDCOM/ui/icons/*.svg ${BUILD_DIR}/${PACKAGE_NAME}/usr/share/${PACKAGE_NAME}/ui/icons/

# Copy virtual environment to package
echo "Bundling Python dependencies..."
cp -r ${BUILD_DIR}/venv/lib/python*/site-packages ${BUILD_DIR}/${PACKAGE_NAME}/usr/lib/${PACKAGE_NAME}/venv_site_packages

# Create launcher script
cat > ${BUILD_DIR}/${PACKAGE_NAME}/usr/bin/droidcom <<'EOF'
#!/bin/bash
export PYTHONPATH=/usr/lib/droidcom/venv_site_packages:/usr/lib/droidcom:$PYTHONPATH
python3 /usr/lib/droidcom/app/main.py "$@"
EOF
chmod +x ${BUILD_DIR}/${PACKAGE_NAME}/usr/bin/droidcom

# Create desktop entry
cat > ${BUILD_DIR}/${PACKAGE_NAME}/usr/share/applications/droidcom.desktop <<EOF
[Desktop Entry]
Name=DROIDCOM
Comment=Android Device Management Tool
Exec=/usr/bin/droidcom
Icon=/usr/share/droidcom/icons/droidcom.png
Terminal=false
Type=Application
Categories=Utility;System;
EOF

# Calculate installed size
INSTALLED_SIZE=$(du -sk ${BUILD_DIR}/${PACKAGE_NAME} | cut -f1)
echo "Installed-Size: ${INSTALLED_SIZE}" >> ${BUILD_DIR}/${PACKAGE_NAME}/DEBIAN/control

# Build the deb package
echo "Building deb package..."
dpkg-deb --build ${BUILD_DIR}/${PACKAGE_NAME} ${BUILD_DIR}/${PACKAGE_NAME}_${VERSION}-1_amd64.deb

echo "Package built successfully: ${BUILD_DIR}/${PACKAGE_NAME}_${VERSION}-1_amd64.deb"

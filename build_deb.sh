#!/usr/bin/env bash
set -e

# ==============================================================================
# Build Script for Preview macOS Linux .deb Package
# Developer: Shivam Prasad
# Powered by: TriviLabs.in
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

APP_NAME="preview-app"
VERSION="1.6.0"
ARCH="amd64"
PACKAGE_NAME="${APP_NAME}_${VERSION}_${ARCH}"
BUILD_DIR="$SCRIPT_DIR/build/deb/$PACKAGE_NAME"
DIST_DIR="$SCRIPT_DIR/dist"

echo "==> [1/5] Building standalone binary with PyInstaller..."
rm -rf "$DIST_DIR/preview-app"
pyinstaller --noconfirm --onedir --windowed \
    --name="preview-app" \
    --add-data "preview/assets:preview/assets" \
    --collect-all pymupdf \
    --hidden-import fitz \
    --hidden-import pymupdf \
    main.py


echo "==> [2/5] Creating Debian package structure..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/usr/bin"
mkdir -p "$BUILD_DIR/usr/lib/$APP_NAME"
mkdir -p "$BUILD_DIR/usr/share/applications"
mkdir -p "$BUILD_DIR/usr/share/icons/hicolor/256x256/apps"

echo "==> [3/5] Copying application binaries and assets..."
cp -a "$DIST_DIR/preview-app/." "$BUILD_DIR/usr/lib/$APP_NAME/"

# Executable launcher wrapper
cat << 'EOF' > "$BUILD_DIR/usr/bin/preview-app"
#!/bin/sh
exec /usr/lib/preview-app/preview-app "$@"
EOF
chmod 755 "$BUILD_DIR/usr/bin/preview-app"

# Application icon
cp "$SCRIPT_DIR/preview/assets/icon.png" "$BUILD_DIR/usr/share/icons/hicolor/256x256/apps/preview-app.png"

# Desktop Entry
cat << 'EOF' > "$BUILD_DIR/usr/share/applications/preview.desktop"
[Desktop Entry]
Name=Preview
GenericName=macOS Preview
Comment=macOS Document and Image Viewer for Linux
Exec=preview-app %F
Icon=preview-app
Terminal=false
Type=Application
Categories=Graphics;Office;Viewer;
MimeType=application/pdf;image/png;image/jpeg;image/webp;image/tiff;image/bmp;image/gif;
StartupNotify=true
StartupWMClass=Preview
EOF
chmod 644 "$BUILD_DIR/usr/share/applications/preview.desktop"

# Debian control file
INSTALLED_SIZE=$(du -ks "$BUILD_DIR/usr" | cut -f1)
cat << EOF > "$BUILD_DIR/DEBIAN/control"
Package: $APP_NAME
Version: $VERSION
Section: graphics
Priority: optional
Architecture: $ARCH
Installed-Size: $INSTALLED_SIZE
Maintainer: Shivam Prasad <info@trivilabs.in>
Homepage: https://trivilabs.in
Description: macOS Preview document and image viewer for Linux
 A pixel-faithful rebuild of Apple's macOS Preview for Linux.
 Features a unified 52px macOS toolbar, PDF navigation and search,
 multi-image galleries, vector markup annotations, color adjustment,
 and high-DPI rendering with authentic Dark and Light themes.
EOF

# postinst script
cat << 'EOF' > "$BUILD_DIR/DEBIAN/postinst"
#!/bin/sh
set -e
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q /usr/share/applications || true
fi
if command -v update-mime-database >/dev/null 2>&1; then
    update-mime-database /usr/share/mime || true
fi
exit 0
EOF
chmod 755 "$BUILD_DIR/DEBIAN/postinst"

# postrm script
cat << 'EOF' > "$BUILD_DIR/DEBIAN/postrm"
#!/bin/sh
set -e
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q /usr/share/applications || true
fi
if command -v update-mime-database >/dev/null 2>&1; then
    update-mime-database /usr/share/mime || true
fi
exit 0
EOF
chmod 755 "$BUILD_DIR/DEBIAN/postrm"

echo "==> [4/5] Building .deb package with dpkg-deb..."
dpkg-deb --build --root-owner-group "$BUILD_DIR" "$DIST_DIR/${PACKAGE_NAME}.deb"

echo "==> [5/5] Build Complete!"
echo "Package generated: $DIST_DIR/${PACKAGE_NAME}.deb"
dpkg-deb --info "$DIST_DIR/${PACKAGE_NAME}.deb"

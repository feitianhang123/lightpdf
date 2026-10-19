#!/usr/bin/env bash
# Build a Debian/Kylin .deb for 轻PDF编辑器 (Light PDF Editor).
# Tested layout: run ON the target machine (Kylin V10 SP1, aarch64/x86_64).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

PKG="lightpdf"
VER="1.0.1"
ARCH="$(dpkg --print-architecture)"      # arm64 on Phytium, amd64 on x86
APP_NAME="轻PDF编辑器"
ICON_SRC="packaging/linux/lightpdf.png"
[ -f "$ICON_SRC" ] || ICON_SRC="resources/icon.png"

echo "==> project : $ROOT"
echo "==> arch    : $ARCH"

command -v python3 >/dev/null 2>&1 || {
  echo "python3 not found. Run packaging/linux/install_deps.sh first."; exit 1; }

PYV="$(python3 -c 'import sys;print("%d.%d"%sys.version_info[:2])')"
echo "==> python  : $PYV"
case "$PYV" in
  3.8|3.9|3.10|3.11|3.12) : ;;
  *) echo "!! Python $PYV may be unsupported by PySide6 (need 3.8-3.12)." ;;
esac

echo "==> creating build venv"
rm -rf .venv-build
python3 -m venv .venv-build
# shellcheck disable=SC1091
. .venv-build/bin/activate
python -m pip install -U pip wheel setuptools

echo "==> installing Python dependencies"
pip install --prefer-binary PySide6 PyMuPDF Pillow numpy pyinstaller

SP="$(python -c 'import sysconfig;print(sysconfig.get_paths()["purelib"])')"
echo "==> site-packages: $SP"

echo "==> PyInstaller (onedir)"
rm -rf build dist
python -m PyInstaller --noconfirm --clean --windowed --onedir --name "$PKG" \
  --paths "$ROOT" \
  --add-data "icon.ico:." \
  --add-data "resources:resources" \
  --add-data "$SP/pymupdf:pymupdf" \
  --add-data "$SP/fitz:fitz" \
  --exclude-module pymupdf --exclude-module fitz \
  --exclude-module tkinter --exclude-module matplotlib --exclude-module PyQt5 \
  --exclude-module pandas --exclude-module scipy \
  run_app.py

echo "==> assembling .deb"
DEBROOT="build/deb/${PKG}_${VER}_${ARCH}"
rm -rf "$DEBROOT"
install -d "$DEBROOT/DEBIAN" \
           "$DEBROOT/opt/$PKG" \
           "$DEBROOT/usr/bin" \
           "$DEBROOT/usr/share/applications" \
           "$DEBROOT/usr/share/icons/hicolor/256x256/apps"
cp -a "dist/$PKG/." "$DEBROOT/opt/$PKG/"
[ -f "$ICON_SRC" ] && cp "$ICON_SRC" "$DEBROOT/usr/share/icons/hicolor/256x256/apps/$PKG.png"

cat > "$DEBROOT/usr/bin/$PKG" <<EOF
#!/bin/sh
exec "/opt/$PKG/$PKG" "\$@"
EOF
chmod 0755 "$DEBROOT/usr/bin/$PKG"

cat > "$DEBROOT/usr/share/applications/$PKG.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=$APP_NAME
Name[en]=Light PDF Editor
Comment=Light PDF Editor
Exec=$PKG %F
Icon=$PKG
Terminal=false
Categories=Office;Graphics;Viewer;
MimeType=application/pdf;
EOF
chmod 0644 "$DEBROOT/usr/share/applications/$PKG.desktop"

cat > "$DEBROOT/DEBIAN/control" <<EOF
Package: $PKG
Version: $VER
Section: utils
Priority: optional
Architecture: $ARCH
Maintainer: feitianhang123
Depends: libc6, libglib2.0-0, libgl1, libegl1, libxkbcommon0, libxkbcommon-x11-0, libxcb-icccm4, libxcb-image0, libxcb-keysyms1, libxcb-randr0, libxcb-render-util0, libxcb-shape0, libxcb-xinerama0, libxcb-xkb1, libdbus-1-3, libfontconfig1, libfreetype6, libxi6, libsm6, libice6
Description: Light PDF Editor ($APP_NAME)
 A trimmed PDF editor built with PyMuPDF + PySide6.
EOF

cat > "$DEBROOT/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database -q || true
command -v gtk-update-icon-cache >/dev/null 2>&1 && gtk-update-icon-cache -q -t /usr/share/icons/hicolor || true
exit 0
EOF
cat > "$DEBROOT/DEBIAN/postrm" <<'EOF'
#!/bin/sh
set -e
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database -q || true
exit 0
EOF
chmod 0755 "$DEBROOT/DEBIAN/postinst" "$DEBROOT/DEBIAN/postrm"

dpkg-deb --build --root-owner-group "$DEBROOT" "dist/${PKG}_${VER}_${ARCH}.deb"
echo
echo "==> DONE: dist/${PKG}_${VER}_${ARCH}.deb"
echo "    install : sudo dpkg -i dist/${PKG}_${VER}_${ARCH}.deb"
echo "    fix deps: sudo apt-get -f install"

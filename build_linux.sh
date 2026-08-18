#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Bắt đầu đóng gói ViTouch cho Linux (Fedora / Ubuntu / Arch / Wayland / X11)..."

# Ensure build dependencies
pip install --upgrade build pyinstaller 2>/dev/null || true

echo "🔨 Đang đóng gói ứng dụng bằng PyInstaller..."
pyinstaller --noconfirm --onedir --windowed \
    --name "ViTouch" \
    --paths "src" \
    --hidden-import "evdev" \
    --hidden-import "PyQt6" \
    --hidden-import "PyQt6.QtCore" \
    --hidden-import "PyQt6.QtGui" \
    --hidden-import "PyQt6.QtWidgets" \
    src/vitouch/app.py

echo "📋 Sao chép tài nguyên kèm theo..."
mkdir -p dist/ViTouch/profiles 2>/dev/null || true
cp -r profiles/* dist/ViTouch/profiles/ 2>/dev/null || true
cp README.md dist/ViTouch/ 2>/dev/null || true
cp setup.sh dist/ViTouch/ 2>/dev/null || true

echo "📦 Tạo file nén Release..."
cd dist
tar -czvf "ViTouch-v0.4.0-linux-x86_64.tar.gz" ViTouch
cd ..

echo "✅ Đóng gói hoàn tất!"
echo "📍 Thư mục binary: dist/ViTouch/ViTouch"
echo "🎁 File Release:   dist/ViTouch-v0.4.0-linux-x86_64.tar.gz"

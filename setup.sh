#!/usr/bin/env bash
# ==============================================================================
# ViTouch Setup & Installation Script (Fedora 44 / Ubuntu)
# ==============================================================================
set -e

echo "=========================================================="
echo "    ViTouch — Waydroid Gaming Keymapper Setup"
echo "=========================================================="

# 1. Detect Distribution & Install System Dependencies
if [ -f /etc/fedora-release ]; then
    echo "[+] Detected Fedora system. Installing dependencies..."
    sudo dnf install -y python3-gobject gtk4 gtk4-devel gtk4-layer-shell gtk4-layer-shell-devel python3-evdev python3-pip
elif [ -f /etc/debian_version ]; then
    echo "[+] Detected Ubuntu/Debian system. Installing dependencies..."
    sudo apt update
    sudo apt install -y python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-gtk4layershell-1.0 libgtk-4-dev libgtk4-layer-shell-dev python3-evdev python3-pip
else
    echo "[!] Unknown distribution. Please ensure GTK4, gtk4-layer-shell, and python3-evdev are installed."
fi

# 2. Permissions for /dev/input/ (Keyboard Capture)
echo "[+] Adding current user ($USER) to 'input' group..."
sudo usermod -aG input "$USER"

# 3. Permissions for /dev/uinput (Virtual Touchscreen)
echo "[+] Setting up udev rules for /dev/uinput..."
sudo bash -c 'cat <<EOF > /etc/udev/rules.d/99-vitouch-uinput.rules
KERNEL=="uinput", MODE="0660", GROUP="input", OPTIONS+="static_node=uinput"
EOF'

# Ensure uinput kernel module is loaded
sudo modprobe uinput || true
if ! grep -q "uinput" /etc/modules-load.d/uinput.conf 2>/dev/null; then
    echo "uinput" | sudo tee /etc/modules-load.d/uinput.conf > /dev/null || true
fi

sudo udevadm control --reload-rules
sudo udevadm trigger

# 4. Install Python project in editable mode
echo "[+] Installing ViTouch..."
pip install -e . --no-deps || pip install -e .

echo ""
echo "=========================================================="
echo "    Setup Complete!"
echo "=========================================================="
echo "LƯU Ý QUAN TRỌNG:"
echo "1. Nếu đây là lần đầu thêm vào nhóm 'input', bạn cần LOG OUT và LOG IN lại"
echo "   (hoặc chạy 'newgrp input') để quyền có hiệu lực."
echo "2. Khởi chạy ViTouch bằng lệnh: vitouch"
echo "   - F1: Bật Chế độ Chỉnh sửa (Kéo thả nút, thêm phím)"
echo "   - F2: Bật Chế độ Chơi (Xuyên thấu, hiện phím mờ)"
echo "   - F3: Ẩn / Hiện Overlay"
echo "=========================================================="

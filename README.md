# ViTouch 🎮✨

**ViTouch** là ứng dụng lớp phủ phím ảo cảm ứng trong suốt (**Ghost Overlay**) siêu nhẹ, hiệu năng cao dành cho các tựa game Android chạy trên **Waydroid / Linux (Wayland & X11)**. Được thiết kế và tối ưu hoá đặc biệt cho **TFT Mobile (Đấu Trường Chân Lý)**, **Liên Minh Tốc Chiến (Wild Rift)**, **Genshin Impact**, v.v.

---

## 🌟 Tính Năng Nổi Bật

- 👻 **100% Trong Suốt & Always-on-Top Kiên Cố**: Sử dụng cờ cửa sổ cấp thấp X11 Bypass Window Manager kết hợp XWayland, đảm bảo lớp phủ luôn nổi trên cửa sổ Waydroid mà không bao giờ bị ẩn hoặc gián đoạn khi click chuột.
- 🖱️ **Chuột Xuyên Thấu Tự Do (`F2 - Play Mode`)**: Di chuyển con trỏ chuột thật, nhặt đồ, di chuyển linh thú, sắp xếp tướng hoàn toàn độc lập mà không bị gián đoạn hay cản trở bởi phím ảo.
- ⚡ **Cảm Ứng Kernel Độc Lập (Pure Direct Touchscreen)**: Tích hợp trực tiếp với `/dev/uinput` và Multitouch Type B, phát tín hiệu chạm ảo chuẩn xác tại đúng toạ độ nút mà không làm ảnh hưởng đến vị trí con trỏ chuột thật.
- ⏱️ **Tùy Chỉnh Thời Gian Giữ Phím (Hold Duration)**: Điều khiển thời gian giữ chạm từ **20ms - 500ms** trực tiếp trên thanh công cụ HUD hoặc trong file cấu hình, phù hợp với từng engine game (Unity, Unreal).
- 🎨 **Thiết Kế Kính Mờ Tối Giản (Frosted Glass)**: Phím tròn xám nhạt tinh tế (`#E2E8F0`), không hiển thị nhãn phụ rườm rà.
- ⌨️ **Đổi Phím Trực Quan Siêu Nhanh (In-Place Quick Rebind)**: Click đúp vào bất kỳ phím ảo nào ở chế độ `F1` $\rightarrow$ ấn ngay phím trên bàn phím thật để gán mới tức thì.
- 📂 **Quản Lý Đa Profile Game**: Tạo, lưu và chuyển đổi mượt mà giữa các cấu hình phím cho nhiều game khác nhau (TFT Mobile, Tốc Chiến, Genshin Impact,...).
- 🚪 **Nút Thoát App Tiện Lợi**: Tích hợp sẵn nút thoát trực tiếp ngay trên thanh HUD của chế độ Chỉnh sửa (`F1`).

---

## 🚀 Hướng Dẫn Cài Đặt

### 1. Yêu Cầu Hệ Thống
- Hệ điều hành: Linux (Fedora, Ubuntu, Debian, Arch Linux, v.v.)
- Môi trường Desktop: GNOME Wayland, KDE Plasma Wayland, X11
- Python 3.10+
- Bộ giả lập Android: **Waydroid**

### 2. Cấp Quyền Truy Cập `/dev/uinput` (Một Lần Duy Nhất)
Để ViTouch có thể tạo thiết bị cảm ứng ảo và đọc bàn phím ở cấp Kernel:
```bash
sudo usermod -aG input $USER
echo 'KERNEL=="uinput", GROUP="input", MODE="0660"' | sudo tee /etc/udev/rules.d/99-uinput.rules
sudo udevadm control --reload-rules && sudo udevadm trigger
```
> **Lưu ý**: Sau khi chạy lệnh trên, vui lòng **Đăng xuất (Log out)** và đăng nhập lại để quyền `input` có hiệu lực.

### 3. Cài Đặt ViTouch
```bash
git clone https://github.com/namtacozz/ViTouch.git
cd ViTouch
pip install -e .
```

Hoặc chạy nhanh file cài đặt:
```bash
chmod +x setup.sh
./setup.sh
```

---

## 🎮 Hướng Dẫn Sử Dụng

### Khởi Chạy
```bash
vitouch
```

### ⌨️ Bảng Phím Tắt & Thao Tác

| Phím / Thao Tác | Chế Độ | Chức Năng |
| :--- | :---: | :--- |
| **`F1`** | **Toàn hệ thống** | Vào **Chế Độ Chỉnh Sửa** (Kéo thả nút, đổi phím, đổi profile, chỉnh độ trễ) |
| **`F2`** | **Toàn hệ thống** | Vào **Chế Độ Chơi** (Trong suốt 100%, Always-on-Top, chuột xuyên thấu) |
| **`F3`** | **Toàn hệ thống** | Ẩn / Hiện nhanh toàn bộ lớp phủ phím ảo |
| **Kéo Thả Chuột Trái** | `F1` (Edit) | Di chuyển phím ảo đến vị trí nút bấm tương ứng trong game |
| **Click Đúp vào Phím** | `F1` (Edit) | Bắt đầu đổi phím $\rightarrow$ Bấm 1 phím bất kỳ trên bàn phím thật để gán |
| **Click Đúp Vùng Trống** | `F1` (Edit) | Tạo thêm một phím ảo mới ngay tại vị trí trỏ chuột |
| **Rê Chuột vào Phím** | `F1` (Edit) | Hiển thị nút `✕` nhỏ màu đỏ ở góc để xóa phím |
| **⏱ Giữ: [ 120 ] ms** | `F1` (Edit) | Điều chỉnh thời gian giữ phím (20ms - 500ms) để game nhận lệnh mượt nhất |
| **💾 Lưu** | `F1` (Edit) | Lưu toàn bộ vị trí phím và thời gian giữ vào profile hiện tại |
| **✕ Thoát** | `F1` (Edit) | Đóng hoàn toàn ứng dụng ViTouch |

---

## ♟️ Cấu Hình Mặc Định Chuẩn TFT Mobile

| Phím | Chức Năng Trong Game |
| :---: | :--- |
| **`S`** | Mở / Đóng Cửa Hàng (Shop) |
| **`D`** | Làm Mới Cửa Hàng (Roll Shop) |
| **`E`** | Mua Kinh Nghiệm (Level Up / Mua EXP) |
| **`1` - `5`** | Mua Tướng Vị Trí 1 đến 5 trong Shop |
| **`TAB`** | Khóa Cửa Hàng (Lock Shop) |
| **`W`** | Bán Tướng (Sell Unit) |
| **`R`** | Chuyển Nhà Soi Bài (Scout Next Player) |

---

## 📦 Đóng Gói Binary Cho Linux

Bạn có thể tự đóng gói bản thực thi độc lập (Standalone Binary) không cần cài Python môi trường ngoài:
```bash
chmod +x build_linux.sh
./build_linux.sh
```
File đóng gói sẽ nằm tại: `dist/ViTouch-v0.4.0-linux-x86_64.tar.gz`.

---

## 📁 Thư Mục Cấu Hình JSON
Tất cả profile và toạ độ phím được lưu trữ dạng JSON rõ ràng tại:
```
~/.config/vitouch/profiles/
```

---

## 📜 Giấy Phép
Dự án được phân phối dưới giấy phép **MIT License**.

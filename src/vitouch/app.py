"""Main application controller for ViTouch using PyQt6."""

import os
import signal
import sys
from pathlib import Path
from typing import Optional

# Ensure XCB / XWayland is used on Wayland desktops for permanent Always-on-Top & Click-Through
if "QT_QPA_PLATFORM" not in os.environ and "WAYLAND_DISPLAY" in os.environ:
    os.environ["QT_QPA_PLATFORM"] = "xcb"

from PyQt6.QtCore import QTimer, pyqtSignal, QObject
from PyQt6.QtWidgets import QApplication

from vitouch.config import AppConfig, get_config_dir
from vitouch.editor import EditorOverlayWindow
from vitouch.input_capture import InputCapture
from vitouch.mapper import MappingEngine
from vitouch.overlay import PlayOverlayWindow
from vitouch.profile import (
    GameProfile,
    get_profiles_dir,
    load_or_init_default_profile,
)
from vitouch.touch_inject import TouchInjector


EVDEV_TO_DISPLAY = {
    "KEY_SPACE": "SPC",
    "KEY_TAB": "TAB",
    "KEY_ENTER": "ENT",
    "KEY_ESC": "ESC",
    "KEY_LEFTSHIFT": "SFT",
    "KEY_LEFTCTRL": "CTL",
    "KEY_LEFTALT": "ALT",
    "KEY_BACKSPACE": "BKSP",
}


class EventBridge(QObject):
    """Bridges background thread events to the Qt Main Thread safely."""
    key_activated = pyqtSignal(str)
    mode_changed = pyqtSignal(str)
    visibility_changed = pyqtSignal(bool)
    rebind_key_received = pyqtSignal(str)


class ViTouchApp:
    """ViTouch main application orchestrator."""

    def __init__(self):
        self.qt_app = QApplication.instance() or QApplication(sys.argv)
        self.config: AppConfig = AppConfig.load()
        self.profile: GameProfile = None
        self.touch_injector: Optional[TouchInjector] = None
        self.input_capture: Optional[InputCapture] = None
        self.mapping_engine: Optional[MappingEngine] = None
        self.play_overlay: Optional[PlayOverlayWindow] = None
        self.edit_overlay: Optional[EditorOverlayWindow] = None
        self.bridge = EventBridge()

    def run(self) -> int:
        """Start ViTouch overlay and run event loop."""
        # 1. Load active profile
        builtin_dir = Path(__file__).parent.parent.parent / "profiles"
        self.profile = load_or_init_default_profile(builtin_dir if builtin_dir.exists() else None)
        print(f"[ViTouch] Loaded profile: {self.profile.name} ({len(self.profile.bindings)} bindings)")

        # Query actual screen geometry
        screen = QApplication.primaryScreen()
        if screen:
            screen_geo = screen.geometry()
            scr_w = screen_geo.width()
            scr_h = screen_geo.height()
        else:
            scr_w = self.profile.resolution.width
        # 2. Sync profile resolution with actual screen geometry
        self.profile.resolution.width = scr_w
        self.profile.resolution.height = scr_h

        # 3. Init Touch Injector (Pro Touchscreen with Android & Unity compatibility)
        self.touch_injector = TouchInjector(
            screen_width=scr_w,
            screen_height=scr_h
        )

        # 3. Init Mapping Engine
        self.mapping_engine = MappingEngine(self.profile, self.touch_injector)

        # 4. Init Dedicated Play & Edit Overlay Windows
        self.play_overlay = PlayOverlayWindow(profile=self.profile)
        self.play_overlay.resize(scr_w, scr_h)

        self.edit_overlay = EditorOverlayWindow(profile=self.profile)
        self.edit_overlay.resize(scr_w, scr_h)

        # 5. Connect Signals
        self.bridge.key_activated.connect(self.play_overlay.pulse_button)
        self.bridge.mode_changed.connect(self._handle_mode_changed)
        self.bridge.visibility_changed.connect(self._handle_visibility_changed)
        self.bridge.rebind_key_received.connect(self._handle_rebind_key_event)

        self.edit_overlay.profile_saved.connect(self._save_active_profile)
        self.edit_overlay.profile_switched.connect(self._on_profile_switched)
        self.edit_overlay.mode_switched_to_play.connect(self.mapping_engine.set_play_mode)
        self.edit_overlay.app_quit_requested.connect(self.shutdown)

        # Connect MappingEngine callbacks to Qt Bridge
        self.mapping_engine.on_key_activated = lambda bid: self.bridge.key_activated.emit(bid)
        self.mapping_engine.on_mode_changed = lambda m: self.bridge.mode_changed.emit(m)
        self.mapping_engine.on_visibility_changed = lambda vis: self.bridge.visibility_changed.emit(vis)
        self.mapping_engine.on_rebind_key = lambda k: self.bridge.rebind_key_received.emit(k)

        # 6. Init and start Global Input Capture
        self.input_capture = InputCapture(
            target_device_path=self.config.keyboard_device_path or None
        )
        self.input_capture.on_key_down = lambda k: self.mapping_engine.handle_key_down(k)
        self.input_capture.on_key_up = lambda k: self.mapping_engine.handle_key_up(k)

        started = self.input_capture.start()
        if not started:
            print("[ViTouch] Warning: Keyboard capture could not start. Check permissions in /dev/input/")

        # Show Play Overlay by default
        self.play_overlay.show()
        self.play_overlay.raise_()

        print("=================================================================")
        print("[ViTouch v0.4 Ghost Overlay] Sẵn sàng hoạt động!")
        print("  - F1: Chế độ Chỉnh sửa (Đổi Profile, Kéo thả, Click đúp đổi phím, Nút Thoát)")
        print("  - F2: Chế độ Chơi (Nền trong suốt 100%, Always-on-Top, Chuột xuyên thấu tự do)")
        print("  - F3: Ẩn / Hiện Overlay")
        print("=================================================================")

        # Handle Ctrl+C gracefully
        signal.signal(signal.SIGINT, lambda *args: self.shutdown())

        # Keep Python interpreter checking for signals
        timer = QTimer()
        timer.timeout.connect(lambda: None)
        timer.start(500)

        ret = self.qt_app.exec()
        self.shutdown()
        return ret

    def _handle_mode_changed(self, mode: str):
        if mode == "edit":
            self.play_overlay.hide()
            self.edit_overlay.load_profile(self.profile)
            self.edit_overlay.show()
            self.edit_overlay.raise_()
        else:
            self.edit_overlay.hide()
            self.play_overlay.reload_profile(self.profile)
            self.play_overlay.show()
            self.play_overlay.raise_()

    def _handle_visibility_changed(self, visible: bool):
        if self.mapping_engine.edit_mode:
            self.edit_overlay.setVisible(visible)
        else:
            self.play_overlay.setVisible(visible)

    def _handle_rebind_key_event(self, evdev_key: str):
        """Handle rebind key triggered from global evdev capture."""
        disp_char = EVDEV_TO_DISPLAY.get(evdev_key, evdev_key.removeprefix("KEY_"))
        self.edit_overlay.handle_rebind_key(evdev_key, disp_char)

    def _on_profile_switched(self, new_profile: GameProfile):
        if self.touch_injector:
            new_profile.resolution.width = self.touch_injector.screen_width
            new_profile.resolution.height = self.touch_injector.screen_height
        self.profile = new_profile
        self.mapping_engine.set_profile(new_profile)
        self.play_overlay.reload_profile(new_profile)

    def _save_active_profile(self, profile: GameProfile):
        if self.touch_injector:
            profile.resolution.width = self.touch_injector.screen_width
            profile.resolution.height = self.touch_injector.screen_height
        safe_name = profile.name.lower().replace(" ", "_")
        save_path = get_profiles_dir() / f"{safe_name}.json"
        profile.save(save_path)
        self.profile = profile
        self.mapping_engine.set_profile(profile)
        self.play_overlay.reload_profile(profile)
        print(f"[ViTouch] Đã lưu cấu hình profile vào {save_path}")

    def shutdown(self):
        """Clean up background threads and devices."""
        print("[ViTouch] Shutting down...")
        if self.input_capture:
            self.input_capture.stop()
        if self.touch_injector:
            self.touch_injector.close()
        if self.play_overlay:
            self.play_overlay.hide()
        if self.edit_overlay:
            self.edit_overlay.hide()
        if self.qt_app:
            self.qt_app.quit()

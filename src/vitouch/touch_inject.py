"""Direct Android/Waydroid touchscreen input injection using Linux uinput."""

import os
import threading
import time
from typing import Optional

try:
    import evdev
    from evdev import UInput, AbsInfo, ecodes as e
    HAVE_EVDEV = True
except ImportError:
    HAVE_EVDEV = False


class TouchInjector:
    """Manages pure multi-touch event injection into Linux kernel, Waydroid, and Android game engines."""

    def __init__(self, screen_width: int = 1366, screen_height: int = 768):
        self.screen_width = max(640, int(screen_width))
        self.screen_height = max(480, int(screen_height))
        self.uinput_device: Optional[UInput] = None
        self._tracking_id_counter = 1
        self._lock = threading.Lock()
        self._active_slots = {}

        self._init_uinput()

    def _init_uinput(self) -> None:
        """Create a dedicated direct multi-touch touchscreen device via /dev/uinput."""
        if not HAVE_EVDEV:
            print("[TouchInject] evdev library not available.")
            return

        try:
            # Pure Direct Touchscreen (Multitouch Type B + Pressure + Touch Major)
            cap = {
                e.EV_KEY: [e.BTN_TOUCH],
                e.EV_ABS: [
                    (e.ABS_MT_SLOT, AbsInfo(value=0, min=0, max=9, fuzz=0, flat=0, resolution=0)),
                    (e.ABS_MT_TRACKING_ID, AbsInfo(value=0, min=0, max=65535, fuzz=0, flat=0, resolution=0)),
                    (e.ABS_MT_POSITION_X, AbsInfo(value=0, min=0, max=self.screen_width, fuzz=0, flat=0, resolution=0)),
                    (e.ABS_MT_POSITION_Y, AbsInfo(value=0, min=0, max=self.screen_height, fuzz=0, flat=0, resolution=0)),
                    (e.ABS_MT_PRESSURE, AbsInfo(value=0, min=0, max=255, fuzz=0, flat=0, resolution=0)),
                    (e.ABS_MT_TOUCH_MAJOR, AbsInfo(value=0, min=0, max=255, fuzz=0, flat=0, resolution=0)),
                    (e.ABS_X, AbsInfo(value=0, min=0, max=self.screen_width, fuzz=0, flat=0, resolution=0)),
                    (e.ABS_Y, AbsInfo(value=0, min=0, max=self.screen_height, fuzz=0, flat=0, resolution=0)),
                    (e.ABS_PRESSURE, AbsInfo(value=0, min=0, max=255, fuzz=0, flat=0, resolution=0)),
                ],
            }

            # Direct input property so Android & Waydroid treat it as an authentic Touchscreen
            props = [e.INPUT_PROP_DIRECT] if hasattr(e, 'INPUT_PROP_DIRECT') else []

            self.uinput_device = UInput(
                cap,
                input_props=props,
                name="ViTouch Direct Touchscreen",
                bustype=e.BUS_VIRTUAL,
                vendor=0x1234,
                product=0x5678,
                version=1
            )
            print(f"[TouchInject] Virtual direct touchscreen ready: {self.screen_width}x{self.screen_height}")
        except Exception as ex:
            print(f"[TouchInject] Failed to initialize uinput device: {ex}")

    def set_resolution(self, width: int, height: int) -> None:
        """Update target resolution and reinitialize device."""
        if self.screen_width != width or self.screen_height != height:
            self.screen_width = max(640, int(width))
            self.screen_height = max(480, int(height))
            if self.uinput_device:
                try:
                    self.uinput_device.close()
                except Exception:
                    pass
                self.uinput_device = None
            self._init_uinput()

    def _next_tracking_id(self) -> int:
        self._tracking_id_counter = (self._tracking_id_counter + 1) % 65500 + 1
        return self._tracking_id_counter

    def touch_down(self, x: int, y: int, slot: int = 0) -> None:
        """Simulate finger touch down at coordinate (x, y) without disturbing physical mouse."""
        x = max(0, min(self.screen_width, int(x)))
        y = max(0, min(self.screen_height, int(y)))

        with self._lock:
            if self.uinput_device:
                try:
                    tid = self._next_tracking_id()
                    self._active_slots[slot] = tid

                    # Multitouch Type B events
                    self.uinput_device.write(e.EV_ABS, e.ABS_MT_SLOT, slot)
                    self.uinput_device.write(e.EV_ABS, e.ABS_MT_TRACKING_ID, tid)
                    self.uinput_device.write(e.EV_ABS, e.ABS_MT_POSITION_X, x)
                    self.uinput_device.write(e.EV_ABS, e.ABS_MT_POSITION_Y, y)
                    self.uinput_device.write(e.EV_ABS, e.ABS_MT_PRESSURE, 100)
                    self.uinput_device.write(e.EV_ABS, e.ABS_MT_TOUCH_MAJOR, 30)

                    # Single Touch fallback coordinates
                    self.uinput_device.write(e.EV_ABS, e.ABS_X, x)
                    self.uinput_device.write(e.EV_ABS, e.ABS_Y, y)
                    self.uinput_device.write(e.EV_ABS, e.ABS_PRESSURE, 100)

                    # BTN_TOUCH only (leaves mouse cursor intact for hero movement)
                    self.uinput_device.write(e.EV_KEY, e.BTN_TOUCH, 1)
                    self.uinput_device.syn()
                except Exception as ex:
                    print(f"[TouchInject] Error during touch_down: {ex}")

    def touch_up(self, slot: int = 0) -> None:
        """Simulate finger release."""
        with self._lock:
            if self.uinput_device:
                try:
                    self.uinput_device.write(e.EV_ABS, e.ABS_MT_SLOT, slot)
                    self.uinput_device.write(e.EV_ABS, e.ABS_MT_TRACKING_ID, -1)
                    self.uinput_device.write(e.EV_ABS, e.ABS_MT_PRESSURE, 0)
                    self.uinput_device.write(e.EV_ABS, e.ABS_PRESSURE, 0)
                    self.uinput_device.write(e.EV_KEY, e.BTN_TOUCH, 0)
                    self.uinput_device.syn()
                    self._active_slots.pop(slot, None)
                except Exception as ex:
                    print(f"[TouchInject] Error during touch_up: {ex}")

    def tap(self, x: int, y: int, duration_ms: int = 120) -> None:
        """Perform a natural tap gesture at (x, y)."""
        def _execute_tap():
            if self.uinput_device:
                self.touch_down(x, y, slot=0)
                time.sleep(max(100, duration_ms) / 1000.0)
                self.touch_up(slot=0)

        threading.Thread(target=_execute_tap, daemon=True).start()

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 250, steps: int = 15) -> None:
        """Perform a swipe gesture from (x1, y1) to (x2, y2)."""
        def _execute_swipe():
            if self.uinput_device:
                self.touch_down(x1, y1, slot=0)
                interval = (duration_ms / 1000.0) / max(steps, 1)
                for step in range(1, steps + 1):
                    cur_x = int(x1 + (x2 - x1) * (step / steps))
                    cur_y = int(y1 + (y2 - y1) * (step / steps))
                    with self._lock:
                        if self.uinput_device:
                            self.uinput_device.write(e.EV_ABS, e.ABS_MT_SLOT, 0)
                            self.uinput_device.write(e.EV_ABS, e.ABS_MT_POSITION_X, cur_x)
                            self.uinput_device.write(e.EV_ABS, e.ABS_MT_POSITION_Y, cur_y)
                            self.uinput_device.write(e.EV_ABS, e.ABS_MT_PRESSURE, 100)
                            self.uinput_device.write(e.EV_ABS, e.ABS_X, cur_x)
                            self.uinput_device.write(e.EV_ABS, e.ABS_Y, cur_y)
                            self.uinput_device.write(e.EV_ABS, e.ABS_PRESSURE, 100)
                            self.uinput_device.syn()
                    time.sleep(interval)
                self.touch_up(slot=0)

        threading.Thread(target=_execute_swipe, daemon=True).start()

    def close(self) -> None:
        """Clean up uinput device."""
        with self._lock:
            if self.uinput_device:
                try:
                    self.uinput_device.close()
                except Exception:
                    pass
                self.uinput_device = None
